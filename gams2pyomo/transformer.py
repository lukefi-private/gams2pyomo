import logging
from typing import List
from lark import Transformer, Tree, Token, v_args
from .components import *
from .util import sequence_set
from .components.container import _ARITHMETIC_TYPES

logging.config.fileConfig('gams2pyomo/config.ini', disable_existing_loggers=False)
logger = logging.getLogger('gams_translator.transformer')
logger.setLevel(logging.WARNING)


@v_args(meta=True)
class GAMSTransformer(Transformer):
    """
    The transformer class that transforms a Lark tree into Python/Pyomo code.
    """

    def __init__(self, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)
        self.container = ComponentContainer()

    # root node transforming ---------------------------------------------------

    def start(self, _, children):
        """
        Assemble the result string at the root node.
        """

        self.container.add_root_statements(children)
        res = self.container.assemble()
        return res

    # statements ---------------------------------------------------------------

    def for_st(self, meta, children):

        symbol = children[0]
        start_n = float(children[1])
        end_n = float(children[2])

        c = children[3]

        if isinstance(c, Token) and c.type == 'NUMBER':
            step = float(c)
            statements = children[4:]
        else:
            step = 1
            statements = children[3:]

        # make sure the stepsize has the correct sign
        if end_n <= start_n:
            step = -step

        return ForStatement(symbol, start_n, end_n, step, statements, meta)

    def put_st(self, meta, children):
        raise NotImplementedError

    def repeat_st(self, meta, children):

        statements = children[:-1]
        conditional = children[-1]
        return RepeatStatement(conditional, statements, meta)

    def while_st(self, meta, children):
        conditional = children[0]
        statements = children[1:]
        return WhileStatement(conditional, statements, meta)

    def break_st(self, meta, children):
        conditional = None
        for c in children:
            # neglect break times
            if isinstance(c, Tree) and c.data == 'break_times':
                pass
            else:
                conditional = c.children[0]
        return BreakStatement(meta, conditional)

    def continue_st(self, meta, children):
        conditional = None
        if children:
            conditional = children[0].children[0]
        return ContinueStatement(meta, conditional)

    def option(self, meta, children):
        name = children[0]
        value = children[1].value
        try:
            value = float(value)
            if value.is_integer():
                value = int(value)
        except ValueError:
            value = value.lower()
        return Option(name, value, meta)

    def model_def(self, meta, children):
        # return one or more `single_model_def`
        return children

    def single_model_def(self, meta, children):
        name = children[0]
        description = None
        equations = []
        for c in children[1:]:
            if isinstance(c, Tree) and c.data == 'model_description':
                description = c.children[0]
            else:
                equations.append(c)
        return ModelDefinition(name, equations, description, meta)

    def solve_st(self, meta, children):
        name = children[0]
        for c in children[1:]:
            if isinstance(c, Tree) and c.data == 'sense':
                sense = c.children[0]
            elif isinstance(c, Tree) and c.data == 'model_type':
                type = c.children[0]
            else:  # objective variable
                obj_var = c
        return SolveStatement(name, type, sense, obj_var, meta)

    def assignment(self, meta, children):
        symbol = children[0]
        if len(children) == 2:
            conditional = None
            expression = children[1]
        else:
            conditional = children[1]
            expression = children[2]
        return Assignment(symbol, conditional, expression, meta)

    def set_list(self, meta, children: List[Definition]):
        # `children` should be a list of Definition; only need to update their
        # `.type` attributes
        for set_def in children:
            set_def.type = 'set'
            # update their names to upper cases
            set_def.symbol.name = set_def.symbol.name.upper()
        return children

    def parameter_list(self, _, children):
        for param in children:
            param.type = 'parameter'
        return children

    def scalar_list(self, _, children):
        for scalar in children:
            scalar.type = 'scalar'
        return children

    def equation_list(self, _, children):
        for eq in children:
            eq.type = 'equation'
        return children

    def table_list(self, _, children):
        for table in children:
            table.type = 'table'
        return children

    def b_variable_list(self, _, children):
        """
        List of binary variables.
        """

        # mark definition type
        for var_def in children:
            var_def.type = 'b_variable'

        return children

    def p_variable_list(self, _, children):
        """
        List of non-negative variables.
        """
        for var_def in children:
            var_def.type = 'p_variable'
        return children

    def variable_list(self, _, children):
        """
        List of variables.
        """
        for var_def in children:
            var_def.type = 'variable'
        return children

    def alias_list(self, meta, children):
        """
        List of aliases.
        """

        # `children` should be a list of a single `index_list` (i.e., nested
        # list)
        return Alias(children[0], meta)

    def if_st(self, meta, children):

        condition = children[0]

        statement = []
        elif_st = []
        else_statement = None

        for c in children[1:]:
            if isinstance(c, Tree) and c.data == 'elseif_st':
                _condition = c.children[0]
                _statement = c.children[1:]
                elif_st.append(ElseIfStatement(_condition, _statement))
            elif isinstance(c, Tree) and c.data == 'else_statement':
                else_statement = c.children
            else:
                statement.append(c)
        return IfStatement(condition, statement, elif_st, else_statement, meta)

    def loop_st(self, meta, children):
        index_item = children[0]

        condition = None
        statements = []

        for child in children[1:]:
            if isinstance(child, Tree) and child.data == 'conditional':
                condition = child
            else:
                statements.append(child)
        return LoopStatement(index_item, condition, statements, meta)

    def abort_st(self, meta, children):
        return AbortStatement(children, meta)

    def display(self, meta, children):
        return Display(children, meta)

    def eq_def(self, meta, children):

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

    def definition(self, meta, children):

        symbol = children[0]
        data = None
        description = None

        for c in children[1:]:
            if isinstance(c, str):
                description = c
            else:
                data = c

        return Definition(symbol, description, data, meta)

    def data(self, meta, children):
        if isinstance(children, list):
            if isinstance(children[0], list) and len(children) == 1:
                return children[0]
            return children
        if len(children) == 1:
            return children[0]
        # idx_value
        elif isinstance(children[0], tuple):
            return children
        raise NotImplementedError

    def idx_value(self, meta, children):
        return (children[0], children[1])

    def data_element(self, meta, children):
        # probably most of the time?
        if len(children) == 1:
            c = children[0]
            if isinstance(c, (list, float, int, str)):
                return c
        raise NotImplementedError

    def string(self, meta, children):
        return children[0].value

    def value(self, meta, children):
        v = float(children[0])
        if v.is_integer():
            v = int(v)
        return v

    def description(self, meta, children):
        # `[1:-1]`: remove quote
        return children[0].value[1:-1]

    def identifier(self, meta, children):
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

    def symbol(self, meta, children):
        return Symbol(children)

    def symbol_name(self, meta, children):
        return children[0]

    def symbol_range(self, meta, children):
        return sequence_set(children[0], children[1])

    def symbol_index(self, meta, children):
        return children[0]

    def symbol_id(self, meta, children):

        # maintain integer
        if len(children) == 1:
            return children[0]

        return '.'.join([str(c) for c in children])

    def index_list(self, meta, children):

        res = []

        # avoid nested list from certain scenarios
        if len(children) == 1 and isinstance(children[0], list):
            return children[0]

        for c in children:
            if isinstance(c, str) or isinstance(c, int):
                res.append(c)
            elif isinstance(c, SpecialIndex):
                res.append(c)
            else:
                raise NotImplementedError
        return res

    def index_item(self, meta, children):
        c = children[0]
        if isinstance(c, (str, int)):
            return c
        elif isinstance(c, Token) and c.value == '*':
            return c
        else:
            raise NotImplementedError

    def symbol_element(self, meta, children):
        return children[0]

    def lead(self, meta, children):
        return SpecialIndex(children[0], 'lead', children[2])

    def lag(self, meta, children):
        return SpecialIndex(children[0], 'lag', children[2])

    def circular_lead(self, meta, children):
        return SpecialIndex(children[0], 'circular_lead', children[2])

    def circular_lag(self, meta, children):
        return SpecialIndex(children[0], 'circular_lag', children[2])

    def suffix(self, meta, children):
        return children[0]

    def add_expr(self, meta, children):
        if len(children) == 1 and isinstance(children[0], _ARITHMETIC_TYPES):
            return children[0]
        elif len(children) == 3:
            # parse the token
            children[1] = children[1].value
            return ArithmeticExpression(*children)
        else:
            raise NotImplementedError

    def mul_expr(self, meta, children):
        if len(children) == 1 and isinstance(children[0], _ARITHMETIC_TYPES):
            return children[0]
        elif len(children) == 3:
            # parse the token
            children[1] = children[1].value
            return ArithmeticExpression(*children)
        else:
            raise NotImplementedError

    def pow_expr(self, meta, children):
        if len(children) == 1 and isinstance(children[0], _ARITHMETIC_TYPES):
            return children[0]
        elif len(children) == 3:
            # parse the token
            children[1] = children[1].value
            return ArithmeticExpression(*children)
        else:
            raise NotImplementedError

    def indexed_operation(self, meta, children):

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

    def expression(self, meta, children):

        # func_expression, value, symbol[suffix], cli_param, quoted_string, expression
        if len(children) == 1:
            c = children[0]
            # value
            if isinstance(c, (float, int, str)):
                return c
            # symbol
            if isinstance(c, Symbol):
                return c
            # expression already processed
            if isinstance(c, (FuncExpression, BinaryExpression, ArithmeticExpression, SumExpression, SetMaxExpression, SetMinExpression)):
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

    def index_list(self, meta, children):
        # `children` should be a list of indices
        return children

    def table(self, meta, children):
        return children[0]

    def table_data(self, meta, children):
        data = {}
        list_j = children[0].children
        len_j = len(list_j)

        _counter = 0
        idx_i = None
        for c in children[1:]:
            if _counter == 0:
                idx_i = c
            else:
                idx_j = list_j[_counter - 1]
                data[idx_i, idx_j] = c
            _counter = (_counter + 1) % (len_j + 1)

        return data

    def macro(self, meta, children):
        option = children[0].value
        args = children[1].value
        return Macro(option, args, meta)

    def table_definition(self, meta, children):

        symbol = children[0]
        data = None
        description = None
        for c in children[1:]:
            if isinstance(c, dict):
                data = c
            else:
                description = c
        return Definition(symbol, description, data, meta, type='parameter')

    # rules not implemented yet ------------------------------------------------


    def func_import(self, _, __):
        return NotImplementedError("Function import is not translated.")

    def quoted_string(self, meta, children):
        res = children[0].value
        for c in children[1:-1]:
            res += c
        res += children[-1].value
        return res

    def operator_indexed(self, meta, children):
        raise NotImplementedError

    def operator_expression(self, meta, children):
        raise NotImplementedError

    def operator_logical(self, meta, children):
        raise NotImplementedError

    def operator_relation(self, meta, children):
        raise NotImplementedError

    def func_expression(self, meta, children):
        operator = children[0]
        if isinstance(children[1], Tree) and hasattr(children[1], 'data') and children[1].data == 'func_arguments':
            operands = children[1].children
        else:
            operands = children[1]
        return FuncExpression(operator, operands)

    def index_element(self, meta, children):
        raise NotImplementedError

    def cli_param(self, meta, children):
        raise NotImplementedError

    def acronym_def(self, meta, children):
        return NotImplementedError("Acronym definition is not translated.")
