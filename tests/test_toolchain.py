import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_tool(script, source):
    return subprocess.run(
        [sys.executable, str(script), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )


class ToolchainSmokeTests(unittest.TestCase):
    def test_assembler_emits_expected_add_program(self):
        project = ROOT / "projects/01-hack-assembler"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Add.asm"
            shutil.copy(project / "examples/Add.asm", source)
            run_tool(project / "src/assembler.py", source)
            actual = source.with_suffix(".hack").read_text().splitlines()
            expected = (project / "examples/Add.hack").read_text().splitlines()
            self.assertEqual(actual, expected)

    def test_basic_vm_translator_emits_assembly(self):
        project = ROOT / "projects/02-vm-translator"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "simpleadd.vm"
            shutil.copy(project / "examples/simpleadd.vm", source)
            run_tool(project / "src/vm_translator.py", source)
            output = source.with_suffix(".asm")
            self.assertTrue(output.exists())
            self.assertIn("@SP", output.read_text())

    def test_full_vm_translator_handles_directory(self):
        project = ROOT / "projects/03-full-vm-translator"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "FibonacciElement"
            shutil.copytree(project / "examples/FibonacciElement", source)
            run_tool(project / "src/vm_translator.py", source)
            output = source / "FibonacciElement.asm"
            self.assertTrue(output.exists())
            self.assertIn("@256", output.read_text())

    def test_jack_analyzer_emits_xml(self):
        project = ROOT / "projects/04-jack-analyzer"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Main.jack"
            shutil.copy(project / "examples/ArrayTest/Main.jack", source)
            run_tool(project / "src/JackAnalyzer.py", source)
            output = source.with_suffix(".xml")
            self.assertTrue(output.exists())
            self.assertIn("<class>", output.read_text())

    def test_jack_compiler_emits_vm(self):
        project = ROOT / "projects/05-jack-compiler"
        wordle = ROOT / "projects/07-wordle/src/Main.jack"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Main.jack"
            shutil.copy(wordle, source)
            run_tool(project / "src/JackCompiler.py", source)
            output = source.with_suffix(".vm")
            self.assertTrue(output.exists())
            self.assertIn("function Main.main", output.read_text())


if __name__ == "__main__":
    unittest.main()
