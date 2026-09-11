"""Made by Sohni Tagirisa"""
class CompilationEngine:
    def __init__(self, tokenizer, output_file):
        """ Creates a new compilation engine with the given input and output.
        arguements:
            - tokenizer: A JackTokenizer object ready to provide tokens
            - output_file: An open file object to write XML output to
        """
        self.tokenizer = tokenizer #the tokenizer that provides tokens
        self.output = output_file #the file we write XML to
        self.indent_level = 0 #track indentation for proper XML output

        """ Get the first token to start parsing -> This way, we are positioned at the first token before compileClass is called. """
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def _write(self, text):
        """ Writes text to output so that each indentation level adds 2 spaces.
        arguements:
            - text: the XML string to write
        """
        self.output.write('  ' * self.indent_level + text + '\n')

    def _writeTerminal(self):
        """ Writes the current token as a terminal (a.k.a leaf) element in the parse tree.
            - terminals are the actual tokens from the source code.
            - handles XML for special characters like < > " &
        """
        token_type = self.tokenizer.tokenType()

        #handle keyword tokens like class, method, if, while
        if token_type == 'KEYWORD':
            token = self.tokenizer.keyWord()
            self._write(f'<keyword> {token} </keyword>')

        #handle symbol tokens like {, }, (, ), ;
        elif token_type == 'SYMBOL':
            token = self.tokenizer.symbol()
            #XML special characters must be escaped
            if token == '<':
                token = '&lt;' #< becomes &lt;
            elif token == '>':
                token = '&gt;' # > becomes &gt;
            elif token == '"':
                token = '&quot;' # " becomes &quot;
            elif token == '&':
                token = '&amp;' # & becomes &amp;
            self._write(f'<symbol> {token} </symbol>')

        #handle identifier tokens (variable names, class names, method names)
        elif token_type == 'IDENTIFIER':
            token = self.tokenizer.identifier()
            self._write(f'<identifier> {token} </identifier>')

        #handle integer constant tokens
        elif token_type == 'INT_CONST':
            token = self.tokenizer.intVal()
            self._write(f'<integerConstant> {token} </integerConstant>')

        #handle string constant tokens
        elif token_type == 'STRING_CONST':
            token = self.tokenizer.stringVal()
            self._write(f'<stringConstant> {token} </stringConstant>')

    def _process(self, expected=None):
        """ Processes the current token then advances to the next one.
        arguements:
            - expected: if provided, checks that current token matches this value
                * this is used for required keywords and symbols
        """
        #if we expect a specific token, verify it matches
        if expected:
            token = None
            if self.tokenizer.tokenType() == 'KEYWORD':
                token = self.tokenizer.keyWord()
            elif self.tokenizer.tokenType() == 'SYMBOL':
                token = self.tokenizer.symbol()

            #raise error if token doesn't match expectation
            if token != expected:
                raise Exception(f'Expected {expected}, got {token}')

        #write the current token to XML output
        self._writeTerminal()

        #move to next token (if there are more)
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

    def compileClass(self):
        """ Compiles a complete class.
        - grammar: 'class' className '{' classVarDec* subroutineDec* '}'
        """
        #opening tag for the class nonterminal
        self._write('<class>')
        self.indent_level += 1

        #process required keyword of 'class'
        self._process('class')

        #process className -> an identifier
        self._process()

        #process required symbol '{'
        self._process('{')

        #process zero or more class variable declarations
        #keep going while we see 'static' or 'field' keywords
        while (self.tokenizer.tokenType() == 'KEYWORD' and
               self.tokenizer.keyWord() in ['static', 'field']):
            self.compileClassVarDec()

        #process zero or more subroutine declarations
        #keep going while we see 'constructor', 'function', or 'method' keywords
        while (self.tokenizer.tokenType() == 'KEYWORD' and
               self.tokenizer.keyWord() in ['constructor', 'function', 'method']):
            self.compileSubroutine()

        #process required symbol '}'
        self._process('}')

        #closing tag for the class nonterminal
        self.indent_level -= 1
        self._write('</class>')

    def compileClassVarDec(self):
        """ Compiles a static declaration or a field declaration.
        - grammar: ('static' | 'field') type varName (',' varName)* ';'
        """
        self._write('<classVarDec>')
        self.indent_level += 1

        #process 'static' or 'field'
        self._process()

        #process type (int, char, boolean, or className)
        self._process()

        #process first variable name
        self._process()

        #process any additional variable names
        while (self.tokenizer.tokenType() == 'SYMBOL' and
               self.tokenizer.symbol() == ','):
            self._process(',') #process the comma
            self._process() #process the variable name

        #process required semicolon
        self._process(';')

        self.indent_level -= 1
        self._write('</classVarDec>')

    def compileSubroutine(self):
        """ Compiles a method, function, or constructor.
        - grammar: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
        """
        self._write('<subroutineDec>')
        self.indent_level += 1

        #process 'constructor', 'function', or 'method'
        self._process()

        #process return type: 'void' or type (int, char, boolean, className)
        self._process()

        #process subroutine name
        self._process()

        #process '('
        self._process('(')

        #process parameter list
        self.compileParameterList()

        #process ')'
        self._process(')')

        #process subroutine body: '{' varDec* statements '}'
        self._write('<subroutineBody>')
        self.indent_level += 1

        #process '{'
        self._process('{')

        #process zero or more variable declarations
        while (self.tokenizer.tokenType() == 'KEYWORD' and
               self.tokenizer.keyWord() == 'var'):
            self.compileVarDec()

        #process statements (let, if, while, do, return)
        self.compileStatements()

        #process '}'
        self._process('}')

        self.indent_level -= 1
        self._write('</subroutineBody>')

        self.indent_level -= 1
        self._write('</subroutineDec>')

    def compileParameterList(self):
        """ Compiles a parameter list -> can be empty
        - grammar: ((type varName) (',' type varName)*)?
        """
        self._write('<parameterList>')
        self.indent_level += 1

        #check if parameter list is not empty -> not immediately followed by ')'
        if not (self.tokenizer.tokenType() == 'SYMBOL' and
                self.tokenizer.symbol() == ')'):

            #process first parameter: type varName
            self._process() # type
            self._process() # varName

            #process additional parameters
            while (self.tokenizer.tokenType() == 'SYMBOL' and
                   self.tokenizer.symbol() == ','):
                self._process(',') #process comma
                self._process() #process type
                self._process() #process varName

        self.indent_level -= 1
        self._write('</parameterList>')

    def compileVarDec(self):
        """
        Compiles a var declaration.
        Grammar: 'var' type varName (',' varName)* ';'

        Example:
            var int x, y, sum;
        """
        self._write('<varDec>')
        self.indent_level += 1

        #process 'var' keyword
        self._process('var')

        #process type
        self._process()

        #process first variable name
        self._process()

        #process additional variable names
        while (self.tokenizer.tokenType() == 'SYMBOL' and
               self.tokenizer.symbol() == ','):
            self._process(',')
            self._process()

        #process semicolon
        self._process(';')

        self.indent_level -= 1
        self._write('</varDec>')

    def compileStatements(self):
        """ Compiles a sequence of statements, not including the enclosing {}.
        """
        self._write('<statements>')
        self.indent_level += 1

        #keep processing statements while we see statement keywords
        while self.tokenizer.tokenType() == 'KEYWORD':
            keyword = self.tokenizer.keyWord()

            #send to appropriate compile method based on statement type
            if keyword == 'let':
                self.compileLet()
            elif keyword == 'if':
                self.compileIf()
            elif keyword == 'while':
                self.compileWhile()
            elif keyword == 'do':
                self.compileDo()
            elif keyword == 'return':
                self.compileReturn()
            else:
                #not a statement keyword so stop processing
                break

        self.indent_level -= 1
        self._write('</statements>')

    def compileDo(self):
        """ Compiles a do statement.
        """
        self._write('<doStatement>')
        self.indent_level += 1

        #process 'do' keyword
        self._process('do')

        #process subroutine call
        #first token is an identifier (subroutineName, className, or varName)
        self._process()

        #check what comes after the identifier
        if (self.tokenizer.tokenType() == 'SYMBOL' and
            self.tokenizer.symbol() == '('):
            #subroutineName '(' expressionList ')'
            self._process('(')
            self.compileExpressionList()
            self._process(')')

        elif (self.tokenizer.tokenType() == 'SYMBOL' and
              self.tokenizer.symbol() == '.'):
            #(className | varName) '.' subroutineName '(' expressionList ')'
            self._process('.')
            self._process() #subroutineName
            self._process('(')
            self.compileExpressionList()
            self._process(')')

        #process the semicolon
        self._process(';')

        self.indent_level -= 1
        self._write('</doStatement>')

    def compileLet(self):
        """ Compiles a let statement.
        """
        self._write('<letStatement>')
        self.indent_level += 1

        #process 'let' keyword
        self._process('let')

        #process variable name
        self._process()

        #check for optional array indexing: '[' expression ']'
        if (self.tokenizer.tokenType() == 'SYMBOL' and
            self.tokenizer.symbol() == '['):
            self._process('[')
            self.compileExpression() #the index expression
            self._process(']')

        #process '='
        self._process('=')

        #process the expression on the right side of =
        self.compileExpression()

        #process semicolon
        self._process(';')

        self.indent_level -= 1
        self._write('</letStatement>')

    def compileWhile(self):
        """ Compiles a while statement.
        """
        self._write('<whileStatement>')
        self.indent_level += 1

        #process 'while' keyword
        self._process('while')

        #process '('
        self._process('(')

        #process condition expression
        self.compileExpression()

        #process ')'
        self._process(')')

        #process '{'
        self._process('{')

        #process loop body statements
        self.compileStatements()

        #process '}'
        self._process('}')

        self.indent_level -= 1
        self._write('</whileStatement>')

    def compileReturn(self):
        """Compiles a return statement.
        """
        self._write('<returnStatement>')
        self.indent_level += 1

        #process 'return' keyword
        self._process('return')

        #check if there's an expression to return (not immediately followed by ';')
        if not (self.tokenizer.tokenType() == 'SYMBOL' and
                self.tokenizer.symbol() == ';'):
            self.compileExpression()

        #process semicolon
        self._process(';')

        self.indent_level -= 1
        self._write('</returnStatement>')

    def compileIf(self):
        """Compiles an if statement, possibly with a trailing else
        """
        self._write('<ifStatement>')
        self.indent_level += 1

        #process 'if' keyword
        self._process('if')

        #process '('
        self._process('(')

        #process condition expression
        self.compileExpression()

        #process ')'
        self._process(')')

        #pocess '{'
        self._process('{')

        #process if-body statements
        self.compileStatements()

        #process '}'
        self._process('}')

        #check for optional else clause
        if (self.tokenizer.tokenType() == 'KEYWORD' and
            self.tokenizer.keyWord() == 'else'):
            self._process('else')
            self._process('{')
            self.compileStatements() #else
            self._process('}')

        self.indent_level -= 1
        self._write('</ifStatement>')

    def compileExpression(self):
        """ Compiles an expression.
        """
        self._write('<expression>')
        self.indent_level += 1

        #compile first term
        self.compileTerm()

        #compile any additional (operator term) pairs
        while (self.tokenizer.tokenType() == 'SYMBOL' and
               self.tokenizer.symbol() in ['+', '-', '*', '/', '&', '|', '<', '>', '=']):
            self._process() #process the operator
            self.compileTerm() #process the next term

        self.indent_level -= 1
        self._write('</expression>')

    def compileTerm(self):
        """Compiles a term.
        """
        self._write('<term>')
        self.indent_level += 1

        token_type = self.tokenizer.tokenType()

        #integer or string constant
        if token_type in ['INT_CONST', 'STRING_CONST']:
            self._process()

        #keyword constant (true, false, null, this)
        elif token_type == 'KEYWORD' and self.tokenizer.keyWord() in ['true', 'false', 'null', 'this']:
            self._process()

        #unary operator (- or ~) followed by another term
        elif token_type == 'SYMBOL' and self.tokenizer.symbol() in ['-', '~']:
            self._process() #process unary operator
            self.compileTerm() #recursively compile the term after it

        #parenthesized expression: '(' expression ')'
        elif token_type == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self._process('(')
            self.compileExpression() #compile the expression inside parens
            self._process(')')

        #variable name, array access, or subroutine call
        elif token_type == 'IDENTIFIER':
            #process the identifier first
            self._process()

            #look at next token to figure out what kind of term this is
            if self.tokenizer.tokenType() == 'SYMBOL':
                sym = self.tokenizer.symbol()

                #array access
                if sym == '[':
                    self._process('[')
                    self.compileExpression() #index expression
                    self._process(']')

                #subroutine call
                elif sym == '(':
                    self._process('(')
                    self.compileExpressionList()
                    self._process(')')

                #method call
                elif sym == '.':
                    self._process('.')
                    self._process() #subroutineName
                    self._process('(')
                    self.compileExpressionList()
                    self._process(')')

        self.indent_level -= 1
        self._write('</term>')

    def compileExpressionList(self):
        """ Compiles a comma-separated list of expressions -> can be empty
        """
        self._write('<expressionList>')
        self.indent_level += 1

        #check if expression list is NOT empty
        if not (self.tokenizer.tokenType() == 'SYMBOL' and
                self.tokenizer.symbol() == ')'):

            #compile first expression
            self.compileExpression()

            #compile any additional expressions
            while (self.tokenizer.tokenType() == 'SYMBOL' and
                   self.tokenizer.symbol() == ','):
                self._process(',')
                self.compileExpression()

        self.indent_level -= 1
        self._write('</expressionList>')