from __future__ import annotations

import ast
import platform
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "aetheris-governance-sync"
CONTRACT = ROOT / "contract.md"
SUDOERS = ROOT / "sudoers" / "aetheris-governance-sync"

EXPECTED_PATHS = {
    "MIRROR": "/opt/pi/governance-mirror/repo",
    "BUNDLE": "/var/lib/aetheris-governance-sync/incoming/governance.bundle",
    "LOCK": "/run/lock/aetheris-governance-sync.lock",
    "RECEIPTS": "/var/lib/aetheris-governance-sync/receipts",
}


class DeploymentContractTests(unittest.TestCase):
    def test_fixed_paths_match_contract(self) -> None:
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        assigned: dict[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if (
                isinstance(target, ast.Name)
                and target.id in EXPECTED_PATHS
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "Path"
            ):
                assigned[target.id] = ast.literal_eval(node.value.args[0])
        self.assertEqual(EXPECTED_PATHS, assigned)

        contract = CONTRACT.read_text(encoding="utf-8")
        for path in EXPECTED_PATHS.values():
            self.assertIn(f"`{path}`", contract)

    def test_sudoers_grants_only_installed_helper(self) -> None:
        active = [
            line.strip()
            for line in SUDOERS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(2, len(active))
        self.assertIn(
            "%aetheris-governance-sync ALL=(pi-governance-sync) NOPASSWD: "
            "/usr/local/sbin/aetheris-governance-sync",
            active,
        )
        self.assertNotIn("(root)", "\n".join(active))
        self.assertNotIn("SETENV", "\n".join(active))
        self.assertNotIn("*", "\n".join(active))

    def test_linux_visudo_accepts_drop_in_when_available(self) -> None:
        visudo = shutil.which("visudo")
        if platform.system() != "Linux" or visudo is None:
            self.skipTest("Linux visudo is not available")
        result = subprocess.run(
            [visudo, "-cf", str(SUDOERS)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_contract_documents_security_transaction_and_orphan_policy(self) -> None:
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("`--dry-run`", contract)
        self.assertIn("rollback", contract.lower())
        self.assertIn("allowlist-only JSON", contract)
        self.assertIn("umask `027`", contract)
        self.assertIn("never group-writable", contract)
        self.assertIn("only as a supplementary read group", contract)
        self.assertIn("group ID must equal the helper effective GID", contract)
        self.assertIn("group ID must equal the helper effective IDs", contract)
        self.assertIn("effective UID 0", contract)
        self.assertIn("exclusive writer", contract)
        self.assertIn("deposit an atomically completed bundle", contract)
        self.assertIn("intentional orphan", contract)
        self.assertIn("system group database", contract)
        self.assertIn("effective-UID-owned `0730` incoming", contract)
        self.assertIn("fixed-group `0640` regular non-symlink bundle", contract)
        self.assertIn("Receipt publication tracks", contract)
        self.assertIn("does **not** roll back the mirror", contract)
        self.assertIn("`receipt_state_uncertain`", contract)
        for command in (
            "flock -x 9",
            "chown -R pi-governance-sync",
            "chgrp -R pi-governance-sync",
            r"\( -type d -o -type f \) -exec chmod g+rX",
            "chmod -R go-w",
            "! -user pi-governance-sync",
            "! -group pi-governance-sync",
            "-perm /022",
            "test -z \"$bad\"",
        ):
            self.assertIn(command, contract)
        self.assertIn("stop it and verify it is", contract)
        self.assertIn("`find` is mandatory verification", contract)
        for mode in ("`0755`", "`0440`", "`0730`", "`0640`", "`0700`", "`0600`"):
            self.assertIn(mode, contract)


if __name__ == "__main__":
    unittest.main()
