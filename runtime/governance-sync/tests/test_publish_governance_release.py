from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "publish-governance-release.py"
SPEC = importlib.util.spec_from_file_location("publish_governance_release", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)

TARGET = "a" * 40
TAG = f"governance-sync-{TARGET}"


class Response:
    def __init__(self, status: int, body: dict[str, Any] | None = None) -> None:
        self.status = status
        self.body = json.dumps(body or {}).encode("utf-8")

    def __enter__(self) -> Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class SequencedAPI:
    def __init__(self, responses: list[Response]) -> None:
        self.responses = responses
        self.requests: list[Any] = []

    def __call__(self, request: Any, timeout: int) -> Response:
        self.requests.append(request)
        if not self.responses:
            raise AssertionError(f"unexpected request: {request.method} {request.full_url}")
        return self.responses.pop(0)

    @property
    def methods(self) -> list[str]:
        return [request.method for request in self.requests]


class PublishGovernanceReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.contents = {
            "governance-sync-manifest.json": b'{"schema_version":1}\n',
            "governance.bundle": b"test bundle bytes",
        }
        for name, content in self.contents.items():
            Path(name).write_bytes(content)

    def tearDown(self) -> None:
        os.chdir(self.previous_cwd)
        self.temp_dir.cleanup()

    def asset(self, name: str, *, digest: str | None = None) -> dict[str, Any]:
        content = self.contents[name]
        return {
            "name": name,
            "size": len(content),
            "state": "uploaded",
            "digest": digest
            or f"sha256:{hashlib.sha256(content).hexdigest()}",
        }

    def release(
        self, *, draft: bool, immutable: bool | None = None
    ) -> dict[str, Any]:
        value: dict[str, Any] = {
            "id": 7,
            "tag_name": TAG,
            "target_commitish": TARGET,
            "draft": draft,
            "assets": [
                self.asset("governance-sync-manifest.json"),
                self.asset("governance.bundle"),
            ],
        }
        if immutable is not None:
            value["immutable"] = immutable
        return value

    def successful_responses(
        self, *, final_immutable: bool = True
    ) -> list[Response]:
        return [
            Response(404),
            Response(404),
            Response(201, {"id": 7}),
            Response(201, self.asset("governance-sync-manifest.json")),
            Response(201, self.asset("governance.bundle")),
            Response(200, self.release(draft=True)),
            Response(200, self.release(draft=False)),
            Response(
                200,
                self.release(draft=False, immutable=final_immutable),
            ),
            Response(
                200,
                {"object": {"type": "commit", "sha": TARGET}},
            ),
        ]

    def run_with(self, responses: list[Response]) -> SequencedAPI:
        api = SequencedAPI(responses)
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            publisher.publish("token", TARGET, TAG)
        self.assertEqual([], api.responses)
        return api

    def test_success_verifies_http_statuses_fixed_urls_and_final_immutable(self) -> None:
        api = self.run_with(self.successful_responses())

        self.assertEqual(
            [
                "GET", "GET", "POST", "POST", "POST",
                "GET", "PATCH", "GET", "GET",
            ],
            api.methods,
        )
        urls = [request.full_url for request in api.requests]
        self.assertEqual(
            f"{publisher.API_ROOT}/releases/tags/{TAG}",
            urls[0],
        )
        self.assertEqual(f"{publisher.API_ROOT}/git/ref/tags/{TAG}", urls[1])
        self.assertEqual(
            f"{publisher.UPLOADS_ROOT}/releases/7/assets?name=governance-sync-manifest.json",
            urls[3],
        )
        self.assertEqual(
            f"{publisher.UPLOADS_ROOT}/releases/7/assets?name=governance.bundle",
            urls[4],
        )
        create_payload = json.loads(api.requests[2].data)
        self.assertIs(create_payload["draft"], True)
        self.assertEqual(TARGET, create_payload["target_commitish"])
        self.assertEqual(TAG, create_payload["tag_name"])
        self.assertEqual({"draft": False}, json.loads(api.requests[6].data))

    def test_unexpected_http_status_fails_before_create(self) -> None:
        api = SequencedAPI([Response(500, {"message": "failure"})])
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            with self.assertRaisesRegex(publisher.PublishError, "HTTP 500, expected 404"):
                publisher.publish("token", TARGET, TAG)
        self.assertEqual(["GET"], api.methods)

    def test_existing_release_or_tag_ref_is_a_conflict(self) -> None:
        cases = (
            [Response(200, {"id": 1})],
            [Response(404), Response(200, {"ref": f"refs/tags/{TAG}"})],
        )
        for responses in cases:
            with self.subTest(responses=len(responses)):
                api = SequencedAPI(responses)
                with mock.patch.object(publisher.urllib.request, "urlopen", api):
                    with self.assertRaisesRegex(
                        publisher.PublishError, "expected 404"
                    ):
                        publisher.publish("token", TARGET, TAG)
                self.assertNotIn("POST", api.methods)

    def test_tag_must_be_derived_from_target_without_any_request(self) -> None:
        api = SequencedAPI([])
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            with self.assertRaisesRegex(publisher.PublishError, "RELEASE_TAG must equal"):
                publisher.publish("token", TARGET, "governance-sync-wrong")
        self.assertEqual([], api.requests)

    def test_partial_upload_failure_leaves_draft_and_never_patches(self) -> None:
        responses = [
            Response(404),
            Response(404),
            Response(201, {"id": 7}),
            Response(201, self.asset("governance-sync-manifest.json")),
            Response(500, {"message": "upload failed"}),
        ]
        api = SequencedAPI(responses)
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            with self.assertRaisesRegex(publisher.PublishError, "HTTP 500"):
                publisher.publish("token", TARGET, TAG)
        self.assertNotIn("PATCH", api.methods)

    def test_uploaded_digest_mismatch_leaves_draft(self) -> None:
        responses = [
            Response(404),
            Response(404),
            Response(201, {"id": 7}),
            Response(
                201,
                self.asset(
                    "governance-sync-manifest.json",
                    digest=f"sha256:{'0' * 64}",
                ),
            ),
        ]
        api = SequencedAPI(responses)
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            with self.assertRaisesRegex(publisher.PublishError, "unexpected digest"):
                publisher.publish("token", TARGET, TAG)
        self.assertNotIn("PATCH", api.methods)

    def test_final_release_must_be_immutable(self) -> None:
        api = SequencedAPI(self.successful_responses(final_immutable=False))
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            with self.assertRaisesRegex(
                publisher.PublishError, "immutable state is not True"
            ):
                publisher.publish("token", TARGET, TAG)
        self.assertEqual(1, api.methods.count("PATCH"))

    def test_published_immutable_tag_is_rechecked(self) -> None:
        responses = self.successful_responses()
        responses[-1] = Response(
            200,
            {"object": {"type": "commit", "sha": "b" * 40}},
        )
        api = SequencedAPI(responses)
        with mock.patch.object(publisher.urllib.request, "urlopen", api):
            with self.assertRaisesRegex(
                publisher.PublishError,
                "tag ref is not a lightweight tag",
            ):
                publisher.publish("token", TARGET, TAG)
        self.assertEqual(1, api.methods.count("PATCH"))


if __name__ == "__main__":
    unittest.main()
