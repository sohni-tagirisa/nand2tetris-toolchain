# Made by Sohni Tagirisa
class VMWriter:
    """translates vm commands into text and writes them to the output file
    """

    # segment constants
    CONST = "constant"    # for pushing constant values
    ARG = "argument"      # function/method arguments
    LOCAL = "local"       # local variables in functions
    STATIC = "static"     # class-level static variables
    THIS = "this"         # fields of current object
    THAT = "that"         # used for array access
    POINTER = "pointer"   # special segment with only 2 entries (THIS and THAT pointers)
    TEMP = "temp"         # temporary storage (8 locations)

    def __init__(self, output):
        """create a new vmwriter that writes to the given output file
        """
        self.output = output

    def write_push(self, segment, index):
        """write a push command
        """
        self.output.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        """write a pop command
        """
        self.output.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command):
        """write an arithmetic or logical command
        """
        self.output.write(f"{command}\n")

    def write_label(self, label):
        """ write a label declaration
        """
        self.output.write(f"label {label}\n")

    def write_goto(self, label):
        """write an unconditional goto command
        """
        self.output.write(f"goto {label}\n")

    def write_if(self, label):
        """write a conditional goto command
        """
        self.output.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        """write a function call command
        """
        self.output.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_vars):
        """write a function declaration
        """
        self.output.write(f"function {name} {n_vars}\n")

    def write_return(self):
        """write a return command
        """
        self.output.write("return\n")

    def close(self):
        """close the output file
        """
        self.output.close()