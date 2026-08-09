from __future__ import annotations

import fcntl
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
    "governance_sync_public",
    SourceFileLoader("governance_sync_public", str(MODULE_PATH)),
)
assert SPEC and SPEC.loader
public = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = public
SPEC.loader.exec_module(public)


def run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["/usr/bin/git", *args],
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": "/nonexistent",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
    )
    return result.stdout.strip()


class ArgumentAndProcessTests(unittest.TestCase):
    def test_uses_fixed_isolated_python_interpreter(self) -> None:
        self.assertEqual("#!/usr/bin/python3 -I", MODULE_PATH.read_text().splitlines()[0])

    def test_requires_exact_commit_and_exactly_one_mode(self) -> None:
        commit = "a" * 40
        self.assertEqual(
            public.Request(commit, True),
            public.parse_args(["--commit", commit, "--dry-run"]),
        )
        self.assertEqual(
            public.Request(commit, False),
            public.parse_args(["--commit", commit, "--apply"]),
        )
        rejected = (
            ["--commit", commit],
            ["--commit", commit, "--dry-run", "--apply"],
            ["--commit", "A" * 40, "--apply"],
            ["--commit", "a" * 39, "--apply"],
            ["--comm", commit, "--apply"],
            ["--commit", commit, "--app"],
            ["--commit", commit, "--apply", "extra"],
        )
        for argv in rejected:
            with self.subTest(argv=argv), self.assertRaises(public.SyncError) as caught:
                public.parse_args(argv)
            self.assertEqual("invalid_arguments", caught.exception.code)

    def test_cli_contract_failure_emits_one_json_object_only(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.object(public, "establish_process_security"),
            redirect_stderr(stderr),
        ):
            self.assertEqual(1, public.main(["--help"]))
        lines = stderr.getvalue().splitlines()
        self.assertEqual(1, len(lines))
        payload = json.loads(lines[0])
        self.assertEqual(
            {"status": "error", "error_code": "invalid_arguments"},
            payload,
        )

    def test_refuses_root(self) -> None:
        with (
            mock.patch.object(public.os, "geteuid", return_value=0),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.establish_process_security()
        self.assertEqual("root_execution_forbidden", caught.exception.code)

    def test_argument_validation_precedes_root_rejection(self) -> None:
        malformed_stderr = io.StringIO()
        with (
            mock.patch.object(public.os, "geteuid", return_value=0),
            redirect_stderr(malformed_stderr),
        ):
            self.assertEqual(1, public.main(["--help"]))
        self.assertEqual(
            {"status": "error", "error_code": "invalid_arguments"},
            json.loads(malformed_stderr.getvalue()),
        )

        valid_stderr = io.StringIO()
        with (
            mock.patch.object(public.os, "geteuid", return_value=0),
            redirect_stderr(valid_stderr),
        ):
            self.assertEqual(
                1,
                public.main(["--commit", "a" * 40, "--dry-run"]),
            )
        self.assertEqual(
            {"status": "error", "error_code": "root_execution_forbidden"},
            json.loads(valid_stderr.getvalue()),
        )

    def test_git_uses_fixed_executable_environment_and_no_credentials(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "ok\n", "")
        ambient = {
            "HOME": "/secret",
            "GITHUB_TOKEN": "secret",
            "GIT_ASKPASS": "/secret/askpass",
        }
        with (
            mock.patch.dict(os.environ, ambient, clear=False),
            mock.patch.object(public.subprocess, "run", return_value=completed) as run,
        ):
            self.assertEqual("ok\n", public.git("status", cwd=Path("/tmp")).stdout)
        argv = run.call_args.args[0]
        kwargs = run.call_args.kwargs
        self.assertEqual("/usr/bin/git", argv[0])
        self.assertIn("credential.helper=", argv)
        self.assertIn("core.hooksPath=/dev/null", argv)
        self.assertIn("maintenance.auto=false", argv)
        self.assertIn("protocol.allow=never", argv)
        self.assertNotIn("secret", json.dumps(kwargs["env"]))
        self.assertEqual("/nonexistent", kwargs["env"]["HOME"])
        self.assertEqual("/dev/null", kwargs["env"]["GIT_CONFIG_GLOBAL"])
        self.assertEqual("0", kwargs["env"]["GIT_TERMINAL_PROMPT"])
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertFalse(kwargs["shell"])
        self.assertEqual(public.GIT_TIMEOUT_SECONDS, kwargs["timeout"])

    def test_fixed_resources_match_contract(self) -> None:
        self.assertEqual(
            "https://github.com/lyosvne/agent-collaboration-standard.git",
            public.PUBLIC_REMOTE,
        )
        self.assertEqual("https", public.PUBLIC_PROTOCOL)
        self.assertEqual("refs/heads/master", public.MASTER_REF)
        self.assertEqual(
            "refs/aetheris-governance-sync/backups",
            public.BACKUP_NAMESPACE,
        )
        self.assertEqual(
            "refs/aetheris-governance-sync/operations",
            public.OPERATION_NAMESPACE,
        )


class PublicSyncIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source = root / "source"
        self.mirror = root / "mirror"
        self.lock = root / "sync.lock"
        self.receipts = root / "receipts"
        self.source.mkdir()
        run_git(self.source, "init", "-b", "master")
        run_git(self.source, "config", "user.name", "Governance Test")
        run_git(self.source, "config", "user.email", "governance@example.invalid")
        (self.source / "governance.txt").write_text("base\n", encoding="utf-8")
        run_git(self.source, "add", "governance.txt")
        run_git(self.source, "commit", "-m", "base")
        self.base = run_git(self.source, "rev-parse", "HEAD")
        run_git(root, "clone", str(self.source), str(self.mirror))
        run_git(self.mirror, "config", "user.name", "Mirror Test")
        run_git(self.mirror, "config", "user.email", "mirror@example.invalid")
        # A malicious or stale configured origin is never the network target.
        run_git(
            self.mirror,
            "remote",
            "set-url",
            "origin",
            "https://example.invalid/untrusted.git",
        )
        self.patch = mock.patch.multiple(
            public,
            MIRROR=self.mirror,
            LOCK=self.lock,
            RECEIPTS=self.receipts,
            PUBLIC_REMOTE=str(self.source),
            PUBLIC_PROTOCOL="file",
        )
        self.patch.start()

    def tearDown(self) -> None:
        self.patch.stop()
        self.temp.cleanup()

    def commit_source(self, content: str, message: str = "update") -> str:
        (self.source / "governance.txt").write_text(content, encoding="utf-8")
        run_git(self.source, "add", "governance.txt")
        run_git(self.source, "commit", "-m", message)
        return run_git(self.source, "rev-parse", "HEAD")

    def refs(self, namespace: str) -> list[str]:
        output = run_git(
            self.mirror,
            "for-each-ref",
            "--format=%(refname)",
            f"{namespace}/",
        )
        return output.splitlines() if output else []

    def mirror_head(self) -> str:
        return run_git(self.mirror, "rev-parse", "HEAD")

    def test_current_commit_dry_run_and_apply_are_side_effect_free(self) -> None:
        dry = public.synchronize(public.Request(self.base, True))
        self.assertEqual(
            {
                "status": "dry-run",
                "before_commit": self.base,
                "commit": self.base,
                "remote_master": self.base,
                "would_change": False,
            },
            dry,
        )
        apply = public.synchronize(public.Request(self.base, False))
        self.assertEqual("no-op", apply["status"])
        self.assertIsNone(apply["backup_ref"])
        self.assertEqual(self.base, self.mirror_head())
        self.assertEqual([], self.refs(public.BACKUP_NAMESPACE))
        self.assertEqual([], self.refs(public.OPERATION_NAMESPACE))
        self.assertFalse(self.receipts.exists())

    def test_fetch_is_isolated_import_is_file_only_and_local_instead_of_is_ignored(
        self,
    ) -> None:
        target = self.commit_source("isolated\n")
        run_git(
            self.mirror,
            "config",
            f"url.https://example.invalid/redirect.git.insteadOf",
            str(self.source),
        )
        run_git(
            self.mirror,
            "config",
            "url.https://example.invalid/local-import.git.insteadOf",
            "/",
        )
        run_git(self.mirror, "config", "protocol.file.allow", "never")
        calls: list[tuple[tuple[str, ...], Path]] = []
        real_git = public.git

        def recording_git(*args: str, **kwargs: object):
            calls.append((args, kwargs["cwd"]))
            return real_git(*args, **kwargs)

        with mock.patch.object(public, "git", side_effect=recording_git):
            result = public.synchronize(public.Request(target, True))

        self.assertTrue(result["would_change"])
        network = [
            (args, cwd)
            for args, cwd in calls
            if "fetch" in args and str(self.source) in args
        ]
        self.assertEqual(1, len(network))
        self.assertNotEqual(self.mirror, network[0][1])
        self.assertIn("protocol.file.allow=always", network[0][0])
        imports = [
            args
            for args, cwd in calls
            if cwd == self.mirror
            and "fetch" in args
            and "protocol.file.allow=always" in args
        ]
        self.assertEqual(1, len(imports))
        self.assertNotIn(str(self.source), imports[0])
        self.assertTrue(any(arg.startswith("url.") for arg in imports[0]))
        self.assertEqual([], self.refs(public.OPERATION_NAMESPACE))
        # File-only import intentionally leaves validated unreachable objects
        # in the mirror object database after its temporary ref is deleted.
        self.assertEqual(target, run_git(self.mirror, "rev-parse", target))

    def test_canonical_fast_forward_creates_backup_and_public_receipt(self) -> None:
        target = self.commit_source("next\n")
        dry = public.synchronize(public.Request(target, True))
        self.assertTrue(dry["would_change"])
        self.assertEqual(target, dry["remote_master"])
        self.assertEqual([], self.refs(public.OPERATION_NAMESPACE))

        applied = public.synchronize(public.Request(target, False))
        self.assertEqual("applied", applied["status"])
        self.assertEqual(target, self.mirror_head())
        self.assertEqual(target, applied["remote_master"])
        self.assertEqual([applied["backup_ref"]], self.refs(public.BACKUP_NAMESPACE))
        self.assertEqual(
            self.base,
            run_git(self.mirror, "rev-parse", applied["backup_ref"]),
        )
        self.assertEqual([], self.refs(public.OPERATION_NAMESPACE))
        receipt_path = self.receipts / applied["receipt"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "schema_version",
                "source_mode",
                "remote_url_id",
                "remote_master",
                "target_commit",
                "before_commit",
                "after_commit",
                "backup_ref",
                "operation_id",
                "started_at",
                "finished_at",
                "status",
            },
            set(receipt),
        )
        self.assertEqual("public-fixed-remote", receipt["source_mode"])
        self.assertEqual("governance-public-origin-v1", receipt["remote_url_id"])
        self.assertEqual(target, receipt["target_commit"])
        self.assertEqual(self.base, receipt["before_commit"])
        self.assertEqual(target, receipt["after_commit"])
        self.assertNotIn("url", json.dumps(receipt).lower().replace("url_id", ""))
        self.assertEqual(0o600, stat.S_IMODE(receipt_path.stat().st_mode))

    def test_apply_refetches_when_remote_changes_after_dry_run(self) -> None:
        target = self.commit_source("target\n", "target")
        first = public.synchronize(public.Request(target, True))
        self.assertEqual(target, first["remote_master"])
        later = self.commit_source("later\n", "later")
        applied = public.synchronize(public.Request(target, False))
        self.assertEqual(target, applied["commit"])
        self.assertEqual(later, applied["remote_master"])

    def test_rejects_side_branch_rollback_divergence_and_non_commit(self) -> None:
        canonical = self.commit_source("canonical\n", "canonical")

        run_git(self.source, "checkout", "-b", "side", self.base)
        (self.source / "side.txt").write_text("side\n", encoding="utf-8")
        run_git(self.source, "add", "side.txt")
        run_git(self.source, "commit", "-m", "side")
        side = run_git(self.source, "rev-parse", "HEAD")
        run_git(self.source, "checkout", "master")
        run_git(self.mirror, "fetch", str(self.source), side)
        with self.assertRaises(public.SyncError) as caught:
            public.synchronize(public.Request(side, True))
        self.assertEqual("target_not_canonical", caught.exception.code)

        public.synchronize(public.Request(canonical, False))
        with self.assertRaises(public.SyncError) as caught:
            public.synchronize(public.Request(self.base, True))
        self.assertEqual("non_fast_forward", caught.exception.code)

        run_git(self.mirror, "checkout", "-b", "local-divergence", self.base)
        (self.mirror / "local.txt").write_text("local\n", encoding="utf-8")
        run_git(self.mirror, "add", "local.txt")
        run_git(self.mirror, "commit", "-m", "local divergence")
        run_git(self.mirror, "branch", "-M", "master")
        with self.assertRaises(public.SyncError) as caught:
            public.synchronize(public.Request(canonical, True))
        self.assertEqual("non_fast_forward", caught.exception.code)

        blob = run_git(
            self.mirror,
            "hash-object",
            "-w",
            str(self.mirror / "governance.txt"),
        )
        with self.assertRaises(public.SyncError) as caught:
            public.synchronize(public.Request(blob, True))
        self.assertEqual("target_not_commit", caught.exception.code)

    def test_rejects_dirty_and_detached_mirror(self) -> None:
        (self.mirror / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaises(public.SyncError) as caught:
            public.synchronize(public.Request(self.base, True))
        self.assertEqual("mirror_dirty", caught.exception.code)
        (self.mirror / "dirty.txt").unlink()
        run_git(self.mirror, "checkout", "--detach", self.base)
        with self.assertRaises(public.SyncError) as caught:
            public.synchronize(public.Request(self.base, True))
        self.assertEqual("mirror_not_attached_master", caught.exception.code)

    def test_cleans_stale_operation_refs_and_reports_cleanup_failure(self) -> None:
        stale = f"{public.OPERATION_NAMESPACE}/stale"
        run_git(self.mirror, "update-ref", stale, self.base)
        public.synchronize(public.Request(self.base, True))
        self.assertEqual([], self.refs(public.OPERATION_NAMESPACE))

        run_git(self.mirror, "update-ref", stale, self.base)
        with (
            mock.patch.object(
                public,
                "delete_operation_ref",
                side_effect=public.SyncError(
                    "operation_ref_cleanup_failed",
                    "injected cleanup failure",
                ),
            ),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.synchronize(public.Request(self.base, True))
        self.assertEqual("operation_ref_cleanup_failed", caught.exception.code)

    def test_lock_contention_fails_closed(self) -> None:
        self.lock.touch(mode=0o600)
        self.lock.chmod(0o600)
        with self.lock.open("r+") as held:
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(public.SyncError) as caught:
                public.synchronize(public.Request(self.base, True))
        self.assertEqual("already_running", caught.exception.code)

    def test_permission_errors_fail_closed(self) -> None:
        self.mirror.chmod(0o777)
        try:
            with self.assertRaises(public.SyncError) as caught:
                public.synchronize(public.Request(self.base, True))
            self.assertEqual("mirror_unsafe", caught.exception.code)
        finally:
            self.mirror.chmod(0o700)

    def test_cas_reset_operation_cleanup_and_receipt_faults_rollback(self) -> None:
        target = self.commit_source("fault target\n")
        fault_cases = (
            (
                "advance_master",
                public.SyncError("master_cas_failed", "injected"),
                "master_cas_failed",
            ),
            (
                "reset_and_verify",
                public.SyncError("postcondition_failed", "injected"),
                "postcondition_failed",
            ),
            (
                "delete_operation_ref",
                public.SyncError("operation_ref_cleanup_failed", "injected"),
                "operation_ref_cleanup_failed",
            ),
            (
                "write_receipt",
                public.SyncError("receipt_write_failed", "injected"),
                "receipt_write_failed",
            ),
        )
        for attribute, failure, expected in fault_cases:
            with self.subTest(stage=attribute):
                run_git(self.mirror, "reset", "--hard", self.base)
                run_git(self.mirror, "update-ref", public.MASTER_REF, self.base)
                for ref in self.refs(public.OPERATION_NAMESPACE):
                    run_git(self.mirror, "update-ref", "-d", ref)
                real_delete = public.delete_operation_ref
                if attribute == "delete_operation_ref":
                    calls = 0

                    def fail_current_operation_once(ref: str) -> None:
                        nonlocal calls
                        calls += 1
                        if calls == 1:
                            raise failure
                        real_delete(ref)

                    replacement = fail_current_operation_once
                else:
                    replacement = mock.DEFAULT
                patcher = (
                    mock.patch.object(public, attribute, side_effect=failure)
                    if replacement is mock.DEFAULT
                    else mock.patch.object(public, attribute, side_effect=replacement)
                )
                with patcher, self.assertRaises(public.SyncError) as caught:
                    public.synchronize(public.Request(target, False))
                self.assertEqual(expected, caught.exception.code)
                self.assertEqual(self.base, self.mirror_head())

    def test_backup_and_master_mutate_then_raise_use_observed_ref_state(self) -> None:
        target = self.commit_source("mutate then raise\n")
        real_git = public.git
        injected = {"backup": False, "master": False}

        def mutate_then_raise(*args: str, **kwargs: object):
            if args[:2] == ("update-ref", public.MASTER_REF) and not injected["master"]:
                injected["master"] = True
                real_git(*args, **kwargs)
                raise OSError("injected after master mutation")
            if (
                args[:1] == ("update-ref",)
                and len(args) > 1
                and args[1].startswith(f"{public.BACKUP_NAMESPACE}/")
                and not injected["backup"]
            ):
                injected["backup"] = True
                real_git(*args, **kwargs)
                raise OSError("injected after backup mutation")
            return real_git(*args, **kwargs)

        with mock.patch.object(public, "git", side_effect=mutate_then_raise):
            applied = public.synchronize(public.Request(target, False))
        self.assertEqual("applied", applied["status"])
        self.assertTrue(all(injected.values()))
        self.assertEqual(target, self.mirror_head())
        self.assertEqual(
            self.base,
            run_git(self.mirror, "rev-parse", applied["backup_ref"]),
        )

    def test_unprovable_backup_and_master_ref_states_use_dedicated_codes(self) -> None:
        target = self.commit_source("target\n", "target")
        later = self.commit_source("later\n", "later")
        run_git(self.mirror, "fetch", str(self.source), later)
        state = public.validate_mirror()
        real_git = public.git

        def corrupt_backup(*args: str, **kwargs: object):
            if args[:1] == ("update-ref",) and args[1].startswith(
                f"{public.BACKUP_NAMESPACE}/"
            ):
                real_git("update-ref", args[1], target, public.ZERO_OID, cwd=self.mirror)
                raise OSError("injected")
            return real_git(*args, **kwargs)

        with (
            mock.patch.object(public, "git", side_effect=corrupt_backup),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.create_backup_ref(state, "corrupt-backup")
        self.assertEqual("backup_ref_state_uncertain", caught.exception.code)

        def corrupt_master(*args: str, **kwargs: object):
            if args[:2] == ("update-ref", public.MASTER_REF):
                real_git(
                    "update-ref",
                    public.MASTER_REF,
                    later,
                    self.base,
                    cwd=self.mirror,
                )
                raise OSError("injected")
            return real_git(*args, **kwargs)

        with (
            mock.patch.object(public, "git", side_effect=corrupt_master),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.advance_master(state, target)
        self.assertEqual("master_ref_state_uncertain", caught.exception.code)

    def test_rollback_failure_and_receipt_uncertain_have_distinct_semantics(self) -> None:
        target = self.commit_source("uncertain target\n")
        with (
            mock.patch.object(
                public,
                "reset_and_verify",
                side_effect=public.SyncError("postcondition_failed", "injected"),
            ),
            mock.patch.object(
                public,
                "rollback_master",
                side_effect=public.SyncError("rollback_cas_failed", "injected"),
            ),
            self.assertRaises(public.SyncError) as caught,
        ):
            public.synchronize(public.Request(target, False))
        self.assertEqual("rollback_failed", caught.exception.code)

        run_git(self.mirror, "reset", "--hard", self.base)
        run_git(self.mirror, "update-ref", public.MASTER_REF, self.base)
        with (
            mock.patch.object(
                public,
                "write_receipt",
                side_effect=public.SyncError("receipt_state_uncertain", "injected"),
            ),
            mock.patch.object(public, "rollback_master") as rollback,
            self.assertRaises(public.SyncError) as caught,
        ):
            public.synchronize(public.Request(target, False))
        self.assertEqual("receipt_state_uncertain", caught.exception.code)
        rollback.assert_not_called()
        self.assertEqual(target, self.mirror_head())


if __name__ == "__main__":
    unittest.main()
