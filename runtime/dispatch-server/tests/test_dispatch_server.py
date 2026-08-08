import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SOURCE = ROOT / "dispatch-server.py"
SOURCE_SPEC = importlib.util.spec_from_file_location("dispatch_server", SOURCE)
DISPATCH_MODULE = importlib.util.module_from_spec(SOURCE_SPEC)
assert SOURCE_SPEC.loader is not None
SOURCE_SPEC.loader.exec_module(DISPATCH_MODULE)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    def __init__(
        self,
        auth_key="test-key",
        read_timeout="5",
        github_fallback_files=None,
    ):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.port = free_port()
        dispatch = self.root / "dispatch"
        self.dispatch = dispatch
        governance_root = self.root / "governance-repo"
        governance = governance_root / "governance"
        dispatch.mkdir()
        governance.mkdir(parents=True)
        (dispatch / "CONTEXT.md").write_text("private context\n")
        (dispatch / "fleet-status.json").write_text("{}\n")
        (dispatch / "survey-zcode.md").write_text("private survey\n")
        (dispatch / "global-roadmap-v1.1.md").write_text("legacy roadmap\n")
        (governance / "north-star-v1.2.md").write_text("# North Star\n")
        (governance / "agent-matrix-architecture-v1.0.md").write_text("# Architecture\n")
        (governance / "fleet-division-v1.1.md").write_text("# Fleet\n")
        (governance / "global-roadmap-v1.1.md").write_text("# Roadmap\n")
        (governance / "version-manifest.json").write_text(json.dumps({
            "schemaVersion": 1,
            "canonicalDocuments": {
                "northStar": {
                    "path": "governance/north-star-v1.2.md",
                    "version": "v1.4",
                    "status": "active",
                },
                "roadmap": {
                    "path": "governance/global-roadmap-v1.1.md",
                    "version": "v1.18",
                    "status": "active",
                },
                "fleetDivision": {
                    "path": "governance/fleet-division-v1.1.md",
                    "version": "v1.2",
                    "status": "active",
                },
                "architecture": {
                    "path": "governance/agent-matrix-architecture-v1.0.md",
                    "version": "v1.1",
                    "status": "active",
                },
            },
        }))
        (governance_root / "START_HERE.md").write_text("# Start\n")
        subprocess.run(["git", "init", "-q", str(governance_root)], check=True)
        subprocess.run(["git", "-C", str(governance_root), "add", "."], check=True)
        subprocess.run(
            [
                "git", "-C", str(governance_root),
                "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                "commit", "-qm", "fixture",
            ],
            check=True,
        )
        drift = self.root / "drift.json"
        drift.write_text('{"timestamp":"test","branches":[]}\n')
        if github_fallback_files:
            raw_root = self.root / "github-raw"
            for relative_path, content in github_fallback_files.items():
                target = raw_root / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            github_raw_base = raw_root.as_uri()
        else:
            github_raw_base = "http://127.0.0.1:1/unavailable"
        env = os.environ.copy()
        env.update({
            "DISPATCH_DIR": str(dispatch),
            "DISPATCH_PORT": str(self.port),
            "DISPATCH_KEY": auth_key,
            "GOVERNANCE_DIR": str(governance),
            "GOVERNANCE_ROOT": str(governance_root),
            "DRIFT_LATEST": str(drift),
            "GITHUB_RAW_BASE": github_raw_base,
            "QODER_PAT": "",
            "HISTORY_BODY_READ_TIMEOUT_SECONDS": read_timeout,
        })
        self.process = subprocess.Popen(
            ["python3", str(SOURCE)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.time() + 5
        while time.time() < deadline:
            if self.process.poll() is not None:
                break
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            self.process.terminate()
            _, details = self.process.communicate(timeout=5)
            self.temp.cleanup()
            raise RuntimeError(f"dispatch test server did not start: {details}")
        if self.process.poll() is not None:
            _, details = self.process.communicate(timeout=5)
            self.temp.cleanup()
            raise RuntimeError(f"dispatch test server exited: {details}")

    def request(self, path, *, key=None, bearer=None, method="GET", body=None):
        headers = {}
        if key is not None:
            headers["X-Dispatch-Key"] = key
        if bearer is not None:
            headers["Authorization"] = f"Bearer {bearer}"
        data = body.encode() if body is not None else None
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            headers=headers,
            method=method,
            data=data,
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, dict(response.headers), response.read().decode()
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read().decode()

    def raw_status(self, request_bytes):
        with socket.create_connection(("127.0.0.1", self.port), timeout=3) as connection:
            connection.sendall(request_bytes)
            response = connection.recv(1024)
        return int(response.split(b" ", 2)[1])

    def commit_governance(self, message, commit_date=None):
        subprocess.run(
            ["git", "-C", str(self.root / "governance-repo"), "add", "-A"],
            check=True,
        )
        env = os.environ.copy()
        if commit_date is not None:
            env["GIT_AUTHOR_DATE"] = commit_date
            env["GIT_COMMITTER_DATE"] = commit_date
        subprocess.run(
            [
                "git", "-C", str(self.root / "governance-repo"),
                "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                "commit", "-qm", message,
            ],
            check=True,
            env=env,
        )

    def close(self):
        if getattr(self, "process", None):
            self.process.terminate()
            self.process.wait(timeout=5)
            if self.process.stderr:
                self.process.stderr.close()
        self.temp.cleanup()


class DispatchRecoveryTests(unittest.TestCase):
    def test_baseline_commit_matches_production_capture(self):
        manifest = json.loads((ROOT / "source-manifest.json").read_text())
        baseline = manifest["productionBaselineCommit"]
        available = subprocess.run(
            ["git", "cat-file", "-e", f"{baseline}^{{commit}}"],
            cwd=REPO,
            capture_output=True,
        )
        if available.returncode != 0:
            self.skipTest("production baseline commit unavailable in shallow checkout")
        for captured in manifest["files"]:
            content = subprocess.check_output(
                ["git", "show", f"{baseline}:runtime/dispatch-server/{captured['path']}"],
                cwd=REPO,
            )
            self.assertEqual(sha256_bytes(content), captured["sha256"])

    def test_public_governance_endpoint_remains_available(self):
        server = Server()
        try:
            status, headers, body = server.request("/dispatch/north-star")
            self.assertEqual(status, 200)
            self.assertIn("text/plain", headers["Content-Type"])
            self.assertEqual(headers["Cache-Control"], "no-cache")
            self.assertIn("# North Star", body)
        finally:
            server.close()

    def test_canonical_unit_uses_dedicated_identity_and_sandbox(self):
        unit = (ROOT / "systemd/pi-dispatch-server.service").read_text()
        self.assertIn("User=pi-dispatch", unit)
        self.assertIn("Group=pi-dispatch", unit)
        self.assertIn("EnvironmentFile=/opt/pi-orchestrator/config/dispatch.env", unit)
        self.assertNotIn("EnvironmentFile=/opt/pi-orchestrator/.env", unit)
        self.assertIn("NoNewPrivileges=true", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("CapabilityBoundingSet=", unit)

    def test_canonical_unit_passes_systemd_verify_when_available(self):
        systemd_analyze = shutil.which("systemd-analyze")
        if systemd_analyze is None:
            self.skipTest("systemd-analyze is unavailable on this platform")
        subprocess.run(
            [
                systemd_analyze,
                "verify",
                str(ROOT / "systemd/pi-dispatch-server.service"),
            ],
            check=True,
        )

    def test_canonical_source_rejects_query_credentials(self):
        source = SOURCE.read_text()
        self.assertNotIn('qs.get("key"', source)
        self.assertIn('"key" in parse_qs', source)

    def test_runtime_endpoints_require_header_key(self):
        server = Server()
        try:
            for endpoint in [
                "/dispatch/all",
                "/dispatch/context",
                "/dispatch/fleet",
                "/dispatch/survey",
                "/dispatch/models",
                "/dispatch/health",
                "/dispatch/drift",
                "/dispatch/history/pi",
            ]:
                self.assertEqual(server.request(endpoint)[0], 403, endpoint)
                self.assertEqual(server.request(endpoint, key="test-key")[0], 200, endpoint)
            self.assertEqual(server.request("/dispatch/health?key=test-key")[0], 400)
            self.assertEqual(server.request("/dispatch/health?key=leaked", key="test-key")[0], 400)
            self.assertEqual(server.request("/dispatch/health", bearer="test-key")[0], 200)
        finally:
            server.close()

    def test_missing_auth_configuration_fails_closed(self):
        server = Server(auth_key="")
        try:
            for endpoint in [
                "/dispatch/all",
                "/dispatch/context",
                "/dispatch/fleet",
                "/dispatch/survey",
                "/dispatch/models",
                "/dispatch/health",
                "/dispatch/drift",
                "/dispatch/history/pi",
            ]:
                status, _, body = server.request(endpoint)
                self.assertEqual(status, 503, endpoint)
                self.assertIn("not configured", body)
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    method="POST",
                    body="{}",
                )[0],
                503,
            )
        finally:
            server.close()

    def test_versions_response_does_not_expose_absolute_paths(self):
        server = Server()
        try:
            status, _, body = server.request("/dispatch/truth/versions")
            self.assertEqual(status, 200)
            payload = json.loads(body)
            self.assertIn("documents", payload)
            self.assertNotIn("governance_dir", payload)
            self.assertNotIn("mirror_root", payload)
            self.assertNotIn(str(server.root), body)
            self.assertEqual(payload["manifest_status"], "ok")
            self.assertFalse(payload["degraded"])
            north_star = payload["documents"]["north-star"]
            self.assertEqual(north_star["version"], "1.2")
            self.assertEqual(north_star["filename_version"], "1.2")
            self.assertEqual(north_star["logical_version"], "1.4")
            self.assertEqual(north_star["version_source"], "manifest")
            self.assertFalse(north_star["degraded"])
            roadmap = payload["documents"]["roadmap"]
            self.assertEqual(roadmap["filename_version"], "1.1")
            self.assertEqual(roadmap["logical_version"], "1.18")
            start_here = payload["documents"]["start-here"]
            self.assertIsNone(start_here["filename_version"])
            self.assertIsNone(start_here["logical_version"])
            self.assertEqual(start_here["version_source"], "unversioned")
        finally:
            server.close()

    def test_versions_degrade_for_malformed_or_missing_manifest(self):
        server = Server()
        manifest = server.root / "governance-repo/governance/version-manifest.json"
        try:
            manifest.write_text("{")
            server.commit_governance("malformed manifest")
            status, _, body = server.request("/dispatch/truth/versions")
            self.assertEqual(status, 200)
            payload = json.loads(body)
            self.assertEqual(payload["manifest_status"], "malformed")
            self.assertTrue(payload["degraded"])
            north_star = payload["documents"]["north-star"]
            self.assertIsNone(north_star["logical_version"])
            self.assertEqual(north_star["version_source"], "filename")
            self.assertIn("manifest-malformed", north_star["degraded_reasons"])

            manifest.unlink()
            server.commit_governance("remove manifest")
            status, _, body = server.request("/dispatch/truth/versions")
            self.assertEqual(status, 200)
            payload = json.loads(body)
            self.assertEqual(payload["manifest_status"], "missing")
            self.assertIn(
                "manifest-missing",
                payload["documents"]["roadmap"]["degraded_reasons"],
            )
        finally:
            server.close()

    def test_versions_use_captured_head_instead_of_dirty_worktree(self):
        server = Server()
        north_star_path = (
            server.root / "governance-repo/governance/north-star-v1.2.md"
        )
        try:
            expected_hash = sha256_bytes(b"# North Star\n")[:12]
            north_star_path.write_text("# DIRTY WORKTREE\n")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            north_star = payload["documents"]["north-star"]
            self.assertEqual(north_star["content_sha12"], expected_hash)
            self.assertEqual(north_star["source"], "mirror")
            self.assertFalse(north_star["degraded"])
            self.assertIsNotNone(north_star["mtime"])
        finally:
            server.close()

    def test_versions_mark_all_documents_if_head_changes_during_request(self):
        handler = object.__new__(DISPATCH_MODULE.DispatchHandler)
        captured = {}
        handler._send_json = lambda payload, status=200: captured.update(payload)
        manifest = {
            "canonicalDocuments": {
                manifest_key: {
                    "path": f"governance/{filename}",
                    "version": "v1.0",
                    "status": "active",
                }
                for key, manifest_key in DISPATCH_MODULE.GOVERNANCE_MANIFEST_KEYS.items()
                for filename in [DISPATCH_MODULE.GOVERNANCE_FILES[key]]
            }
        }
        first_head = "a" * 40
        second_head = "b" * 40
        with (
            patch.object(
                DISPATCH_MODULE,
                "get_mirror_head",
                side_effect=[first_head, second_head],
            ),
            patch.object(
                DISPATCH_MODULE,
                "read_version_manifest",
                return_value=(manifest, "ok"),
            ),
            patch.object(
                DISPATCH_MODULE,
                "read_snapshot_file",
                return_value=(b"# snapshot\n", "ok"),
            ),
            patch.object(
                DISPATCH_MODULE,
                "snapshot_file_commit_time",
                return_value="2026-08-08T00:00:00+00:00",
            ),
        ):
            handler._handle_truth_versions()
        self.assertTrue(captured["degraded"])
        for document in captured["documents"].values():
            self.assertEqual(document["commit_sha"], first_head)
            self.assertIn("mirror-head-changed", document["degraded_reasons"])

    def test_versions_report_successful_github_fallback_as_degraded(self):
        fallback = "# GitHub fallback\n"
        server = Server(github_fallback_files={
            "governance/north-star-v1.2.md": fallback,
        })
        north_star_path = (
            server.root / "governance-repo/governance/north-star-v1.2.md"
        )
        try:
            north_star_path.unlink()
            server.commit_governance("remove mirror north star")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            north_star = payload["documents"]["north-star"]
            self.assertEqual(north_star["source"], "github")
            self.assertFalse(north_star["missing"])
            self.assertIsNone(north_star["mtime"])
            self.assertEqual(
                north_star["content_sha12"],
                sha256_bytes(fallback.encode())[:12],
            )
            self.assertTrue(north_star["degraded"])
            self.assertIn("snapshot-missing", north_star["degraded_reasons"])
            self.assertIn(
                "document-source-github",
                north_star["degraded_reasons"],
            )
        finally:
            server.close()

    def test_versions_mtime_is_last_file_commit_time_at_captured_head(self):
        server = Server()
        north_star = server.root / "governance-repo/governance/north-star-v1.2.md"
        roadmap = server.root / "governance-repo/governance/global-roadmap-v1.1.md"
        try:
            north_star.write_text("# North Star updated\n")
            server.commit_governance(
                "update north star",
                "2026-01-01T00:00:00+00:00",
            )
            north_star_mtime = north_star.stat().st_mtime
            roadmap.write_text("# Roadmap updated\n")
            server.commit_governance(
                "update roadmap",
                "2026-02-01T00:00:00+00:00",
            )
            os.utime(north_star, (north_star_mtime + 1000, north_star_mtime + 1000))

            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            self.assertEqual(
                payload["documents"]["north-star"]["mtime"],
                "2026-01-01T00:00:00Z",
            )
            self.assertEqual(
                payload["documents"]["roadmap"]["mtime"],
                "2026-02-01T00:00:00Z",
            )
        finally:
            server.close()

    def test_versions_degrade_for_invalid_manifest_entry_and_missing_document(self):
        server = Server()
        manifest = server.root / "governance-repo/governance/version-manifest.json"
        north_star_path = (
            server.root / "governance-repo/governance/north-star-v1.2.md"
        )
        try:
            data = json.loads(manifest.read_text())
            del data["canonicalDocuments"]["northStar"]
            manifest.write_text(json.dumps(data))
            server.commit_governance("remove north star entry")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            self.assertIn(
                "manifest-entry-missing",
                payload["documents"]["north-star"]["degraded_reasons"],
            )

            data["canonicalDocuments"]["northStar"] = {
                "path": "governance/other.md",
                "version": "v1.4",
                "status": "active",
            }
            manifest.write_text(json.dumps(data))
            north_star_path.unlink()
            server.commit_governance("mismatch path and remove document")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            north_star = payload["documents"]["north-star"]
            self.assertTrue(north_star["missing"])
            self.assertIn("manifest-path-mismatch", north_star["degraded_reasons"])
            self.assertIn("document-source-missing", north_star["degraded_reasons"])
        finally:
            server.close()

    def test_versions_degrade_for_invalid_schema_status_and_version(self):
        server = Server()
        manifest = server.root / "governance-repo/governance/version-manifest.json"
        try:
            data = json.loads(manifest.read_text())
            data["schemaVersion"] = 2
            manifest.write_text(json.dumps(data))
            server.commit_governance("invalid schema")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            self.assertEqual(payload["manifest_status"], "invalid")

            data["schemaVersion"] = 1
            data["canonicalDocuments"]["northStar"]["status"] = "retired"
            manifest.write_text(json.dumps(data))
            server.commit_governance("inactive entry")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            self.assertIn(
                "manifest-entry-inactive",
                payload["documents"]["north-star"]["degraded_reasons"],
            )

            data["canonicalDocuments"]["northStar"]["status"] = "active"
            data["canonicalDocuments"]["northStar"]["version"] = "latest"
            manifest.write_text(json.dumps(data))
            server.commit_governance("invalid logical version")
            payload = json.loads(
                server.request("/dispatch/truth/versions")[2]
            )
            self.assertIn(
                "manifest-version-invalid",
                payload["documents"]["north-star"]["degraded_reasons"],
            )
        finally:
            server.close()

    def test_public_read_errors_do_not_expose_paths_or_exceptions(self):
        server = Server()
        try:
            roadmap = server.root / "dispatch/global-roadmap-v1.1.md"
            roadmap.unlink()
            roadmap.mkdir()
            status, _, body = server.request("/dispatch/roadmap")
            self.assertEqual(status, 200)
            self.assertEqual(body, "（读取失败）")
            self.assertNotIn(str(server.root), body)

            north_star = server.root / "governance-repo/governance/north-star-v1.2.md"
            north_star.unlink()
            north_star.mkdir()
            status, _, body = server.request("/dispatch/north-star")
            self.assertEqual(status, 200)
            self.assertIn("mirror 和 github 都失败", body)
            self.assertNotIn(str(server.root), body)
            self.assertNotIn("Connection refused", body)
        finally:
            server.close()

    def test_history_write_requires_object_json_and_known_agent(self):
        server = Server()
        try:
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    method="POST",
                    body="{}",
                )[0],
                403,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="wrong-key",
                    method="POST",
                    body="{}",
                )[0],
                403,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="test-key",
                    method="POST",
                    body="not-json",
                )[0],
                400,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="test-key",
                    method="POST",
                    body='{"task":1}',
                )[0],
                400,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi?key=leaked",
                    key="test-key",
                    method="POST",
                    body="{}",
                )[0],
                400,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="test-key",
                    method="POST",
                    body="[]",
                )[0],
                400,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/unknown",
                    key="test-key",
                    method="POST",
                    body="{}",
                )[0],
                404,
            )
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="test-key",
                    method="POST",
                    body='{"caller":"test","task":"safe","status":"done"}',
                )[0],
                200,
            )
        finally:
            server.close()

    def test_history_write_rejects_invalid_or_oversized_content_length(self):
        server = Server()
        try:
            request = (
                b"POST /dispatch/history/pi HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"X-Dispatch-Key: test-key\r\n"
                b"Content-Length: invalid\r\n"
                b"Connection: close\r\n\r\n"
            )
            self.assertEqual(server.raw_status(request), 400)
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="test-key",
                    method="POST",
                    body=json.dumps({"result": "x" * 66000}),
                )[0],
                413,
            )
        finally:
            server.close()

    def test_history_write_enforces_total_body_read_deadline(self):
        server = Server(read_timeout="0.2")
        try:
            headers = (
                b"POST /dispatch/history/pi HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"X-Dispatch-Key: test-key\r\n"
                b"Content-Length: 10\r\n"
                b"Connection: close\r\n\r\n"
            )
            started = time.monotonic()
            with socket.create_connection(("127.0.0.1", server.port), timeout=3) as connection:
                connection.sendall(headers + b"{")
                stop = threading.Event()
                sent = []

                def drip():
                    while not stop.wait(0.05):
                        try:
                            connection.sendall(b" ")
                            sent.append(time.monotonic())
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            break

                sender = threading.Thread(target=drip)
                sender.start()
                try:
                    response = connection.recv(1024)
                finally:
                    stop.set()
                    sender.join(timeout=1)
            self.assertEqual(int(response.split(b" ", 2)[1]), 408)
            self.assertGreaterEqual(len(sent), 3)
            self.assertGreaterEqual(time.monotonic() - started, 0.15)
            self.assertLess(time.monotonic() - started, 0.6)
        finally:
            server.close()

    def test_history_write_normalizes_markdown_and_control_characters(self):
        server = Server()
        try:
            payload = {
                "caller": "test\n### forged",
                "task": "safe ```\n# injected",
                "status": "done\r\nfalse",
                "session_id": "abc\tdef",
                "result": "line one\n```\n## fake governance",
            }
            self.assertEqual(
                server.request(
                    "/dispatch/history/pi",
                    key="test-key",
                    method="POST",
                    body=json.dumps(payload),
                )[0],
                200,
            )
            history = (server.dispatch / "pi/history.md").read_text()
            self.assertNotIn("```", history)
            self.assertNotIn("\n### forged", history)
            self.assertNotIn("\n# injected", history)
            self.assertNotIn("\n## fake governance", history)
            self.assertIn("test ### forged", history)
            self.assertIn("line one ''' ## fake governance", history)
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
