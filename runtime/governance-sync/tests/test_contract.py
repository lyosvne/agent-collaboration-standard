from __future__ import annotations

import ast
import json
import os
import platform
import pwd
import shutil
import subprocess
import tempfile
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
            'env_keep += "SSH_ORIGINAL_COMMAND", !use_pty',
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
        self.assertEqual(1, "\n".join(active).count("!use_pty"))
        self.assertTrue(active[0].startswith(
            "Defaults!/usr/local/sbin/aetheris-governance-sync-ssh "
        ))
        self.assertFalse(any(
            line.startswith("Defaults ") and "!use_pty" in line
            for line in active
        ))
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
            "d /run/aetheris-governance-sync "
            "0750 root pi-governance-sync -\n"
            "f /run/aetheris-governance-sync/gate.lock "
            "0640 root pi-governance-sync -\n",
            TMPFILES.read_text(encoding="utf-8"),
        )

        deployment = SSH_DEPLOYMENT.read_text(encoding="utf-8")
        for requirement in (
            "runtime/governance-sync/tmpfiles/aetheris-governance-sync.conf",
            "/usr/lib/tmpfiles.d",
            "/etc/tmpfiles.d",
            "systemd-tmpfiles --create",
            "test -d /run/aetheris-governance-sync",
            "test ! -L /run/aetheris-governance-sync",
            "test -f /run/aetheris-governance-sync/gate.lock",
            "test ! -L /run/aetheris-governance-sync/gate.lock",
            "stat -c '%U:%G:%a'",
            "root:pi-governance-sync:750",
            "root:pi-governance-sync:640",
            "recreates it during boot",
        ):
            self.assertIn(requirement, deployment)
        self.assertNotIn(
            "/dev/null /run/aetheris-governance-sync/gate.lock",
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
            "systemd tmpfiles type `d`, mode `0750`",
            "type `f`, mode `0640`",
            "`/usr/lib/tmpfiles.d` or `/etc/tmpfiles.d`",
            "`systemd-tmpfiles --create`",
            "type, non-symlink status, ownership, and exact mode",
            "directory before the lock",
            "each boot",
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

    def test_linux_sudo_gate_streams_more_than_5_mib_without_a_pty(self) -> None:
        sudo = shutil.which("sudo")
        visudo = shutil.which("visudo")
        if platform.system() != "Linux" or sudo is None or visudo is None:
            self.skipTest("Linux sudo and visudo are required")
        sudo_probe = subprocess.run(
            [sudo, "-n", "true"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if sudo_probe.returncode != 0:
            self.skipTest("passwordless sudo is not available")

        username = pwd.getpwuid(os.getuid()).pw_name
        payload = os.urandom(5 * 1024 * 1024 + 4097)
        drop_in = Path(
            f"/etc/sudoers.d/aetheris-governance-sync-stream-test-{os.getpid()}"
        )
        with tempfile.TemporaryDirectory(prefix="governance-sudo-gate-") as tmp:
            root = Path(tmp)
            gate = root / "stdin-gate"
            gate.write_text(
                "#!/usr/bin/python3 -I\n"
                "import json, os\n"
                "total = 0\n"
                "while True:\n"
                "    chunk = os.read(0, 65536)\n"
                "    if not chunk:\n"
                "        break\n"
                "    total += len(chunk)\n"
                "print(json.dumps({'bytes': total, 'stdin_isatty': os.isatty(0)}))\n",
                encoding="utf-8",
            )
            gate.chmod(0o755)
            candidate = root / "sudoers"
            candidate.write_text(
                f"Defaults:{username} use_pty\n"
                f"Defaults!{gate} !use_pty\n"
                f"{username} ALL=({username}) NOPASSWD: {gate} \"\"\n",
                encoding="utf-8",
            )
            syntax = subprocess.run(
                [visudo, "-cf", str(candidate)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(0, syntax.returncode, syntax.stderr)

            try:
                install = subprocess.run(
                    [
                        sudo, "-n", "install", "-o", "root", "-g", "root",
                        "-m", "0440", str(candidate), str(drop_in),
                    ],
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(0, install.returncode, install.stderr)
                installed_syntax = subprocess.run(
                    [sudo, "-n", visudo, "-cf", str(drop_in)],
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(
                    0, installed_syntax.returncode, installed_syntax.stderr
                )
                result = subprocess.run(
                    [sudo, "-n", "-u", username, str(gate)],
                    input=payload,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=20,
                )
                self.assertEqual(0, result.returncode, result.stderr.decode())
                self.assertEqual(
                    {"bytes": len(payload), "stdin_isatty": False},
                    json.loads(result.stdout),
                )
            finally:
                subprocess.run(
                    [sudo, "-n", "rm", "-f", str(drop_in)],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

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
                "GATE_LOCK": "/run/aetheris-governance-sync/gate.lock",
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
            "`/run/aetheris-governance-sync/gate.lock`",
            "`/run/aetheris-governance-sync`",
            "`root:pi-governance-sync`",
            "`0750`",
            "`0640`",
            "standard `/run/lock` directory",
            "`1777` mode",
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
            "opaque binary bytes",
            "input without text decoding",
            "`upload <decimal_size>`",
            "1 byte\nthrough 64 MiB",
            "`upload_short`",
            "without\nwaiting for EOF",
            "`Defaults!/usr/local/sbin/aetheris-governance-sync-ssh !use_pty`",
            "all other commands",
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
            "command-specific `Defaults!`",
            "Do not set `!use_pty`\nglobally",
            "opaque binary bundle",
            "sudo's stdin",
            "size=$(wc -c < governance.bundle",
            "`upload_short`",
            "without waiting for EOF",
        ):
            self.assertIn(requirement, deployment)
        for command in (
            'ssh GOVERNANCE_HOST "upload $size"',
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
