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
from contextlib import nullcontext, redirect_stderr, redirect_stdout
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
    def test_accepts_exactly_five_commands(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        upload_id = "c" * 32
        self.assertEqual(("upload", "1"), gate.parse_command("upload 1"))
        self.assertEqual(
            ("upload", str(64 * 1024 * 1024)),
            gate.parse_command(f"upload {64 * 1024 * 1024}"),
        )
        self.assertEqual(
            ("upload-chunk", upload_id, "9", "0", "4"),
            gate.parse_command(f"upload-chunk {upload_id} 9 0 4"),
        )
        self.assertEqual(
            ("upload-chunk", upload_id, str(64 * 1024 * 1024), "1", "1"),
            gate.parse_command(
                f"upload-chunk {upload_id} {64 * 1024 * 1024} 1 1"
            ),
        )
        self.assertEqual(("cleanup",), gate.parse_command("cleanup"))
        self.assertEqual(("apply", commit, digest), gate.parse_command(f"apply {commit} {digest}"))
        self.assertEqual(
            ("dry-run", commit, digest),
            gate.parse_command(f"dry-run {commit} {digest}"),
        )

    def test_rejects_shell_syntax_whitespace_and_malformed_values(self) -> None:
        commit = "a" * 40
        digest = "b" * 64
        upload_id = "c" * 32
        rejected = (
            None,
            "",
            "upload",
            "upload 0",
            "upload 01",
            "upload +1",
            "upload 1.0",
            f"upload {64 * 1024 * 1024 + 1}",
            "upload extra",
            "upload-chunk",
            "upload-chunk abc 8 0 1",
            f"upload-chunk {'C' * 32} 8 0 1",
            f"upload-chunk {upload_id} 0 0 1",
            f"upload-chunk {upload_id} 01 0 1",
            f"upload-chunk {upload_id} 8 00 1",
            f"upload-chunk {upload_id} 8 +0 1",
            f"upload-chunk {upload_id} 8 0 0",
            f"upload-chunk {upload_id} 8 0 01",
            f"upload-chunk {upload_id} 8 8 1",
            f"upload-chunk {upload_id} 8 7 2",
            f"upload-chunk {upload_id} {64 * 1024 * 1024 + 1} 0 1",
            f"upload-chunk {upload_id} 8 0 1 extra",
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

    def test_main_emits_chunk_and_final_json_with_upload_id_protocol(self) -> None:
        upload_id = "d" * 32
        for published, expected in (
            (
                False,
                {"status": "chunk_uploaded", "offset": 4, "total": 8},
            ),
            (True, {"status": "uploaded"}),
        ):
            stdout = io.StringIO()
            with (
                self.subTest(published=published),
                mock.patch.object(gate, "runtime_identity", return_value=(10, 20)),
                mock.patch.object(
                    gate,
                    "incoming_gate",
                    return_value=nullcontext(99),
                ),
                mock.patch.object(
                    gate,
                    "upload_chunk",
                    return_value=published,
                ) as upload_chunk,
                mock.patch.dict(
                    os.environ,
                    {
                        "SSH_ORIGINAL_COMMAND":
                            f"upload-chunk {upload_id} 8 0 4"
                    },
                    clear=False,
                ),
                redirect_stdout(stdout),
            ):
                self.assertEqual(0, gate.main([]))
            self.assertEqual(expected, json.loads(stdout.getvalue()))
            upload_chunk.assert_called_once_with(
                99,
                10,
                20,
                upload_id,
                8,
                0,
                4,
            )

    def test_main_emits_stable_json_for_chunk_transaction_mismatch(self) -> None:
        upload_id = "e" * 32
        stderr = io.StringIO()
        with (
            mock.patch.object(gate, "runtime_identity", return_value=(10, 20)),
            mock.patch.object(
                gate,
                "incoming_gate",
                return_value=nullcontext(99),
            ),
            mock.patch.object(
                gate,
                "upload_chunk",
                side_effect=gate.GateError("upload_transaction_mismatch"),
            ),
            mock.patch.dict(
                os.environ,
                {
                    "SSH_ORIGINAL_COMMAND":
                        f"upload-chunk {upload_id} 8 4 4"
                },
                clear=False,
            ),
            redirect_stderr(stderr),
        ):
            self.assertEqual(1, gate.main([]))
        self.assertEqual(
            {
                "status": "error",
                "error_code": "upload_transaction_mismatch",
            },
            json.loads(stderr.getvalue()),
        )


class UploadTests(unittest.TestCase):
    UPLOAD_ID = "a" * 32

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

    def upload(self, content, expected_size: int | None = None) -> None:
        if expected_size is None:
            expected_size = len(content.getvalue())
        with mock.patch.object(gate, "global_gate_lock", side_effect=nullcontext):
            with gate.incoming_gate(self.uid, self.gid) as directory_fd:
                gate.upload_bundle(
                    directory_fd,
                    self.uid,
                    self.gid,
                    expected_size,
                    content,
                )

    def upload_chunk(
        self,
        content,
        *,
        total: int,
        offset: int,
        length: int | None = None,
        upload_id: str | None = None,
    ) -> bool:
        if length is None:
            length = len(content.getvalue())
        if upload_id is None:
            upload_id = self.UPLOAD_ID
        with mock.patch.object(gate, "global_gate_lock", side_effect=nullcontext):
            with gate.incoming_gate(self.uid, self.gid) as directory_fd:
                return gate.upload_chunk(
                    directory_fd,
                    self.uid,
                    self.gid,
                    upload_id,
                    total,
                    offset,
                    length,
                    content,
                )

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

    def test_upload_short_fails_and_cleans_temporary_file(self) -> None:
        with self.assertRaises(gate.GateError) as caught:
            self.upload(io.BytesIO(b"1234567"), expected_size=8)
        self.assertEqual("upload_short", caught.exception.code)
        self.assertFalse((self.incoming / gate.BUNDLE_NAME).exists())
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())

    def test_upload_chunk_preserves_complete_chunks_and_publishes_only_last(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        upload = self.incoming / gate.UPLOAD_NAME
        meta = self.incoming / gate.UPLOAD_META_NAME

        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"1234"), total=9, offset=0)
        )
        self.assertFalse(bundle.exists())
        self.assertEqual(b"1234", upload.read_bytes())
        self.assertEqual(
            {"id": self.UPLOAD_ID, "total": 9},
            json.loads(meta.read_text(encoding="ascii")),
        )
        self.assertEqual(0o600, stat.S_IMODE(meta.stat().st_mode))

        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"567"), total=9, offset=4)
        )
        self.assertFalse(bundle.exists())
        self.assertEqual(b"1234567", upload.read_bytes())

        self.assertTrue(
            self.upload_chunk(io.BytesIO(b"89"), total=9, offset=7)
        )
        self.assertEqual(b"123456789", bundle.read_bytes())
        self.assertFalse(upload.exists())
        self.assertFalse(meta.exists())

    def test_upload_chunk_rejects_cross_total_and_interleaved_id(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"1234"), total=8, offset=0)
        )
        for upload_id, total in (("b" * 32, 8), (self.UPLOAD_ID, 9)):
            with (
                self.subTest(upload_id=upload_id, total=total),
                self.assertRaises(gate.GateError) as caught,
            ):
                self.upload_chunk(
                    io.BytesIO(b"56"),
                    upload_id=upload_id,
                    total=total,
                    offset=4,
                )
            self.assertEqual("upload_transaction_mismatch", caught.exception.code)
            self.assertEqual(b"1234", upload.read_bytes())
        self.assertTrue(
            self.upload_chunk(io.BytesIO(b"5678"), total=8, offset=4)
        )

    def test_upload_chunk_replay_is_rejected_without_mutation(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"1234"), total=8, offset=0)
        )
        for offset, expected_code in (
            (0, "upload_pending"),
            (2, "upload_offset_mismatch"),
        ):
            with (
                self.subTest(offset=offset),
                self.assertRaises(gate.GateError) as caught,
            ):
                self.upload_chunk(
                    io.BytesIO(b"xx"),
                    total=8,
                    offset=offset,
                )
            self.assertEqual(expected_code, caught.exception.code)
            self.assertEqual(b"1234", upload.read_bytes())

    def test_upload_chunk_short_read_rolls_back_only_current_chunk(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"complete"), total=12, offset=0)
        )

        with self.assertRaises(gate.GateError) as caught:
            self.upload_chunk(
                io.BytesIO(b"xy"),
                total=12,
                offset=8,
                length=4,
            )
        self.assertEqual("upload_short", caught.exception.code)
        self.assertEqual(b"complete", upload.read_bytes())
        self.assertFalse((self.incoming / gate.BUNDLE_NAME).exists())

        self.assertTrue(
            self.upload_chunk(io.BytesIO(b"done"), total=12, offset=8)
        )
        self.assertEqual(
            b"completedone",
            (self.incoming / gate.BUNDLE_NAME).read_bytes(),
        )

    def test_upload_chunk_rejects_nonsequential_offset_without_mutation(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"1234"), total=8, offset=0)
        )
        with self.assertRaises(gate.GateError) as caught:
            self.upload_chunk(io.BytesIO(b"xx"), total=8, offset=3)
        self.assertEqual("upload_offset_mismatch", caught.exception.code)
        self.assertEqual(b"1234", upload.read_bytes())

    def test_upload_chunk_first_short_read_removes_empty_transaction(self) -> None:
        with self.assertRaises(gate.GateError) as caught:
            self.upload_chunk(
                io.BytesIO(b"x"),
                total=4,
                offset=0,
                length=2,
            )
        self.assertEqual("upload_short", caught.exception.code)
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())
        self.assertFalse((self.incoming / gate.UPLOAD_META_NAME).exists())

    def test_upload_chunk_recovers_source_runtime_and_type_errors(self) -> None:
        class BrokenInput:
            def __init__(self, failure: Exception) -> None:
                self.failure = failure

            def read(self, size: int) -> bytes:
                raise self.failure

        for failure_type in (RuntimeError, TypeError):
            for offset in (0, 4):
                with self.subTest(failure_type=failure_type, offset=offset):
                    if offset:
                        self.assertFalse(
                            self.upload_chunk(
                                io.BytesIO(b"safe"),
                                total=8,
                                offset=0,
                            )
                        )
                    with self.assertRaises(gate.GateError) as caught:
                        self.upload_chunk(
                            BrokenInput(failure_type("injected read failure")),
                            total=8,
                            offset=offset,
                            length=2,
                        )
                    self.assertEqual("upload_failed", caught.exception.code)
                    upload = self.incoming / gate.UPLOAD_NAME
                    meta = self.incoming / gate.UPLOAD_META_NAME
                    if offset:
                        self.assertEqual(b"safe", upload.read_bytes())
                        self.assertTrue(meta.exists())
                        upload.unlink()
                        meta.unlink()
                    else:
                        self.assertFalse(upload.exists())
                        self.assertFalse(meta.exists())

    def test_upload_chunk_recovers_before_reraising_interrupts(self) -> None:
        class InterruptedInput:
            def __init__(self, failure: BaseException) -> None:
                self.failure = failure

            def read(self, size: int) -> bytes:
                raise self.failure

        for failure_type in (SystemExit, KeyboardInterrupt):
            for offset in (0, 4):
                with self.subTest(failure_type=failure_type, offset=offset):
                    if offset:
                        self.assertFalse(
                            self.upload_chunk(
                                io.BytesIO(b"safe"),
                                total=8,
                                offset=0,
                            )
                        )
                    with self.assertRaises(failure_type):
                        self.upload_chunk(
                            InterruptedInput(failure_type()),
                            total=8,
                            offset=offset,
                            length=2,
                        )
                    upload = self.incoming / gate.UPLOAD_NAME
                    meta = self.incoming / gate.UPLOAD_META_NAME
                    if offset:
                        self.assertEqual(b"safe", upload.read_bytes())
                        upload.unlink()
                        meta.unlink()
                    else:
                        self.assertFalse(upload.exists())
                        self.assertFalse(meta.exists())

    def test_upload_chunk_first_creation_faults_clean_created_identities(self) -> None:
        real_operations = {
            "open": gate.os.open,
            "fstat": gate.os.fstat,
            "fchown": gate.os.fchown,
            "fchmod": gate.os.fchmod,
            "validate": gate._safe_opened_file,
        }
        cases = (
            ("upload-open", "open", 1),
            ("meta-open", "open", 2),
            ("upload-fstat", "fstat", 1),
            ("meta-fstat", "fstat", 3),
            ("upload-fchown", "fchown", 1),
            ("meta-fchown", "fchown", 2),
            ("upload-fchmod", "fchmod", 1),
            ("meta-fchmod", "fchmod", 2),
            ("upload-validate", "validate", 1),
            ("meta-validate", "validate", 2),
        )

        for label, operation, fail_at in cases:
            with self.subTest(stage=label):
                calls = 0
                real_operation = real_operations[operation]

                def fail_nth(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        if operation == "validate":
                            raise gate.GateError("upload_unsafe")
                        raise OSError(f"injected {label} failure")
                    return real_operation(*args, **kwargs)

                target = gate if operation == "validate" else gate.os
                attribute = (
                    "_safe_opened_file" if operation == "validate" else operation
                )
                with (
                    mock.patch.object(
                        gate,
                        "global_gate_lock",
                        side_effect=nullcontext,
                    ),
                    gate.incoming_gate(self.uid, self.gid) as directory_fd,
                    mock.patch.object(target, attribute, side_effect=fail_nth),
                    self.assertRaises(gate.GateError) as caught,
                ):
                    gate.upload_chunk(
                        directory_fd,
                        self.uid,
                        self.gid,
                        self.UPLOAD_ID,
                        8,
                        0,
                        4,
                        io.BytesIO(b"data"),
                    )
                self.assertEqual(
                    "upload_unsafe" if operation == "validate" else "upload_failed",
                    caught.exception.code,
                )
                self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())
                self.assertFalse((self.incoming / gate.UPLOAD_META_NAME).exists())

    def test_upload_chunk_rollback_failure_reports_unknown_and_keeps_staging(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"safe"), total=8, offset=0)
        )
        with (
            mock.patch.object(
                gate.os,
                "ftruncate",
                side_effect=OSError("injected rollback failure"),
            ),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload_chunk(
                io.BytesIO(b"x"),
                total=8,
                offset=4,
                length=2,
            )
        self.assertEqual("upload_state_unknown", caught.exception.code)
        self.assertTrue(upload.exists())
        self.assertFalse((self.incoming / gate.BUNDLE_NAME).exists())

    def test_upload_chunk_rollback_fsync_failure_reports_unknown(self) -> None:
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"safe"), total=8, offset=0)
        )
        with (
            mock.patch.object(
                gate.os,
                "fsync",
                side_effect=OSError("injected rollback fsync failure"),
            ),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload_chunk(
                io.BytesIO(b"x"),
                total=8,
                offset=4,
                length=2,
            )
        self.assertEqual("upload_state_unknown", caught.exception.code)

    def test_upload_chunk_first_rollback_unlink_failure_reports_unknown(self) -> None:
        with (
            mock.patch.object(
                gate.os,
                "unlink",
                side_effect=OSError("injected rollback unlink failure"),
            ),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload_chunk(
                io.BytesIO(b"x"),
                total=4,
                offset=0,
                length=2,
            )
        self.assertEqual("upload_state_unknown", caught.exception.code)

    def test_upload_chunk_fsyncs_every_complete_block_and_publish_directory(self) -> None:
        real_fsync = os.fsync
        fsync_types: list[str] = []

        def record_fsync(fd: int) -> None:
            fsync_types.append(
                "directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file"
            )
            real_fsync(fd)

        with mock.patch.object(gate.os, "fsync", side_effect=record_fsync):
            self.assertFalse(
                self.upload_chunk(io.BytesIO(b"first"), total=10, offset=0)
            )
            self.assertTrue(
                self.upload_chunk(io.BytesIO(b"final"), total=10, offset=5)
            )
        self.assertEqual(
            ["file", "file", "directory", "file", "directory"],
            fsync_types,
        )

    def test_upload_chunk_first_success_fsyncs_both_files_then_directory(self) -> None:
        real_fsync = os.fsync
        fsync_names: list[str] = []

        def record_fsync(fd: int) -> None:
            metadata = os.fstat(fd)
            if stat.S_ISDIR(metadata.st_mode):
                fsync_names.append("directory")
            else:
                upload_inode = (self.incoming / gate.UPLOAD_NAME).stat().st_ino
                fsync_names.append(
                    "upload" if metadata.st_ino == upload_inode else "meta"
                )
            real_fsync(fd)

        with mock.patch.object(gate.os, "fsync", side_effect=record_fsync):
            self.assertFalse(
                self.upload_chunk(io.BytesIO(b"first"), total=10, offset=0)
            )
        self.assertEqual(["upload", "meta", "directory"], fsync_names)

    def test_upload_chunk_first_directory_fsync_failure_reports_unknown(self) -> None:
        real_fsync = os.fsync

        def fail_directory_fsync(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("injected first directory fsync failure")
            real_fsync(fd)

        with (
            mock.patch.object(gate.os, "fsync", side_effect=fail_directory_fsync),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload_chunk(io.BytesIO(b"first"), total=10, offset=0)
        self.assertEqual("upload_state_unknown", caught.exception.code)
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())
        self.assertFalse((self.incoming / gate.UPLOAD_META_NAME).exists())

    def test_upload_chunk_subsequent_write_opens_upload_with_append(self) -> None:
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"1234"), total=8, offset=0)
        )
        real_open = os.open
        observed_flags: list[int] = []

        def record_open(path, flags, *args, **kwargs):
            if path == gate.UPLOAD_NAME:
                observed_flags.append(flags)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(gate.os, "open", side_effect=record_open):
            self.assertTrue(
                self.upload_chunk(io.BytesIO(b"5678"), total=8, offset=4)
            )
        self.assertTrue(observed_flags)
        self.assertTrue(observed_flags[0] & os.O_APPEND)

    def test_upload_reads_exact_declared_size_without_waiting_for_eof(self) -> None:
        class PartialNonEofInput:
            def __init__(self) -> None:
                self.blocks = [b"12", b"345", b"6789"]
                self.read_sizes: list[int] = []

            def read(self, size: int) -> bytes:
                self.read_sizes.append(size)
                if len(self.read_sizes) > 3:
                    raise AssertionError("upload waited for EOF after reading declared size")
                block = self.blocks.pop(0)
                self.assert_block_fits(block, size)
                return block

            @staticmethod
            def assert_block_fits(block: bytes, size: int) -> None:
                if len(block) > size:
                    raise AssertionError("test input returned more bytes than requested")

        source = PartialNonEofInput()
        self.upload(source, expected_size=9)
        self.assertEqual([9, 7, 4], source.read_sizes)
        self.assertEqual(
            b"123456789",
            (self.incoming / gate.BUNDLE_NAME).read_bytes(),
        )

    def test_upload_failure_does_not_replace_existing_bundle_and_cleans(self) -> None:
        destination = self.incoming / gate.BUNDLE_NAME
        destination.write_bytes(b"trusted")
        destination.chmod(0o600)

        class BrokenInput:
            def read(self, size: int) -> bytes:
                raise OSError("injected read failure")

        with self.assertRaises(gate.GateError) as caught:
            self.upload(BrokenInput(), expected_size=1)
        self.assertEqual("upload_failed", caught.exception.code)
        self.assertEqual(b"trusted", destination.read_bytes())
        self.assertFalse((self.incoming / gate.UPLOAD_NAME).exists())

    def test_upload_never_unlinks_a_replaced_upload_inode(self) -> None:
        upload = self.incoming / gate.UPLOAD_NAME
        real_metadata = gate._fixed_file_metadata

        def replace_before_publish(directory_fd, name, uid, gid, **kwargs):
            if name == gate.UPLOAD_NAME and not kwargs["missing_ok"]:
                replacement = self.incoming / "replacement"
                replacement.write_bytes(b"trusted replacement")
                replacement.chmod(0o600)
                os.replace(replacement, upload)
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
        for name in (
            gate.BUNDLE_NAME,
            gate.UPLOAD_NAME,
            gate.UPLOAD_META_NAME,
        ):
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

    def test_upload_chunk_final_meta_unlink_failure_reports_unknown(self) -> None:
        self.assertFalse(
            self.upload_chunk(io.BytesIO(b"1234"), total=8, offset=0)
        )
        real_unlink = os.unlink

        def fail_meta_unlink(path, **kwargs) -> None:
            if path == gate.UPLOAD_META_NAME:
                raise OSError("injected final meta unlink failure")
            real_unlink(path, **kwargs)

        with (
            mock.patch.object(gate.os, "unlink", side_effect=fail_meta_unlink),
            self.assertRaises(gate.GateError) as caught,
        ):
            self.upload_chunk(io.BytesIO(b"5678"), total=8, offset=4)
        self.assertEqual("upload_state_unknown", caught.exception.code)
        self.assertEqual(
            b"12345678",
            (self.incoming / gate.BUNDLE_NAME).read_bytes(),
        )
        self.assertTrue((self.incoming / gate.UPLOAD_META_NAME).exists())

    def test_cleanup_removes_only_fixed_regular_files_and_fsyncs_directory(self) -> None:
        bundle = self.incoming / gate.BUNDLE_NAME
        upload = self.incoming / gate.UPLOAD_NAME
        meta = self.incoming / gate.UPLOAD_META_NAME
        unrelated = self.incoming / "keep"
        for path in (bundle, upload, meta):
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
        self.assertEqual(
            [gate.BUNDLE_NAME, gate.UPLOAD_NAME, gate.UPLOAD_META_NAME],
            removed,
        )
        self.assertFalse(bundle.exists())
        self.assertFalse(upload.exists())
        self.assertFalse(meta.exists())
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
            st_mode=stat.S_IFDIR | 0o750,
            st_uid=0,
            st_gid=self.gid,
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

    def test_gate_lock_uses_dedicated_directory_not_standard_run_lock(self) -> None:
        self.assertEqual(
            Path("/run/aetheris-governance-sync/gate.lock"),
            gate.GATE_LOCK,
        )
        self.assertNotEqual(Path("/run/lock"), gate.GATE_LOCK.parent)

    def test_rejects_unsafe_dedicated_gate_lock_directory(self) -> None:
        safe_directory, _ = self._safe_lock_metadata()
        unsafe_directories = {
            "symlink": SimpleNamespace(
                **{
                    **safe_directory.__dict__,
                    "st_mode": stat.S_IFLNK | 0o750,
                }
            ),
            "wrong_owner": SimpleNamespace(
                **{**safe_directory.__dict__, "st_uid": 1}
            ),
            "wrong_group": SimpleNamespace(
                **{**safe_directory.__dict__, "st_gid": self.gid + 1}
            ),
            "dedicated_directory_1777": SimpleNamespace(
                **{
                    **safe_directory.__dict__,
                    "st_mode": stat.S_IFDIR | 0o1777,
                }
            ),
            "permissive_0755": SimpleNamespace(
                **{
                    **safe_directory.__dict__,
                    "st_mode": stat.S_IFDIR | 0o755,
                }
            ),
            "different_resolved_inode": SimpleNamespace(
                **{**safe_directory.__dict__, "st_ino": safe_directory.st_ino + 1}
            ),
        }
        for case, unsafe in unsafe_directories.items():
            with self.subTest(case=case):
                resolved = (
                    unsafe
                    if case != "different_resolved_inode"
                    else safe_directory
                )
                with (
                    mock.patch.object(
                        Path,
                        "lstat",
                        side_effect=[unsafe, resolved],
                    ),
                    mock.patch.object(
                        Path,
                        "resolve",
                        return_value=gate.GATE_LOCK.parent,
                    ),
                    mock.patch.object(gate.os, "open") as open_file,
                    self.assertRaises(gate.GateError) as caught,
                ):
                    with gate.global_gate_lock(self.gid):
                        pass
                self.assertEqual(
                    "gate_lock_directory_unsafe",
                    caught.exception.code,
                )
                open_file.assert_not_called()

    def test_rejects_unsafe_gate_lock_inode(self) -> None:
        directory, safe_lock = self._safe_lock_metadata()
        unsafe_locks = {
            "not_regular": SimpleNamespace(
                **{**safe_lock.__dict__, "st_mode": stat.S_IFIFO | 0o640}
            ),
            "wrong_owner": SimpleNamespace(
                **{**safe_lock.__dict__, "st_uid": 1}
            ),
            "wrong_group": SimpleNamespace(
                **{**safe_lock.__dict__, "st_gid": self.gid + 1}
            ),
            "wrong_mode": SimpleNamespace(
                **{**safe_lock.__dict__, "st_mode": stat.S_IFREG | 0o660}
            ),
        }
        for case, unsafe_lock in unsafe_locks.items():
            with self.subTest(case=case):
                with (
                    mock.patch.object(Path, "lstat", return_value=directory),
                    mock.patch.object(
                        Path,
                        "resolve",
                        return_value=gate.GATE_LOCK.parent,
                    ),
                    mock.patch.object(gate.os, "open", return_value=99),
                    mock.patch.object(gate.os, "fstat", return_value=unsafe_lock),
                    mock.patch.object(gate.os, "close") as close,
                    self.assertRaises(gate.GateError) as caught,
                ):
                    with gate.global_gate_lock(self.gid):
                        pass
                self.assertEqual("gate_lock_unsafe", caught.exception.code)
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
