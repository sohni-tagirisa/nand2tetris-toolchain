"""Made by Sohni Tagirisa"""
import sys
import os
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine


def tokenize_file_only(jack_file_path):
    """Tokenizes a single .jack file and produces the corresponding T.xml file.
        - the output is a simple list of tokens wrapped in <tokens> tags so that we can see that the tokenizer is working correctly
    arguements:
        - jack_file_path: the path to the .jack file to tokenize
    """
    #create output filename: replace .jack with T.xml
    xml_file_path = jack_file_path.replace('.jack', 'T.xml')
    print(f"Tokenizing {jack_file_path}...")

    try:
        #create tokenizer from input file
        tokenizer = JackTokenizer(jack_file_path)

        #create output file and write tokens
        with open(xml_file_path, 'w') as output:
            #write opening <tokens> tag
            output.write('<tokens>\n')

            #loop through all tokens
            while tokenizer.hasMoreTokens():
                #get next token
                tokenizer.advance()
                token_type = tokenizer.tokenType()

                #write token
                if token_type == 'KEYWORD':
                    token = tokenizer.keyWord()
                    output.write(f'<keyword> {token} </keyword>\n')

                elif token_type == 'SYMBOL':
                    token = tokenizer.symbol()
                    #escapes XML special characters
                    if token == '<':
                        token = '&lt;' #< becomes &lt;
                    elif token == '>':
                        token = '&gt;' #> becomes &gt;
                    elif token == '"':
                        token = '&quot;' #" becomes &quot;
                    elif token == '&':
                        token = '&amp;' #& becomes &amp;
                    output.write(f'<symbol> {token} </symbol>\n')

                elif token_type == 'IDENTIFIER':
                    token = tokenizer.identifier()
                    output.write(f'<identifier> {token} </identifier>\n')

                elif token_type == 'INT_CONST':
                    token = tokenizer.intVal()
                    output.write(f'<integerConstant> {token} </integerConstant>\n')

                elif token_type == 'STRING_CONST':
                    token = tokenizer.stringVal()
                    output.write(f'<stringConstant> {token} </stringConstant>\n')

            #write closing </tokens> tag
            output.write('</tokens>\n')

        print(f"Successfully created {xml_file_path}")

    except Exception as e:
        #make sure that if something goes wrong, print error and exit
        print(f"Error tokenizing {jack_file_path}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def analyze_file(jack_file_path):
    """Analyzes a single .jack file and produces corresponding .xml file.
    arguement:
        jack_file_path: path to the .jack file to analyze
    """
    #for output file replace .jack extension with .xml
    xml_file_path = jack_file_path.replace('.jack', '.xml')

    print(f"Compiling {jack_file_path}...")

    try:
        #create a JackTokenizer from the input file
        tokenizer = JackTokenizer(jack_file_path)

        #create an output file
        with open(xml_file_path, 'w') as output_file:
            #create a CompilationEngine with tokenizer and output file
            engine = CompilationEngine(tokenizer, output_file)

            #compile the class -> entry point for parsing
            #compileClass will recursively call other compile methods
            #to parse the entire program structure
            engine.compileClass()

        print(f"Successfully created {xml_file_path}")

    except Exception as e:
        #if anything goes wrong, the print error with full traceback and exit
        print(f"Error compiling {jack_file_path}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """ Parses command-line arguments and processes the specified files
    """
    #check for tokenizer-only mode flag (-t)
    tokenizer_only = False
    args = sys.argv[1:] #get all arguments after program name

    if len(args) > 0 and args[0] == '-t':
        #-t flag found, switch to tokenizer-only mode
        tokenizer_only = True
        args = args[1:] #remove the flag from arguments

    #validate we have exactly one argument (the source)
    if len(args) != 1:
        print("Please input either")
        print(" 1. python JackAnalyzer.py <source>")
        print(" 2. python JackAnalyzer.py -t <source>")
        print("")
        print("  Where <source> is either:")
        print("  1. a fileName.jack (a single Jack file)")
        print("  2. directoryName (a directory containing .jack files)")
        sys.exit(1)

    source = args[0]

    #choose the processing function based on mode
    #if -t flag was used, use tokenize_file_only(), otherwise use analyze_file()
    process_function = tokenize_file_only if tokenizer_only else analyze_file
    mode_name = "Tokenizer" if tokenizer_only else "Full Parser"

    #process the source
    if os.path.isfile(source):
        #if source is a single file

        #verify it has .jack extension
        if not source.endswith('.jack'):
            print("Error, input file must have .jack extension")
            sys.exit(1)

        #pocess the single file
        process_function(source)

    elif os.path.isdir(source):
        #if source is a directory

        #find all .jack files in the directory
        jack_files = [f for f in os.listdir(source) if f.endswith('.jack')]

        #verify directory contains at least one .jack file
        if not jack_files:
            print(f"Error, no .jack files found in directory {source}")
            sys.exit(1)

        print(f"Running {mode_name} mode on {len(jack_files)} file(s)...\n")

        #process each .jack file in sorted order
        for jack_file in sorted(jack_files):
            #construct full path to file
            file_path = os.path.join(source, jack_file)
            #process the file
            process_function(file_path)

        print(f"\nSuccess! Processed {len(jack_files)} file(s) :)")

    else:
        #source is neither a valid file nor directory
        print(f"Error, {source} is not a valid file or directory")
        sys.exit(1)

if __name__ == '__main__':
    main()