import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get("REPORT_SOURCE", str(Path(__file__).parent)))

class EmptyRepositoryCliTests(unittest.TestCase):
    def test_empty_and_documentation_only(self):
        for documented in (False, True):
            with self.subTest(documented=documented), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                root.mkdir()
                if documented:
                    (root / "README.md").write_text("# Synthetic documentation\n")
                output = Path(temporary) / "report.md"
                result = subprocess.run([sys.executable, str(SOURCE / "generate_review_report.py"), str(root), "-o", str(output)], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = output.read_text()
                self.assertIn("No supported code files found", report)
                self.assertIn("Code files: 0.", report)
                self.assertIn("not assessed", report)
                self.assertNotIn("Reviewer Confidence", report)
                self.assertNotIn("Maintain current code quality", report)

    def test_python_and_javascript_keep_reports_unchanged(self):
        for extension, text in (("py", "def sample():\n    return 1\n"), ("js", "function sample() { return 1; }\n")):
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repo"
                root.mkdir()
                (root / ("main." + extension)).write_text(text)
                output = Path(temporary) / "report.md"
                result = subprocess.run([sys.executable, str(SOURCE / "generate_review_report.py"), str(root), "-o", str(output)], capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("1** files", output.read_text())
                self.assertIn("1** functions", output.read_text())

if __name__ == "__main__":
    unittest.main()
