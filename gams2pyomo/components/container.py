from lark import Token
from .basic import Definition, ModelDefinition, logger, SolveStatement, Assignment, EquationDefinition, Symbol, _NL
from .expressions import *
from .flow_control import *
from .misc import Display, Option, Macro
from .misc import Alias

_NON_DEF_STATEMENT_TYPES = \
    (EquationDefinition, ModelDefinition, SolveStatement, Assignment,
    Definition, IfStatement, LoopStatement, AbortStatement, Alias, Display,
    Option, Macro, ForStatement, RepeatStatement, WhileStatement, BreakStatement, ContinueStatement)
_STATEMENT_TYPES = (Definition, ) + _NON_DEF_STATEMENT_TYPES
_ARITHMETIC_TYPES = (Symbol, int, float, FuncExpression,
                     ArithmeticExpression, SetMinExpression, SetMaxExpression, SumExpression)


class ComponentContainer(object):
    """The class for storing optimization components from GAMS code.

    Args:
        symbols (dict): The symbols declared in the code.
        equation_defs (list): The equation definitions.
        assignments (list): The assignment statements.
        model_defs (list): The optimization definitions.
        solve (list): The solve statements.
        options (dict): The options.
        if_st (list): The if statements.
        loop_st (list): The loop statements.
        abort_st (list): The abort statements.
        display_statement (list): The display statements.
    """

    def __init__(self):
        self.symbols = {
            "set": [],
            "parameter": [],
            "variable": [],
            "b_variable": [],
            "p_variable": [],
            "equation": [],
            "scalar": [],
            "table": [],
            'alias': []
        }
        self.equation_defs = []
        self.assignments = []
        self.model_defs = []
        self.solve = []
        self.options = {}
        self.if_st = []
        self.loop_st = []
        self.abort_st = []
        self.display = []

        self.root_statements = []

        self.model_title = ''

        self.required_packages = set()

        self.inner_scope = set()

    def assemble(self):

        logger.info("Assembling...")

        res = ''

        # assemble each statement
        for statement in self.root_statements:

            # insert comments before the statements
            res += self.insert_comment(statement)

            # record alias
            if isinstance(statement, Alias):
                self.add_alias(statement.aliases)

            # assemble each statement
            try:
                # non-definition statements
                if isinstance(statement, _NON_DEF_STATEMENT_TYPES):
                    _res = statement.assemble(self)
                    if isinstance(_res, str):
                        res += _res
                    else:
                        raise _res

                # definition lists
                elif isinstance(statement, list):

                    # go through each definition
                    for _c in statement:
                        if isinstance(_c, (Definition, ModelDefinition)):
                            res += _c.assemble(self)

                            # record symbols
                            self.add_symbol(_c)
                        else:
                            raise NotImplementedError(f"failed to assemble type {type(_c)} in the definition list at root node.")

                # comment block
                elif isinstance(statement, Token) and statement.type == 'COMMENT_BLOCK':
                    # `[8:-8]`: remove `$ontext\n` and `$offtext`
                    comment_block = statement.value[8:-8]
                    res += f'\n"""{comment_block}"""\n\n'

                # handle returned exceptions
                elif isinstance(statement, Exception):
                    raise statement
                else:
                    raise NotImplementedError(f"failed to assemble type {type(statement)} at root node.")
            except Exception as e:
                error_msg = "The statement cannot be translated into Pyomo. It is skipped in the generated code.\n"
                if hasattr(statement, 'lines'):
                    if statement.lines[0] == statement.lines[1]:
                        loc = f"line {statement.lines[0]}"
                    else:
                        loc = f"lines {statement.lines[0]}-{statement.lines[1]}"
                    error_msg += f"statement location: {loc}.\n"
                error_msg += f"An exception of type {type(e).__name__} occurred."
                if e.args:
                    if len(e.args) > 1:
                        error_msg += f" Arguments: {e.args!r}\n"
                    else:
                        error_msg += f" Argument: {e.args[0]!r}\n"
                logger.error(error_msg)

        # check if there are comments at the end
        if self.comments:
            while self.comments:
                comment = self.comments.pop(0)[1]
                res += '# ' + comment + '\n'

        # add header
        res = self._assemble_header() + res

        logger.info("Done.")

        return res

    def _assemble_header(self):

        # auto-generated sign
        header = "# " + "-" * 15 + " THIS SCRIPT WAS AUTO-GENERATED FROM GAMS2PYOMO " + "-" * 15 + "\n"
        f_name_len = len(self.f_name)
        if f_name_len > 0:
            total_l = 19 + f_name_len
            left_l = (80 - total_l) // 2
            right_l = (80 - total_l) - left_l
            header += "# " + "-" * left_l + f" FILE SOURCE: '{self.f_name}' " + "-" * right_l + "\n\n"

        # package import
        header += r"from pyomo.environ import *" + _NL

        for p in self.required_packages:
            header += rf"import {p}" + _NL
        header += "\n\n"

        # model declaration
        header += "m = ConcreteModel("
        if len(self.model_title) > 0:
            header += f"name='{self.model_title}'"
        header += ")" + _NL

        return header

    def add_root_statements(self, statements):
        self.root_statements = statements

    def import_comments(self, comments):
        """

        Add comments reserved from preprocessing.

        Args:
            comments (list): The list of tuples (line number, comment).
        """

        self.comments = comments

    def insert_comment(self, statement):
        """
        Insert the comment before the statement.
        """

        res = ''

        # definition list
        if isinstance(statement, list):
            for _s in statement:
                # recursive call
                res += self.insert_comment(_s)
            return res

        # comment block, skip
        if isinstance(statement, Token) and statement.type == 'COMMENT_BLOCK':
            return res

        # other statement types
        if type(statement) in _STATEMENT_TYPES:
            # check if the line number of the first unprocessed comments is
            # smaller than the end line of the statement
            while self.comments and self.comments[0][0] < statement.lines[1]:
                comment = self.comments.pop(0)[1]
                res += '# ' + comment + '\n'
            return res

        return res

    def import_f_name(self, f_name):
        """
        Import file name.
        """
        self.f_name = f_name

    def add_alias(self, component):
        self.symbols['alias'].append(component)

    def add_symbol(self, component):

        if isinstance(component, Definition):
            self.symbols[component.type].append(component.symbol.name)
        elif isinstance(component, ModelDefinition):
            self.model_defs.append(component.name)
        else:
            raise NotImplementedError

    def add_option(self, option_name, value):
        self.options[option_name] = value

    @property
    def set(self):
        return self.symbols['set']

    @property
    def parameter(self):
        return self.symbols['parameter']

    @property
    def equation(self):
        return self.symbols['equation']

    @property
    def variable(self):
        return self.symbols['variable'] + self.symbols['p_variable'] + self.symbols['b_variable']

    @property
    def scalar(self):
        return self.symbols['scalar']

    @property
    def symbol(self):
        """Returns the symbols.
        """
        for i in self.symbols:
            for j in self.symbols[i]:
                yield j

    def check_symbol(self, s):
        for i in self.symbols:
            for j in self.symbols[i]:
                if s == j:
                    return True

        return False

    # def __repr__(self):
    #     output = ["** model **", "\nsymbols:"]
    #     for i in self.symbols:
    #         if len(self.symbols[i]) > 0:
    #             output.append("n_{name}={num}".format(
    #                 name=i, num=len(self.symbols[i])))
    #     if len(self.assignments) > 0:
    #         output.append("\nn_assignments={num}".format(
    #             num=len(self.assignments)))

    #     for m in self.model_defs:
    #         output.append("\n{}".format(m))

    #     for s in self.solve:
    #         output.append("\n{}".format(s))

    #     output.append("\n** end model **")
    #     return " ".join(output)

