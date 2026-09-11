# Made by Sohni Tagirisa
import re

class JackTokenizer:
    """reads the entire file at initialization and stores all tokens in a list
    """

    # all keywords in the jack language
    KEYWORDS = {
        "class",        # class declaration
        "constructor",  # constructor method
        "function",     # function (no object)
        "method",       # method (operates on object)
        "field",        # instance variable
        "static",       # class variable
        "var",          # local variable
        "int",          # integer type
        "char",         # character type
        "boolean",      # boolean type
        "void",         # no return value
        "true",         # boolean constant
        "false",        # boolean constant
        "null",         # null
        "this",         # current object
        "let",          # assignment statement
        "do",           # subroutine call statement
        "if",           # if statement
        "else",         # else
        "while",        # while loop
        "return"        # return statement
    }

    # all symbols
    SYMBOLS = set("{}()[].,;+-*/&|<>=~")

    def __init__(self, input_stream):
        """reads the file, strips comments, and tokenizes it
        """
        # read the entire file into a string
        with open(input_stream, "r") as f:
            data = f.read()

        # strip comments from the source code
        data = re.sub(r"//.*", "", data)

        # remove multi-line comments
        data = re.sub(r"/\*.*?\*/", "", data, flags=re.S)

        # now tokenize the cleaned source code
        self.tokens = []

        # scan through the source code character by character
        i = 0
        n = len(data)

        while i < n:
            c = data[i]

            # skip whitespace
            if c.isspace():
                i += 1
                continue

            # handle string constants
            if c == '"':
                # find the closing quote
                j = i + 1
                while j < n and data[j] != '"':
                    j += 1

                # check if we found the closing quote
                if j >= n:
                    raise ValueError("Unterminated string constant")

                # extract the string content
                string_content = data[i+1:j]
                self.tokens.append(("STRING_CONST", string_content))

                # move past the closing quote
                i = j + 1

            # handle symbols (single-character operators and punctuation)
            elif c in self.SYMBOLS:
                self.tokens.append(("SYMBOL", c))
                i += 1

            # handle keywords, identifiers, and integer constants
            else:
                # scan until we hit whitespace, symbol, or quote
                j = i
                while j < n and not data[j].isspace() and data[j] not in self.SYMBOLS and data[j] != '"':
                    j += 1

                # extract the word/number we found -> technically called lexeme
                lex = data[i:j]

                # determine what kind of token it is
                if lex in self.KEYWORDS:
                    # it's a keyword
                    self.tokens.append(("KEYWORD", lex))

                elif lex.isdigit():
                    # it's an integer constant
                    # convert to int for easier use later
                    self.tokens.append(("INT_CONST", int(lex)))

                else:
                    # it's an identifier
                    self.tokens.append(("IDENTIFIER", lex))

                i = j

        # initialize position to before first token
        self.current_token = -1

    def has_more_tokens(self):
        """check if there are more tokens in the input
        """
        return self.current_token + 1 < len(self.tokens)

    def advance(self):
        """get the next token from the input and make it the current token
        """
        if not self.has_more_tokens():
            raise StopIteration("No more tokens")

        # move to next token
        self.current_token += 1

        # return the current token
        return self.tokens[self.current_token]

    def token_type(self):
        """return the type of the current token
        """
        # check if we're on a valid token
        if self.current_token < 0 or self.current_token >= len(self.tokens):
            return None

        # return the type (first element of tuple)
        return self.tokens[self.current_token][0]

    def keyWord(self):
        """return the keyword which is the current token
        """
        t, v = self.tokens[self.current_token]

        if t != "KEYWORD":
            raise TypeError(f"Not a keyword: {t}")

        return v

    def symbol(self):
        """return the character which is the current token
        """
        t, v = self.tokens[self.current_token]

        if t != "SYMBOL":
            raise TypeError(f"Not a symbol: {t}")

        return v

    def identifier(self):
        """return the identifier which is the current token
        """
        t, v = self.tokens[self.current_token]

        if t != "IDENTIFIER":
            raise TypeError(f"Not an identifier: {t}")

        return v

    def int_val(self):
        """return the integer value of the current token
        """
        t, v = self.tokens[self.current_token]

        if t != "INT_CONST":
            raise TypeError(f"Not an int const: {t}")

        return v

    def string_val(self):
        """return the string value of the current token, without the opening and closing double quotes
        """
        t, v = self.tokens[self.current_token]

        if t != "STRING_CONST":
            raise TypeError(f"Not a string const: {t}")

        return v