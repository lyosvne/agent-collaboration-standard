import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check-governance-truth.py")
SPEC = importlib.util.spec_from_file_location("governance_truth", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

DISPATCH_TEST = (
    Path(__file__).resolve().parents[1]
    / "runtime"
    / "dispatch-server"
    / "tests"
    / "test_dispatch_server.py"
)
DISPATCH_SPEC = importlib.util.spec_from_file_location(
    "dispatch_server_tests", DISPATCH_TEST
)
DISPATCH_MODULE = importlib.util.module_from_spec(DISPATCH_SPEC)
assert DISPATCH_SPEC.loader is not None
DISPATCH_SPEC.loader.exec_module(DISPATCH_MODULE)


class SecretPatternTests(unittest.TestCase):
    def matches(self, value: str) -> bool:
        return any(pattern.search(value) for pattern in MODULE.secret_patterns())

    def test_supported_github_tokens(self) -> None:
        values = [
            "_".join(["github", "pat", "EXAMPLEONLY", "A" * 32]),
            *["".join(["gh", prefix, "_", "A" * 32]) for prefix in "pousr"],
        ]
        for value in values:
            with self.subTest(prefix=value.split("_", 1)[0]):
                self.assertTrue(self.matches(value))

    def test_private_key_header(self) -> None:
        value = "-----" + "BEGIN " + "OPENSSH " + "PRIVATE KEY-----"
        self.assertTrue(self.matches(value))

    def test_aws_and_slack_tokens(self) -> None:
        aws = "".join(["AK", "IA", "A" * 16])
        slack = "".join(["xo", "xb-", "A" * 24])
        self.assertTrue(self.matches(aws))
        self.assertTrue(self.matches(slack))

    def test_safe_governance_text(self) -> None:
        self.assertFalse(self.matches("credential source: host-managed"))


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(tests)
    suite.addTests(loader.loadTestsFromModule(DISPATCH_MODULE))
    return suite


if __name__ == "__main__":
    unittest.main()
