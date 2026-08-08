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

GOVERNANCE_SYNC_TESTS = (
    Path(__file__).resolve().parents[1] / "runtime" / "governance-sync" / "tests"
)
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "governance-validate.yml"
REAL_READER_TEST_SUFFIX = (
    "IntegrationTests."
    "test_linux_root_group_reader_has_real_read_only_io_before_and_after_sync"
)


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


def iter_test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from iter_test_ids(test)
        else:
            yield test.id()


class SuiteCompositionTests(unittest.TestCase):
    def test_load_tests_includes_dispatch_and_governance_sync_suites(self) -> None:
        loaded = load_tests(unittest.TestLoader(), unittest.TestSuite(), None)
        test_ids = set(iter_test_ids(loaded))
        self.assertTrue(
            any(
                test_id.startswith("dispatch_server_tests.")
                for test_id in test_ids
            ),
            "dispatch-server suite was not loaded",
        )
        self.assertTrue(
            any(
                ".test_governance_sync." in test_id
                or test_id.startswith("test_governance_sync.")
                for test_id in test_ids
            ),
            "governance-sync suite was not loaded",
        )
        self.assertTrue(
            any(test_id.endswith(REAL_READER_TEST_SUFFIX) for test_id in test_ids),
            "real reader privilege test was not loaded",
        )
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "python3 -m unittest scripts/check_governance_truth_test.py",
            workflow,
            "CI does not run the composed scanner/dispatch/governance-sync suite",
        )


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(tests)
    suite.addTests(loader.loadTestsFromModule(DISPATCH_MODULE))
    suite.addTests(loader.discover(str(GOVERNANCE_SYNC_TESTS), pattern="test_*.py"))
    return suite


if __name__ == "__main__":
    unittest.main()
