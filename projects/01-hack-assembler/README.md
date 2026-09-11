# Hack Assembler

A two-pass assembler that translates Hack assembly (`.asm`) into 16-bit machine code (`.hack`). The first pass records labels; the second resolves symbols and variables before encoding A- and C-instructions.

```bash
python3 src/assembler.py examples/Add.asm
```
