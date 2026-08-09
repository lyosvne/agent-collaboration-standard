from __future__ import annotations

import fcntl
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "aetheris-governance-sync-public"
SPEC = importlib.util.spec_from_loader(
    "governance_sync_public_release",
    SourceFileLoader("governance_sync_public_release", str(MODULE_PATH)),
)
assert SPEC and SPEC.loader
public = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = public
SPEC.loader.exec_module(public)


class ArgumentsAndTransportTests(unittest.TestCase):
    def test_exact_cli_and_isolated_interpreter(self) -> None:
        self.assertEqual("#!/usr/bin/python3 -I", MODULE_PATH.read_text().splitlines()[0])
        commit = "a" * 40
        self.assertEqual(
            public.Request(commit, True),
            public.parse_args(["--commit", commit, "--dry-run"]),
        )
        self.assertEqual(
            public.Request(commit, False),
            public.parse_args(["--commit", commit, "--apply"]),
        )
        for argv in (
            ["--commit", commit],
            ["--commit", commit, "--dry-run", "--apply"],
            ["--commit", "A" * 40, "--apply"],
            ["--commit", commit, "--app"],
            ["--commit", commit, "--apply", "extra"],
            ["--help"],
        ):
            with self.subTest(argv=argv), self.assertRaises(public.SyncError) as caught:
                public.parse_args(argv)
            self.assertEqual("invalid_arguments", caught.exception.code)

    def test_refuses_root_and_sanitizes_cli_error(self) -> None:
        with (
            mock.patch.object(public.os, "geteuid", return_value=0),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.establish_process_security()
        self.assertEqual("root_execution_forbidden", caught.exception.code)

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(1, public.main(["--help"]))
        self.assertEqual(
            {"status": "error", "error_code": "invalid_arguments"},
            json.loads(stderr.getvalue()),
        )

    def test_curl_uses_only_fixed_api_https_limits_and_sanitized_environment(self) -> None:
        completed = subprocess.CompletedProcess([], 0, b"", b"")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "metadata"

            def create_output(argv, **kwargs):
                destination.write_bytes(b"{}")
                return completed

            with (
                mock.patch.dict(
                    os.environ,
                    {
                        "GITHUB_TOKEN": "secret",
                        "HTTPS_PROXY": "https://attacker.invalid",
                        "CURL_HOME": "/secret",
                    },
                    clear=False,
                ),
                mock.patch.object(
                    public.subprocess, "run", side_effect=create_output
                ) as run,
            ):
                public.download(
                    f"{public.RELEASE_API_BASE}/releases/tags/governance-sync-v2-{'a' * 40}",
                    destination,
                    public.MAX_METADATA_BYTES,
                    asset=False,
                )
        argv = run.call_args.args[0]
        kwargs = run.call_args.kwargs
        self.assertEqual("/usr/bin/curl", argv[0])
        for required in (
            "--disable",
            "--proto",
            "=https",
            "--proto-redir",
            "--max-filesize",
            "--connect-timeout",
            "--max-time",
            "--proxy",
        ):
            self.assertIn(required, argv)
        self.assertEqual("", argv[argv.index("--proxy") + 1])
        self.assertNotIn("secret", json.dumps(kwargs["env"]))
        self.assertNotIn("TOKEN", json.dumps(kwargs["env"]))
        self.assertEqual("/nonexistent", kwargs["env"]["HOME"])
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertFalse(kwargs["shell"])
        self.assertEqual(public.CURL_TIMEOUT_SECONDS + 5, kwargs["timeout"])

    def test_curl_rejects_nonfixed_url_timeout_failure_and_oversize(self) -> None:
        with self.assertRaises(public.SyncError) as caught:
            public.download(
                "https://example.invalid/asset", Path("/tmp/not-used"), 1, asset=True
            )
        self.assertEqual("download_url_invalid", caught.exception.code)

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "asset"
            with (
                mock.patch.object(
                    public.subprocess,
                    "run",
                    side_effect=subprocess.TimeoutExpired(["curl"], 1),
                ),
                self.assertRaises(public.SyncError) as caught,
            ):
                public.download(
                    f"{public.RELEASE_API_BASE}/releases/assets/1",
                    destination,
                    1,
                    asset=True,
                )
            self.assertEqual("download_failed", caught.exception.code)

            def oversize(argv, **kwargs):
                destination.write_bytes(b"xx")
                return subprocess.CompletedProcess([], 0, b"", b"")

            with (
                mock.patch.object(public.subprocess, "run", side_effect=oversize),
                self.assertRaises(public.SyncError) as caught,
            ):
                public.download(
                    f"{public.RELEASE_API_BASE}/releases/assets/1",
                    destination,
                    1,
                    asset=True,
                )
            self.assertEqual("download_size_invalid", caught.exception.code)


class MetadataAndManifestTests(unittest.TestCase):
    COMMIT = "a" * 40

    def release(self) -> dict[str, object]:
        return {
            "tag_name": f"governance-sync-v2-{self.COMMIT}",
            "target_commitish": self.COMMIT,
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "html_url": "https://attacker.invalid/release",
            "assets": [
                {
                    "name": public.MANIFEST_NAME,
                    "id": 101,
                    "size": 100,
                    "url": "https://attacker.invalid/manifest",
                    "browser_download_url": "file:///etc/passwd",
                },
                {
                    "name": public.BUNDLE_NAME,
                    "id": 202,
                    "size": 200,
                    "url": "https://attacker.invalid/bundle",
                },
                {"name": "ignored", "id": 303, "size": 1},
            ],
        }

    def test_trusts_only_release_identity_and_asset_name_id_size(self) -> None:
        assets = public.parse_release_metadata(self.release(), self.COMMIT)
        self.assertEqual(
            f"{public.RELEASE_API_BASE}/releases/assets/101",
            public.asset_api_url(assets[public.MANIFEST_NAME]),
        )
        self.assertEqual(
            f"{public.RELEASE_API_BASE}/releases/assets/202",
            public.asset_api_url(assets[public.BUNDLE_NAME]),
        )
        self.assertNotIn("attacker", public.asset_api_url(assets[public.BUNDLE_NAME]))

    def test_rejects_wrong_identity_duplicate_missing_and_invalid_assets(self) -> None:
        cases = []
        wrong_tag = self.release()
        wrong_tag["tag_name"] = "other"
        cases.append(wrong_tag)
        wrong_target = self.release()
        wrong_target["target_commitish"] = "b" * 40
        cases.append(wrong_target)
        draft = self.release()
        draft["draft"] = True
        cases.append(draft)
        prerelease = self.release()
        prerelease["prerelease"] = True
        cases.append(prerelease)
        mutable = self.release()
        mutable["immutable"] = False
        cases.append(mutable)
        missing_immutable = self.release()
        del missing_immutable["immutable"]
        cases.append(missing_immutable)
        missing = self.release()
        missing["assets"] = missing["assets"][:1]
        cases.append(missing)
        duplicate = self.release()
        duplicate["assets"] = duplicate["assets"] + [duplicate["assets"][0]]
        cases.append(duplicate)
        boolean_id = self.release()
        boolean_id["assets"][0]["id"] = True
        cases.append(boolean_id)
        oversize = self.release()
        oversize["assets"][1]["size"] = public.MAX_BUNDLE_BYTES + 1
        cases.append(oversize)
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(public.SyncError):
                public.parse_release_metadata(payload, self.COMMIT)

    def test_manifest_requires_exact_schema_commit_name_size_and_sha(self) -> None:
        digest = "b" * 64
        valid = {
            "bundle": {
                "name": public.BUNDLE_NAME,
                "sha256": digest,
                "size": 123,
            },
            "commit": self.COMMIT,
            "base_commit": public.BASE_COMMIT,
            "bundle_kind": "incremental",
            "schema_version": 2,
        }
        self.assertEqual(
            public.Manifest(self.COMMIT, 123, digest),
            public.parse_manifest(valid, self.COMMIT),
        )
        invalid = (
            {**valid, "extra": True},
            {**valid, "commit": "c" * 40},
            {**valid, "schema_version": 1},
            {**valid, "base_commit": "c" * 40},
            {**valid, "bundle_kind": "full"},
            {**valid, "bundle": {**valid["bundle"], "name": "../bundle"}},
            {**valid, "bundle": {**valid["bundle"], "size": True}},
            {**valid, "bundle": {**valid["bundle"], "sha256": "B" * 64}},
        )
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(public.SyncError) as caught:
                public.parse_manifest(payload, self.COMMIT)
            self.assertEqual("manifest_schema_invalid", caught.exception.code)

    def test_json_duplicate_keys_and_bundle_size_hash_faults_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            duplicate = root / "duplicate.json"
            duplicate.write_text('{"commit":"a","commit":"b"}', encoding="utf-8")
            with self.assertRaises(public.SyncError):
                public.read_json(duplicate, 100, "manifest_schema_invalid")

            bundle = root / "bundle"
            bundle.write_bytes(b"trusted")
            digest = hashlib.sha256(b"trusted").hexdigest()
            public.validate_downloaded_asset(bundle, 7, digest)
            with self.assertRaises(public.SyncError) as caught:
                public.validate_downloaded_asset(bundle, 8, digest)
            self.assertEqual("bundle_size_mismatch", caught.exception.code)
            with self.assertRaises(public.SyncError) as caught:
                public.validate_downloaded_asset(bundle, 7, "0" * 64)
            self.assertEqual("bundle_sha256_mismatch", caught.exception.code)


class PublishCleanupAndRelayTests(unittest.TestCase):
    COMMIT = "a" * 40

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.incoming = self.root / "incoming"
        self.incoming.mkdir(mode=0o700)
        self.incoming.chmod(0o700)
        self.patch = mock.patch.multiple(
            public,
            INCOMING=self.incoming,
            BUNDLE=self.incoming / public.BUNDLE_NAME,
        )
        self.patch.start()

    def tearDown(self) -> None:
        self.patch.stop()
        self.temporary.cleanup()

    def test_atomically_publishes_fixed_bundle_and_finally_removes_own_inode(self) -> None:
        source = self.root / "download"
        source.write_bytes(b"release bundle")
        directory_fd, identity = public.publish_bundle(source)
        bundle = self.incoming / public.BUNDLE_NAME
        self.assertEqual(b"release bundle", bundle.read_bytes())
        self.assertEqual(0o600, stat.S_IMODE(bundle.stat().st_mode))
        self.assertEqual(identity, (bundle.stat().st_dev, bundle.stat().st_ino))
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())
        self.assertEqual(
            "clean", public.cleanup_published_bundle(directory_fd, identity)
        )
        self.assertFalse(bundle.exists())

    def test_publish_rejects_symlink_and_cleans_staging_on_copy_fault(self) -> None:
        outside = self.root / "outside"
        outside.write_bytes(b"outside")
        (self.incoming / public.BUNDLE_NAME).symlink_to(outside)
        source = self.root / "download"
        source.write_bytes(b"release")
        with self.assertRaises(public.SyncError) as caught:
            public.publish_bundle(source)
        self.assertEqual("bundle_unsafe", caught.exception.code)
        self.assertEqual(b"outside", outside.read_bytes())
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())

    def test_publish_preserves_preexisting_staging_collision(self) -> None:
        staging = self.incoming / public.STAGING_NAME
        staging.write_bytes(b"preexisting")
        staging.chmod(0o600)
        source = self.root / "download"
        source.write_bytes(b"release")
        with self.assertRaises(public.SyncError) as caught:
            public.publish_bundle(source)
        self.assertEqual("incoming_busy", caught.exception.code)
        self.assertEqual(b"preexisting", staging.read_bytes())
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())

    def test_publish_preserves_preexisting_valid_bundle_inode(self) -> None:
        bundle = self.incoming / public.BUNDLE_NAME
        bundle.write_bytes(b"preexisting")
        bundle.chmod(0o600)
        identity = (bundle.stat().st_dev, bundle.stat().st_ino)
        source = self.root / "download"
        source.write_bytes(b"release")
        with self.assertRaises(public.SyncError) as caught:
            public.publish_bundle(source)
        self.assertEqual("incoming_busy", caught.exception.code)
        self.assertEqual(identity, (bundle.stat().st_dev, bundle.stat().st_ino))
        self.assertEqual(b"preexisting", bundle.read_bytes())
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())

    def test_publish_cleans_its_staging_inode_after_copy_fault(self) -> None:
        source = self.root / "download-directory"
        source.mkdir()
        with self.assertRaises(public.SyncError) as caught:
            public.publish_bundle(source)
        self.assertEqual("bundle_publish_failed", caught.exception.code)
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())

    def test_post_rename_fsync_fault_removes_published_bundle(self) -> None:
        source = self.root / "download"
        source.write_bytes(b"release")
        real_fsync = os.fsync
        failed = False

        def fail_first_directory_fsync(fd: int) -> None:
            nonlocal failed
            if stat.S_ISDIR(os.fstat(fd).st_mode) and not failed:
                failed = True
                raise OSError("injected directory fsync failure")
            real_fsync(fd)

        with (
            mock.patch.object(public.os, "fsync", side_effect=fail_first_directory_fsync),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.publish_bundle(source)
        self.assertEqual("bundle_publish_failed", caught.exception.code)
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())

    def test_replace_mutates_then_raises_removes_only_created_inode(self) -> None:
        source = self.root / "download"
        source.write_bytes(b"release")
        real_replace = os.replace

        def mutate_then_raise(*args, **kwargs) -> None:
            real_replace(*args, **kwargs)
            raise OSError("injected replace failure")

        with (
            mock.patch.object(public.os, "replace", side_effect=mutate_then_raise),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.publish_bundle(source)
        self.assertEqual("bundle_publish_failed", caught.exception.code)
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())

    def test_cleanup_never_unlinks_replaced_bundle_inode(self) -> None:
        source = self.root / "download"
        source.write_bytes(b"release")
        directory_fd, identity = public.publish_bundle(source)
        replacement = self.incoming / "replacement"
        replacement.write_bytes(b"replacement")
        replacement.chmod(0o600)
        os.replace(replacement, self.incoming / public.BUNDLE_NAME)
        self.assertEqual(
            "state-unknown",
            public.cleanup_published_bundle(directory_fd, identity),
        )
        self.assertEqual(
            b"replacement", (self.incoming / public.BUNDLE_NAME).read_bytes()
        )

    def test_cleanup_reports_pending_for_unlink_and_unknown_for_fsync(self) -> None:
        source = self.root / "download"
        source.write_bytes(b"release")
        directory_fd, identity = public.publish_bundle(source)
        with mock.patch.object(
            public.os, "unlink", side_effect=OSError("injected unlink failure")
        ):
            self.assertEqual(
                "pending",
                public.cleanup_published_bundle(directory_fd, identity),
            )
        self.assertTrue((self.incoming / public.BUNDLE_NAME).exists())

        os.unlink(self.incoming / public.BUNDLE_NAME)
        directory_fd, identity = public.publish_bundle(source)
        with mock.patch.object(
            public.os, "fsync", side_effect=OSError("injected fsync failure")
        ):
            self.assertEqual(
                "state-unknown",
                public.cleanup_published_bundle(directory_fd, identity),
            )
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())

    def test_bundle_helper_uses_fixed_argv_closed_stdin_and_relays_exact_json(self) -> None:
        request = public.Request(self.COMMIT, True)
        digest = "b" * 64
        payload = {
            "status": "dry-run",
            "commit": self.COMMIT,
            "sha256": digest,
            "before_commit": "c" * 40,
            "would_change": True,
        }
        completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
        with mock.patch.object(public.subprocess, "run", return_value=completed) as run:
            self.assertEqual((0, payload), public.run_bundle_helper(request, digest))
        self.assertEqual(
            [
                "/usr/local/sbin/aetheris-governance-sync",
                "--bundle",
                str(self.incoming / public.BUNDLE_NAME),
                "--commit",
                self.COMMIT,
                "--sha256",
                digest,
                "--dry-run",
            ],
            run.call_args.args[0],
        )
        self.assertIs(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertNotIn("GITHUB", json.dumps(run.call_args.kwargs["env"]))

    def test_helper_attack_responses_and_faults_are_not_relayed(self) -> None:
        request = public.Request(self.COMMIT, False)
        for completed in (
            subprocess.CompletedProcess([], 0, '{"status":"applied","url":"leak"}', ""),
            subprocess.CompletedProcess([], 1, "", "traceback secret"),
            subprocess.CompletedProcess(
                [], 1, "", '{"status":"error","error_code":"safe"}\n{"leak":1}'
            ),
        ):
            with (
                self.subTest(completed=completed),
                mock.patch.object(public.subprocess, "run", return_value=completed),
                self.assertRaises(public.SyncError),
            ):
                public.run_bundle_helper(request, "b" * 64)

    def test_synchronize_uses_constructed_asset_urls_and_cleans_after_relay(self) -> None:
        commit = self.COMMIT
        content = b"complete bundle"
        digest = hashlib.sha256(content).hexdigest()
        release = {
            "tag_name": f"governance-sync-v2-{commit}",
            "target_commitish": commit,
            "draft": False,
            "prerelease": False,
            "immutable": True,
            "assets": [
                {"name": public.MANIFEST_NAME, "id": 11, "size": 1},
                {"name": public.BUNDLE_NAME, "id": 22, "size": len(content)},
            ],
        }
        manifest = {
            "bundle": {
                "name": public.BUNDLE_NAME,
                "size": len(content),
                "sha256": digest,
            },
            "commit": commit,
            "base_commit": public.BASE_COMMIT,
            "bundle_kind": "incremental",
            "schema_version": 2,
        }
        manifest_bytes = (
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        release["assets"][0]["size"] = len(manifest_bytes)
        urls: list[str] = []

        def fake_download(url: str, destination: Path, maximum: int, *, asset: bool):
            urls.append(url)
            if "/releases/tags/" in url:
                destination.write_text(json.dumps(release), encoding="utf-8")
            elif url.endswith("/11"):
                destination.write_bytes(manifest_bytes)
            elif url.endswith("/22"):
                destination.write_bytes(content)
            else:
                raise AssertionError(url)

        relay = {
            "status": "no-op",
            "commit": commit,
            "before_commit": commit,
            "backup_ref": None,
        }
        expected = {**relay, "source_cleanup": "clean"}
        with (
            mock.patch.object(public, "download", side_effect=fake_download),
            mock.patch.object(
                public,
                "rebuild_full_bundle",
                side_effect=lambda incremental, root, requested: (incremental, digest),
            ),
            mock.patch.object(
                public, "run_bundle_helper", return_value=(0, relay)
            ) as helper,
        ):
            self.assertEqual(
                (0, expected), public.synchronize(public.Request(commit, False))
            )
        self.assertEqual(
            [
                f"{public.RELEASE_API_BASE}/releases/tags/governance-sync-v2-{commit}",
                f"{public.RELEASE_API_BASE}/releases/assets/11",
                f"{public.RELEASE_API_BASE}/releases/assets/22",
            ],
            urls,
        )
        helper.assert_called_once_with(public.Request(commit, False), digest)
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())

    def test_synchronize_success_reports_cleanup_without_being_overwritten(self) -> None:
        request = public.Request(self.COMMIT, False)
        relay = {
            "status": "no-op",
            "commit": self.COMMIT,
            "before_commit": self.COMMIT,
            "backup_ref": None,
        }
        with (
            mock.patch.object(
                public, "publish_bundle", return_value=(91, (1, 2))
            ),
            mock.patch.object(
                public, "run_bundle_helper", return_value=(0, relay)
            ),
            mock.patch.object(
                public, "cleanup_published_bundle", return_value="pending"
            ),
            mock.patch.object(public, "download"),
            mock.patch.object(public, "read_json", return_value={}),
            mock.patch.object(
                public,
                "parse_release_metadata",
                return_value={
                    public.MANIFEST_NAME: public.Asset(
                        public.MANIFEST_NAME, 11, 1
                    ),
                    public.BUNDLE_NAME: public.Asset(public.BUNDLE_NAME, 22, 1),
                },
            ),
            mock.patch.object(
                public,
                "parse_manifest",
                return_value=public.Manifest(self.COMMIT, 1, "b" * 64),
            ),
            mock.patch.object(public, "validate_downloaded_asset"),
            mock.patch.object(
                public,
                "rebuild_full_bundle",
                return_value=(Path("/unused"), "c" * 64),
            ),
            mock.patch.object(Path, "stat", return_value=mock.Mock(st_size=1)),
        ):
            self.assertEqual(
                (0, {**relay, "source_cleanup": "pending"}),
                public.synchronize(request),
            )

    def test_synchronize_nonzero_requires_clean_cleanup_to_relay(self) -> None:
        request = public.Request(self.COMMIT, False)
        old_error = {"status": "error", "error_code": "old_helper_error"}

        def exercise(cleanup: str) -> tuple[int, dict[str, object]]:
            with (
                mock.patch.object(
                    public, "publish_bundle", return_value=(91, (1, 2))
                ),
                mock.patch.object(
                    public, "run_bundle_helper", return_value=(7, old_error)
                ),
                mock.patch.object(
                    public, "cleanup_published_bundle", return_value=cleanup
                ),
                mock.patch.object(public, "download"),
                mock.patch.object(public, "read_json", return_value={}),
                mock.patch.object(
                    public,
                    "parse_release_metadata",
                    return_value={
                        public.MANIFEST_NAME: public.Asset(
                            public.MANIFEST_NAME, 11, 1
                        ),
                        public.BUNDLE_NAME: public.Asset(
                            public.BUNDLE_NAME, 22, 1
                        ),
                    },
                ),
                mock.patch.object(
                    public,
                    "parse_manifest",
                    return_value=public.Manifest(self.COMMIT, 1, "b" * 64),
                ),
                mock.patch.object(public, "validate_downloaded_asset"),
                mock.patch.object(
                    public,
                    "rebuild_full_bundle",
                    return_value=(Path("/unused"), "c" * 64),
                ),
                mock.patch.object(Path, "stat", return_value=mock.Mock(st_size=1)),
            ):
                return public.synchronize(request)

        self.assertEqual((7, old_error), exercise("clean"))
        self.assertEqual(
            (
                1,
                {
                    "status": "error",
                    "error_code": "bundle_cleanup_pending",
                },
            ),
            exercise("pending"),
        )
        self.assertEqual(
            (
                1,
                {
                    "status": "error",
                    "error_code": "bundle_cleanup_state_unknown",
                },
            ),
            exercise("state-unknown"),
        )

    def test_synchronize_finally_cleans_when_bundle_helper_fails(self) -> None:
        request = public.Request(self.COMMIT, False)
        content = b"bundle"
        digest = hashlib.sha256(content).hexdigest()
        assets = {
            public.MANIFEST_NAME: public.Asset(public.MANIFEST_NAME, 11, 1),
            public.BUNDLE_NAME: public.Asset(
                public.BUNDLE_NAME, 22, len(content)
            ),
        }

        def fake_download(url: str, destination: Path, maximum: int, *, asset: bool):
            destination.write_bytes(
                content if destination.name == public.BUNDLE_NAME else b"x"
            )

        with (
            mock.patch.object(public, "download", side_effect=fake_download),
            mock.patch.object(public, "read_json", return_value={}),
            mock.patch.object(
                public, "parse_release_metadata", return_value=assets
            ),
            mock.patch.object(
                public,
                "parse_manifest",
                return_value=public.Manifest(self.COMMIT, len(content), digest),
            ),
            mock.patch.object(
                public,
                "rebuild_full_bundle",
                side_effect=lambda incremental, root, requested: (incremental, digest),
            ),
            mock.patch.object(
                public,
                "run_bundle_helper",
                side_effect=public.SyncError("injected"),
            ),
        ):
            with self.assertRaises(public.SyncError):
                public.synchronize(request)
        self.assertFalse((self.incoming / public.BUNDLE_NAME).exists())
        self.assertFalse((self.incoming / public.STAGING_NAME).exists())


class IncrementalBundleRebuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.mirror = self.root / "mirror"
        self._git(self.root, "init", "-b", "master", str(self.source))
        self._git(self.source, "config", "user.name", "Test")
        self._git(self.source, "config", "user.email", "test@example.invalid")
        (self.source / "seed").write_text("seed\n", encoding="utf-8")
        self._git(self.source, "add", "seed")
        self._git(self.source, "commit", "-m", "seed")
        self.base_parent = self._git_output(self.source, "rev-parse", "HEAD")
        (self.source / "base").write_text("baseline\n", encoding="utf-8")
        self._git(self.source, "add", "base")
        self._git(self.source, "commit", "-m", "baseline")
        self.base = self._git_output(self.source, "rev-parse", "HEAD")
        self._git(self.root, "clone", str(self.source), str(self.mirror))
        (self.source / "increment.bin").write_bytes(os.urandom(109 * 1024))
        self._git(self.source, "add", "increment.bin")
        self._git(self.source, "commit", "-m", "target")
        self.target = self._git_output(self.source, "rev-parse", "HEAD")
        self.incremental = self.root / "incremental.bundle"
        self.lock = self.root / "helper.lock"
        self.lock.write_bytes(b"")
        self.lock.chmod(0o600)
        self._git(
            self.source,
            "bundle",
            "create",
            "--version=3",
            str(self.incremental),
            "refs/heads/master",
            f"^{self.base}",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _git(cwd: Path, *arguments: str) -> None:
        subprocess.run(
            ["/usr/bin/git", *arguments],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C"},
        )

    @staticmethod
    def _git_output(cwd: Path, *arguments: str) -> str:
        return subprocess.run(
            ["/usr/bin/git", *arguments],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C"},
        ).stdout.strip()

    def rebuild(self, bundle: Path, commit: str) -> tuple[Path, str, tempfile.TemporaryDirectory]:
        output = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(output.cleanup)
        with mock.patch.multiple(
            public,
            MIRROR_OBJECTS=self.mirror / ".git" / "objects",
            LOCK=self.lock,
            BASE_COMMIT=self.base,
            BASE_PARENT=self.base_parent,
        ):
            full, digest = public.rebuild_full_bundle(bundle, Path(output.name), commit)
        return full, digest, output

    def test_rebuilds_109kb_increment_and_reports_full_bundle_hash(self) -> None:
        self.assertEqual(
            b"# v3 git bundle\n", self.incremental.read_bytes().splitlines(keepends=True)[0]
        )
        self.assertGreater(self.incremental.stat().st_size, 100 * 1024)
        self.assertLess(self.incremental.stat().st_size, 130 * 1024)
        full, digest, _ = self.rebuild(self.incremental, self.target)
        self.assertEqual(hashlib.sha256(full.read_bytes()).hexdigest(), digest)
        clone = self.root / "full-clone"
        self._git(self.root, "clone", "-b", "master", str(full), str(clone))
        self.assertEqual(self.target, self._git_output(clone, "rev-parse", "HEAD"))
        self.assertEqual(
            self._git_output(self.source, "rev-list", "--count", self.target),
            self._git_output(clone, "rev-list", "--count", "HEAD"),
        )

    def test_baseline_bundle_rebuilds_to_existing_mirror_commit_for_no_op(self) -> None:
        baseline_bundle = self.root / "baseline.bundle"
        self._git(self.source, "update-ref", "refs/heads/master", self.base)
        self._git(
            self.source,
            "bundle",
            "create",
            "--version=2",
            str(baseline_bundle),
            "refs/heads/master",
            f"^{self.base}^",
        )
        self._git(self.source, "update-ref", "refs/heads/master", self.target)
        self.assertEqual(
            b"# v2 git bundle\n", baseline_bundle.read_bytes().splitlines(keepends=True)[0]
        )
        full, _, _ = self.rebuild(baseline_bundle, self.base)
        heads = self._git_output(self.root, "bundle", "list-heads", str(full))
        self.assertEqual(f"{self.base} refs/heads/master", heads)
        self.assertEqual(self.base, self._git_output(self.mirror, "rev-parse", "HEAD"))

    def test_missing_prerequisite_fails_closed(self) -> None:
        empty = self.root / "empty.git"
        self._git(self.root, "init", "--bare", str(empty))
        output = self.root / "missing-output"
        output.mkdir()
        with (
            mock.patch.multiple(
                public,
                MIRROR_OBJECTS=empty / "objects",
                LOCK=self.lock,
                BASE_COMMIT=self.base,
                BASE_PARENT=self.base_parent,
            ),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.rebuild_full_bundle(self.incremental, output, self.target)
        self.assertEqual("bundle_prerequisite_missing", caught.exception.code)

    def test_malicious_wrong_target_bundle_is_rejected(self) -> None:
        wrong_target = self.root / "wrong-target.bundle"
        self._git(
            self.source,
            "bundle",
            "create",
            "--version=2",
            str(wrong_target),
            "refs/heads/master",
            f"^{self.base_parent}",
        )
        output = self.root / "malicious-output"
        output.mkdir()
        with (
            mock.patch.multiple(
                public,
                MIRROR_OBJECTS=self.mirror / ".git" / "objects",
                LOCK=self.lock,
                BASE_COMMIT=self.base,
                BASE_PARENT=self.base_parent,
            ),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.rebuild_full_bundle(wrong_target, output, self.base)
        self.assertEqual("bundle_header_invalid", caught.exception.code)

    def test_rejects_wrong_prerequisite_even_when_mirror_has_it(self) -> None:
        wrong = self.root / "wrong-prerequisite.bundle"
        self._git(
            self.source,
            "bundle",
            "create",
            "--version=3",
            str(wrong),
            "refs/heads/master",
            f"^{self.base_parent}",
        )
        self.assertEqual(
            "commit", self._git_output(self.mirror, "cat-file", "-t", self.base_parent)
        )
        output = self.root / "wrong-prerequisite-output"
        output.mkdir()
        with (
            mock.patch.multiple(
                public,
                MIRROR_OBJECTS=self.mirror / ".git" / "objects",
                LOCK=self.lock,
                BASE_COMMIT=self.base,
                BASE_PARENT=self.base_parent,
            ),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.rebuild_full_bundle(wrong, output, self.target)
        self.assertEqual("bundle_prerequisites_invalid", caught.exception.code)

    def test_rejects_extra_duplicate_and_malformed_real_bundle_headers(self) -> None:
        raw = self.incremental.read_bytes()
        header, pack = raw.split(b"\n\n", 1)
        prerequisite = f"-{self.base} baseline".encode()
        self.assertIn(prerequisite, header)
        fixtures = {
            "extra": (
                header.replace(
                prerequisite,
                prerequisite + f"\n-{self.base_parent} extra".encode(),
            )
                + b"\n\n"
                + pack,
                "bundle_prerequisites_invalid",
            ),
            "duplicate": (
                header.replace(prerequisite, prerequisite + b"\n" + prerequisite)
                + b"\n\n"
                + pack,
                "bundle_header_invalid",
            ),
            "malformed": (
                header.replace(prerequisite, b"-not-an-object malformed")
                + b"\n\n"
                + pack,
                "bundle_header_invalid",
            ),
            "oversized": (
                b"# v2 git bundle\n-" + self.base.encode() + b" " + b"x" * 65536,
                "bundle_header_invalid",
            ),
        }
        for name, (content, error_code) in fixtures.items():
            candidate = self.root / f"{name}.bundle"
            candidate.write_bytes(content)
            with self.subTest(name=name), self.assertRaises(public.SyncError) as caught:
                public.validate_bundle_header(candidate, self.target)
            self.assertEqual(error_code, caught.exception.code)

    def test_helper_lock_is_nonblocking_strict_and_released_after_rebuild(self) -> None:
        held = os.open(self.lock, os.O_RDWR)
        try:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            output = self.root / "contended-output"
            output.mkdir()
            with (
                mock.patch.multiple(
                    public,
                    MIRROR_OBJECTS=self.mirror / ".git" / "objects",
                    LOCK=self.lock,
                    BASE_COMMIT=self.base,
                    BASE_PARENT=self.base_parent,
                ),
                self.assertRaises(public.SyncError) as caught,
            ):
                public.rebuild_full_bundle(self.incremental, output, self.target)
            self.assertEqual("already_running", caught.exception.code)
        finally:
            os.close(held)

        self.rebuild(self.incremental, self.target)
        probe = os.open(self.lock, os.O_RDWR)
        try:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(probe)

        opened = self.lock.stat()
        wrong_group = mock.Mock(
            st_mode=stat.S_IFREG | 0o600,
            st_uid=os.geteuid(),
            st_gid=os.getegid() + 1,
            st_dev=opened.st_dev,
            st_ino=opened.st_ino,
        )
        with (
            mock.patch.object(public, "LOCK", self.lock),
            mock.patch.object(public.os, "fstat", return_value=wrong_group),
            self.assertRaises(public.SyncError) as caught,
        ):
            with public.exclusive_helper_lock():
                self.fail("wrong-group lock was acquired")
        self.assertEqual("lock_unsafe", caught.exception.code)

        self.lock.chmod(0o640)
        with (
            mock.patch.object(public, "LOCK", self.lock),
            self.assertRaises(public.SyncError) as caught,
        ):
            with public.exclusive_helper_lock():
                self.fail("unsafe lock was acquired")
        self.assertEqual("lock_unsafe", caught.exception.code)

        self.lock.unlink()
        target = self.root / "lock-target"
        target.write_bytes(b"")
        target.chmod(0o600)
        self.lock.symlink_to(target)
        with (
            mock.patch.object(public, "LOCK", self.lock),
            self.assertRaises(public.SyncError) as caught,
        ):
            with public.exclusive_helper_lock():
                self.fail("symlink lock was acquired")
        self.assertEqual("lock_unavailable", caught.exception.code)

    def test_git_inputs_cannot_override_fixed_alternates_or_temporary_repository(self) -> None:
        attacker = self.root / "attacker"
        attacker.mkdir()
        with mock.patch.dict(
            os.environ,
            {
                "GIT_DIR": str(attacker),
                "GIT_OBJECT_DIRECTORY": str(attacker),
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(attacker),
                "GIT_CONFIG_GLOBAL": str(attacker / "config"),
                "TMPDIR": str(attacker),
            },
            clear=False,
        ):
            full, digest, output = self.rebuild(self.incremental, self.target)
        self.assertTrue(full.is_relative_to(Path(output.name)))
        self.assertEqual(hashlib.sha256(full.read_bytes()).hexdigest(), digest)
        self.assertEqual(
            {
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_ALLOW_PROTOCOL": "file",
            },
            {
                key: public._git_environment()[key]
                for key in (
                    "GIT_CONFIG_NOSYSTEM",
                    "GIT_CONFIG_GLOBAL",
                    "GIT_TERMINAL_PROMPT",
                    "GIT_ALLOW_PROTOCOL",
                )
            },
        )
        self.assertEqual([], list(attacker.iterdir()))


if __name__ == "__main__":
    unittest.main()
