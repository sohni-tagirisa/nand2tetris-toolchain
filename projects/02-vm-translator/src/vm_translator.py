#!/usr/bin/env python3
import os, sys
""" 1. input can be a directory of files
        a) he will write a bit of stub code to do the file system handling for us
    2. Function, Call, label, goto, if goto, return """
class Parser:
    #reads a VM file and provides access to its commands
    def __init__(self, path: str):
        with open(path) as f:
            self.lines = [
                l.split('//')[0].strip() #remove comments and spaces
                for l in f.readlines() #read every line in file
                if l.split('//')[0].strip() #only keep non-blank code lines
            ]
        self.i, self.parts = -1, None
        """opens the .vm file, strips comments, trims whitespace,
           and stores only non-blank lines in self.lines"""

    def has_more(self):
        return self.i + 1 < len(self.lines)
    """returns true if another command remains"""

    def advance(self):
        self.i += 1 #move to next command
        self.parts = self.lines[self.i].split() #split into tokens
        """cuts strings at every space, returning a list of the
           separate words --> we call those tokens"""

    def ctype(self):
        cmd = self.parts[0] #first token = command word
        if cmd == 'push': return 'C_PUSH'
        elif cmd == 'pop': return 'C_POP'
        elif cmd in {'add','sub','neg','eq','gt','lt','and','or','not'}:
            return 'C_ARITHMETIC'
        else: return None
    """returns what type of VM command this line is"""

    def arg1(self):
        # if arithmetic, return the command itself, else return the 1st argument
        return self.parts[0] if self.ctype() == 'C_ARITHMETIC' else self.parts[1]

    def arg2(self):
        return int(self.parts[2]) #always numeric second argument


class CodeWriter:
    """translates VM commands into hack assembly"""
    SEG = {'local':'LCL', 'argument':'ARG', 'this':'THIS', 'that':'THAT'}
    """mapping between VM segment names and their Hack base symbols"""

    def __init__(self, out_path: str, src_vm: str):
        self.out = open(out_path, 'w') #open output .asm file
        self.file_label = os.path.splitext(os.path.basename(src_vm))[0]
        self.label_count = 0 #counter for unique labels

    def write_arithmetic(self, cmd: str):
        """Table for arithmetic commands"""
        {   'add': self.add,
            'sub': self.sub,
            'and': self._and,
            'or': self._or,
            'neg': self.neg,
            'not': self._not,
            'eq': self.eq,
            'lt': self.lt,
            'gt': self.gt,
        }[cmd]() #call the correct helper

    #commutative operations
    def binary_comm(self, comp: str):
        """template for commands like add, and, or"""
        self.out.write(
            "@SP\nAM=M-1\nD=M\n" #pop y (top) into D, SP--
            "A=A-1\n"  #point to x (SP-1)
            f"M={comp}\n" #perform x = x op y
        )

    #unary helper
    def unary(self, comp: str):
        """template for neg / not"""
        self.out.write(
            "@SP\nA=M-1\n"
            f"M={comp}M\n" #modify top of stack directly
        )

    #comparison helper
    def compare(self, jump: str):
        """template for eq, lt, gt (needs branching)"""
        t = f"TRUE{self.label_count}"
        e = f"END{self.label_count}"
        self.label_count += 1 #increment for next call
        self.out.write(
            "@SP\nAM=M-1\nD=M\n" #pop y -> D
            "A=A-1\nD=M-D\n" #D = x - y
            f"@{t}\nD;J{jump}\n" #if (x?y) goto TRUE
            "@SP\nA=M-1\nM=0\n" #else: write 0 (false)
            f"@{e}\n0;JMP\n" #jump to END
            f"({t})\n@SP\nA=M-1\nM=-1\n" #TRUE: write -1 (true)
            f"({e})\n"
        )

    #arithmetic commands
    def add(self): self.binary_comm("D+M") #addition
    def _and(self): self.binary_comm("D&M") #logical AND
    def _or (self): self.binary_comm("D|M") #logical OR
    def sub(self):
        self.out.write(
            "@SP\nAM=M-1\nD=M\nA=A-1\nM=M-D\n" #subtraction x - y
        )
    def neg(self): self.unary('-') #negate top of stack
    def _not(self): self.unary('!') #logical NOT top of stack
    def eq (self): self.compare('EQ') #equality check
    def lt (self): self.compare('LT') #less than
    def gt (self): self.compare('GT') #greater than

    #handles push and pop
    def write_push_pop(self, cmd: str, segment: str, index: int):
        """determines if it's a push or pop command"""
        (self.push if cmd == 'push' else self.pop)(segment, index)

    #push helpers
    def push(self, segment: str, i: int):
        """generate assembly for push command"""
        if segment == 'constant': #push constant i
            self.out.write(f"@{i}\nD=A\n")
        elif segment in self.SEG: #push local/argument/this/that i
            self.out.write(
                f"@{self.SEG[segment]}\nD=M\n@{i}\nA=D+A\nD=M\n"
            )
        elif segment == 'temp': #push temp i (R5–R12)
            self.out.write(f"@{5+i}\nD=M\n")
        elif segment == 'pointer': #push pointer 0/1 (THIS/THAT)
            self.out.write(f"@{'THIS' if i==0 else 'THAT'}\nD=M\n")
        elif segment == 'static': #push static i (file.i)
            self.out.write(f"@{self.file_label}.{i}\nD=M\n")
        #*SP = D; SP++
        self.out.write("@SP\nA=M\nM=D\n@SP\nM=M+1\n")

    #pop helpers
    def pop(self, segment: str, i: int):
        """generate assembly for pop command"""
        if segment in self.SEG: #pop into local/argument/this/that
            self.out.write(
                f"@{self.SEG[segment]}\nD=M\n@{i}\nD=D+A\n@R13\nM=D\n"
                "@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n"
            )
        elif segment == 'temp': #pop temp i
            self.out.write(
                "@SP\nAM=M-1\nD=M\n"
                f"@{5+i}\nM=D\n"
            )
        elif segment == 'pointer': #pop pointer 0/1
            self.out.write(
                "@SP\nAM=M-1\nD=M\n"
                f"@{'THIS' if i==0 else 'THAT'}\nM=D\n"
            )
        elif segment == 'static': #pop static i
            self.out.write(
                "@SP\nAM=M-1\nD=M\n"
                f"@{self.file_label}.{i}\nM=D\n"
            )

    def close(self):
        """write infinite loop & close file"""
        self.out.write("(END)\n@END\n0;JMP\n")
        self.out.close()


class VMTranslator:
    """main driver class that coordinates Parser and CodeWriter"""
    def __init__(self, vm_path: str):
        if not vm_path.endswith('.vm'):
            raise ValueError("Input file must have .vm extension")
        self.vm = vm_path
        self.asm = vm_path.replace('.vm', '.asm') #output filename

    def translate(self):
        """loops through each VM command and writes corresponding ASM"""
        parser = Parser(self.vm)
        writer = CodeWriter(self.asm, self.vm)

        while parser.has_more(): #iterate through commands
            parser.advance()
            ct = parser.ctype() #determine command type
            if ct == 'C_ARITHMETIC': #arithmetic command
                writer.write_arithmetic(parser.arg1())
            elif ct in ('C_PUSH', 'C_POP'): #memory access commands
                writer.write_push_pop('push' if ct=='C_PUSH' else 'pop',
                                      parser.arg1(), parser.arg2())

        writer.close()
        print(f"{self.vm} has been translated to {self.asm}")


if __name__ == '__main__':
    #runs only if executed directly
    if len(sys.argv) != 2:
        sys.exit("Input: python vm_translator.py prog.vm")
    try:
        VMTranslator(sys.argv[1]).translate()
    except Exception as err:
        sys.exit(f"Error: {err}")
