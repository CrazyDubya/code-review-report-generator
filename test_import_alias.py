#!/usr/bin/env python3
"""`import x as y` must be counted under the real module name."""
import tempfile
import unittest
from pathlib import Path

from code_analyzer import CodeAnalyzer


class ImportAliasTests(unittest.TestCase):
    def analyze(self, source):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text(source)
            return CodeAnalyzer(d).analyze_repository()["top_imports"]

    def test_aliases_are_not_part_of_the_module_name(self):
        imports = self.analyze("import numpy as np\nimport os, sys as system\nimport pandas as pd\n")
        self.assertEqual(imports, {"numpy": 1, "os": 1, "sys": 1, "pandas": 1})

    def test_plain_and_from_imports_unchanged(self):
        imports = self.analyze("import os.path\nfrom collections import Counter\nimport json\n")
        self.assertEqual(imports, {"os": 1, "collections": 1, "json": 1})


if __name__ == "__main__":
    unittest.main()
