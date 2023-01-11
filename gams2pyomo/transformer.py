from typing import List
from lark import Transformer, Tree, Token, v_args
import logging
from .components import *
from .util import sequence_set

logger = logging.getLogger('gams_parser.model')
logging.basicConfig(level=logging.DEBUG)

HEADING = \
r"""from pyomo.environ import *
import math


m = ConcreteModel()
options = {}

"""

_STATEMENT_TYPES = (EquationDefinition, ModelDefinition, SolveStatement,
                    Assignment, Definition, IfStatement, LoopStatement,
                    AbortStatement, Alias, Display, Option)

_ARITHMETIC_TYPES = (Symbol, int, float, UnaryExpression, ArithmeticExpression, SetMinExpression, SetMaxExpression, SumExpression)

@v_args(meta=True)
class GAMSTransformer(Transformer):

    comments = ''
    _with_head = True

    def import_comments(self, comments):
        """

        Add comments reserved from preprocessing.

        Args:
            comments (list): The list of tuples (line number, comment).
        """

        self.comments = comments

    def insert_comment(self, statement):

        res = ''

        # iterate through definition list
        if isinstance(statement, list):
            for s in statement:
                res += self.insert_comment(s)
            return res
        elif isinstance(statement, Token) and statement.type == 'COMMENT_BLOCK':
            return res
        elif type(statement) in _STATEMENT_TYPES:
            # check if the line number of the first unprocessed comments is
            # smaller than the end line of the statement
            while self.comments and self.comments[0][0] < statement.lines[1]:
                comment = self.comments.pop(0)[1]
                res += '# ' + comment + '\n'
            return res
        else:
            raise NotImplementedError

    def start(self, children, meta):
        """
        Assemble the result string at the root node.
        """

        # create a container to check sets, etc.
        container = ComponentContainer()

        res = ''
        # heading
        if self._with_head:
            res += HEADING

        # assemble each statement
        for c in children:

            # print(type(c))
            # if isinstance(c, list):
            #     print('\t', type(c[0]))

            # insert comments before the statements
            res += self.insert_comment(c)

            # record alias
            if isinstance(c, Alias):
                container.add_alias(c.aliases)

            # non-definition statements
            if isinstance(c, (Option, Alias, EquationDefinition, ModelDefinition, SolveStatement, Display, Assignment, IfStatement, LoopStatement, AbortStatement)):
                res += c.assemble(container)

            # definition lists
            elif isinstance(c, list):

                # go through each definition
                for _c in c:
                    if isinstance(_c, Definition):
                        res += _c.assemble(container)

                        # record symbols
                        container.add_symbol(_c)
                    else:
                        raise NotImplementedError(
                            f"failed to assemble type {type(_c)} in the definition list at root node.")

            # comment block
            elif isinstance(c, Token) and c.type == 'COMMENT_BLOCK':
                # `[8:-8]`: remove `$ontext\n` and `$offtext`
                comment_block = c.value[8:-8]
                res += f'\n"""{comment_block}"""\n\n'

            # # comment
            # elif isinstance(c, Token) and c.type == 'COMMENT':
            #     res += '# ' + c.value[1:] + '\n'
            # new line
            # elif isinstance(c, Tree) and c.data == 'statement' and len(c.children) == 0:
            #     pass

            else:
                raise NotImplementedError(f"failed to assemble type {type(c)} (not in the definition list) at root node.")

        # check if there are comments at the end
        if self.comments:
            while self.comments:
                comment = self.comments.pop(0)[1]
                res += '# ' + comment + '\n'

        return res

    # statements ---------------------------------------------------------------

    def option(self, children, meta):
        name = children[0]
        value = children[1].value
        try:
            value = float(value)
            if value.is_integer():
                value = int(value)
        except ValueError:
            value = value.lower()
        return Option(name, value, meta)

    def model_definition(self, children, meta):
        name = children[0]
        equations = children[1:]
        return ModelDefinition(name, equations, meta)

    def solve_statement(self, children, meta):
        name = children[0]
        for c in children[1:]:
            if isinstance(c, Tree) and c.data == 'sense':
                sense = c.children[0]
            elif isinstance(c, Tree) and c.data == 'model_type':
                type = c.children[0]
            else:  # objective variable
                obj_var = c
        return SolveStatement(name, type, sense, obj_var, meta)

    def assignment(self, children, meta):
        symbol = children[0]
        if len(children) == 2:
            conditional = None
            expression = children[1]
        else:
            conditional = children[1]
            expression = children[2]
        return Assignment(symbol, conditional, expression, meta)

    def set_list(self, children: List[Definition], _):
        # `children` should be a list of Definition; only need to update their
        # `.type` attributes
        for set_def in children:
            set_def.type = 'set'
            # update their names to upper cases
            set_def.symbol.name = set_def.symbol.name.upper()
        return children

    def parameter_list(self, children, _):
        for param in children:
            param.type = 'parameter'
        return children

    def scalar_list(self, children, _):
        for scalar in children:
            scalar.type = 'scalar'
        return children

    def equation_list(self, children, _):
        for eq in children:
            eq.type = 'equation'
        return children

    def table_list(self, children, _):
        for table in children:
            table.type = 'table'
        return children

    def b_variable_list(self, children, _):
        """
        List of binary variables.
        """

        # mark definition type
        for var_def in children:
            var_def.type = 'b_variable'

        return children

    def p_variable_list(self, children, _):
        """
        List of non-negative variables.
        """
        for var_def in children:
            var_def.type = 'p_variable'
        return children

    def variable_list(self, children, _):
        """
        List of variables.
        """
        for var_def in children:
            var_def.type = 'variable'
        return children

    def alias_list(self, children, meta):
        """
        List of aliases.
        """

        # `children` should be a list of a single `index_list` (i.e., nested
        # list)
        return Alias(children[0], meta)

    def if_statement(self, children, meta):

        condition = children[0]

        statement = []
        elif_statement = []
        else_statement = None

        for c in children[1:]:
            if isinstance(c, Tree) and c.data == 'elseif_statement':
                _condition = c.children[0]
                _statement = c.children[1:]
                elif_statement.append(ElseIfStatement(_condition, _statement))
            elif isinstance(c, Tree) and c.data == 'else_statement':
                else_statement = c.children
            else:
                statement.append(c)
        return IfStatement(condition, statement, elif_statement, else_statement, meta)

    def loop_statement(self, children, meta):
        index_item = children[0]

        condition = None
        statement = []

        for child in children[1:]:
            if isinstance(child, Tree) and child.data == 'conditional':
                condition = child
            else:
                statement.append(child)
        return LoopStatement(index_item, condition, statement, meta)

    def abort_statement(self, children, meta):
        return AbortStatement(children, meta)

    def display(self, children, meta):
        return Display(children, meta)

    def eq_definition(self, children, meta):

        name = children[0].name
        index_list = None
        conditional = None

        if children[0].index_list:
            index_list = children[0].index_list

        if len(children) == 4:
            lhs = children[1].children[0]
            eq_sign = children[2].data
            rhs = children[3].children[0]
        else:  # len == 5
            conditional = children[1]
            lhs = children[2].children[0]
            eq_sign = children[3].data
            rhs = children[4].children[0]
        return EquationDefinition(name, index_list, conditional, lhs, eq_sign, rhs, meta)

    # basic elements -----------------------------------------------------------

    def definition(self, children, meta):
        return Definition(children, meta)

    def data(self, children, _):
        if len(children) == 1:
            return children[0]
        # idx_value
        elif isinstance(children[0], tuple):
            return children
        raise NotImplementedError

    def idx_value(self, children, _):
        return (children[0], children[1])

    def data_element(self, children, _):
        # probably most of the time?
        if len(children) == 1:
            c = children[0]
            if isinstance(c, (list, float, int)):
                return c
        raise NotImplementedError

    def string(self, children, _):
        return children[0].value

    def value(self, children, _):
        v = float(children[0])
        if v.is_integer():
            v = int(v)
        return v

    def description(self, children, _):
        # `[1:-1]`: remove quote
        return children[0].value[1:-1]

    def identifier(self, children, _):
        v = children[0].value

        if children[0].type == 'WORD_IDENTIFIER':
            return v

        try:
            v = float(v)
            if v.is_integer():
                v = int(v)
        except:
            pass
        return v

    def symbol(self, children, _):
        return Symbol(children)

    def symbol_name(self, children, _):
        return children[0]

    def symbol_range(self, children, _):
        return sequence_set(children[0], children[1])

    def symbol_index(self, children, _):
        return children[0]

    def symbol_id(self, children, _):

        # maintain integer
        if len(children) == 1:
            return children[0]

        return '.'.join([str(c) for c in children])

    def index_list(self, children, _):

        res = []
        for c in children:
            if isinstance(c, str) or isinstance(c, int):
                res.append(c)
            elif isinstance(c, SpecialIndex):
                res.append(c)
            else:
                raise NotImplementedError
        return res

    def index_item(self, children, _):
        c = children[0]
        if isinstance(c, (str, int)):
            return c
        else:
            raise NotImplementedError

    def symbol_element(self, children, _):
        return children[0]

    def lead(self, children, _):
        return SpecialIndex(children[0], 'lead', children[1])

    def lag(self, children, _):
        return SpecialIndex(children[0], 'lag', children[1])

    def circular_lead(self, children, _):
        return SpecialIndex(children[0], 'circular_lead', children[1])

    def circular_lag(self, children, _):
        return SpecialIndex(children[0], 'circular_lag', children[1])

    def suffix(self, children, _):
        return children[0]

    def add_expr(self, children, _):
        if len(children) == 1 and isinstance(children[0], _ARITHMETIC_TYPES):
            return children[0]
        elif len(children) == 3:
            # parse the token
            children[1] = children[1].value
            return ArithmeticExpression(*children)
        else:
            raise NotImplementedError

    def mul_expr(self, children, _):
        if len(children) == 1 and isinstance(children[0], _ARITHMETIC_TYPES):
            return children[0]
        elif len(children) == 3:
            # parse the token
            children[1] = children[1].value
            return ArithmeticExpression(*children)
        else:
            raise NotImplementedError

    def pow_expr(self, children, _):
        if len(children) == 1 and isinstance(children[0], _ARITHMETIC_TYPES):
            return children[0]
        elif len(children) == 3:
            # parse the token
            children[1] = children[1].value
            return ArithmeticExpression(*children)
        else:
            raise NotImplementedError

    def indexed_operation(self, children, _):

        _indexed_expression_dict = {
            'summation': SumExpression,
            'set_maximum': SetMaxExpression,
            'set_minimum': SetMinExpression,
        }

        if isinstance(children[0], Tree) and not isinstance(children[0], Symbol):
            if children[0].data in ('summation', 'set_maximum', 'set_minimum'):
                idx = []
                expression = None
                for c in children[1:]:
                    if isinstance(c, list):
                        idx += c
                    else:
                        expression = c
                return _indexed_expression_dict[children[0].data](idx, expression)
            else:
                raise NotImplementedError

    def expression(self, children, _):

        # func_expression, value, symbol[suffix], compiler_variable, quoted_string, expression
        if len(children) == 1:
            c = children[0]
            # value
            if isinstance(c, (float, int)):
                return c
            # symbol
            if isinstance(c, Symbol):
                return c
            # expression already processed
            if isinstance(c, (UnaryExpression, BinaryExpression, ArithmeticExpression, SumExpression, SetMaxExpression, SetMinExpression)):
                return c
            else:
                raise NotImplementedError

        # negate expression/conditional expression
        elif len(children) == 2:

            if isinstance(children[1], Tree) and children[1].data == 'conditional':
                return ConditionalExpression(*children)
            else:
                raise NotImplementedError

        elif len(children) == 3:
            # expression/logical/relation operation
            return BinaryExpression(*children)
        raise NotImplementedError

    def index_list(self, children, _):
        # `children` should be a list of indices
        return children
        # raise NotImplementedError
        # logger.debug("IndexList {}".format(children))
        # return IndexList('index_list', children, meta)

    # rules not implemented yet ------------------------------------------------

    def quoted_string(self, children, _):
        raise NotImplementedError

    def operator_indexed(self, children, _):
        raise NotImplementedError

    def operator_expression(self, children, _):
        raise NotImplementedError

    def operator_logical(self, children, _):
        raise NotImplementedError

    def operator_relation(self, children, _):
        raise NotImplementedError

    def func_expression(self, children, _):
        return UnaryExpression(*children)

    def table_data(self, children, _):
        raise NotImplementedError

    def macro(self, children, _):
        raise NotImplementedError

    def table_definition(self, children, _):
        raise NotImplementedError

    def index_element(self, children, _):
        raise NotImplementedError

    def compiler_variable(self, children, _):
        raise NotImplementedError
