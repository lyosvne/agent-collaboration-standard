#!/usr/bin/env python3
"""Publish and verify the fixed governance release without replacing conflicts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPOSITORY = "lyosvne/agent-collaboration-standard"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
UPLOADS_ROOT = f"https://uploads.github.com/repos/{REPOSITORY}"
API_VERSION = "2022-11-28"
RELEASE_TAG_PREFIX = "governance-sync-v2-"
ASSET_PATHS = (
    Path("governance-sync-manifest.json"),
    Path("governance.bundle"),
)


class PublishError(RuntimeError):
    """Raised when GitHub does not confirm the exact requested release."""


class GitHub:
    def __init__(self, token: str) -> None:
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
        }

    def request(
        self,
        method: str,
        url: str,
        *,
        expected: int,
        payload: dict[str, Any] | None = None,
        data: bytes | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        if payload is not None:
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            content_type = "application/json"
        headers = dict(self.headers)
        if content_type is not None:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                status = response.status
                body = response.read()
        except urllib.error.HTTPError as error:
            status = error.code
            body = error.read()
        if status != expected:
            detail = body.decode("utf-8", errors="replace")
            raise PublishError(f"{method} {url} returned HTTP {status}, expected {expected}: {detail}")
        if not body:
            return {}
        try:
            value = json.loads(body)
        except json.JSONDecodeError as error:
            raise PublishError(f"{method} {url} returned invalid JSON") from error
        if not isinstance(value, dict):
            raise PublishError(f"{method} {url} returned a non-object JSON response")
        return value

    def require_missing(self, url: str) -> None:
        self.request("GET", url, expected=404)


def asset_expectations() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in ASSET_PATHS:
        try:
            content = path.read_bytes()
        except OSError as error:
            raise PublishError(f"cannot read release asset {path}") from error
        result[path.name] = {
            "name": path.name,
            "size": len(content),
            "digest": f"sha256:{hashlib.sha256(content).hexdigest()}",
            "content": content,
        }
    return result


def require_asset(actual: Any, expected: dict[str, Any]) -> None:
    if not isinstance(actual, dict):
        raise PublishError("release asset is not an object")
    for field in ("name", "size", "digest"):
        if actual.get(field) != expected[field]:
            raise PublishError(
                f"asset {expected['name']} has unexpected {field}: {actual.get(field)!r}"
            )
    if actual.get("state") != "uploaded":
        raise PublishError(
            f"asset {expected['name']} has unexpected state: {actual.get('state')!r}"
        )


def require_assets(actual: Any, expected: dict[str, dict[str, Any]]) -> None:
    if not isinstance(actual, list) or len(actual) != 2:
        raise PublishError("release must contain exactly two assets")
    by_name: dict[str, Any] = {}
    for asset in actual:
        if not isinstance(asset, dict) or not isinstance(asset.get("name"), str):
            raise PublishError("release contains an invalid asset")
        name = asset["name"]
        if name in by_name:
            raise PublishError(f"release contains duplicate asset {name}")
        by_name[name] = asset
    if set(by_name) != set(expected):
        raise PublishError(f"release has unexpected asset names: {sorted(by_name)}")
    for name, wanted in expected.items():
        require_asset(by_name[name], wanted)


def require_release(
    release: dict[str, Any],
    *,
    target: str,
    tag: str,
    draft: bool,
    immutable: bool | None,
    assets: dict[str, dict[str, Any]],
) -> None:
    if release.get("tag_name") != tag:
        raise PublishError("release tag does not match requested tag")
    if release.get("target_commitish") != target:
        raise PublishError("release target does not match requested commit")
    if release.get("name") != tag:
        raise PublishError("release name does not match requested tag")
    if release.get("draft") is not draft:
        raise PublishError(f"release draft state is not {draft}")
    if release.get("prerelease") is not False:
        raise PublishError("release must not be a prerelease")
    if immutable is not None and release.get("immutable") is not immutable:
        raise PublishError(f"release immutable state is not {immutable}")
    require_assets(release.get("assets"), assets)


def require_lightweight_ref(reference: dict[str, Any], target: str) -> None:
    obj = reference.get("object")
    if not isinstance(obj, dict):
        raise PublishError("tag ref response has no object")
    if obj.get("type") != "commit" or obj.get("sha") != target:
        raise PublishError("tag ref is not a lightweight tag for the requested commit")


def publish(token: str, target: str, tag: str) -> None:
    if not token:
        raise PublishError("GH_TOKEN is required")
    if re.fullmatch(r"[0-9a-f]{40}", target) is None:
        raise PublishError("TARGET_COMMIT must be exactly 40 lowercase hexadecimal characters")
    expected_tag = f"{RELEASE_TAG_PREFIX}{target}"
    if tag != expected_tag:
        raise PublishError(f"RELEASE_TAG must equal {expected_tag}")

    github = GitHub(token)
    encoded_tag = urllib.parse.quote(tag, safe="")
    release_by_tag_url = f"{API_ROOT}/releases/tags/{encoded_tag}"
    tag_ref_url = f"{API_ROOT}/git/ref/tags/{encoded_tag}"
    github.require_missing(release_by_tag_url)
    github.require_missing(tag_ref_url)

    expected_assets = asset_expectations()
    created = github.request(
        "POST",
        f"{API_ROOT}/releases",
        expected=201,
        payload={
            "tag_name": tag,
            "target_commitish": target,
            "name": tag,
            "draft": True,
            "prerelease": False,
        },
    )
    release_id = created.get("id")
    if type(release_id) is not int or release_id <= 0:
        raise PublishError("created release has no valid id")

    for path in ASSET_PATHS:
        wanted = expected_assets[path.name]
        upload_url = (
            f"{UPLOADS_ROOT}/releases/{release_id}/assets?"
            + urllib.parse.urlencode({"name": path.name})
        )
        uploaded = github.request(
            "POST",
            upload_url,
            expected=201,
            data=wanted["content"],
            content_type="application/octet-stream",
        )
        require_asset(uploaded, wanted)

    release_url = f"{API_ROOT}/releases/{release_id}"
    draft_release = github.request("GET", release_url, expected=200)
    require_release(
        draft_release,
        target=target,
        tag=tag,
        draft=True,
        immutable=None,
        assets=expected_assets,
    )

    github.request(
        "PATCH",
        release_url,
        expected=200,
        payload={"draft": False},
    )
    final_release = github.request("GET", release_by_tag_url, expected=200)
    require_release(
        final_release,
        target=target,
        tag=tag,
        draft=False,
        immutable=True,
        assets=expected_assets,
    )
    require_lightweight_ref(github.request("GET", tag_ref_url, expected=200), target)


def main() -> int:
    try:
        publish(
            os.environ.get("GH_TOKEN", ""),
            os.environ.get("TARGET_COMMIT", ""),
            os.environ.get("RELEASE_TAG", ""),
        )
    except PublishError as error:
        print(f"publish-governance-release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
