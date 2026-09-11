# Nand2Tetris Toolchain

[![Tests](https://github.com/sohni-tagirisa/nand2tetris-toolchain/actions/workflows/test.yml/badge.svg)](https://github.com/sohni-tagirisa/nand2tetris-toolchain/actions/workflows/test.yml)

An end-to-end software toolchain for the Hack computer, built in Python and Jack. The project follows a high-level Jack program through compilation, virtual-machine translation, assembly, and machine-code generation, then applies the stack in a playable Wordle-style game.

## Project goals

- Explore how high-level programs become executable machine instructions.
- Build each translation layer with small, testable components.
- Implement the runtime services a Jack program needs without relying on a host operating system.
- Work within the Hack platform's constraints, including a 16-bit architecture and a limited heap.

## Architecture

```text
Jack source
    |
    v
Jack compiler  ->  VM code  ->  VM translator  ->  Hack assembly  ->  assembler  ->  Hack machine code
    |
    +-> Jack OS services: memory, math, strings, graphics, text, keyboard, arrays, and system control
```

## Components

| Component | Language | What it demonstrates |
| --- | --- | --- |
| [Hack assembler](projects/01-hack-assembler) | Python | Two-pass symbol resolution and 16-bit instruction encoding |
| [VM translator](projects/02-vm-translator) | Python | Stack arithmetic and memory-segment translation |
| [Full VM translator](projects/03-full-vm-translator) | Python | Branching, functions, calls, returns, scoped labels, and bootstrap code |
| [Jack syntax analyzer](projects/04-jack-analyzer) | Python | Tokenization and recursive-descent parsing into an XML syntax tree |
| [Jack compiler](projects/05-jack-compiler) | Python | Jack-to-VM compilation with scoped symbol-table management |
| [Jack operating system](projects/06-operating-system) | Jack | Core memory, I/O, graphics, string, math, and system services |
| [Wordle](projects/07-wordle) | Jack | Game logic and rendering designed around Jack's constrained heap |

## Engineering highlights

- A complete translation path from Jack source to Hack binary instructions.
- Separate parsing and code-generation responsibilities across the assembler, VM translators, and compiler.
- Recursive-descent parsing for the Jack grammar and scoped symbol tracking during compilation.
- Explicit memory reuse in Wordle to avoid unnecessary allocations on a platform without garbage collection.
- Automated syntax checks and smoke tests on every push and pull request through GitHub Actions.

## Quick start

The Python tools require Python 3 and use only the standard library.

```bash
# Assemble Hack assembly into machine code
python3 projects/01-hack-assembler/src/assembler.py Program.asm

# Translate a single VM file
python3 projects/02-vm-translator/src/vm_translator.py Program.vm

# Translate a VM file or a directory of VM files
python3 projects/03-full-vm-translator/src/vm_translator.py path/to/program

# Analyze Jack source into XML
python3 projects/04-jack-analyzer/src/JackAnalyzer.py path/to/source

# Compile Jack source into VM code
python3 projects/05-jack-compiler/src/JackCompiler.py path/to/source
```

Run the repository smoke tests with:

```bash
python3 -m unittest discover -s tests -v
```

Jack applications and OS classes run with the emulators in the [Nand2Tetris software suite](https://www.nand2tetris.org/software).

## Project status

The assembler, translators, analyzer, compiler, and Wordle application are implemented. The Jack OS classes pass their individual component tests; loading every custom OS class together still has a known integration issue documented in the [OS component](projects/06-operating-system).

Generated `.asm`, `.hack`, `.xml`, and `.vm` files are retained when they demonstrate a result or serve as a useful test fixture.

## Background and attribution

This project began as a sequence of Computer Organization assignments at Occidental College based on the [Nand2Tetris](https://www.nand2tetris.org/) curriculum. It is presented here as a cohesive toolchain to document the architecture, implementation choices, and skills developed across the full software stack. Example programs and official test fixtures remain attributed to Nand2Tetris in their source headers.

## Author

[Sohni Tagirisa](https://github.com/sohni-tagirisa)
