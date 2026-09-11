#!/usr/bin/env python3
import os, sys

class Parser:
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
    """returns true if another command is present"""

    def advance(self):
        self.i += 1 #move to next command
        self.parts = self.lines[self.i].split() #split into tokens
        """cuts strings at every space, returning a list of the separate words
        --> we call those tokens"""

    def ctype(self):
        cmd = self.parts[0] #the first token is a command word
        if cmd == 'push': return 'C_PUSH'
        if cmd == 'pop': return 'C_POP'
        if cmd in {'add','sub','neg','eq','gt','lt','and','or','not'}: return 'C_ARITHMETIC'
        if cmd == 'label': return 'C_LABEL'
        if cmd == 'goto': return 'C_GOTO'
        if cmd == 'if-goto': return 'C_IF'
        if cmd == 'function': return 'C_FUNCTION'
        if cmd == 'call': return 'C_CALL'
        if cmd == 'return': return 'C_RETURN'
        return None
    """returns what type of VM command this line is"""

    def arg1(self):
        t = self.ctype() #get the current command type
        if t == 'C_ARITHMETIC':
            return self.parts[0] #for arithmetic, return the command itself
        if t in ('C_LABEL','C_GOTO','C_IF','C_FUNCTION','C_CALL'):
            return self.parts[1] #for these, return the first argument
        return self.parts[1] #by default, also return first argument for push/pop

    def arg2(self):
        if self.ctype() in ('C_PUSH','C_POP','C_FUNCTION','C_CALL'):
            return int(self.parts[2]) #only these specific commands have a second numeric argument (index/count)
        return 0 #otherwise, return 0 (unused)

class CodeWriter:
    """translates VM commands into hack assembly"""
    SEG = {'local':'LCL','argument':'ARG','this':'THIS','that':'THAT'}
    """mapping between VM segment names and their Hack base symbols"""

    def __init__(self, out_path: str, write_bootstrap: bool, files_note: str):
        self.out = open(out_path, 'w') #open .asm file
        self.out.write(f"// output: {out_path}\n") #header
        self.out.write(files_note) #list VM sources
        self.file_label = None #current file tag
        self.label_count = 0 #unique comparison labels
        self.func_name = None #current function
        self.call_count = 0 #return-label counter
        if write_bootstrap: #optional bootstrap
            self.write_bootstrap_code()
        else:
            self.out.write("// BOOTSTRAP OFF\n")

    def set_file_label(self, file_path: str):
        self.file_label = os.path.splitext(os.path.basename(file_path))[0]

    def _qual(self, label: str) -> str:
        return f"{self.func_name}${label}" if self.func_name else f"{self.file_label}${label}"

    def write_bootstrap_code(self):
        self.out.write("// BOOTSTRAP ON\n") #mark that bootstrap code is included in output
        self.out.write(
            "@256\n" #load constant 256 (base of the stack)
            "D=A\n" #store it in D-register
            "@SP\n" #access the stack pointer
            "M=D\n" #set SP = 256
        )
        self.write_call("Sys.init", 0) #call Sys.init to begin program execution


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

    def unary(self, comp: str):
        self.out.write("@SP\nA=M-1\n" f"M={comp}M\n")

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

    #branching
    def write_label(self, label): self.out.write(f"({self._qual(label)})\n")
    def write_goto(self, label):  self.out.write(f"@{self._qual(label)}\n0;JMP\n")
    def write_if(self, label):
        self.out.write("@SP\nAM=M-1\nD=M\n" f"@{self._qual(label)}\nD;JNE\n")

    #functions/calls/return
    def write_function(self, func_name, num_locals):
        self.func_name = func_name
        self.out.write(f"({func_name})\n")
        for _ in range(num_locals):
            self.out.write("@SP\nA=M\nM=0\n@SP\nM=M+1\n")

    def write_call(self, func_name, num_args):
        base = self.func_name if self.func_name else "RET"
        ret_label = f"{base}$ret.{self.call_count}"
        self.call_count += 1
        #push ret
        self.out.write(f"@{ret_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        #push LCL, ARG, THIS, THAT
        for seg in ('LCL','ARG','THIS','THAT'):
            self.out.write(f"@{seg}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        #ARG = SP - num_args - 5 ; LCL = SP
        self.out.write("@SP\nD=M\n" f"@{num_args+5}\nD=D-A\n@ARG\nM=D\n")
        self.out.write("@SP\nD=M\n@LCL\nM=D\n")
        #goto f; (ret)
        self.out.write(f"@{func_name}\n0;JMP\n({ret_label})\n")

    def write_return(self):
        self.out.write("@LCL\nD=M\n@R13\nM=D\n") #FRAME= LCL
        self.out.write("@5\nD=A\n@R13\nA=M-D\nD=M\n@R14\nM=D\n") #RET=*(FRAME-5)
        self.out.write("@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n")  #*ARG=pop()
        self.out.write("@ARG\nD=M\n@SP\nM=D+1\n") #SP=ARG+1
        for k, seg in enumerate(("THAT","THIS","ARG","LCL"), start=1): #Restore
            self.out.write("@R13\nD=M\n" f"@{k}\nA=D-A\nD=M\n" f"@{seg}\nM=D\n")
        self.out.write("@R14\nA=M\n0;JMP\n") #goto RET

    def close(self):
        self.out.write("(END)\n@END\n0;JMP\n")
        self.out.close()

class VMTranslator:
    def __init__(self, path: str):
        self.path = path
        self.is_dir = os.path.isdir(path)
        self.vm_files = []

        if self.is_dir:
            for f in os.listdir(path):
                if f.endswith('.vm'):
                    self.vm_files.append(os.path.join(path, f))
            if not self.vm_files: raise ValueError("No .vm files found in directory")
            self.asm = os.path.join(path, os.path.basename(path) + '.asm')
        else:
            if not path.endswith('.vm'): raise ValueError("Input file must have .vm extension")
            self.vm_files.append(path)
            self.asm = path.replace('.vm', '.asm')

    def _needs_bootstrap(self) -> bool:
        """Bootstrap ON if: directory OR any file named Sys.vm OR any file defines function Sys.init."""
        if self.is_dir: return True
        for f in self.vm_files:
            if os.path.basename(f) == "Sys.vm": return True
            #scan for 'function Sys.init'
            with open(f) as fin:
                for raw in fin:
                    line = raw.split('//')[0].strip()
                    if not line: continue
                    parts = line.split()
                    if parts[0] == 'function' and len(parts) >= 2 and parts[1] == 'Sys.init':
                        return True
        return False

    def translate(self):
        write_bootstrap = self._needs_bootstrap()
        files_note = "// files:\n" + "".join(f"//   - {f}\n" for f in sorted(self.vm_files))
        files_note += f"// bootstrap?: {'YES' if write_bootstrap else 'NO'}\n"

        writer = CodeWriter(self.asm, write_bootstrap, files_note)

        for vm_file in sorted(self.vm_files):
            parser = Parser(vm_file)
            writer.set_file_label(vm_file)
            while parser.has_more(): #iterate through commands
                parser.advance()
                ct = parser.ctype() #determine command type
                if ct == 'C_ARITHMETIC': #arithmetic command
                    writer.write_arithmetic(parser.arg1())
                elif ct in ('C_PUSH','C_POP'): #memory access commands
                    writer.write_push_pop('push' if ct == 'C_PUSH' else 'pop',
                                          parser.arg1(), parser.arg2())
                elif ct == 'C_LABEL': #label declaration
                    writer.write_label(parser.arg1())
                elif ct == 'C_GOTO': #unconditional jump
                    writer.write_goto(parser.arg1())
                elif ct == 'C_IF': #conditional jump
                    writer.write_if(parser.arg1())
                elif ct == 'C_FUNCTION': #function definition
                    writer.write_function(parser.arg1(), parser.arg2())
                elif ct == 'C_CALL': #function call
                    writer.write_call(parser.arg1(), parser.arg2())
                elif ct == 'C_RETURN': #return from function
                    writer.write_return()

        writer.close()
        print(f"{self.path if self.is_dir else self.vm_files[0]} has been translated to {self.asm}")

if __name__ == '__main__':
    #runs only if executed directly
    if len(sys.argv) != 2:
        sys.exit("Input: python3 vm_translator.py prog.vm")
    try:
        VMTranslator(sys.argv[1]).translate()
    except Exception as err:
        sys.exit(f"Error: {err}")