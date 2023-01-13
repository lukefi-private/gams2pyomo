from typing import List
from lark import Tree
from lark.tree import Meta
import logging
from .util import find_alias

logger = logging.getLogger('gams_parser.model')
logging.basicConfig(level=logging.WARNING)

_PREFIX = 'm.'
_NL = '\n'


class ComponentContainer(object):
    """The class for storing optimization components from GAMS code.

    Args:
        symbols (dict): The symbols declared in the code.
        equation_defs (list): The equation definitions.
        assignments (list): The assignment statements.
        model_defs (list): The optimization definitions.
        solve (list): The solve statements.
    """
    symbols = {}

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
        self.if_statement = []
        self.loop_statement = []
        self.abort_statement = []
        self.display = []

    def add_alias(self, component):
        self.symbols['alias'].append(component)

    def add_symbol(self, component):

        if isinstance(component, Definition):
            self.symbols[component.type].append(component.symbol.name)
        else:
            raise NotImplementedError

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


class Symbol(Tree):
    """
    The class for symbols.

    Symbol can be set, parameter, variable, equation, or alias.

    Arguments:
        name (str): The symbol name.
        index_list (list): The list of indices for the symbol.
        suffix (str): The suffix of the symbol
    """

    def __init__(self, children):

        self.name = children[0]
        self.index_list = None
        self.suffix = None

        for c in children[1:]:
            if isinstance(c, list):
                self.index_list = c
            elif isinstance(c, str):
                self.suffix = c
            else:
                raise NotImplementedError

        # info = tree.children

        # self.name = info[0].name

        # logger.debug("Creating Symbol: {}".format(self.name))

        # if len(info) > 1:
        #     if info[1].data == 'index_list':
        #         if info[1].children[0].data == 'symbol_element':
        #             self.index = info[1]
        #             try:
        #                 self.index = self.index
        #             except ValueError:
        #                 pass
        #         else:
        #             self.index_list = info[1].items()
        #     else:  # TODO what if there is suffix
        #         pass

    def assemble(self, container: ComponentContainer, _indent='', at_begin=False, **kwargs):

        if at_begin:
            res = _indent
        else:
            res = ''
        res += _PREFIX

        res += self.name
        if self.index_list:
            _idx = self.index_list[0]
            if isinstance(_idx, SpecialIndex):
                res += f'[{_idx.assemble(container, _indent):}'
            else:
                _idx = find_alias(_idx, container)
                res += f'[{_idx}'
            for _idx in self.index_list[1:]:
                if isinstance(_idx, SpecialIndex):
                    res += f', {_idx.assemble(container, _indent)}'
                else:
                    _idx = find_alias(_idx, container)
                    res += f', {_idx}'
            res += ']'

        # add .value suffix
        if 'value_suffix' in globals():
            global value_suffix
            if value_suffix:
                res += '.value'

        return res

    # def __eq__(self, other):
    #     return self.name == other.name

    # def __repr__(self):
    #     if self.index_list:
    #         return '__{name}{index_list}__'.format(name=self.name, index_list=self.index_list)
    #     else:
    #         return '__{name}__'.format(name=self.name)


class EquationDefinition():

    def __init__(self, name, index_list, conditional, lhs, eq_sign, rhs, meta):
        self.name, self.index_list, self.conditional, self.lhs, self.eq_sign, self.rhs = name, index_list, conditional, lhs, eq_sign, rhs
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        global leap_lag_op, leap_lag_var, leap_lag_val
        leap_lag_op, leap_lag_var, leap_lag_val = None, None, None

        _eq_sign_dict = {
            'eqn_equality': '==',
            'eqn_less_than': '<=',
            'eqn_greater_than': '>=',
        }

        index_list = self.index_list

        # function definition
        # def line
        res = f'def {self.name}(m'
        if index_list:
            for _idx in index_list:
                res += f', {_idx}'
        res += '):' + _NL
        # increase indent
        _indent += '\t'

        # conditional line
        if self.conditional:
            raise NotImplementedError

        # return line
        res += _indent + 'return '
        # LHS
        if isinstance(self.lhs, (_ASSEMBLE_TYPES)):
            res += self.lhs.assemble(container, _indent, top_level=False)
        elif isinstance(self.lhs, (int, float)):
            res += str(self.lhs)
        else:
            raise NotImplementedError
        # eq sign
        res += ' ' + _eq_sign_dict[self.eq_sign] + ' '
        # RHS
        if isinstance(self.rhs, (_ASSEMBLE_TYPES)):
            res += self.rhs.assemble(container, _indent, top_level=False)
        elif isinstance(self.rhs, (int, float)):
            res += str(self.rhs)
        else:
            raise NotImplementedError

        res += _NL

        # declaration line
        res += self._assemble_declaration()

        return res

    def _assemble_declaration(self):

        res = _PREFIX + self.name + ' = Constraint('

        global leap_lag_op, leap_lag_var, leap_lag_val
        if leap_lag_op:
            if self.index_list:
                for _idx in self.index_list:
                    if _idx == leap_lag_var:
                        if leap_lag_op == 'leap':
                            res += f'list({_PREFIX +_idx.upper()})[{leap_lag_val}:], '
                        else:  # 'lag'
                            res += f'list({_PREFIX +_idx.upper()})[:-{leap_lag_val}], '
                    else:
                        res += f'{_PREFIX +_idx.upper()}, '
            res += f'rule={self.name})' + _NL
            return res
        else:
            if self.index_list:
                for _idx in self.index_list:
                    res += f'{_PREFIX +_idx.upper()}, '
            res += f'rule={self.name})' + _NL
            return res


class ModelDefinition():
    """
    The class for defined optimization models in the GAMS code. A single .gms
    file can define multiple optimization models.
    """

    def __init__(self, name, equations, meta):

        self.name = name

        if len(equations) == 1 and isinstance(equations[0], str) and equations[0].lower() == 'all':
            self.all_equation = True
            self.equations = None
        else:
            self.all_equation = False
            self.equations = equations
            raise NotImplementedError

        self.lines = (meta.line, meta.end_line)

    def __repr__(self):
        return "<model={} eqn={}>".format(self.name, ",".join([str(e) for e in self.equations]))

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        # no need to do anything
        if self.all_equation:
            return ''
        else:
            raise NotImplementedError


class SolveStatement():
    """
    The class for "solve" statement in the GAMS code.
    """

    def __init__(self, name, type, sense, obj_var, meta):

        self.name, self.type, self.sense, self.obj_var = name, type, sense, obj_var
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        _sense_dict = {
            'minimizing': 1,
            'maximizing': -1,
        }

        # declare objective
        # NOTE what if _obj_ is used
        res = f'm._obj_ = Objective(rule={_PREFIX + self.obj_var}, sense={_sense_dict[self.sense]})' + _NL

        # assign solver via model type
        res += f"opt = SolverFactory(options['{self.type.lower()}'])" + _NL
        # solve
        res += f'opt.solve(m, tee=True)' + _NL
        return res


class Assignment():
    """
    The class for assignment statement.
    """

    def __init__(self, symbol: Symbol, conditional, expression, meta):

        self.symbol, self.conditional, self.expression = symbol, conditional, expression
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        if self.symbol.suffix:
            try:
                return self._assemble_set_attribute(container, self.symbol.suffix, _indent)
            except Exception:
                return Exception
        else:
            return self._assemble_basic(container, _indent)

    def _assemble_basic(self, container: ComponentContainer, _indent=''):

        res, _indent = self._assemble_loop_conditional(container, _indent)

        # symbol
        res += self.symbol.assemble(container, _indent,
                                    at_begin=True, top_level=True)

        # equate sign
        res += ' = '

        # expression
        res += self._assemble_expression(container, _indent) + _NL

        return res

    def _assemble_set_attribute(self, container: ComponentContainer, attr, _indent=''):

        _attribute_dict = {
            'up': 'setub',
            'lo': 'setlb',
            'fx': 'fix',
        }

        res, _indent = self._assemble_loop_conditional(container, _indent)

        # symbol
        res += self.symbol.assemble(container, _indent,
                                    at_begin=True, top_level=True)

        # set ubd
        res += '.' + _attribute_dict[attr] + '('
        # expression
        res += self._assemble_expression(container, _indent)
        res += ')' + _NL

        return res

    def _assemble_loop_conditional(self, container: ComponentContainer, _indent):

        # whether it is necessary to build a loop to assign values to a set of parameters
        build_loop = False
        _set_dict = {}

        # parse the symbol indices
        symbol = self.symbol
        if symbol.index_list:
            for i in symbol.index_list:
                # check if the symbol is indexed by a single index or a whole set
                if isinstance(i, str) and i.upper() in container.set:
                    build_loop = True
                    # only store set ot _set_dict
                    _set_dict[i] = i.upper()

        res = ''

        # loop lines
        if build_loop:
            for (_i, _s) in _set_dict.items():
                res += _indent + f'for {_i} in {_PREFIX + _s}:' + _NL
                _indent += '\t'

        # conditional lines
        if self.conditional:

            res += _indent + 'if '

            c = self.conditional.children[0]
            if isinstance(c, BinaryExpression):
                res += c.assemble(container, _indent, top_level=True)
                res += ':' + _NL
            else:
                raise NotImplementedError
            _indent += '\t'

        return res, _indent

    def _assemble_expression(self, container: ComponentContainer, _indent):
        res = ''
        if isinstance(self.expression, (_ASSEMBLE_TYPES)):
            res += self.expression.assemble(container, _indent, top_level=True)
        elif isinstance(self.expression, (int, float)):
            res += str(self.expression)
        else:
            raise NotImplementedError

        return res


# class IndexList(Tree):

#     type = None
#     symbol = None
#     description = None
#     data = None
#     equation = None
#     symbol_ref = []

#     """
#     The class for lists of indices.
#     """
#     def items(self):
#         return [s.name for s in self.children]

#     def __repr__(self):
#         return "({items})".format(items=",".join([str(c) for c in self.children]))

#     def assemble(self):
#         if self.type == 'alias':
#             return self._assemble_alias()
#         else:
#             return ''

#     def _assemble_alias(self):
#         res = f'alias.append({[c.name.upper() for c in self.children]})\n'
#         return res


# class Data(Tree):
#     """
#     The class for GAMS data.
#     """
#     # def __init__(self, args):
#     #     logger.debug("BUILD Data {}".format(args))
#     #     self.data = args

#     def __repr__(self):
#         return "<data block len={length}>".format(length=len(self.data))

#     def to_dict(self):

#         res = {}

#         for child in self.children:

#             _idx = child.children[0].children[0].value
#             try:
#                 _idx = int(_idx)
#             except ValueError:
#                 pass

#             _value = child.children[1]

#             res[_idx] = _value

#         return res


class Definition():
    """
    Definition of set, parameter, scalar, variable, equation, table, or alias.
    """

    type = None
    symbol = None
    description = None
    data = None
    equation = None
    symbol_ref = []

    def __init__(self, symbol, description, data, meta, type=None):

        self.symbol, self.description, self.data = symbol, description, data
        if type:
            self.type = type

        self.lines = (meta.line, meta.end_line)

    # def __repr__(self):
    #     output = []
    #     if self.type:
    #         output.append('[{}]'.format(self.type))
    #     output.append('{}'.format(self.symbol))
    #     if self.description:
    #         output.append('"{}"'.format(self.description))
    #     if self.data:
    #         output.append('{}'.format(self.data))
    #     return " ".join(output)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        if self.type == 'set':
            return self._assemble_set()
        elif self.type == 'scalar':
            return self._assemble_scalar()
        elif self.type == 'parameter':
            return self._assemble_parameter()
        elif self.type in ('variable', 'b_variable', 'p_variable'):
            _domain_dict = {
                'b_variable': 'b',
                'p_variable': 'p',
                'variable': ''
            }
            return self._assemble_variable(_domain_dict[self.type], container)
        elif self.type == 'equation':
            # no need to declare equation name, skip
            return ''
        else:
            raise NotImplementedError

    def _assemble_set(self):

        symbol_name = self.symbol.name
        doc = self.description
        data = self.data

        res = _PREFIX + f"{symbol_name} = Set(initialize={data}, ordered=True"
        if doc:
            res += f", doc='{doc}')"
        else:
            res += ')'
        res += _NL

        return res

    def _assemble_scalar(self):
        symbol_name = self.symbol.name
        data = self.data
        doc = self.description

        # make all parameters mutable to handle potential update later
        res = _PREFIX + f"{symbol_name} = Param(mutable=True"
        if data:
            if isinstance(data, list):
                res += f", initialize={data[0]}"
            else:
                res += f", initialize={data}"
        if doc:
            res += f", doc='{doc}'"
        res += ")" + _NL
        return res

    def _assemble_parameter(self):
        symbol_name = self.symbol.name
        data = self.data
        doc = self.description

        # update the data structure
        if isinstance(data, list):
            data = {k: v for (k, v) in data}

        res = _PREFIX + f"{symbol_name} = Param("

        # add index
        if hasattr(self.symbol, 'index_list') and self.symbol.index_list:
            for _idx in self.symbol.index_list:
                res += _PREFIX + f"{_idx.upper()}, "
        # make all parameters mutable to handle potential update later
        res += "mutable=True"
        # data
        if data:
            # when scalar is declared as parameter
            if len(data) == 1:
                res += f", initialize={data[0]}"
            else:
                res += f", initialize={data}"
        # doc
        if doc:
            res += f", doc='{doc}'"
        res += ")" + _NL
        return res

    def _assemble_variable(self, domain, container: ComponentContainer):

        symbol_name = self.symbol.name
        doc = self.description
        data = self.data

        # before assembling, check if the declaration is to update domain
        if symbol_name in container.variable:
            res = _PREFIX + symbol_name
            res += '.domain = '
            if domain == 'b':
                res += 'Binary'
            elif domain == 'p':
                res += 'NonNegativeReals'
            else:
                res += 'Any'
            return res + _NL
        else:


            # update the data structure
            if isinstance(data, list):
                data = {k: v for (k, v) in data}

            res = _PREFIX + f"{symbol_name} = Var("

            _tmp_res = []
            # add index
            if hasattr(self.symbol, 'index_list') and self.symbol.index_list:
                for _idx in self.symbol.index_list:
                    _tmp_res.append(_PREFIX + f"{_idx.upper()}")
            # domain
            if domain == 'b':
                _tmp_res.append("within=Binary")
            elif domain == 'p':
                _tmp_res.append("within=NonNegativeReals")
            else:
                pass

            if data:
                _tmp_res.append(f"initialize={data}")
            if doc:
                _tmp_res.append(f"doc='{doc}'")

            res += ", ".join(_tmp_res) + ")" + _NL

            return res


class SymbolId():
    """
    The class for symbol IDs.
    """

    def __init__(self, sid):
        logger.debug("Creating Symbol ID {}".format(sid))
        self.sid = str(sid)

    def __str__(self):
        return self.sid

    def __repr__(self):
        return '*{sid}*'.format(sid=self.sid)


class ElseIfStatement():
    def __init__(self, condition, statement):

        self.condition = condition
        self.statement = statement

        # Tree.__init__(self, data, children, meta=meta)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):
        res = _indent + 'elif '

        # condition
        if isinstance(self.condition, BinaryExpression):
            res += self.condition.assemble(container, _indent, top_level=True)
            res += ':' + _NL
        else:
            raise NotImplementedError

        # increase indent
        _indent += '\t'

        # statement(s)
        for s in self.statement:
            if isinstance(s, (Assignment, LoopStatement)):
                res += s.assemble(container, _indent)
            else:
                raise NotImplementedError

        return res


class IfStatement():
    """
    The class for if statement.
    """

    def __init__(self, condition, statement, elif_statement: List[ElseIfStatement], else_statement, meta):
        self.condition, self.statement, self.elif_statement, self.else_statement = condition, statement, elif_statement, else_statement
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        res = 'if '

        # condition
        if isinstance(self.condition, BinaryExpression):
            res += self.condition.assemble(container, _indent, top_level=True)
            res += ':' + _NL
            _indent += '\t'
        else:
            raise NotImplementedError

        # statement(s)
        for s in self.statement:
            if isinstance(s, Assignment):
                res += s.assemble(container, _indent)
                # res += '\n'
            else:
                raise NotImplementedError

        # elif
        if self.elif_statement:
            # reduce indent level
            _indent = (len(_indent) - 1) * '\t'
            for s in self.elif_statement:
                res += s.assemble(container, _indent)

        # else statement
        if self.else_statement:

            # reduce indent level
            _indent = (len(_indent) - 1) * '\t'
            res += _indent + 'else:' + _NL
            _indent += '\t'

            for s in self.else_statement:
                if isinstance(s, (Assignment, AbortStatement)):
                    res += s.assemble(container, _indent)
                    # res += '\n'
                else:
                    raise NotImplementedError
            ...

        return res


class LoopStatement():
    def __init__(self, index_item: str, conditional, statement, meta):

        self.index_item, self.conditional, self.statement = index_item, conditional, statement
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        _idx, _set = self.index_item, self.index_item.upper()

        res = ''

        # loop lines
        res += _indent + f'for {_idx} in {_PREFIX + _set}:' + _NL
        # increase indent
        _indent += '\t'

        # conditional lines
        if self.conditional:

            res += _indent + 'if '

            c = self.conditional.children[0]
            if isinstance(c, BinaryExpression):
                res += c.assemble(container, _indent, top_level=True)
                res += ':' + _NL
            else:
                raise NotImplementedError

            # increase indent
            _indent += '\t'

        # statement(s)
        for s in self.statement:
            if isinstance(s, (Assignment, LoopStatement)):
                res += s.assemble(container, _indent)
            else:
                raise NotImplementedError

        return res


class AbortStatement():
    def __init__(self, descriptions, meta):
        self.descriptions = descriptions
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):
        res = ''
        for d in self.descriptions:
            # res += _indent + f"print('{d}')" + _NL
            res += _indent + f"raise ValueError('{d}')" + _NL
        return res


class Alias():
    def __init__(self, aliases, meta):

        self.aliases = aliases
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):
        # return f"aliases.append({self.aliases})" + _NL
        # no return for alias; aliases are directly transformed in other steps
        return ''


class Display():
    def __init__(self, symbols, meta):
        self.symbols = symbols
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):
        res = ''

        _tmp_res = []
        for symbol in self.symbols:

            if symbol.index_list:
                raise NotImplementedError
            elif symbol.suffix:
                # activity level
                if symbol.suffix == 'l':
                    _res = symbol.name
                    _res = _PREFIX + _res + '.pprint()' + _NL
                else:
                    logger.warn(f"Not supported suffix type for display: '.{symbol.suffix}'")
                    continue
            else:
                _res = symbol.assemble(container, _indent)

            _tmp_res.append(_res)

        res += ''.join(_tmp_res)

        return res


class Option():

    def __init__(self, name, value, meta):

        self.name = name.lower()
        self.value = value
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        # TODO: filter out certain irrelevant options
        _irrelevant_options = [
            'limrow', 'limcol'
        ]
        if self.name in _irrelevant_options:
            return ''

        if isinstance(self.value, str):
            # add quote to mark it as string
            v_string = f"'{self.value}'"
        else:
            v_string = f"{self.value}"
        return f"options['{self.name}'] = {v_string}" + _NL


class SpecialIndex():

    def __init__(self, idx, type, value):

        self.index = idx
        self.type = type
        self.value = value

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        # update global variables for lead and lag for special constraint definition
        if self.type in ('lead', 'lag'):
            global leap_lag_op, leap_lag_var, leap_lag_val
            leap_lag_op = self.type
            leap_lag_var = self.index
            leap_lag_val = self.value

        _type_dict = {
            'lead': 'next',
            'lag': 'prev',
            'circular_lead': 'nextw',
            'circular_lag': 'prevw',
        }

        res = _PREFIX + self.index.upper() + '.' + _type_dict[self.type] + '('
        res += self.index + ', ' + str(self.value) + ')'

        return res


class UnaryExpression():

    def __init__(self, operator, operand):

        self.operator = operator
        self.operand = operand

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        o = self.operand
        if self.operator.data == 'fn_card':
            res = f'len({_PREFIX + o.name.upper()})'
        elif self.operator.data == 'fn_ord':
            res = f'list({_PREFIX + o.name.upper()}).index({o.name}) + 1'
        elif self.operator.data == 'fn_errorf':
            res = f'(1 + math.erf(({o.assemble(container, _indent)}) / math.sqrt(2))) / 2'
        elif self.operator.data == 'fn_sqrt':
            res = f'({o.assemble(container, _indent)}) ** 0.5'
        else:
            raise NotImplementedError

        return res


class BinaryExpression():

    operator_dict = {
        'addition': '+',
        'subtraction': '-',
        'multiplication': '*',
        'division': '/',
        'exponentiation': '**',
        'rel_le': '<=',
        'rel_ge': '>=',
        'rel_eq': '==',
        'rel_ne': '!=',
        'rel_eq_macro': '==',
        'abs_gt': '>',
        'abs_lt': '<',
        'bool_and': 'and',
        'bool_or': 'or',
        'bool_xor': '!='
    }

    top_level_operator = ['rel_eq', 'rel_ge', 'rel_eq', 'rel_ne',
                          'rel_eq_macro', 'abs_gt', 'abs_lt', 'exponentiation']

    def __init__(self, operand_1, operator, operand_2):

        self.operand_1 = operand_1
        self.operator = operator
        self.operand_2 = operand_2

    def assemble(self, container: ComponentContainer, _indent='', top_level=False, **kwargs):

        res = ''

        if not top_level:
            # add parenthesis around the expression
            res += '('

        if isinstance(self.operand_1, (int, float)):
            res += str(self.operand_1)
        elif isinstance(self.operand_1, (_ASSEMBLE_TYPES)):
            res += self.operand_1.assemble(container, _indent,
                                           top_level=self.operator in self.top_level_operator)
        else:
            raise NotImplementedError

        if isinstance(self.operator, Tree):
            try:
                res += ' ' + self.operator_dict[self.operator.data] + ' '
            except:
                raise NotImplementedError
        else:
            raise NotImplementedError

        if isinstance(self.operand_2, (int, float)):
            res += str(self.operand_2)
        elif isinstance(self.operand_2, (_ASSEMBLE_TYPES)):
            res += self.operand_2.assemble(container, _indent,
                                           top_level=self.operator in self.top_level_operator)
        else:
            raise NotImplementedError

        if not top_level:
            # add parenthesis around the expression
            res += ')'

        return res


class ArithmeticExpression():

    top_level_operator = ['+', '-']

    def __init__(self, operand_1, operator, operand_2):

        self.operand_1 = operand_1
        self.operator = operator
        self.operand_2 = operand_2

    def assemble(self, container: ComponentContainer, _indent='', top_level=False, **kwargs):

        res = ''

        if not top_level:
            # add parenthesis around the expression
            res += '('

        if isinstance(self.operand_1, (int, float)):
            res += str(self.operand_1)
        elif isinstance(self.operand_1, (_ASSEMBLE_TYPES)):
            res += self.operand_1.assemble(container, _indent,
                                           top_level=self.operator in self.top_level_operator)
        else:
            raise NotImplementedError

        res += ' ' + self.operator + ' '
        # if isinstance(self.operator, Tree):
        #     try:
        #         res += ' ' + self.operator_dict[self.operator.data] + ' '
        #     except:
        #         raise NotImplementedError
        # else:
        #     raise NotImplementedError

        if isinstance(self.operand_2, (int, float)):
            res += str(self.operand_2)
        elif isinstance(self.operand_2, (_ASSEMBLE_TYPES)):
            res += self.operand_2.assemble(container, _indent,
                                           top_level=self.operator in self.top_level_operator)
        else:
            raise NotImplementedError

        if not top_level:
            # add parenthesis around the expression
            res += ')'

        return res


class ConditionalExpression():

    def __init__(self, expression, condition):
        self.expression = expression
        self.condition = condition


class IndexedExpression():

    def __init__(self, idx, exp):

        self.idx = idx
        self.exp = exp


class SumExpression(IndexedExpression):

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):
        res = 'sum('

        if isinstance(self.exp, (_ASSEMBLE_TYPES)):
            res += self.exp.assemble(container, _indent)
        else:
            raise NotImplementedError

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'
        res += ')'

        return res


class SetMaxExpression(IndexedExpression):

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        # set global variable for adding .value suffix in symbols
        global value_suffix
        value_suffix = True

        res = 'max(['

        if isinstance(self.exp, (_ASSEMBLE_TYPES)):
            res += self.exp.assemble(container, _indent)
        else:
            raise NotImplementedError

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        res += '])'

        value_suffix = False

        return res


class SetMinExpression(IndexedExpression):

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        # set global variable for adding .value suffix in symbols
        global value_suffix
        value_suffix = True

        res = 'min(['

        if isinstance(self.exp, (_ASSEMBLE_TYPES)):
            res += self.exp.assemble(container, _indent)
        else:
            raise NotImplementedError

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        res += '])'

        value_suffix = False

        return res


class Macro():

    def __init__(self, option, args, meta):
        self.option, self.args = option, args
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container: ComponentContainer, _indent='', **kwargs):

        if self.option == 'title':
            global model_title
            model_title = self.args
            return ''
        else:
            raise NotImplementedError

_ASSEMBLE_TYPES = (Symbol, SumExpression, BinaryExpression,
                   ArithmeticExpression, UnaryExpression, SetMaxExpression,
                   SetMinExpression)
