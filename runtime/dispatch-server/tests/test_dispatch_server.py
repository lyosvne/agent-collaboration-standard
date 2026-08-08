import hashlib
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


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SOURCE = ROOT / "dispatch-server.py"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    def __init__(self, auth_key="test-key", read_timeout="5"):
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
        env = os.environ.copy()
        env.update({
            "DISPATCH_DIR": str(dispatch),
            "DISPATCH_PORT": str(self.port),
            "DISPATCH_KEY": auth_key,
            "GOVERNANCE_DIR": str(governance),
            "GOVERNANCE_ROOT": str(governance_root),
            "DRIFT_LATEST": str(drift),
            "GITHUB_RAW_BASE": "http://127.0.0.1:1/unavailable",
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
