#!/usr/bin/env python3

#Input: ./ST_assembler.py FILE.asm
#Output: FILE.hack


# Command line argument parsing
import argparse as ap
# File path utilities
import os
# Regular expressions
import re
# Access to stderr, exit codes, etc.
import sys


# Symbol table (predefined) with all built in symbols
PREDEFINED_SYMBOLS = {
    'SP': 0,
    'LCL': 1,
    'ARG': 2,
    'THIS': 3,
    'THAT': 4,
    'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7,
    'R8': 8, 'R9': 9, 'R10': 10, 'R11': 11, 'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15,
    'SCREEN': 16384,
    'KBD': 24576
}

# Comp mapping (comp bits c1c2c3c4c5c6 and a bit)
COMP_TABLE = {
    # a=0 computations
    '0': (0, 0b101010),
    '1': (0, 0b111111),
    '-1': (0, 0b111010),
    'D': (0, 0b001100),
    'A': (0, 0b110000),
    '!D': (0, 0b001101),
    '!A': (0, 0b110001),
    '-D': (0, 0b001111),
    '-A': (0, 0b110011),
    'D+1': (0, 0b011111),
    'A+1': (0, 0b110111),
    'D-1': (0, 0b001110),
    'A-1': (0, 0b110010),
    'D+A': (0, 0b000010),
    'D-A': (0, 0b010011),
    'A-D': (0, 0b000111),
    'D&A': (0, 0b000000),
    'D|A': (0, 0b010101),
    # a=1 computations
    'M': (1, 0b110000),
    '!M': (1, 0b110001),
    '-M': (1, 0b110011),
    'M+1': (1, 0b110111),
    'M-1': (1, 0b110010),
    'D+M': (1, 0b000010),
    'D-M': (1, 0b010011),
    'M-D': (1, 0b000111),
    'D&M': (1, 0b000000),
    'D|M': (1, 0b010101)
}

# Destination field mappings (d1d2d3 bits)
DEST_TABLE = {
    '': 0b000,
    'M': 0b001,
    'D': 0b010,
    'MD': 0b011,
    'DM': 0b011,
    'A': 0b100,
    'AM': 0b101,
    'MA': 0b101,
    'AD': 0b110,
    'DA': 0b110,
    'AMD': 0b111,
    'ADM': 0b111,
    'MAD': 0b111,
    'MDA': 0b111,
    'DAM': 0b111,
    'DMA': 0b111
}

# Jump mappings
JUMP_TABLE = {
    '': 0b000,
    'JGT': 0b001,
    'JEQ': 0b010,
    'JGE': 0b011,
    'JLT': 0b100,
    'JNE': 0b101,
    'JLE': 0b110,
    'JMP': 0b111
}

# Regular expressions
LABEL_REGEX = re.compile(r'^\((.+)\)$')
A_INSTRUCTION_REGEX = re.compile(r'^@(\d+|[A-Za-z_.$:][A-Za-z0-9_.$:]*)$')
C_INSTRUCTION_REGEX = re.compile(r'^(([ADM]{1,3})=)?([ADM10\-+|&!=]{1,3})(;(J\w\w))?$')
COMMENT_REGEX = re.compile(r'//.*$')


def clean_line(line):
    # Remove comments
    line = COMMENT_REGEX.sub('', line)
    # Remove whitespace
    line = line.strip()
    return line


def parse_instruction(line):
    # Returns line type and components
    # Label
    label_match = LABEL_REGEX.match(line)
    if label_match:
        return 'L_COMMAND', label_match.group(1), None, None, None

    # A instruction
    a_match = A_INSTRUCTION_REGEX.match(line)
    if a_match:
        return 'A_COMMAND', a_match.group(1), None, None, None

    # C instruction
    c_match = C_INSTRUCTION_REGEX.match(line)
    if c_match:
        dest = c_match.group(2) if c_match.group(2) else ''
        comp = c_match.group(3)
        jump = c_match.group(5) if c_match.group(5) else ''
        return 'C_COMMAND', None, dest, comp, jump

    return None, None, None, None, None


def translate_a_instruction(symbol, symbol_table, next_var_address):
    # Translate an A instruction to binary
    # Check if it's a number
    if symbol.isdigit():
        address = int(symbol)
    else:
        # Symbol --> look it up in symbol table
        if symbol in symbol_table:
            address = symbol_table[symbol]
        else:
            # New variable --> add to symbol table
            symbol_table[symbol] = next_var_address[0]
            address = next_var_address[0]
            next_var_address[0] += 1

    # A instruction --> 0 followed by 15-bit address
    return address & 0x7FFF  # Ensure it's 15 bits max


def translate_c_instruction(dest, comp, jump):
    # Translate a C instruction to binary
    # Get comp bits
    if comp not in COMP_TABLE:
        raise ValueError(f"Unknown computation: {comp}")
    a_bit, comp_bits = COMP_TABLE[comp]

    # Get dest bits
    if dest not in DEST_TABLE:
        raise ValueError(f"Unknown destination: {dest}")
    dest_bits = DEST_TABLE[dest]

    # Get jump bits
    if jump not in JUMP_TABLE:
        raise ValueError(f"Unknown jump: {jump}")
    jump_bits = JUMP_TABLE[jump]

    # C instruction --> 111a cccccc ddd jjj
    instruction = 0b1110000000000000  # Start with 111
    instruction |= (a_bit << 12)       # a bit
    instruction |= (comp_bits << 6)    # comp bits
    instruction |= (dest_bits << 3)    # dest bits
    instruction |= jump_bits           # jump bits

    return instruction


def first_pass(lines):
    # First pass --> build symbol table with labels
    symbol_table = PREDEFINED_SYMBOLS.copy()
    rom_address = 0

    for line_num, line in lines:
        cleaned = clean_line(line)
        # Skip empty lines
        if not cleaned:
            continue

        cmd_type, symbol, dest, comp, jump = parse_instruction(cleaned)

        if cmd_type == 'L_COMMAND':
            # Label definition --> add to symbol table with current ROM address
            symbol_table[symbol] = rom_address
        elif cmd_type in ['A_COMMAND', 'C_COMMAND']:
            # Actual instruction --> increment ROM address
            rom_address += 1
        elif cmd_type is None:
            print(f"Warning! Could not parse line {line_num}: '{cleaned}'", file=sys.stderr)

    return symbol_table


def second_pass(lines, symbol_table):
    # Second pass --> translate instructions to binary
    instructions = []
    next_var_address = [16]

    for line_num, line in lines:
        cleaned = clean_line(line)
        # Skip empty lines
        if not cleaned:
            continue

        cmd_type, symbol, dest, comp, jump = parse_instruction(cleaned)
        # Skip labels in second pass
        if cmd_type == 'A_COMMAND':
            binary = translate_a_instruction(symbol, symbol_table, next_var_address)
            instructions.append(binary)
        elif cmd_type == 'C_COMMAND':
            binary = translate_c_instruction(dest, comp, jump)
            instructions.append(binary)

    return instructions


def main():
    # Parse command line arguments
    parser = ap.ArgumentParser(description='Hack Assembly Language Assembler')
    parser.add_argument('file', help='Input .asm file to assemble')
    args = parser.parse_args()

    # Resolve the supplied path and place output beside the input file.
    infilename = os.path.abspath(args.file)
    outfilename = os.path.splitext(infilename)[0] + '.hack'

    # Check whether output file already exists
    if os.path.exists(outfilename):
        raise FileExistsError(f"Output file '{outfilename}' exists, aborting.")

    try:
        # Read input file
        lines = []
        with open(infilename, 'r') as f:
            lines = list(enumerate([line.rstrip('\n\r') for line in f], start=1))

        # Two pass assembly
        print(f"First pass, building symbol table")
        symbol_table = first_pass(lines)

        print(f"Second pass, generating binary code")
        instructions = second_pass(lines, symbol_table)

        # Write output file
        with open(outfilename, 'w') as of:
            for instruction in instructions:
                of.write(f'{instruction:016b}\n')

        print(f"Assembly complete, {len(instructions)} instructions written to '{outfilename}'")

    except FileNotFoundError:
        print(f"Error, input file '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
