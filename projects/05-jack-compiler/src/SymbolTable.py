
# Made by Sohni Tagirisa
class SymbolTable:
    """the symbol table maps variable names to their properties:
        - type: int, boolean, String, Point, etc.
        - kind: where is it stored? (static, field, argument, local)
        - index: what's its position in that storage segment?
    """

    # constants for the four kinds of variables in jack
    STATIC = "static"    # shared by all instances
    FIELD = "field"      # instance-level variables, one per object
    ARG = "argument"     # function/method parameters
    VAR = "local"        # jack var -> vm local

    def __init__(self):
        """create a new symbol table with two scopes
        """
        # class-scope table: holds static and field variables, remain for the lifetime of the class/program
        self.class_table = {}

        # subroutine-scope table: holds argument and local variables, this gets reset when we start compiling a new subroutine
        self.subroutine_table = {}

        # running indices: we assign each variable a sequential index within its kind (ex- static 0, static 1, ...)
        self.class_count = {self.STATIC: 0, self.FIELD: 0}
        self.subroutine_count = {self.ARG: 0, self.VAR: 0}

    def start_subroutine(self, is_method: bool):
        """reset the subroutine's symbol table.
        """
        # clear the subroutine table
        self.subroutine_table = {}

        # reset the counters for arguments and local variables
        self.subroutine_count = {self.ARG: 0, self.VAR: 0}

        if is_method:
            # methods have a hidden first parameter of this
            # it's the object the method is being called on, we reserve argument 0 for it
            self.subroutine_table["this"] = {
                "type": "this",
                "kind": self.ARG,
                "index": self.subroutine_count[self.ARG],
            }
            # increment arg count so next parameter gets index 1
            self.subroutine_count[self.ARG] += 1

    def define(self, name: str, type_: str, kind: str):
        """define a new identifier of a given name, type, and kind, and assign it a running index
        """
        if kind in (self.STATIC, self.FIELD):
            # class-level variable: get the next available index for this kind
            index = self.class_count[kind]

            # add to class table
            self.class_table[name] = {"type": type_, "kind": kind, "index": index}

            # increment counter for next variable of this kind
            self.class_count[kind] += 1

        elif kind in (self.ARG, self.VAR):
            # subroutine-level variable: get the next available index for this kind
            index = self.subroutine_count[kind]

            # add to subroutine table
            self.subroutine_table[name] = {"type": type_, "kind": kind, "index": index}

            # increment counter for next variable of this kind
            self.subroutine_count[kind] += 1

        else:
            raise ValueError(f"Unknown kind: {kind}")

    def var_count(self, kind: str) -> int:
        """return the number of variables of the given kind already defined.
        """
        if kind in (self.STATIC, self.FIELD):
            return self.class_count[kind]
        elif kind in (self.ARG, self.VAR):
            return self.subroutine_count[kind]
        else:
            return 0

    def kind_of(self, name):
        """ return the kind of the named identifier in the current scope and if the identifier is unknown, return none
        """
        # check subroutine scope first
        if name in self.subroutine_table:
            return self.subroutine_table[name]["kind"]

        # then check class scope
        if name in self.class_table:
            return self.class_table[name]["kind"]

        # not found
        return None

    def type_of(self, name):
        """return the type of the named identifier.
        """
        # check subroutine scope first
        if name in self.subroutine_table:
            return self.subroutine_table[name]["type"]

        # then check class scope
        if name in self.class_table:
            return self.class_table[name]["type"]

        # not found
        return None

    def index_of(self, name):
        """return the index assigned to the named identifier (or none) -> the index is the position within its memory segment.
        """
        # check subroutine scope first
        if name in self.subroutine_table:
            return self.subroutine_table[name]["index"]

        # then check class scope
        if name in self.class_table:
            return self.class_table[name]["index"]

        # not found
        return None