import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from researchguard.local_env import load_local_env


class LocalEnvironmentTests(unittest.TestCase):
    def test_loads_simple_values_without_overriding_process_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "# local fixture\nFIXTURE_ONE=plain\nFIXTURE_TWO='quoted value'\nFIXTURE_EXISTING=file\n"
            )
            with patch.dict(os.environ, {"FIXTURE_EXISTING": "process"}, clear=False):
                for name in ("FIXTURE_ONE", "FIXTURE_TWO"):
                    os.environ.pop(name, None)
                try:
                    self.assertEqual(load_local_env(path), 2)
                    self.assertEqual(os.environ["FIXTURE_ONE"], "plain")
                    self.assertEqual(os.environ["FIXTURE_TWO"], "quoted value")
                    self.assertEqual(os.environ["FIXTURE_EXISTING"], "process")
                finally:
                    os.environ.pop("FIXTURE_ONE", None)
                    os.environ.pop("FIXTURE_TWO", None)

    def test_rejects_shell_like_multiword_and_malformed_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            for value in ("BAD value", "'unterminated"):
                path.write_text(f"FIXTURE_BAD={value}\n")
                with self.subTest(value=value), self.assertRaises(ValueError):
                    load_local_env(path)


if __name__ == "__main__":
    unittest.main()
