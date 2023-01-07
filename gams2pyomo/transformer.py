from pyomo.environ import ConcreteModel
from lark import Transformer, Tree, Token, v_args
from lark.tree import Meta
import logging
from .model import *

logger = logging.getLogger('gams_parser.model')
logging.basicConfig(level = logging.DEBUG)


@v_args(meta=True)
class TreeToModel(Transformer):

    def assemble(self):
        """
        Assemble Pyomo models.
        """

        ...

    def start(self, children, meta):
        """
        The root node.
        """

        logger.debug("Start root transforming...")

        # # initialize model
        # model = Model()

        # title
        res = \
r"""from pyomo.environ import *

m = ConcreteModel()

"""

        # options
        res += \
r"""options = []

alias = []
"""

        # go through each statement
        for statement in children:

            if isinstance(statement, Option) or isinstance(statement, Assignment):
                res += statement.assemble()
            # if isinstance(statement, Alias):
            #     res += statement.assemble()
            elif isinstance(statement, list):

                if isinstance(statement[0], Definition) or isinstance(statement[0], IndexList):
                    for _statement in statement:
                        res += _statement.assemble()
            # try:
            #     if isinstance(statement, Option):
            #         res += statement.assemble()
            # except:
            #     pass

            # logger.debug("\tProcessing new statement...")

            # append statements in order
            # model.append(statement)

            # try:
            #     # # alias
            #     # if isinstance(statement, Tree) and statement.data == 'alias':
            #     #     logger.debug('\t\ttype: alias statement')
            #     #     model.add_alias(statement)

            #     # display
            #     if isinstance(statement, Tree) and statement.data == 'display':
            #         logger.debug('\t\ttype: display statement')
            #         model.add_display(statement)

            #     # abort statement
            #     elif isinstance(statement, Tree) and statement.data == 'abort_statement':
            #         logger.debug('\t\ttype: abort statement')
            #         model.add_loop(statement)

            #     # loop statement
            #     elif isinstance(statement, Tree) and statement.data == 'loop_statement':
            #         logger.debug('\t\ttype: loop statement')
            #         model.add_loop(statement)

            #     # if statement
            #     elif isinstance(statement, Tree) and statement.data == 'if_statement':
            #         logger.debug('\t\ttype: if-statement')
            #         model.add_if(statement)

            #     # equation
            #     elif isinstance(statement, Tree) and statement.data == 'eq_definition':
            #         logger.debug('\t\ttype: equation definition')
            #         model.add_equation(statement)

            #     # model declaration
            #     elif isinstance(statement, Tree) and statement.data == 'model_definition':
            #         logger.debug('\t\ttype: model definition')
            #         model.add_model(statement)

            #     # solving statement
            #     elif isinstance(statement, Tree) and statement.data == 'solve_statement':
            #         logger.debug('\t\ttype: solving statement')
            #         model.add_solve(statement)

            #     # assignment
            #     elif isinstance(statement, Tree) and statement.data == 'assignment':
            #         logger.debug('\t\ttype: assignment statement')
            #         model.add_assignment(statement)

            #     # option
            #     elif isinstance(statement, tuple):
            #         logger.debug(f'\t\ttype: option setting ({statement[0]})')
            #         model.add_option(statement)

            #     # list of symbols (variables, parameters, etc.)
            #     elif isinstance(statement, list):
            #         logger.debug('\t\ttype: symbol list')
            #         for symbol_def in statement:
            #             model.add_symbol(symbol_def)

            #     # throw an exception for other statements
            #     else:
            #         raise Exception(f"Statement not handled: unknown statement {statement.data}")
            #     logger.debug("\tDone.")

            # # handle any exception
            # except Exception as e:
            #     logger.error("Statement not processed, error: {}".format(e))

        # return model
        return res

    def string(self, children, meta):
        return "".join(children)

    # def option_setting(self, children, meta):
    #     return (children[0].value, children[1].value)
    def option_setting(self, children, meta):
        return Option(children, meta)

    def value(self, children, meta):
        return float(children[0])

    def symbol_name(self, children, meta):
        if len(children) > 1:
            raise Exception("Only a single identifier allowed for name")
        logger.debug('Create symbol name={}'.format(children[0]))
        return SymbolName('symbol_name', children, meta=meta)

    def definition(self, children, meta):
        return Definition(children, meta)

    def model_definition(self, children, meta):
        return ModelDefinition('model_definition', children, meta)

    def solve_statement(self, children, meta):
        return SolveStatement('solve_statement', children, meta)

    def assignment(self, children, meta):
        return Assignment('assignment', children, meta)

    def index_list(self, children, meta):
        logger.debug("IndexList {}".format(children))
        return IndexList('index_list', children, meta)

    def set_list(self, children, meta):
        new_set_list = []
        for set_def in children:
            set_def.symbol_type = 'set'
        return children

    def parameter_list(self, children, meta):
        for param in children:
            param.symbol_type = 'parameter'
        return children

    def scalar_list(self, children, meta):
        for scalar in children:
            scalar.symbol_type = 'scalar'
        return children

    def equation_list(self, children, meta):
        for eq in children:
            eq.symbol_type = 'equation'
        return children

    def table_list(self, children, meta):
        for table in children:
            table.symbol_type = 'table'
        return children

    def b_variable_list(self, children, meta):
        """
        List of binary variables.
        """

        # mark definition type
        for var_def in children:
            var_def.symbol_type = 'b_variable'

        return children

    def p_variable_list(self, children, meta):
        """
        List of non-negative variables.
        """
        for var_def in children:
            var_def.symbol_type = 'p_variable'
        return children

    def variable_list(self, children, meta):
        """
        List of variables.
        """
        for var_def in children:
            var_def.symbol_type = 'variable'
        return children

    def alias_list(self, children, meta):
        """
        List of aliases.
        """
        for symbol in children:
            symbol.symbol_type = 'alias'
        return children
        # return Alias(children, meta)

    def if_statement(self, children, meta):
        return IfStatement('if_statement', children, meta)

    def loop_statement(self, children, meta):
        return LoopStatement('loop_statement', children, meta)

    def abort_statement(self, children, meta):
        return AbortStatement('abort_statement', children, meta)

    # TODO: drop the first arguments for these classes
    def display(self, children, meta):
        return Display(children, meta)

    def start_pyomo(self, children, meta):

        logger.debug("Processing statements...")

        m = ConcreteModel()

        for statement in children:
            ...
