from __future__ import annotations

import errno
import fcntl
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "aetheris-governance-sync"
REAL_READER_TEST = (
    "IntegrationTests."
    "test_linux_root_group_reader_has_real_read_only_io_before_and_after_sync"
)
REAL_READER_METHOD = REAL_READER_TEST.split(".", 1)[1]
REAL_READER_SUDO_ENV = "GOVERNANCE_SYNC_READER_TEST_UNDER_SUDO"
SPEC = importlib.util.spec_from_loader(
    "governance_sync",
    SourceFileLoader("governance_sync", str(MODULE_PATH)),
)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sync
SPEC.loader.exec_module(sync)


def run_git(cwd: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Governance Test",
            "GIT_AUTHOR_EMAIL": "governance@example.invalid",
            "GIT_COMMITTER_NAME": "Governance Test",
            "GIT_COMMITTER_EMAIL": "governance@example.invalid",
        }
    )
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


class CliValidationTests(unittest.TestCase):
    def test_process_security_sets_umask_and_rejects_root(self) -> None:
        original = os.umask(0o022)
        try:
            with mock.patch.object(sync.os, "geteuid", return_value=1234):
                sync.establish_process_security()
            observed = os.umask(original)
            self.assertEqual(0o027, observed)
        finally:
            os.umask(original)
        with mock.patch.object(sync.os, "geteuid", return_value=0):
            with self.assertRaises(sync.SyncError) as caught:
                sync.establish_process_security()
        self.assertEqual("root_execution_forbidden", caught.exception.code)

    def test_accepts_only_exact_fixed_bundle_and_full_lowercase_hashes(self) -> None:
        request = sync.parse_args(
            [
                "--bundle",
                str(sync.BUNDLE),
                "--commit",
                "a" * 40,
                "--sha256",
                "b" * 64,
                "--dry-run",
            ]
        )
        self.assertTrue(request.dry_run)

    def test_rejects_nonfixed_bundle(self) -> None:
        with self.assertRaises(SystemExit):
            sync.parse_args(
                ["--bundle", "/tmp/x", "--commit", "a" * 40, "--sha256", "b" * 64]
            )

    def test_rejects_short_or_uppercase_identifiers(self) -> None:
        invalid = (("a" * 39, "b" * 64), ("A" * 40, "b" * 64), ("a" * 40, "B" * 64))
        for commit, digest in invalid:
            with self.subTest(commit=commit[:4], digest=digest[:4]):
                with self.assertRaises(SystemExit):
                    sync.parse_args(
                        [
                            "--bundle",
                            str(sync.BUNDLE),
                            "--commit",
                            commit,
                            "--sha256",
                            digest,
                        ]
                    )

    def test_rejects_unknown_arguments(self) -> None:
        with self.assertRaises(SystemExit):
            sync.parse_args(
                [
                    "--bundle",
                    str(sync.BUNDLE),
                    "--commit",
                    "a" * 40,
                    "--sha256",
                    "b" * 64,
                    "--apply",
                ]
            )

    def test_receipt_state_uncertain_has_stable_error_output(self) -> None:
        request = sync.Request(sync.BUNDLE, "a" * 40, "b" * 64, False)
        stderr = io.StringIO()
        with (
            mock.patch.object(sync, "establish_process_security"),
            mock.patch.object(sync, "parse_args", return_value=request),
            mock.patch.object(
                sync,
                "synchronize",
                side_effect=sync.SyncError("receipt_state_uncertain", "hidden details"),
            ),
            redirect_stderr(stderr),
        ):
            self.assertEqual(1, sync.main([]))
        self.assertEqual(
            {"status": "error", "error_code": "receipt_state_uncertain"},
            json.loads(stderr.getvalue()),
        )
        self.assertNotIn("hidden", stderr.getvalue())

    def test_linux_nonroot_real_reader_test_reexecutes_only_itself(self) -> None:
        test = IntegrationTests(methodName=REAL_READER_METHOD)
        completed = subprocess.CompletedProcess([], 0, "", "")
        with (
            mock.patch.object(sys, "platform", "linux"),
            mock.patch.object(os, "geteuid", return_value=1000),
            mock.patch.object(shutil, "which", return_value="/usr/bin/sudo"),
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(
                subprocess,
                "run",
                side_effect=(completed, completed),
            ) as run,
        ):
            getattr(test, REAL_READER_METHOD)()

        self.assertEqual(["/usr/bin/sudo", "-n", "true"], run.call_args_list[0].args[0])
        command = run.call_args_list[1].args[0]
        self.assertEqual(["/usr/bin/sudo", "-n", "env"], command[:3])
        self.assertIn(f"{REAL_READER_SUDO_ENV}=1", command)
        self.assertEqual(
            [sys.executable, str(Path(__file__).resolve()), REAL_READER_TEST],
            command[-3:],
        )

    def test_linux_nonroot_real_reader_test_propagates_sudo_failure(self) -> None:
        test = IntegrationTests(methodName=REAL_READER_METHOD)
        available = subprocess.CompletedProcess([], 0, "", "")
        failed = subprocess.CompletedProcess([], 7, "child stdout", "child stderr")
        with (
            mock.patch.object(sys, "platform", "linux"),
            mock.patch.object(os, "geteuid", return_value=1000),
            mock.patch.object(shutil, "which", return_value="/usr/bin/sudo"),
            mock.patch.dict(os.environ, {}, clear=True),
            mock.patch.object(
                subprocess,
                "run",
                side_effect=(available, failed),
            ),
            self.assertRaisesRegex(AssertionError, "sudo reader unittest failed"),
        ):
            getattr(test, REAL_READER_METHOD)()


class BundleSafetyTests(unittest.TestCase):
    def test_hash_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "real.bundle"
            real.write_bytes(b"data")
            link = root / "link.bundle"
            link.symlink_to(real)
            with self.assertRaises(sync.SyncError) as caught:
                sync.hash_bundle(link)
            self.assertEqual("bundle_unreadable", caught.exception.code)

    def test_hash_detects_expected_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "governance.bundle"
            bundle.write_bytes(b"governance")
            self.assertEqual(hashlib.sha256(b"governance").hexdigest(), sync.hash_bundle(bundle))


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.mirror = self.root / "mirror"
        self.bundle = self.root / "incoming" / "governance.bundle"
        self.lock = self.root / "sync.lock"
        self.receipts = self.root / "receipts"
        self.source.mkdir()
        self.bundle.parent.mkdir()
        run_git(self.source, "init", "-q", "-b", "master")
        (self.source / "truth.txt").write_text("old\n", encoding="utf-8")
        run_git(self.source, "add", "truth.txt")
        run_git(self.source, "commit", "-q", "-m", "old")
        self.old_commit = run_git(self.source, "rev-parse", "HEAD")
        run_git(self.source, "clone", "-q", str(self.source), str(self.mirror))
        (self.source / "truth.txt").write_text("new\n", encoding="utf-8")
        run_git(self.source, "commit", "-q", "-am", "new")
        self.new_commit = run_git(self.source, "rev-parse", "HEAD")
        run_git(self.source, "bundle", "create", str(self.bundle), "--all")
        self.bundle.chmod(0o600)
        self.bundle.parent.chmod(0o700)
        self.digest = hashlib.sha256(self.bundle.read_bytes()).hexdigest()
        self.request = sync.Request(self.bundle, self.new_commit, self.digest, False)
        self.paths = mock.patch.multiple(
            sync,
            MIRROR=self.mirror,
            BUNDLE=self.bundle,
            LOCK=self.lock,
            RECEIPTS=self.receipts,
        )
        self.paths.start()
    def tearDown(self) -> None:
        self.paths.stop()
        self.temp.cleanup()

    def test_dry_run_validates_without_persistent_artifacts(self) -> None:
        request = sync.Request(self.bundle, self.new_commit, self.digest, True)
        result = sync.synchronize(request)
        self.assertEqual("dry-run", result["status"])
        self.assertTrue(result["would_change"])
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertFalse(self.receipts.exists())

    def test_apply_fast_forwards_attached_master_with_backup_ref_and_receipt(self) -> None:
        result = sync.synchronize(self.request)
        self.assertEqual("applied", result["status"])
        self.assertEqual(self.new_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertEqual("master", run_git(self.mirror, "symbolic-ref", "--short", "HEAD"))
        self.assertEqual("new\n", (self.mirror / "truth.txt").read_text(encoding="utf-8"))

        backup_ref = str(result["backup_ref"])
        receipt_path = self.receipts / str(result["receipt"])
        self.assertTrue(backup_ref.startswith(f"{sync.BACKUP_NAMESPACE}/"))
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", backup_ref))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "after_commit",
                "backup_ref",
                "before_commit",
                "bundle_sha256",
                "dry_run",
                "error_code",
                "finished_at",
                "operation_id",
                "requested_commit",
                "schema_version",
                "started_at",
                "status",
            },
            set(receipt),
        )
        serialized = receipt_path.read_text(encoding="utf-8")
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("stderr", serialized)

    def test_target_equal_head_is_noop_without_backup_or_receipt(self) -> None:
        request = sync.Request(self.bundle, self.old_commit, self.digest, False)
        result = sync.synchronize(request)
        self.assertEqual("no-op", result["status"])
        self.assertIsNone(result["backup_ref"])
        self.assertFalse(self.receipts.exists())
        refs = run_git(
            self.mirror,
            "for-each-ref",
            "--format=%(refname)",
            sync.BACKUP_NAMESPACE,
        )
        self.assertEqual("", refs)
        self.assertEqual("master", run_git(self.mirror, "symbolic-ref", "--short", "HEAD"))

    def test_receipt_failure_cas_rolls_back_master_and_worktree(self) -> None:
        with mock.patch.object(
            sync,
            "write_receipt",
            side_effect=sync.SyncError("receipt_write_failed", "secret details"),
        ):
            with self.assertRaises(sync.SyncError):
                sync.synchronize(self.request)
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "master"))
        self.assertEqual("master", run_git(self.mirror, "symbolic-ref", "--short", "HEAD"))
        self.assertEqual("old\n", (self.mirror / "truth.txt").read_text(encoding="utf-8"))
        refs = run_git(
            self.mirror,
            "for-each-ref",
            "--format=%(objectname)",
            sync.BACKUP_NAMESPACE,
        ).splitlines()
        self.assertEqual([self.old_commit], refs)

    def test_post_rename_receipt_fsync_failure_cleans_receipt_and_rolls_back(self) -> None:
        real_fsync = sync.os.fsync
        directory_fsync_calls = 0

        def fail_first_directory_fsync(fd: int) -> None:
            nonlocal directory_fsync_calls
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                directory_fsync_calls += 1
                if directory_fsync_calls == 1:
                    raise OSError("injected receipt directory fsync failure")
            real_fsync(fd)

        with mock.patch.object(sync.os, "fsync", side_effect=fail_first_directory_fsync):
            with self.assertRaises(sync.SyncError) as caught:
                sync.synchronize(self.request)
        self.assertEqual("receipt_write_failed", caught.exception.code)
        self.assertEqual(2, directory_fsync_calls)
        self.assertEqual([], list(self.receipts.glob("*.receipt.json")))
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertEqual("old\n", (self.mirror / "truth.txt").read_text(encoding="utf-8"))

    def test_receipt_cleanup_failure_preserves_applied_mirror(self) -> None:
        real_fsync = sync.os.fsync
        real_unlink = Path.unlink
        directory_fsync_calls = 0

        def fail_first_directory_fsync(fd: int) -> None:
            nonlocal directory_fsync_calls
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                directory_fsync_calls += 1
                if directory_fsync_calls == 1:
                    raise OSError("injected receipt directory fsync failure")
            real_fsync(fd)

        def reject_published_receipt_unlink(
            path: Path, missing_ok: bool = False
        ) -> None:
            if path.name.endswith(".receipt.json"):
                raise OSError("injected receipt cleanup failure")
            real_unlink(path, missing_ok=missing_ok)

        with (
            mock.patch.object(sync.os, "fsync", side_effect=fail_first_directory_fsync),
            mock.patch.object(Path, "unlink", reject_published_receipt_unlink),
        ):
            with self.assertRaises(sync.SyncError) as caught:
                sync.synchronize(self.request)
        self.assertEqual("receipt_state_uncertain", caught.exception.code)
        self.assertEqual(1, directory_fsync_calls)
        self.assertEqual(1, len(list(self.receipts.glob("*.receipt.json"))))
        self.assertEqual(self.new_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertEqual(self.new_commit, run_git(self.mirror, "rev-parse", "master"))
        self.assertEqual("new\n", (self.mirror / "truth.txt").read_text(encoding="utf-8"))

    def test_rollback_cas_failure_is_reported_and_leaves_recovery_ref(self) -> None:
        real_git = sync.git

        def reject_rollback_cas(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
            if (
                args[:2] == ("update-ref", sync.MASTER_REF)
                and args[2:4] == (self.old_commit, self.new_commit)
            ):
                return subprocess.CompletedProcess(list(args), 1, "", "CAS rejected")
            return real_git(*args, **kwargs)

        with (
            mock.patch.object(sync, "git", side_effect=reject_rollback_cas),
            mock.patch.object(
                sync,
                "write_receipt",
                side_effect=sync.SyncError("receipt_write_failed", "hidden"),
            ),
        ):
            with self.assertRaises(sync.SyncError) as caught:
                sync.synchronize(self.request)
        self.assertEqual("rollback_failed", caught.exception.code)
        self.assertEqual(self.new_commit, run_git(self.mirror, "rev-parse", "master"))
        refs = run_git(
            self.mirror,
            "for-each-ref",
            "--format=%(objectname)",
            sync.BACKUP_NAMESPACE,
        ).splitlines()
        self.assertEqual([self.old_commit], refs)

    def test_rollback_worktree_failure_is_reported_after_master_restore(self) -> None:
        real_git = sync.git

        def reject_rollback_reset(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
            if args[:4] == ("reset", "--quiet", "--hard", self.old_commit):
                raise sync.SyncError("git_validation_failed", "hidden")
            return real_git(*args, **kwargs)

        with (
            mock.patch.object(sync, "git", side_effect=reject_rollback_reset),
            mock.patch.object(
                sync,
                "write_receipt",
                side_effect=sync.SyncError("receipt_write_failed", "hidden"),
            ),
        ):
            with self.assertRaises(sync.SyncError) as caught:
                sync.synchronize(self.request)
        self.assertEqual("rollback_failed", caught.exception.code)
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "master"))
        self.assertEqual("new\n", (self.mirror / "truth.txt").read_text(encoding="utf-8"))

    def test_master_cas_failure_does_not_reset_worktree(self) -> None:
        real_git = sync.git

        def reject_master_cas(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
            if (
                args[:2] == ("update-ref", sync.MASTER_REF)
                and args[2:4] == (self.new_commit, self.old_commit)
            ):
                return subprocess.CompletedProcess(list(args), 1, "", "CAS rejected")
            return real_git(*args, **kwargs)

        with mock.patch.object(sync, "git", side_effect=reject_master_cas):
            with self.assertRaises(sync.SyncError) as caught:
                sync.synchronize(self.request)
        self.assertEqual("master_cas_failed", caught.exception.code)
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertEqual(self.old_commit, run_git(self.mirror, "rev-parse", "master"))
        self.assertEqual("old\n", (self.mirror / "truth.txt").read_text(encoding="utf-8"))

    def test_rejects_non_fast_forward_before_creating_backup(self) -> None:
        sync.synchronize(self.request)
        existing_refs = run_git(
            self.mirror,
            "for-each-ref",
            "--format=%(refname)",
            sync.BACKUP_NAMESPACE,
        )

        run_git(self.source, "checkout", "-q", "-b", "divergent", self.old_commit)
        (self.source / "truth.txt").write_text("divergent\n", encoding="utf-8")
        run_git(self.source, "commit", "-q", "-am", "divergent")
        divergent = run_git(self.source, "rev-parse", "HEAD")
        divergent_bundle = self.bundle.parent / "divergent.bundle"
        run_git(self.source, "bundle", "create", str(divergent_bundle), "--all")
        divergent_bundle.chmod(0o600)
        request = sync.Request(
            divergent_bundle,
            divergent,
            hashlib.sha256(divergent_bundle.read_bytes()).hexdigest(),
            False,
        )

        with self.assertRaises(sync.SyncError) as caught:
            sync.synchronize(request)
        self.assertEqual("non_fast_forward", caught.exception.code)
        self.assertEqual(self.new_commit, run_git(self.mirror, "rev-parse", "HEAD"))
        self.assertEqual(
            existing_refs,
            run_git(
                self.mirror,
                "for-each-ref",
                "--format=%(refname)",
                sync.BACKUP_NAMESPACE,
            ),
        )

    def test_rejects_detached_nonmaster_and_dirty_mirrors(self) -> None:
        cases = ("detached", "other", "dirty")
        for case in cases:
            with self.subTest(case=case):
                run_git(self.mirror, "checkout", "-q", "master")
                run_git(self.mirror, "reset", "-q", "--hard", self.old_commit)
                run_git(self.mirror, "clean", "-ffdx")
                if case == "detached":
                    run_git(self.mirror, "checkout", "-q", "--detach", self.old_commit)
                elif case == "other":
                    run_git(self.mirror, "checkout", "-q", "-B", "other", self.old_commit)
                else:
                    (self.mirror / "untracked").write_text("dirty", encoding="utf-8")
                with self.assertRaises(sync.SyncError) as caught:
                    sync.synchronize(self.request)
                self.assertIn(
                    caught.exception.code,
                    {"mirror_not_attached_master", "mirror_dirty"},
                )

    def test_rejects_group_or_world_writable_git_config(self) -> None:
        config = self.mirror / ".git" / "config"
        config.chmod(0o666)
        with self.assertRaises(sync.SyncError) as caught:
            sync.validate_mirror()
        self.assertEqual("mirror_config_unsafe", caught.exception.code)

    def test_rejects_mirror_root_with_wrong_effective_group(self) -> None:
        real_lstat = Path.lstat

        def lstat_with_wrong_mirror_gid(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if path == self.mirror:
                fields = list(metadata)
                fields[5] = os.getegid() + 1
                return os.stat_result(fields)
            return metadata

        with mock.patch.object(Path, "lstat", lstat_with_wrong_mirror_gid):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_mirror()
        self.assertEqual("mirror_unsafe", caught.exception.code)

    def test_rejects_git_directory_with_wrong_effective_group(self) -> None:
        git_directory = self.mirror / ".git"
        real_lstat = Path.lstat

        def lstat_with_wrong_git_gid(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if path == git_directory:
                fields = list(metadata)
                fields[5] = os.getegid() + 1
                return os.stat_result(fields)
            return metadata

        with mock.patch.object(Path, "lstat", lstat_with_wrong_git_gid):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_mirror()
        self.assertEqual("mirror_gitdir_invalid", caught.exception.code)

    def test_rejects_git_config_with_wrong_effective_group(self) -> None:
        config = self.mirror / ".git" / "config"
        real_lstat = Path.lstat

        def lstat_with_wrong_config_gid(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if path == config:
                fields = list(metadata)
                fields[5] = os.getegid() + 1
                return os.stat_result(fields)
            return metadata

        with mock.patch.object(Path, "lstat", lstat_with_wrong_config_gid):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_mirror()
        self.assertEqual("mirror_config_unsafe", caught.exception.code)

    def test_recheck_rejects_mirror_root_with_wrong_effective_group(self) -> None:
        real_lstat = Path.lstat
        real_git = sync.git
        git_inspection_started = False

        def lstat_with_wrong_gid_on_recheck(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if git_inspection_started and path == self.mirror:
                fields = list(metadata)
                fields[5] = os.getegid() + 1
                return os.stat_result(fields)
            return metadata

        def mark_git_inspection(*args: str, **kwargs: object):
            nonlocal git_inspection_started
            git_inspection_started = True
            return real_git(*args, **kwargs)

        with (
            mock.patch.object(Path, "lstat", lstat_with_wrong_gid_on_recheck),
            mock.patch.object(sync, "git", side_effect=mark_git_inspection),
        ):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_mirror()
        self.assertEqual("mirror_changed", caught.exception.code)

    def test_recheck_rejects_git_directory_with_wrong_effective_group(self) -> None:
        git_directory = self.mirror / ".git"
        real_lstat = Path.lstat
        real_git = sync.git
        git_inspection_started = False

        def lstat_with_wrong_gid_on_recheck(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if git_inspection_started and path == git_directory:
                fields = list(metadata)
                fields[5] = os.getegid() + 1
                return os.stat_result(fields)
            return metadata

        def mark_git_inspection(*args: str, **kwargs: object):
            nonlocal git_inspection_started
            git_inspection_started = True
            return real_git(*args, **kwargs)

        with (
            mock.patch.object(Path, "lstat", lstat_with_wrong_gid_on_recheck),
            mock.patch.object(sync, "git", side_effect=mark_git_inspection),
        ):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_mirror()
        self.assertEqual("mirror_changed", caught.exception.code)

    def test_linux_root_group_reader_has_real_read_only_io_before_and_after_sync(
        self,
    ) -> None:
        if not sys.platform.startswith("linux"):
            self.skipTest("requires Linux setgroups/setgid/setuid semantics")
        if os.geteuid() != 0:
            if os.environ.get(REAL_READER_SUDO_ENV) == "1":
                self.fail("sudo re-execution did not acquire root")
            sudo = shutil.which("sudo")
            if sudo is None:
                self.skipTest("sudo is unavailable for the Linux reader test")
            available = subprocess.run(
                [sudo, "-n", "true"],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if available.returncode != 0:
                self.skipTest("passwordless sudo is unavailable for the Linux reader test")
            env = os.environ.copy()
            env[REAL_READER_SUDO_ENV] = "1"
            command = [
                sudo,
                "-n",
                "env",
                *[f"{key}={value}" for key, value in env.items()],
                sys.executable,
                str(Path(__file__).resolve()),
                REAL_READER_TEST,
            ]
            completed = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(
                0,
                completed.returncode,
                "sudo reader unittest failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}",
            )
            return

        writer_gid = os.getegid()
        reader_uid = 65534 if writer_gid != 65534 else 65533
        reader_gid = 65534 if writer_gid != 65534 else 65533
        document = self.mirror / "truth.txt"
        git_directory = self.mirror / ".git"

        self.root.chmod(0o751)
        for path in (self.mirror, *self.mirror.rglob("*")):
            os.chown(path, os.geteuid(), writer_gid)
            mode = stat.S_IMODE(path.stat().st_mode) & ~0o022
            if path.is_dir():
                mode |= stat.S_IRGRP | stat.S_IXGRP
            elif path.is_file():
                mode |= stat.S_IRGRP
            path.chmod(mode)

        def reader_probe(expected_document: str, readable_commit: str) -> dict[str, object]:
            read_fd, write_fd = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(read_fd)
                result: dict[str, object]
                try:
                    os.setgroups([writer_gid])
                    os.setgid(reader_gid)
                    os.setuid(reader_uid)

                    head = (git_directory / "HEAD").read_text(encoding="utf-8")
                    content = document.read_text(encoding="utf-8")
                    object_type = subprocess.run(
                        [
                            "git",
                            "-c",
                            f"safe.directory={self.mirror}",
                            "cat-file",
                            "-t",
                            readable_commit,
                        ],
                        cwd=self.mirror,
                        check=True,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    ).stdout.strip()

                    def denied(operation) -> bool:
                        try:
                            operation()
                        except OSError as exc:
                            if exc.errno in (errno.EACCES, errno.EPERM, errno.EROFS):
                                return True
                            raise
                        return False

                    operations = {
                        "worktree_create": lambda: os.open(
                            self.mirror / "reader-created",
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                            0o600,
                        ),
                        "worktree_overwrite": lambda: document.write_text(
                            "reader overwrite\n", encoding="utf-8"
                        ),
                        "worktree_rename": lambda: os.rename(
                            document, self.mirror / "truth.reader-moved"
                        ),
                        "refs_create": lambda: os.open(
                            git_directory / "refs" / "reader-created",
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                            0o600,
                        ),
                        "refs_overwrite": lambda: (
                            git_directory / "refs" / "heads" / "master"
                        ).write_text("0" * 40 + "\n", encoding="ascii"),
                        "refs_rename": lambda: os.rename(
                            git_directory / "refs" / "heads" / "master",
                            git_directory / "refs" / "heads" / "master.reader-moved",
                        ),
                        "config_create": lambda: os.open(
                            git_directory / "config.reader-created",
                            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                            0o600,
                        ),
                        "config_overwrite": lambda: (
                            git_directory / "config"
                        ).write_text("[reader]\nwrite = true\n", encoding="utf-8"),
                        "config_rename": lambda: os.rename(
                            git_directory / "config",
                            git_directory / "config.reader-moved",
                        ),
                    }
                    result = {
                        "head_readable": head.startswith("ref: refs/heads/master"),
                        "document": content,
                        "object_type": object_type,
                        "denied": {
                            name: denied(operation)
                            for name, operation in operations.items()
                        },
                    }
                except BaseException as exc:
                    result = {"child_error": f"{type(exc).__name__}: {exc}"}
                payload = json.dumps(result, sort_keys=True).encode("utf-8")
                os.write(write_fd, payload)
                os.close(write_fd)
                os._exit(1 if "child_error" in result else 0)

            os.close(write_fd)
            chunks = []
            while True:
                chunk = os.read(read_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            os.close(read_fd)
            _, status = os.waitpid(pid, 0)
            result = json.loads(b"".join(chunks).decode("utf-8"))
            self.assertTrue(os.WIFEXITED(status))
            self.assertEqual(
                0,
                os.WEXITSTATUS(status),
                f"reader child failed: {result.get('child_error', 'unknown error')}",
            )
            return result

        before = reader_probe("old\n", self.old_commit)
        self.assertNotIn("child_error", before)
        self.assertTrue(before["head_readable"])
        self.assertEqual("old\n", before["document"])
        self.assertEqual("commit", before["object_type"])
        self.assertTrue(all(before["denied"].values()))

        original_umask = os.umask(0o027)
        try:
            sync.synchronize(self.request)
        finally:
            os.umask(original_umask)

        after = reader_probe("new\n", self.new_commit)
        self.assertNotIn("child_error", after)
        self.assertTrue(after["head_readable"])
        self.assertEqual("new\n", after["document"])
        self.assertEqual("commit", after["object_type"])
        self.assertTrue(all(after["denied"].values()))

    def test_incoming_contract_accepts_effective_owner_and_group(self) -> None:
        expected_gid, identity = sync.validate_incoming_bundle(self.bundle)
        self.assertEqual(os.getgid(), expected_gid)
        metadata = self.bundle.stat()
        self.assertEqual((metadata.st_dev, metadata.st_ino), identity)

    def test_incoming_contract_rejects_wrong_directory_mode(self) -> None:
        self.bundle.parent.chmod(0o750)
        with self.assertRaises(sync.SyncError) as caught:
            sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("incoming_directory_unsafe", caught.exception.code)

    def test_incoming_contract_rejects_wrong_directory_owner(self) -> None:
        with mock.patch.object(sync.os, "geteuid", return_value=os.geteuid() + 1):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("incoming_directory_unsafe", caught.exception.code)

    def test_incoming_contract_rejects_wrong_effective_group(self) -> None:
        with mock.patch.object(sync.os, "getegid", return_value=os.getgid() + 1):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("incoming_directory_unsafe", caught.exception.code)

    def test_incoming_contract_rejects_wrong_bundle_mode(self) -> None:
        self.bundle.chmod(0o640)
        with self.assertRaises(sync.SyncError) as caught:
            sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("bundle_unsafe", caught.exception.code)

    def test_incoming_contract_rejects_wrong_bundle_group(self) -> None:
        real_lstat = Path.lstat

        def lstat_with_wrong_bundle_gid(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if path == self.bundle:
                fields = list(metadata)
                fields[5] = os.getgid() + 1
                return os.stat_result(fields)
            return metadata

        with mock.patch.object(Path, "lstat", lstat_with_wrong_bundle_gid):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("bundle_unsafe", caught.exception.code)

    def test_incoming_contract_rejects_bundle_symlink(self) -> None:
        real_bundle = self.bundle.with_name("real.bundle")
        self.bundle.rename(real_bundle)
        self.bundle.symlink_to(real_bundle)
        with self.assertRaises(sync.SyncError) as caught:
            sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("bundle_unsafe", caught.exception.code)

    def test_incoming_contract_rejects_wrong_bundle_owner(self) -> None:
        real_lstat = Path.lstat

        def lstat_with_wrong_bundle_uid(path: Path) -> os.stat_result:
            metadata = real_lstat(path)
            if path == self.bundle:
                fields = list(metadata)
                fields[4] = os.geteuid() + 1
                return os.stat_result(fields)
            return metadata

        with mock.patch.object(Path, "lstat", lstat_with_wrong_bundle_uid):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_incoming_bundle(self.bundle)
        self.assertEqual("bundle_unsafe", caught.exception.code)

    def test_rejects_gitfile_and_symlink_git_directory(self) -> None:
        git_dir = self.mirror / ".git"
        saved = self.root / "saved.git"
        git_dir.rename(saved)
        try:
            git_dir.write_text(f"gitdir: {saved}\n", encoding="utf-8")
            with self.assertRaises(sync.SyncError) as gitfile_error:
                sync.validate_mirror()
            self.assertEqual("mirror_gitdir_invalid", gitfile_error.exception.code)
            git_dir.unlink()
            git_dir.symlink_to(saved, target_is_directory=True)
            with self.assertRaises(sync.SyncError) as symlink_error:
                sync.validate_mirror()
            self.assertEqual("mirror_gitdir_invalid", symlink_error.exception.code)
        finally:
            if git_dir.is_symlink() or git_dir.is_file():
                git_dir.unlink()
            saved.rename(git_dir)

    def test_config_replacement_during_validation_fails_closed(self) -> None:
        real_git = sync.git
        config = self.mirror / ".git" / "config"
        replaced = False

        def replace_config_then_git(
            *args: str, **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            nonlocal replaced
            if not replaced:
                replacement = config.with_name("config.replacement")
                replacement.write_bytes(config.read_bytes())
                replacement.chmod(0o644)
                os.replace(replacement, config)
                replaced = True
            return real_git(*args, **kwargs)

        with mock.patch.object(sync, "git", side_effect=replace_config_then_git):
            with self.assertRaises(sync.SyncError) as caught:
                sync.validate_mirror()
        self.assertEqual("mirror_changed", caught.exception.code)

    def test_lock_contention_fails_closed(self) -> None:
        self.lock.touch(mode=0o600)
        with self.lock.open("r+") as held:
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(sync.SyncError) as caught:
                with sync.exclusive_lock():
                    self.fail("contended lock was acquired")
        self.assertEqual("already_running", caught.exception.code)

    def test_lock_rejects_nonregular_inode_after_open(self) -> None:
        os.mkfifo(self.lock)
        with self.assertRaises(sync.SyncError) as caught:
            with sync.exclusive_lock():
                self.fail("nonregular lock was acquired")
        self.assertEqual("lock_not_regular", caught.exception.code)

    def test_lock_rejects_symlink(self) -> None:
        target = self.root / "attacker.lock"
        target.touch(mode=0o600)
        self.lock.symlink_to(target)
        with self.assertRaises(sync.SyncError) as caught:
            with sync.exclusive_lock():
                self.fail("symlink lock was acquired")
        self.assertEqual("lock_unavailable", caught.exception.code)

    def test_bad_sha_and_missing_commit_are_rejected(self) -> None:
        with self.assertRaises(sync.SyncError) as digest_error:
            sync.validate_bundle_file(
                sync.Request(self.bundle, self.new_commit, "0" * 64, False)
            )
        self.assertEqual("sha256_mismatch", digest_error.exception.code)
        with self.assertRaises(sync.SyncError):
            sync.validate_bundle_git(
                sync.Request(self.bundle, "0" * 40, self.digest, False)
            )


if __name__ == "__main__":
    unittest.main()
