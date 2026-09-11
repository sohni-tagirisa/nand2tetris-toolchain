# Made by Sohni Tagirisa
import sys
import os
from pathlib import Path

from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter
from CompilationEngine import CompilationEngine


def compile_file(jack_file):
    """Compile a single .jack file to .vm file
    """
    # create output file name
    vm_file = jack_file.replace('.jack', '.vm')

    print(f"Compiling {jack_file} -> {vm_file}")

    try:
        # initialize tokenizer
        tokenizer = JackTokenizer(jack_file)

        # advance to first token
        if tokenizer.has_more_tokens():
            tokenizer.advance()

        # extract class name from file name
        class_name = Path(jack_file).stem

        # open output file and create vm_writer
        with open(vm_file, 'w') as output:
            vm_writer = VMWriter(output)
            compilation_engine = CompilationEngine(tokenizer, vm_writer, class_name)

            # compile the class
            compilation_engine.compile_class()

        print(f"Successfully compiled {jack_file}! :)")

    except Exception as e:
        print(f"Error with compiling {jack_file}: {e}")
        import traceback
        traceback.print_exc()


def compile_directory(directory):
    """ Compile all .jack files in a directory
    """
    jack_files = list(Path(directory).glob('*.jack'))

    if not jack_files:
        print(f"No .jack files found in {directory}")
        return

    print(f"Found {len(jack_files)} .jack file(s) in {directory}")

    for jack_file in jack_files:
        compile_file(str(jack_file))

    print(f"\nSuccessfully compiled {len(jack_files)} file(s)! :)")


def main():
    if len(sys.argv) != 2:
        print("Input: python JackCompiler.py <source>")
        print("Source: Xxx.jack file or directory containing .jack files")
        sys.exit(1)

    source = sys.argv[1]

    # check if source exists
    if not os.path.exists(source):
        print(f"Error: {source} does not exist")
        sys.exit(1)

    # compile file or directory
    if os.path.isfile(source):
        if not source.endswith('.jack'):
            print("Error: File must have .jack extension")
            sys.exit(1)
        compile_file(source)
    elif os.path.isdir(source):
        compile_directory(source)
    else:
        print(f"Error: {source} is neither a file nor a directory")
        sys.exit(1)


if __name__ == '__main__':
    main()