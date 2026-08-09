from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "governance-release.yml"


class GovernanceReleaseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_triggers_only_push_master_and_manual_target(self) -> None:
        self.assertRegex(
            self.source,
            r"(?ms)^on:\n  push:\n    branches:\n      - master\n  workflow_dispatch:",
        )
        self.assertIn("target_commit:", self.source)
        for forbidden in ("pull_request:", "schedule:", "repository_dispatch:"):
            self.assertNotIn(forbidden, self.source)

    def test_has_contents_write_and_pinned_checkout(self) -> None:
        self.assertIn("permissions:\n  contents: write", self.source)
        checkout = re.search(r"uses: actions/checkout@([0-9a-f]{40})", self.source)
        self.assertIsNotNone(checkout)
        self.assertNotIn("actions/checkout@v", self.source)
        self.assertIn("ref: master", self.source)
        self.assertIn("fetch-depth: 0", self.source)
        self.assertIn("persist-credentials: false", self.source)

    def test_target_is_exact_commit_reachable_from_origin_master(self) -> None:
        for required in (
            "test \"$(printf '%s' \"$target\" | wc -c)\" -eq 40",
            "*[!0-9a-f]*",
            'git cat-file -e "$target^{commit}"',
            "git rev-parse refs/remotes/origin/master",
            'git merge-base --is-ancestor "$target" "$master"',
        ):
            self.assertIn(required, self.source)

    def test_builds_complete_master_bundle_and_exact_canonical_manifest(self) -> None:
        self.assertIn(
            "git bundle create governance.bundle refs/heads/master", self.source
        )
        self.assertIn("git bundle verify governance.bundle", self.source)
        self.assertIn('"schema_version": 1', self.source)
        self.assertIn('"commit": os.environ["TARGET_COMMIT"]', self.source)
        self.assertIn('"name": "governance.bundle"', self.source)
        self.assertIn('"sha256": hashlib.sha256(bundle.read_bytes()).hexdigest()', self.source)
        self.assertIn('"size": bundle.stat().st_size', self.source)
        self.assertIn(
            'json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\\n"',
            self.source,
        )

    def test_release_tag_is_commit_bound(self) -> None:
        self.assertIn("tag=governance-sync-%s", self.source)
        self.assertIn("TARGET_COMMIT: ${{ steps.target.outputs.commit }}", self.source)
        self.assertIn("RELEASE_TAG: ${{ steps.target.outputs.tag }}", self.source)

    def test_publisher_step_has_only_token_target_and_tag_environment(self) -> None:
        step = self.source.split(
            "      - name: Create and verify immutable release\n", maxsplit=1
        )[1]
        self.assertRegex(
            step,
            re.compile(
                r"^        env:\n"
                r"          GH_TOKEN: .+\n"
                r"          TARGET_COMMIT: .+\n"
                r"          RELEASE_TAG: .+\n"
                r"        run: python3 scripts/publish-governance-release\.py\n?$"
            ),
        )
        self.assertNotIn("REPOSITORY:", step)


if __name__ == "__main__":
    unittest.main()
