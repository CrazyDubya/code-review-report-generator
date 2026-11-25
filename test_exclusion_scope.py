from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from code_analyzer import CodeAnalyzer


class ExclusionScopeTests(unittest.TestCase):
    def test_named_ancestor_does_not_hide_selected_repository(self):
        for name in ('build', 'dist', 'node_modules', '.venv'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / name / 'repo'
                root.mkdir(parents=True)
                (root / 'app.py').write_text('def work():\n    return 1\n')
                result = CodeAnalyzer(str(root)).analyze_repository()
                self.assertEqual(result['code_files'], 1)
                self.assertEqual(result['total_functions'], 1)

    def test_selected_root_name_is_not_an_excluded_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'build'
            root.mkdir()
            (root / 'app.py').write_text('def work():\n    pass\n')
            (root / 'build').mkdir()
            (root / 'build' / 'generated.py').write_text('def ignore():\n    pass\n')
            result = CodeAnalyzer(str(root)).analyze_repository()
            self.assertEqual(result['code_files'], 1)
            self.assertEqual(result['largest_files'][0]['path'], 'app.py')

    def test_cli_under_lib_ancestor_still_counts_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'lib' / 'repo'
            root.mkdir(parents=True)
            (root / 'app.py').write_text('def work():\n    pass\n')
            output = Path(directory) / 'report.md'
            result = subprocess.run([
                sys.executable, str(Path(__file__).parent / 'generate_review_report.py'),
                str(root), '-o', str(output),
            ], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('1** functions', output.read_text())
            self.assertNotIn('No supported code files found', output.read_text())

    def test_nested_excluded_directories_remain_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'src').mkdir()
            (root / 'src' / 'app.py').write_text('def work():\n    pass\n')
            for excluded in ('build', '.git', 'custom'):
                path = root / 'src' / excluded
                path.mkdir()
                (path / 'skip.py').write_text('def skip():\n    pass\n')
            result = CodeAnalyzer(str(root), exclude_dirs={'build', '.git', 'custom'}).analyze_repository()
            self.assertEqual(result['code_files'], 1)

    def test_relative_selected_repository_has_same_scope(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            original = Path.cwd()
            try:
                os.chdir(directory)
                root = Path('build') / 'repo'
                root.mkdir(parents=True)
                (root / 'app.py').write_text('def work():\n    pass\n')
                result = CodeAnalyzer(str(root)).analyze_repository()
                self.assertEqual(result['code_files'], 1)
            finally:
                os.chdir(original)


    def test_outside_root_predicate_keeps_previous_boolean_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'repo'
            root.mkdir()
            analyzer = CodeAnalyzer(str(root))
            self.assertTrue(analyzer.should_exclude(Path(directory) / 'other' / 'node_modules' / 'x'))
            self.assertFalse(analyzer.should_exclude(Path(directory) / 'other' / 'src'))
            relative_analyzer = CodeAnalyzer('repo')
            self.assertTrue(relative_analyzer.should_exclude(Path(directory) / 'build' / 'x'))
            self.assertFalse(relative_analyzer.should_exclude(Path(directory) / 'src'))
