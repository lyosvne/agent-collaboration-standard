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
SSH_GATE = ROOT / "aetheris-governance-sync-ssh"
SSH_CONTRACT = ROOT / "ssh-gate-contract.md"
SSH_DEPLOYMENT = ROOT / "ssh-gate-deployment.md"
TMPFILES = ROOT / "tmpfiles" / "aetheris-governance-sync.conf"

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

    def test_sudoers_allows_deploy_to_run_only_no_argument_gate(self) -> None:
        active = [
            line.strip()
            for line in SUDOERS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(2, len(active))
        self.assertEqual(
            "Defaults!/usr/local/sbin/aetheris-governance-sync-ssh "
            'secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin, '
            'env_keep += "SSH_ORIGINAL_COMMAND"',
            active[0],
        )
        self.assertEqual(
            "aetheris-sync-deploy ALL=(pi-governance-sync) NOPASSWD: "
            '/usr/local/sbin/aetheris-governance-sync-ssh ""',
            active[1],
        )
        self.assertNotIn("(root)", "\n".join(active))
        self.assertNotIn("SETENV", "\n".join(active))
        self.assertNotIn("*", "\n".join(active))
        self.assertNotIn("%aetheris-governance-sync", "\n".join(active))
        self.assertNotEqual(
            "/usr/local/sbin/aetheris-governance-sync",
            active[1].split()[-1].strip('"'),
        )

    def test_deploy_is_outside_caller_group_and_cannot_write_incoming(self) -> None:
        deployment = SSH_DEPLOYMENT.read_text(encoding="utf-8")
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "gpasswd -d aetheris-sync-deploy aetheris-governance-sync",
            deployment,
        )
        self.assertNotIn(
            "usermod -aG aetheris-governance-sync aetheris-sync-deploy",
            deployment,
        )
        self.assertIn(
            "! sudo -u aetheris-sync-deploy test -w "
            "/var/lib/aetheris-governance-sync/incoming",
            deployment,
        )
        self.assertIn(
            "`aetheris-sync-deploy` identity. It is not a\n"
            "member of `aetheris-governance-sync`, cannot write the incoming directory",
            contract,
        )

    def test_canonical_tmpfiles_creates_root_owned_gate_lock_at_boot(self) -> None:
        self.assertEqual(
            "f /run/lock/aetheris-governance-sync-ssh-gate.lock "
            "0640 root pi-governance-sync -\n",
            TMPFILES.read_text(encoding="utf-8"),
        )

        deployment = SSH_DEPLOYMENT.read_text(encoding="utf-8")
        for requirement in (
            "runtime/governance-sync/tmpfiles/aetheris-governance-sync.conf",
            "/usr/lib/tmpfiles.d",
            "/etc/tmpfiles.d",
            "systemd-tmpfiles --create",
            "test -f /run/lock/aetheris-governance-sync-ssh-gate.lock",
            "test ! -L /run/lock/aetheris-governance-sync-ssh-gate.lock",
            "stat -c '%U:%G:%a'",
            "root:pi-governance-sync:640",
            "recreates it during boot",
        ):
            self.assertIn(requirement, deployment)
        self.assertNotIn(
            "/dev/null /run/lock/aetheris-governance-sync-ssh-gate.lock",
            deployment,
        )

        helper_contract = CONTRACT.read_text(encoding="utf-8")
        gate_contract = SSH_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "canonical `tmpfiles/aetheris-governance-sync.conf`",
            helper_contract,
        )
        for requirement in (
            "`tmpfiles/aetheris-governance-sync.conf`",
            "systemd\n"
            "tmpfiles type `f`, mode `0640`, owner `root`, and group\n"
            "`pi-governance-sync`",
            "`/usr/lib/tmpfiles.d` or `/etc/tmpfiles.d`",
            "`systemd-tmpfiles --create`",
            "with `stat`",
            "after each boot",
        ):
            self.assertIn(requirement, gate_contract)

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
        self.assertRegex(contract, r"exclusive\s+writer")
        self.assertRegex(contract, r"deposits an atomically completed bundle")
        self.assertIn("intentional orphan", contract)
        self.assertNotIn("system group database", contract)
        self.assertIn("effective-ID-owned `0700` incoming", contract)
        self.assertIn("effective-ID-owned `0600` regular non-symlink bundle", contract)
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
        for mode in ("`0755`", "`0440`", "`0640`", "`0700`", "`0600`"):
            self.assertIn(mode, contract)

    def test_ssh_gate_fixed_paths_and_limit_match_contract(self) -> None:
        source = SSH_GATE.read_text(encoding="utf-8")
        self.assertTrue(source.startswith("#!/usr/bin/python3 -I\n"))
        tree = ast.parse(source)
        assigned: dict[str, object] = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if target.id in {"HELPER_USER", "HELPER"}:
                assigned[target.id] = ast.literal_eval(node.value)
            elif target.id == "GATE_LOCK":
                assigned[target.id] = ast.literal_eval(node.value.args[0])
            elif target.id == "MAX_BUNDLE_BYTES":
                self.assertEqual("64 * 1024 * 1024", ast.unparse(node.value))
                assigned[target.id] = 64 * 1024 * 1024
        self.assertEqual(
            {
                "HELPER_USER": "pi-governance-sync",
                "HELPER": "/usr/local/sbin/aetheris-governance-sync",
                "GATE_LOCK": "/run/lock/aetheris-governance-sync-ssh-gate.lock",
                "MAX_BUNDLE_BYTES": 64 * 1024 * 1024,
            },
            assigned,
        )

        contract = SSH_CONTRACT.read_text(encoding="utf-8")
        for required in (
            "`pwd.getpwnam`",
            "effective UID and effective GID",
            "`fchown(fd, sync_uid, sync_gid)`",
            "`O_NOFOLLOW`",
            "nonblocking `flock`",
            "`/run/lock/aetheris-governance-sync-ssh-gate.lock`",
            "`root:pi-governance-sync`",
            "`0640`",
            "`.upload`",
            "regular file",
            "atomically",
            "incoming directory is fsynced",
            "`upload_state_unknown`",
            "may already be published",
            "`cleanup_partial`",
            "`cleanup_state_unknown`",
            "regardless of\nwhether an unlink also failed",
            "64 MiB",
            "directly, without\nsudo",
            "`shell=False`",
            "Raw helper stderr",
            "tracebacks are never forwarded",
        ):
            self.assertIn(required, contract)

    def test_ssh_deployment_documents_hardened_account_and_all_four_commands(self) -> None:
        deployment = SSH_DEPLOYMENT.read_text(encoding="utf-8")
        self.assertIn(
            'restrict,command="sudo -n -u pi-governance-sync '
            '/usr/local/sbin/aetheris-governance-sync-ssh"',
            deployment,
        )
        self.assertIn("visudo -cf", deployment)
        for requirement in (
            "dedicated account `aetheris-sync-deploy`",
            "passwd --lock aetheris-sync-deploy",
            "exactly one forced key",
            "root:root:755",
            "aetheris-sync-deploy:aetheris-sync-deploy:700",
            "aetheris-sync-deploy:aetheris-sync-deploy:600",
            "PermitUserEnvironment no",
            "PasswordAuthentication no",
            "KbdInteractiveAuthentication no",
            "dangerous `AcceptEnv` entries",
            "removed globally",
            "`PYTHONPATH`",
            "`LD_*`",
            "cannot create,\nreplace, or unlink either fixed incoming name",
            "helper probe must be denied",
            "No\nwildcard, alternate arguments, shell, or direct helper command is granted",
            "fixed root-owned lock inode",
        ):
            self.assertIn(requirement, deployment)
        for command in (
            "ssh GOVERNANCE_HOST upload",
            '"dry-run $commit $sha256"',
            '"apply $commit $sha256"',
            "ssh GOVERNANCE_HOST cleanup",
        ):
            self.assertIn(command, deployment)
        self.assertIn(
            "root:pi-governance-sync:640",
            deployment,
        )
        self.assertNotIn("%aetheris-governance-sync", deployment)


if __name__ == "__main__":
    unittest.main()
