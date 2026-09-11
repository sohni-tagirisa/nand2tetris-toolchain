# Made by Sohni Tagirisa
from SymbolTable import SymbolTable
from VMWriter import VMWriter

class CompilationEngine:
    # binary operators and their vm translations
    BINARY_OP = {
        '+': 'add',
        '-': 'sub',
        '=': 'eq',
        '<': 'lt',
        '>': 'gt',
        '&': 'and',
        '|': 'or'
    }

    # multiplication and division need to call "os" functions
    MULT_DIV = {'*': 'Math.multiply', '/': 'Math.divide'}

    # unary operators
    UNARY_OP = {'-': 'neg', '~': 'not'}

    def __init__(self, tokenizer, vm_writer, class_name):
        # the tokenizer provides tokens from the jack source file
        self.tokenizer = tokenizer

        # the vm_writer writes vm commands to the output file
        self.vm_writer = vm_writer

        # the name of the class being compiled
        self.class_name = class_name

        # symbol table tracks all variables and their properties
        self.symbols = SymbolTable()

        # counter for generating unique labels
        self.label_index = 0


    def _expect(self, kind, value=None):
        """ check that the current token matches expected kind and value
        """
        # check if token type matches
        if self.tokenizer.token_type() != kind:
            raise SyntaxError(f"Expected {kind}, got {self.tokenizer.token_type()}")

        # if a specific value was expected, check that too
        if value is not None:
            if kind == "SYMBOL":
                if self.tokenizer.symbol() != value:
                    raise SyntaxError(f"Expected symbol '{value}', got '{self.tokenizer.symbol()}'")
            elif kind == "KEYWORD":
                if self.tokenizer.keyWord() != value:
                    raise SyntaxError(f"Expected keyword '{value}', got '{self.tokenizer.keyWord()}'")

    def _eat(self, kind, value=None):
        """ verify token matches expected kind/value, save it, and move on to next token
        """
        # verify the token is what we expect
        self._expect(kind, value)

        # save the current token before moving on
        tok = self.tokenizer.tokens[self.tokenizer.current_token]

        # move to the next token or applicable
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

        return tok

    def _new_label(self, prefix):
        """ generate a unique label
        """
        self.label_index += 1
        return f"{prefix}{self.label_index}"

    def _segment_of_kind(self, kind):
        """ map a symbol kind to its vm memory segment
        """
        if kind == SymbolTable.FIELD:
            return "this"
        if kind == SymbolTable.STATIC:
            return "static"
        if kind == SymbolTable.ARG:
            return "argument"
        if kind == SymbolTable.VAR:
            return "local"
        return None

    def compile_class(self):
        """ compile a complete class
        """
        # advance to first token if we haven't yet
        # tokenizer starts at position -1
        if self.tokenizer.current_token < 0:
            if self.tokenizer.has_more_tokens():
                self.tokenizer.advance()

        # eat the class keyword
        self._eat("KEYWORD", "class")

        # get and save the class name
        self.class_name = self.tokenizer.identifier() if self._peek_is("IDENTIFIER") else self.class_name
        self._eat("IDENTIFIER")

        # eat the opening brace
        self._eat("SYMBOL", "{")

        # compile all class variable declarations (static and field)
        while self._peek_is("KEYWORD") and self._peek_kw() in ("static", "field"):
            self.compile_class_var_dec()

        # compile all subroutines (constructor, function, method)
        while self._peek_is("KEYWORD") and self._peek_kw() in ("constructor", "function", "method"):
            self.compile_subroutine()

        # eat the closing brace
        self._eat("SYMBOL", "}")

    def compile_class_var_dec(self):
        """
        compile a static or field variable declaration
        """
        # get the kind
        kind_kw = self._eat("KEYWORD")[1]

        # get the type
        type_tok = self._eat_type()

        # get the first variable name and add to symbol table
        name = self._eat("IDENTIFIER")[1]
        # map static -> STATIC, field -> FIELD
        self.symbols.define(name, type_tok, SymbolTable.STATIC if kind_kw == "static" else SymbolTable.FIELD)

        # handle additional variables in the same declaration
        while self._peek_sym(","):
            self._eat("SYMBOL", ",")
            name = self._eat("IDENTIFIER")[1]
            self.symbols.define(name, type_tok, SymbolTable.STATIC if kind_kw == "static" else SymbolTable.FIELD)

        # eat the semicolon
        self._eat("SYMBOL", ";")

    def compile_subroutine(self):
        """ compile a complete method, function, or constructor
        """
        # get the subroutine kind
        sub_kind = self._eat("KEYWORD")[1]

        # get the return type
        _ret_type = self._eat_type_or_void()

        # get the subroutine name
        sub_name = self._eat("IDENTIFIER")[1]

        # methods operate on an object
        # the object reference is passed as the first arguement
        is_method = (sub_kind == "method")

        # reset the subroutine level symbol table for this new subroutine
        self.symbols.start_subroutine(is_method=is_method)

        # compile the parameter list
        self._eat("SYMBOL", "(")
        self.compile_parameter_list()
        self._eat("SYMBOL", ")")

        # start the subroutine body
        self._eat("SYMBOL", "{")

        # compile all local variable declarations
        while self._peek_is("KEYWORD") and self._peek_kw() == "var":
            self.compile_var_dec()

        # generate the function declaration
        n_locals = self.symbols.var_count(SymbolTable.VAR)
        self.vm_writer.write_function(f"{self.class_name}.{sub_name}", n_locals)

        if sub_kind == "constructor":
            # constructor must allocate memory for the new object
            n_fields = self.symbols.var_count(SymbolTable.FIELD)

            # call Memory.alloc(n_fields) to allocate memory
            self.vm_writer.write_push("constant", n_fields)
            self.vm_writer.write_call("Memory.alloc", 1)

            # the returned address is the base of the new object
            # set THIS pointer to point to it
            self.vm_writer.write_pop("pointer", 0)

        elif sub_kind == "method":
            # method operates on an existing object
            # the object reference was passed as argument 0
            # set THIS pointer to argument 0 so we can access the object's fields
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)

        # compile the statements in the subroutine body
        self.compile_statements()

        # eat the closing brace
        self._eat("SYMBOL", "}")

    def compile_parameter_list(self):
        """compile a parameter list (possibly empty).
        """
        # check if parameter list is empty
        if self._peek_sym(")"):
            return

        # get first parameter
        type_tok = self._eat_type()
        name = self._eat("IDENTIFIER")[1]
        # parameters go in the argument segment
        self.symbols.define(name, type_tok, SymbolTable.ARG)

        # handle additional parameters
        while self._peek_sym(","):
            self._eat("SYMBOL", ",")
            type_tok = self._eat_type()
            name = self._eat("IDENTIFIER")[1]
            self.symbols.define(name, type_tok, SymbolTable.ARG)

    def compile_var_dec(self):
        """compile a var declaration
        """
        # eat keyword
        self._eat("KEYWORD", "var")

        # get the type
        type_tok = self._eat_type()

        # get first variable name and add to symbol table
        name = self._eat("IDENTIFIER")[1]
        self.symbols.define(name, type_tok, SymbolTable.VAR)

        # handle additional variables
        while self._peek_sym(","):
            self._eat("SYMBOL", ",")
            name = self._eat("IDENTIFIER")[1]
            self.symbols.define(name, type_tok, SymbolTable.VAR)

        # eat semicolon
        self._eat("SYMBOL", ";")

    def compile_statements(self):
        """compile a sequence of statements
        """
        # keep compiling statements as long as we see statement keywords
        while self._peek_is("KEYWORD") and self._peek_kw() in ("let", "if", "while", "do", "return"):
            kw = self._peek_kw()

            # send to appropriate compile method based on statement type
            if kw == "let":
                self.compile_let()
            elif kw == "if":
                self.compile_if()
            elif kw == "while":
                self.compile_while()
            elif kw == "do":
                self.compile_do()
            elif kw == "return":
                self.compile_return()

    def compile_do(self):
        """compile a do statement
        """
        # eat do keyword
        self._eat("KEYWORD", "do")

        # compile the subroutine call
        # this will push the return value onto the stack
        self._compile_subroutine_call()

        # do statements ignore the return value, so pop and discard it
        self.vm_writer.write_pop("temp", 0)

        # eat semicolon
        self._eat("SYMBOL", ";")

    def compile_let(self):
        """compile a let statement
        """
        # eat let keyword
        self._eat("KEYWORD", "let")

        # get the variable name
        var_name = self._eat("IDENTIFIER")[1]

        # check if this is array assignment (has '[')
        is_array = False
        if self._peek_sym("["):
            # array assignment: arr[expression1] = expression2
            is_array = True

            # eat '['
            self._eat("SYMBOL", "[")

            # compile the index expression
            # this pushes the index value onto the stack
            self.compile_expression()

            # eat ]
            self._eat("SYMBOL", "]")

            # get the base address of the array from the symbol table
            kind = self.symbols.kind_of(var_name)
            index = self.symbols.index_of(var_name)
            seg = self._segment_of_kind(kind)

            # push the base address of the array
            self.vm_writer.write_push(seg, index)

            # add base + index to get the target address
            self.vm_writer.write_arithmetic("add")
            # now stack top = address we want to write to

        # eat =
        self._eat("SYMBOL", "=")

        # compile the expression on the right side of =
        # this pushes the value to assign onto the stack
        self.compile_expression()

        # eat ;
        self._eat("SYMBOL", ";")

        if is_array:
            self.vm_writer.write_pop("temp", 0)       # save value to temp 0
            self.vm_writer.write_pop("pointer", 1)    # set THAT = target address
            self.vm_writer.write_push("temp", 0)      # restore value
            self.vm_writer.write_pop("that", 0)       # store value at THAT[0]
        else:
            # get variable info from symbol table
            kind = self.symbols.kind_of(var_name)
            index = self.symbols.index_of(var_name)
            seg = self._segment_of_kind(kind)

            # pop the value into the variable's location
            self.vm_writer.write_pop(seg, index)

    def compile_while(self):
        """compile a while statement.
        """
        # eat while keyword
        self._eat("KEYWORD", "while")

        # generate unique labels for this while loop
        label_exp = self._new_label("WHILE_EXP")
        label_end = self._new_label("WHILE_END")

        # label for loop start (where we check condition)
        self.vm_writer.write_label(label_exp)

        # compile the condition
        self._eat("SYMBOL", "(")
        self.compile_expression()  # pushes true/false onto stack
        self._eat("SYMBOL", ")")

        # negate the condition (we exit if condition is false)
        self.vm_writer.write_arithmetic("not")

        # if condition is false (after not), jump to end
        self.vm_writer.write_if(label_end)

        # compile the loop body
        self._eat("SYMBOL", "{")
        self.compile_statements()
        self._eat("SYMBOL", "}")

        # jump back to check condition again
        self.vm_writer.write_goto(label_exp)

        # label for loop end
        self.vm_writer.write_label(label_end)

    def compile_return(self):
        """compile a return statement
        """
        # eat return keyword
        self._eat("KEYWORD", "return")

        # check if this is a void return (no expression)
        if self._peek_sym(";"):
            # void functions must still return something
            # by convention, they return 0
            self.vm_writer.write_push("constant", 0)
            self._eat("SYMBOL", ";")
            self.vm_writer.write_return()
            return

        # compile the return expression
        # this pushes the return value onto the stack
        self.compile_expression()

        # eat semicolon
        self._eat("SYMBOL", ";")

        # generate return command
        self.vm_writer.write_return()

    def compile_if(self):
        """compile an if statement, possibly with else
        """
        # eat if keyword
        self._eat("KEYWORD", "if")

        # compile the condition
        self._eat("SYMBOL", "(")
        self.compile_expression()  # pushes true/false onto stack
        self._eat("SYMBOL", ")")

        # generate unique labels
        label_true = self._new_label("IF_TRUE")
        label_false = self._new_label("IF_FALSE")
        label_end = self._new_label("IF_END")

        # if condition is true, jump to true branch
        self.vm_writer.write_if(label_true)

        # otherwise fall through to false branch
        self.vm_writer.write_goto(label_false)

        # label for true branch
        self.vm_writer.write_label(label_true)

        # compile the true branch statements
        self._eat("SYMBOL", "{")
        self.compile_statements()
        self._eat("SYMBOL", "}")

        # check if there's an else
        if self._peek_is("KEYWORD") and self._peek_kw() == "else":
            # if there's an else, need to skip over it after true branch
            self.vm_writer.write_goto(label_end)

            # label for false branch
            self.vm_writer.write_label(label_false)

            # compile the else statements
            self._eat("KEYWORD", "else")
            self._eat("SYMBOL", "{")
            self.compile_statements()
            self._eat("SYMBOL", "}")

            # label for end of entire if-else
            self.vm_writer.write_label(label_end)
        else:
            # no else, false branch just continues after if
            self.vm_writer.write_label(label_false)


    def compile_expression(self):
        """compile an expression
        """
        # compile the first term
        self.compile_term()

        # check if current token is a binary operator
        while self._peek_is("SYMBOL") and self.tokenizer.tokens[self.tokenizer.current_token][1] in (list(self.BINARY_OP.keys()) + list(self.MULT_DIV.keys())):
            # get the operator
            op = self._eat("SYMBOL")[1]

            # compile the next term
            self.compile_term()

            # generate the operation
            # terms are already on stack, now we operate on them
            if op in self.BINARY_OP:
                # simple operations
                self.vm_writer.write_arithmetic(self.BINARY_OP[op])
            else:
                # multiplication and division require "os" function calls
                self.vm_writer.write_call(self.MULT_DIV[op], 2)

    def compile_term(self):
        """compile a term
        """
        # integer constant
        if self._peek_is("INT_CONST"):
            val = self._eat("INT_CONST")[1]
            self.vm_writer.write_push("constant", val)
            return

        # string constant
        if self._peek_is("STRING_CONST"):
            s = self._eat("STRING_CONST")[1]

            # strings are created by:
            # 1. calling String.new(length) to allocate the string
            self.vm_writer.write_push("constant", len(s))
            self.vm_writer.write_call("String.new", 1)

            # 2. calling appendChar for each character
            for ch in s:
                self.vm_writer.write_push("constant", ord(ch))
                self.vm_writer.write_call("String.appendChar", 2)
            return

        # keyword constants
        if self._peek_is("KEYWORD") and self._peek_kw() in ("true","false","null","this"):
            kw = self._eat("KEYWORD")[1]

            if kw == "true":
                # true is represented as -1
                self.vm_writer.write_push("constant", 0)
                self.vm_writer.write_arithmetic("not")  # 0 -> -1
            elif kw in ("false", "null"):
                # false and null are both 0
                self.vm_writer.write_push("constant", 0)
            else:  # this
                # 'this' refers to the current object (pointer 0)
                self.vm_writer.write_push("pointer", 0)
            return

        # parenthesized expression
        if self._peek_is("SYMBOL") and self._peek_sym("("):
            self._eat("SYMBOL", "(")
            self.compile_expression()  # recursively compile inner expression
            self._eat("SYMBOL", ")")
            return

        # unary operator
        if self._peek_is("SYMBOL") and self._peek_sym(("-", "~")):
            op = self._eat("SYMBOL")[1]
            self.compile_term()  # recursively compile the term
            # apply unary operation to result
            self.vm_writer.write_arithmetic(self.UNARY_OP[op])
            return

        # identifier
        name = self._eat("IDENTIFIER")[1]

        # array access: varName[expression]
        if self._peek_sym("["):
            self._eat("SYMBOL", "[")

            # compile the index expression
            self.compile_expression()

            self._eat("SYMBOL", "]")

            # get array base address from symbol table
            kind = self.symbols.kind_of(name)
            index = self.symbols.index_of(name)
            seg = self._segment_of_kind(kind)

            # push base address
            self.vm_writer.write_push(seg, index)

            # add base + index to get target address
            self.vm_writer.write_arithmetic("add")

            # set THAT to point to target address
            self.vm_writer.write_pop("pointer", 1)

            # push the value at that address
            self.vm_writer.write_push("that", 0)
            return

        # subroutine call
        if self._peek_sym(("(", ".")):
            self._compile_subroutine_call_after_name(name)
            return

        # variable reference
        kind = self.symbols.kind_of(name)
        index = self.symbols.index_of(name)
        seg = self._segment_of_kind(kind)

        # push the variable's value
        self.vm_writer.write_push(seg, index)

    def _compile_subroutine_call(self):
        """compile a subroutine call (used by compile_do)
        """
        # get the first name
        name = self._eat("IDENTIFIER")[1]

        # handle the rest of the call
        self._compile_subroutine_call_after_name(name)

    def _compile_subroutine_call_after_name(self, first):
        """compile a subroutine call after the first name has been consumed
        """
        n_args = 0

        # form 1: functionName(...)
        if self._peek_sym("("):
            # this is a method call on the current object
            # push 'this' as the first argument
            self.vm_writer.write_push("pointer", 0)

            # the full name is ClassName.functionName
            full = f"{self.class_name}.{first}"

            # compile the arguments
            self._eat("SYMBOL", "(")
            n_args += self.compile_expression_list()
            self._eat("SYMBOL", ")")

            # call the function (with this + args = n_args + 1)
            self.vm_writer.write_call(full, n_args + 1)
            return

        # form 2: (className|varName).functionName(...)
        self._eat("SYMBOL", ".")
        sub = self._eat("IDENTIFIER")[1]

        # check if first is a variable or a class name
        target_kind = self.symbols.kind_of(first)

        if target_kind is None:
            # first is not in symbol table, so it's a class name
            # this is a function call: ClassName.functionName(...)
            full = f"{first}.{sub}"
        else:
            # first is a variable name (an object)
            # this is a method call: object.methodName(...)

            # push the object reference as first argument
            seg = self._segment_of_kind(target_kind)
            idx = self.symbols.index_of(first)
            self.vm_writer.write_push(seg, idx)

            # the full name uses the object's type (class)
            full = f"{self.symbols.type_of(first)}.{sub}"

            # count this as an argument
            n_args += 1

        # compile the arguments
        self._eat("SYMBOL", "(")
        n_args += self.compile_expression_list()
        self._eat("SYMBOL", ")")

        # call the function
        self.vm_writer.write_call(full, n_args)

    def compile_expression_list(self):
        """ compile a comma-separated list of expressions (possibly empty)
        """
        count = 0

        # check if list is empty (next token is ')')
        if self._peek_sym(")"):
            return 0

        # compile first expression
        self.compile_expression()
        count += 1

        # compile additional expressions separated by commas
        while self._peek_sym(","):
            self._eat("SYMBOL", ",")
            self.compile_expression()
            count += 1

        return count

    def _eat_type(self):
        """consume and return a type
        """
        if self._peek_is("KEYWORD") and self._peek_kw() in ("int","char","boolean"):
            return self._eat("KEYWORD")[1]
        # must be a class name
        return self._eat("IDENTIFIER")[1]

    def _eat_type_or_void(self):
        """consume and return a type or 'void'
        """
        if self._peek_is("KEYWORD") and self._peek_kw() == "void":
            return self._eat("KEYWORD")[1]
        return self._eat_type()

    def _peek_is(self, kind):
        """check if current token is of given kind
        """
        # make sure we're within bounds
        if self.tokenizer.current_token < 0 or self.tokenizer.current_token >= len(self.tokenizer.tokens):
            return False

        # check if token type matches
        return self.tokenizer.tokens[self.tokenizer.current_token][0] == kind

    def _peek_kw(self):
        """get the current keyword value
        """
        if not self._peek_is("KEYWORD"):
            return None
        return self.tokenizer.tokens[self.tokenizer.current_token][1]

    def _peek_sym(self, s):
        """check if current token is a symbol and optionally matches specific value
        """
        # first check if current token is a symbol at all
        if not self._peek_is("SYMBOL"):
            return False

        # get the symbol value
        sym = self.tokenizer.tokens[self.tokenizer.current_token][1]

        # check if it matches
        if isinstance(s, (tuple, list, set)):
            return sym in s
        return sym == s