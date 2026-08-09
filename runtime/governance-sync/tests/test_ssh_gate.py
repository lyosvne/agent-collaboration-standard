from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
import os
import fcntl
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "aetheris-governance-sync-ssh"
SPEC = importlib.util.spec_from_loader(
    "governance_sync_ssh",
    SourceFileLoader("governance_sync_ssh", str(MODULE_PATH)),
)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


class CommandTests(unittest.TestCase):
    def test_accepts_exactly_four_commands(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        self.assertEqual(("upload",), gate.parse_command("upload"))
        self.assertEqual(("cleanup",), gate.parse_command("cleanup"))
        self.assertEqual(("apply", commit, digest), gate.parse_command(f"apply {commit} {digest}"))
        self.assertEqual(
            ("dry-run", commit, digest),
            gate.parse_command(f"dry-run {commit} {digest}"),
        )

    def test_rejects_shell_syntax_whitespace_and_malformed_values(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        rejected = (
            None,
            "",
            "upload extra",
            "cleanup extra",
            f"apply  {commit} {digest}",
            f"apply {commit} {digest};id",
            f"apply {'A' * 40} {digest}",
            f"dry-run {commit} {'b' * 63}",
            f"sync {commit} {digest}",
        )
        for command in rejected:
            with self.subTest(command=command):
                with self.assertRaises(gate.GateError) as caught:
                    gate.parse_command(command)
                self.assertEqual("command_rejected", caught.exception.code)

    def test_requires_pi_sync_effective_ids_without_caller_group(self) -> None:
        with (
            mock.patch.object(
                gate.pwd,
                "getpwnam",
                return_value=SimpleNamespace(pw_uid=1234, pw_gid=2345),
            ) as user_lookup,
            mock.patch.object(gate.os, "geteuid", return_value=1234),
            mock.patch.object(gate.os, "getegid", return_value=2345),
        ):
            self.assertEqual((1234, 2345), gate.runtime_identity())
        user_lookup.assert_called_once_with("pi-governance-sync")

        with (
            mock.patch.object(
                gate.pwd,
                "getpwnam",
                return_value=SimpleNamespace(pw_uid=1234, pw_gid=2345),
            ),
            mock.patch.object(gate.os, "geteuid", return_value=9999),
            mock.patch.object(gate.os, "getegid", return_value=2345),
            self.assertRaises(gate.GateError) as caught,
        ):
            gate.runtime_identity()
        self.assertEqual("sync_identity_required", caught.exception.code)

    def test_helper_uses_fixed_direct_argv_without_sudo_or_shell(self) -> None:
        payload = {
            "status": "dry-run",
            "commit": "a" * 40,
            "sha256": "b" * 64,
            "before_commit": "c" * 40,
            "would_change": True,
        }
        completed = subprocess.CompletedProcess([], 0, json.dumps(payload), "")
        with mock.patch.object(
            gate.subprocess, "run", return_value=completed
        ) as run:
            result = gate.run_helper("dry-run", "a" * 40, "b" * 64)
        self.assertEqual((0, payload), result)
        self.assertEqual(
            [
                "/usr/local/sbin/aetheris-governance-sync",
                "--bundle",
                "/var/lib/aetheris-governance-sync/incoming/governance.bundle",
                "--commit",
                "a" * 40,
                "--sha256",
                "b" * 64,
                "--dry-run",
            ],
            run.call_args.args[0],
        )
        self.assertIs(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertIs(run.call_args.kwargs["stdout"], subprocess.PIPE)
        self.assertIs(run.call_args.kwargs["stderr"], subprocess.PIPE)
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_helper_forwards_only_validated_single_json_object(self) -> None:
        error = {"status": "error", "error_code": "sha256_mismatch"}
        completed = subprocess.CompletedProcess([], 1, "", json.dumps(error))
        with mock.patch.object(gate.subprocess, "run", return_value=completed):
            self.assertEqual(
                (1, error),
                gate.run_helper("apply", "a" * 40, "b" * 64),
            )

        rejected = (
            subprocess.CompletedProcess([], 1, "", "secret traceback"),
            subprocess.CompletedProcess(
                [],
                1,
                "",
                '{"status":"error","error_code":"safe"}\n{"secret":"leak"}',
            ),
            subprocess.CompletedProcess(
                [],
                0,
                json.dumps(
                    {
                        "status": "dry-run",
                        "commit": "a" * 40,
                        "sha256": "b" * 64,
                        "before_commit": "c" * 40,
                        "would_change": True,
                        "stderr": "leak",
                    }
                ),
                "",
            ),
        )
        for result in rejected:
            with (
                self.subTest(result=result),
                mock.patch.object(gate.subprocess, "run", return_value=result),
                self.assertRaises(gate.GateError) as caught,
            ):
                gate.run_helper("dry-run", "a" * 40, "b" * 64)
            self.assertIn(
                caught.exception.code,
                {"helper_failed", "helper_invalid_response"},
            )

    def test_unexpected_failure_emits_stable_json_without_traceback(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.object(
                gate,
                "runtime_identity",
                side_effect=RuntimeError("secret traceback detail"),
            ),
            redirect_stderr(stderr),
        ):
            self.assertEqual(1, gate.main([]))
        self.assertEqual(
            {"status": "error", "error_code": "internal_error"},
            json.loads(stderr.getvalue()),
        )
        self.assertNotIn("secret", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


class UploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.incoming = Path(self.temp.name) / "incoming"
        self.incoming.mkdir(mode=0o700)
        self.incoming.chmod(0o700)
        self.uid = os.geteuid()
        self.gid = os.getgid()
        self.path_patch = mock.patch.multiple(
            gate,
            INCOMING=self.incoming,
            BUNDLE=self.incoming / gate.BUNDLE_NAME,
        )
        self.path_patch.start()

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temp.cleanup()

    def upload(self, content) -> None:
        with mock.patch.object(gate, "global_gate_lock", side_effect=nullcontext):
            with gate.incoming_gate(self.uid, self.gid) as directory_fd:
                gate.upload_bundle(directory_fd, self.uid, self.gid, content)

    def cleanup(self) -> list[str]:
        with mock.patch.object(gate, "global_gate_lock", side_effect=nullcontext):
            with gate.incoming_gate(self.uid, self.gid) as directory_fd:
                return gate.cleanup_bundle(directory_fd, self.uid, self.gid)

    def test_upload_fchowns_regular_file_and_atomically_replaces_destination(self) -> None:
        destination = self.incoming / gate.BUNDLE_NAME
        destination.write_bytes(b"old")
        destination.chmod(0o600)
        real_fchown = os.fchown
        real_replace = os.replace
        observed: dict[str, object] = {}

        def record_fchown(fd: int, uid: int, gid: int) -> None:
            observed["fchown"] = (uid, gid)
            real_fchown(fd, uid, gid)

        def record_replace(src, dst, **kwargs) -> None:
            source_fd = os.open(
                src,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=kwargs["src_dir_fd"],
            )
            try:
                observed["regular_before_rename"] = stat.S_ISREG(os.fstat(source_fd).st_mode)
            finally:
                os.close(source_fd)
            observed["replace"] = (src, dst)
            real_replace(src, dst, **kwargs)

        with (
            mock.patch.object(gate.os, "fchown", side_effect=record_fchown),
            mock.patch.object(gate.os, "replace", side_effect=record_replace),
        ):
            self.upload(io.BytesIO(b"new bundle"))

        self.assertEqual((self.uid, self.gid), observed["fchown"])
        self.assertTrue(observed["regular_before_rename"])
        self.assertEqual(gate.BUNDLE_NAME, observed["replace"][1])
        self.assertEqual(b"new bundle", destination.read_bytes())
        metadata = destination.stat()
        self.assertTrue(stat.S_ISREG(metadata.st_mode))
        self.assertEqual(self.gid, metadata.st_gid)
        self.assertEqual(0o600, stat.S_IMODE(metadata.st_mode))
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())

    def test_upload_enforces_size_limit_and_cleans_temporary_file(self) -> None:
        with (
            mock.patch.object(gate, "MAX_BUNDLE_BYTES", 8),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload(io.BytesIO(b"123456789"))
        self.assertEqual("bundle_too_large", caught.exception.code)
        self.assertFalse((self.incoming / gate.BUNDLE_NAME).exists())
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())

    def test_upload_failure_does_not_replace_existing_bundle_and_cleans(self) -> None:
        destination = self.incoming / gate.BUNDLE_NAME
        destination.write_bytes(b"trusted")
        destination.chmod(0o600)

        class BrokenInput:
            def read(self, size: int) -> bytes:
                raise OSError("injected read failure")

        with self.assertRaises(gate.GateError) as caught:
            self.upload(BrokenInput())
        self.assertEqual("upload_failed", caught.exception.code)
        self.assertEqual(b"trusted", destination.read_bytes())
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())

    def test_upload_never_unlinks_a_replaced_upload_inode(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        real_metadata = gate._fixed_file_metadata

        def replace_before_publish(directory_fd, name, uid, gid, **kwargs):
            if name == gate.UPLOAD_NAME and not kwargs["missing_ok"]:
                upload.unlink()
                upload.write_bytes(b"trusted replacement")
                upload.chmod(0o600)
            return real_metadata(directory_fd, name, uid, gid, **kwargs)

        with (
            mock.patch.object(
                gate,
                "_fixed_file_metadata",
                side_effect=replace_before_publish,
            ),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload(io.BytesIO(b"untrusted upload"))
        self.assertEqual("upload_unsafe", caught.exception.code)
        self.assertEqual(b"trusted replacement", upload.read_bytes())
        self.assertFalse((self.incoming / gate.BUNDLE_NAME).exists())

    def test_rejects_wrong_directory_group_or_mode(self) -> None:
        self.incoming.chmod(0o730)
        with self.assertRaises(gate.GateError) as caught:
            self.upload(io.BytesIO(b"x"))
        self.assertEqual("incoming_unsafe", caught.exception.code)

    def test_rejects_incoming_not_owned_by_effective_sync_user(self) -> None:
        metadata = SimpleNamespace(
            st_mode=stat.S_IFDIR | 0o700,
            st_uid=os.geteuid() + 1,
            st_gid=self.gid,
        )
        with (
            mock.patch.object(gate.os, "open", return_value=99),
            mock.patch.object(gate.os, "fstat", return_value=metadata),
            mock.patch.object(gate.os, "close") as close,
            self.assertRaises(gate.GateError) as caught,
        ):
            gate._open_incoming(self.uid, self.gid)
        self.assertEqual("incoming_unsafe", caught.exception.code)
        close.assert_called_once_with(99)

    def test_upload_and_cleanup_reject_symlink_fifo_and_directory_targets(self) -> None:
        outside = Path(self.temp.name) / "outside"
        outside.write_bytes(b"outside")
        for name in (gate.BUNDLE_NAME, gate.UPLOAD_NAME):
            target = self.incoming / name
            for kind in ("symlink", "fifo", "directory"):
                with self.subTest(name=name, kind=kind):
                    if kind == "symlink":
                        target.symlink_to(outside)
                    elif kind == "fifo":
                        os.mkfifo(target)
                    else:
                        target.mkdir()
                    expected = "bundle_unsafe" if name == gate.BUNDLE_NAME else "upload_unsafe"
                    with self.assertRaises(gate.GateError) as caught:
                        self.cleanup()
                    self.assertEqual(expected, caught.exception.code)
                    self.assertTrue(target.exists() or target.is_symlink())
                    with self.assertRaises(gate.GateError) as caught:
                        self.upload(io.BytesIO(b"x"))
                    self.assertEqual(expected, caught.exception.code)
                    if target.is_dir() and not target.is_symlink():
                        target.rmdir()
                    else:
                        target.unlink()

    def test_cleanup_removes_only_fixed_regular_files_and_fsyncs_directory(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        upload = self.incoming / gate.UPLOAD_NAME
        unrelated = self.incoming / "keep"
        for path in (bundle, upload):
            path.write_bytes(path.name.encode())
            path.chmod(0o600)
        unrelated.write_bytes(b"keep")
        real_fsync = os.fsync
        directory_fsyncs = 0

        def record_fsync(fd: int) -> None:
            nonlocal directory_fsyncs
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                directory_fsyncs += 1
            real_fsync(fd)

        with mock.patch.object(gate.os, "fsync", side_effect=record_fsync):
            removed = self.cleanup()
        self.assertEqual([gate.BUNDLE_NAME, gate.UPLOAD_NAME], removed)
        self.assertFalse(bundle.exists())
        self.assertFalse(upload.exists())
        self.assertEqual(b"keep", unrelated.read_bytes())
        self.assertEqual(1, directory_fsyncs)

    def test_cleanup_validates_all_fixed_inodes_before_deleting_any(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        upload = self.incoming / gate.UPLOAD_NAME
        outside = Path(self.temp.name) / "outside"
        bundle.write_bytes(b"keep")
        bundle.chmod(0o600)
        outside.write_bytes(b"outside")
        upload.symlink_to(outside)

        with self.assertRaises(gate.GateError) as caught:
            self.cleanup()
        self.assertEqual("upload_unsafe", caught.exception.code)
        self.assertEqual(b"keep", bundle.read_bytes())
        self.assertTrue(upload.is_symlink())

    def test_upload_fsyncs_file_and_directory_after_rename(self) -> None:
        real_fsync = os.fsync
        fsync_types: list[str] = []

        def record_fsync(fd: int) -> None:
            fsync_types.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            real_fsync(fd)

        with mock.patch.object(gate.os, "fsync", side_effect=record_fsync):
            self.upload(io.BytesIO(b"bundle"))
        self.assertIn("file", fsync_types)
        self.assertEqual("directory", fsync_types[-1])

    def test_post_rename_directory_fsync_failure_reports_unknown_published_state(self) -> None:
        real_fsync = os.fsync

        def fail_directory_fsync(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("injected directory fsync failure")
            real_fsync(fd)

        with (
            mock.patch.object(gate.os, "fsync", side_effect=fail_directory_fsync),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload(io.BytesIO(b"published-or-not"))
        self.assertEqual("upload_state_unknown", caught.exception.code)
        self.assertEqual(
            b"published-or-not",
            (self.incoming / gate.BUNDLE_NAME).read_bytes(),
        )

    def test_cleanup_partial_failure_still_fsyncs_and_reports_fixed_state(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        upload = self.incoming / gate.UPLOAD_NAME
        for path in (bundle, upload):
            path.write_bytes(path.name.encode())
            path.chmod(0o600)
        real_unlink = os.unlink
        real_fsync = os.fsync
        directory_fsyncs = 0

        def fail_second_unlink(path, **kwargs) -> None:
            if path == gate.UPLOAD_NAME:
                raise OSError("injected unlink failure")
            real_unlink(path, **kwargs)

        def record_fsync(fd: int) -> None:
            nonlocal directory_fsyncs
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                directory_fsyncs += 1
            real_fsync(fd)

        with (
            mock.patch.object(gate.os, "unlink", side_effect=fail_second_unlink),
            mock.patch.object(gate.os, "fsync", side_effect=record_fsync),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.cleanup()
        self.assertEqual("cleanup_partial", caught.exception.code)
        self.assertFalse(bundle.exists())
        self.assertTrue(upload.exists())
        self.assertEqual(1, directory_fsyncs)

    def test_cleanup_fsync_failure_after_deletion_reports_unknown_state(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        bundle.write_bytes(b"bundle")
        bundle.chmod(0o600)

        with (
            mock.patch.object(
                gate.os,
                "fsync",
                side_effect=OSError("injected directory fsync failure"),
            ),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.cleanup()
        self.assertEqual("cleanup_state_unknown", caught.exception.code)
        self.assertFalse(bundle.exists())

    def test_cleanup_unlink_and_fsync_failures_report_unknown_state(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        upload = self.incoming / gate.UPLOAD_NAME
        for path in (bundle, upload):
            path.write_bytes(path.name.encode())
            path.chmod(0o600)
        real_unlink = os.unlink

        def fail_second_unlink(path, **kwargs) -> None:
            if path == gate.UPLOAD_NAME:
                raise OSError("injected unlink failure")
            real_unlink(path, **kwargs)

        with (
            mock.patch.object(gate.os, "unlink", side_effect=fail_second_unlink),
            mock.patch.object(
                gate.os,
                "fsync",
                side_effect=OSError("injected directory fsync failure"),
            ),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.cleanup()
        self.assertEqual("cleanup_state_unknown", caught.exception.code)
        self.assertFalse(bundle.exists())
        self.assertTrue(upload.exists())

    def _safe_lock_metadata(self) -> tuple[SimpleNamespace, SimpleNamespace]:
        directory = SimpleNamespace(
            st_mode=stat.S_IFDIR | 0o755,
            st_uid=0,
            st_gid=0,
            st_dev=1,
            st_ino=2,
        )
        lock = SimpleNamespace(
            st_mode=stat.S_IFREG | 0o640,
            st_uid=0,
            st_gid=self.gid,
        )
        return directory, lock

    def test_all_operations_use_fixed_root_owned_flock_inode(self) -> None:
        directory, lock = self._safe_lock_metadata()
        with (
            mock.patch.object(Path, "lstat", return_value=directory),
            mock.patch.object(Path, "resolve", return_value=gate.GATE_LOCK.parent),
            mock.patch.object(gate.os, "open", return_value=99) as open_file,
            mock.patch.object(gate.os, "fstat", return_value=lock),
            mock.patch.object(gate.fcntl, "flock") as flock,
            mock.patch.object(gate.os, "close") as close,
        ):
            with gate.global_gate_lock(self.gid):
                pass
        open_file.assert_called_once_with(
            gate.GATE_LOCK,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        flock.assert_called_once_with(99, fcntl.LOCK_EX | fcntl.LOCK_NB)
        close.assert_called_once_with(99)

    def test_flock_contention_fails_without_waiting(self) -> None:
        directory, lock = self._safe_lock_metadata()
        with (
            mock.patch.object(Path, "lstat", return_value=directory),
            mock.patch.object(Path, "resolve", return_value=gate.GATE_LOCK.parent),
            mock.patch.object(gate.os, "open", return_value=99),
            mock.patch.object(gate.os, "fstat", return_value=lock),
            mock.patch.object(
                gate.fcntl,
                "flock",
                side_effect=BlockingIOError("in use"),
            ),
            mock.patch.object(gate.os, "close"),
            self.assertRaises(gate.GateError) as caught,
        ):
            with gate.global_gate_lock(self.gid):
                pass
        self.assertEqual("already_running", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
