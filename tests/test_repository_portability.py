from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryPortabilityTests(unittest.TestCase):
    def test_acceptance_artifacts_force_lf_checkout(self):
        fixture = "tests/acceptance/scenario-01/request.md"
        result = subprocess.run(
            ["git", "check-attr", "eol", "--", fixture],
            cwd=ROOT,
            check=True,
            capture_output=True,
            encoding="utf-8",
            text=True,
        )

        self.assertEqual(f"{fixture}: eol: lf", result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
