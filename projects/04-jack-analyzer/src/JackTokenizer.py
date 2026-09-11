"""Made by Sohni Tagirisa"""
class JackTokenizer:
    """Tokenizer for the Jack language."""
    #jack language keywords are reserved words that cannot be used as identifiers
    KEYWORDS = {
        'class', 'constructor', 'function', 'method', 'field', 'static',
        'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
        'this', 'let', 'do', 'if', 'else', 'while', 'return'
    }

    #jack language symbols: single character operators and punctuation
    SYMBOLS = {
        '{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*',
        '/', '&', '|', '<', '>', '=', '~'
    }

    def __init__(self, input_file):
        """Opens the input file and gets ready to tokenize it. Reads the entire file, removes all comments, then tokenizes everything into a list
        """
        #read the entire file content
        with open(input_file, 'r') as f:
            content = f.read()

        #remove all comments (// and /* */) from the text
        self.clean_text = self._remove_comments(content)

        #initialize empty token list
        self.tokens = [] #will store tuples of (token_type, token_value)

        #initialize position tracking
        self.current_token_index = -1 #start before first token
        self.current_token = None #value of current token
        self.token_type_value = None #type of current token

        #tokenize the entire text
        self._tokenize()

    def _remove_comments(self, text):
        """Remove all comments from the text.
        arguements:
            - text: the source code as a string
        """
        result = [] #build result character by character
        i = 0 #current position in text

        while i < len(text):
            #check for single-line comment: //
            if i < len(text) - 1 and text[i:i+2] == '//':
                #skip everything until end of line
                while i < len(text) and text[i] != '\n':
                    i += 1
                continue #move to next iteration without adding to result

            #check for multi-line comment: /* or /**
            if i < len(text) - 1 and text[i:i+2] == '/*':
                #skip past the opening /*
                i += 2
                #keep going until we find the closing */
                while i < len(text) - 1:
                    if text[i:i+2] == '*/':
                        i += 2  #skip past the closing */
                        break
                    i += 1
                continue #move to next iteration without adding to result

            #not a comment, so add this character to result
            result.append(text[i])
            i += 1

        #combine all characters back into a string
        return ''.join(result)

    def _tokenize(self):
        """Tokenize the entire clean text into a list of (type, value) tuples.
        """
        i = 0 #current position in clean_text

        while i < len(self.clean_text):
            char = self.clean_text[i]

            #skip all whitespace (spaces, tabs, newlines)
            if char.isspace():
                i += 1
                continue

            #check if current character is a symbol (single character token)
            if char in self.SYMBOLS:
                #add symbol token to list
                self.tokens.append(('SYMBOL', char))
                i += 1
                continue

            #check if it's the start of a string constant (begins with ")
            if char == '"':
                i += 1 #skip opening quote
                start = i
                #find the closing quote
                while i < len(self.clean_text) and self.clean_text[i] != '"':
                    i += 1
                #extract string between quotes
                string_val = self.clean_text[start:i]
                self.tokens.append(('STRING_CONST', string_val))
                i += 1 #skip closing quote
                continue

            #check if it's a number
            if char.isdigit():
                start = i
                #keep going while we see digits
                while i < len(self.clean_text) and self.clean_text[i].isdigit():
                    i += 1
                #extract the number and convert to int
                num_val = self.clean_text[start:i]
                self.tokens.append(('INT_CONST', int(num_val)))
                continue

            #must be a keyword or identifier
            if char.isalpha() or char == '_':
                start = i
                #keep going while we see characters or underscore
                while i < len(self.clean_text):
                    c = self.clean_text[i]
                    if not (c.isalnum() or c == '_'):
                        break #stop at first nonidentifier character
                    i += 1

                #extract the word
                word = self.clean_text[start:i]

                #check if it's a keyword or just an identifier
                if word in self.KEYWORDS:
                    self.tokens.append(('KEYWORD', word))
                else:
                    self.tokens.append(('IDENTIFIER', word))
                continue

            #unknown character so skip it
            i += 1

    def hasMoreTokens(self):
        """ Returns True if there are more tokens in the input.
        """
        #we check if current_token_index is less than the last valid index
        #since we start at -1, the first call will check if -1 < len(tokens)-1
        return self.current_token_index < len(self.tokens) - 1

    def advance(self):
        """Gets the next token from the input and makes it the current token.
        """
        if self.hasMoreTokens():
            #move to next token position
            self.current_token_index += 1
            #unpack the tuple: (type, value)
            self.token_type_value, self.current_token = self.tokens[self.current_token_index]

    def tokenType(self):
        """Returns the type of the current token.
        """
        return self.token_type_value

    def keyWord(self):
        """Returns the keyword which is the current token.
        """
        if self.token_type_value == 'KEYWORD':
            return self.current_token
        return None

    def symbol(self):
        """Returns the character which is the current token.
        """
        if self.token_type_value == 'SYMBOL':
            return self.current_token
        return None

    def identifier(self):
        """Returns the identifier which is the current token.
        """
        if self.token_type_value == 'IDENTIFIER':
            return self.current_token
        return None

    def intVal(self):
        """Returns the integer value of the current token.
        """
        if self.token_type_value == 'INT_CONST':
            return self.current_token
        return None

    def stringVal(self):
        """ Returns the string value of the current token, without the opening/closing quotes.
        """
        if self.token_type_value == 'STRING_CONST':
            return self.current_token
        return None