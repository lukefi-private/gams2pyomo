from .util import find_alias
import logging, logging.config
from abc import abstractclassmethod

_PREFIX = 'm_'
_NL = '\n'

logging.config.fileConfig('gams2pyomo/config.ini', disable_existing_loggers=False)
logger = logging.getLogger('gams_translator.julia_components')
logger.setLevel(logging.WARNING)

class BasicElement:

    negate = False
    minus = False

    @abstractclassmethod
    def assemble(self, container, _indent='', **kwargs):
        pass

class Symbol(BasicElement):
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

    def assemble(self, container, _indent='', at_begin=False, **kwargs):
        """
        It is possible that the parser cannot differentiate a specific index and
        a set. Therefore, it is necessary to check with the container if the
        index has been defined.
        """

        if at_begin:
            res = _indent
        else:
            res = ''

        if self.name in container.inner_scope:
            res += self.name
        else:
            res += self.name

        if False and self.index_list:
            res += '['
            _idx = self.index_list[0]
            if isinstance(_idx, SpecialIndex):
                res += f'{_idx.assemble(container, _indent):}'
            elif _idx.upper() in container.set:
                res += f'{_idx}'
            else:
                __idx = find_alias(_idx, container)
                # no alias, not defined, treat as specific index
                if __idx == _idx:
                    res += f"'{_idx}'"
                # alias found
                else:
                    res += f"{__idx}"
            for _idx in self.index_list[1:]:
                res += ', '
                if isinstance(_idx, SpecialIndex):
                    res += f'{_idx.assemble(container, _indent)}'
                elif _idx.upper() in container.set:
                    res += f'{_idx}'
                else:
                    __idx = find_alias(_idx, container)
                    # no alias, not defined, treat as specific index
                    if __idx == _idx:
                        res += f"'{_idx}'"
                    # alias found
                    else:
                        res += f"{__idx}"
            res += ']'

        # add .value suffix
        if 'value_suffix' in globals():
            global value_suffix
            if value_suffix:
                res += '.value'

        if self.minus:
            res = '- ' + res
        if self.negate:
            res = '!' + res

        return res

    def __repr__(self):
        res = self.name
        if self.index_list:
            res += '['
            res += ', '.join(i for i in self.index_list)
            res += ']'
        if self.suffix:
            res += '.' + self.suffix
        return res


class EquationDefinition(BasicElement):

    def __init__(self, name, index_list, condition, lhs, eq_sign, rhs, meta):
        self.name, self.index_list, self.condition, self.lhs, self.eq_sign, self.rhs = name, index_list, condition, lhs, eq_sign, rhs
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

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
        res = f'@constraint(m, {self.name}, '
        if index_list:
            for _idx in index_list:
                res += f', {_idx}'
        # increase indent
        _indent += '\t'

        # conditional line
        if self.condition:
            res += _indent + 'if '
            if isinstance(self.condition, (int, float)):
                res += str(self.condition)
            else:
                res += self.condition.assemble(container, _indent)
            res += _NL
            # increase indent
            _indent += '\t'

        # return line
        # res += _indent + 'return '
        # LHS
        if isinstance(self.lhs, (int, float)):
            res += str(self.lhs)
        else:
            try:
                res += self.lhs.assemble(container, _indent, top_level=False)
            except Exception as e:
                msg = "Error while trying to assemble the LHS of the equation."
                logger.error(msg)
                raise e
        # eq sign
        res += ' ' + _eq_sign_dict[self.eq_sign] + ' '
        # RHS
        if isinstance(self.rhs, (int, float)):
            res += str(self.rhs)
        else:
            try:
                res += self.rhs.assemble(container, _indent, top_level=False)
            except Exception as e:
                msg = "Error while trying to assemble the RHS of the equation."
                logger.error(msg)
                raise e
        # res += _NL

        # add else -> return skip
        if self.condition:
            # decrease indent
            _indent = _indent[:-1]
            # else line
            res += _indent + 'else' + _NL
            # increase indent
            _indent += '\t'
            res += _indent + 'return Constraint.Skip' + _NL

        # res += _indent[:-1] + 'end' + _NL
        # declaration line
        #res += self._assemble_declaration()

        res += ')' + _NL

        return res

    def _assemble_declaration(self):

        res = f"@constraint(m, {self.name}"

        global leap_lag_op, leap_lag_var, leap_lag_val
        if leap_lag_op:
            if self.index_list:
                for _idx in self.index_list:
                    if _idx == leap_lag_var:
                        if leap_lag_op == 'leap':
                            res += f'list({_PREFIX + _idx.upper()})[:-{leap_lag_val}], '
                        else:  # 'lag'
                            res += f'list({_PREFIX +_idx.upper()})[{leap_lag_val}:], '
                    else:
                        res += f'{_PREFIX +_idx.upper()}, '
            res += "()"
            res += f')' + _NL
            return res
        else:
            if self.index_list:
                for _idx in self.index_list:
                    res += f'{_PREFIX +_idx.upper()}, '
            res += "()"
            res += ')' + _NL
            return res


class ModelDefinition(BasicElement):
    """
    The class for defined optimization models in the GAMS code. A single .gms
    file can define multiple optimization models.
    """

    def __init__(self, name, equations, description, meta):

        self.name = name

        if description:
            self.description = description

        if len(equations) == 1 and isinstance(equations[0], str) and equations[0].lower() == 'all':
            self.all_equation = True
            self.equations = None
        else:
            self.all_equation = False
            self.equations = equations

        self.lines = (meta.line, meta.end_line)

    # def __repr__(self):
    #     return "<model={} eqn={}>".format(self.name, ",".join([str(e) for e in self.equations]))

    def assemble(self, container, _indent='', **kwargs):
        """
        No code is directly generated from model statement. The corresponding
        code is stored in the container and popped out when the model is solved.

        This is to prevent the impact of data manipulation after cloning.
        """

        # no need to do anything
        if self.all_equation:
            container.model_def_scripts[self.name] = f'm_{self.name} = copy(m)' + _NL
        else:
            m_name = f'm_{self.name}'
            # clone the original model
            res = f'{m_name} = copy(m)' + _NL
            # iterate through declared equations
            for eq in container.equation:
                if eq not in self.equations:
                    res += f"delete({m_name}, {m_name}[:{eq}])" + _NL
                    res += f"unregister({m_name}, :{eq})" + _NL
            container.model_def_scripts[self.name] = res

        return ''


class SolveStatement(BasicElement):
    """
    The class for "solve" statement in the GAMS code.
    """

    def __init__(self, name, type, sense, obj_var, meta):

        self.name, self.type, self.sense, self.obj_var = name, type, sense, obj_var
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        # get the model statement code
        res = container.model_def_scripts[self.name]

        _sense_dict = {
            'minimizing': "Min",
            'maximizing': "Max",
        }

        # declare objective
        res += f"@objective(m_{self.name}, {_sense_dict[self.sense]}, m_{self.name}[:{self.obj_var}])" + _NL

        # assign solver via model type
        if self.type.lower() in container.options:
            res += f"set_optimizer(m, {container.options[self.type.lower()]})" + _NL
        else:
            _default_solvers = {
                'lp': 'Ipopt',
                'mip': 'HiGHS',
                'nlp': 'Ipopt',
                'cns': 'Ipopt',
                'dnlp': 'Ipopt',
                'minlp': 'Alpine',
                'qcp': 'Ipopt',
                'miqcp': 'Juniper',
                'global': 'Alpine',
                # 'mcp', 'mpec', 'Stoch.'
            }
            solver = _default_solvers[self.type.lower()]
            res += f"set_optimizer(m_{self.name}, () -> {solver}.Optimizer())" + _NL
            container.required_packages.add(solver)

        # solve
        res += f"optimize!(m_{self.name})" + _NL

        # update global variable
        global last_solved_model
        last_solved_model = self.name

        return res


class Assignment(BasicElement):
    """
    The class for assignment statement.
    """

    def __init__(self, symbol: Symbol, condition, expression, meta):

        self.symbol, self.condition, self.expression = symbol, condition, expression
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        if self.symbol.suffix:
            return self._assemble_set_attribute(container, self.symbol.suffix, _indent)
        else:
            return self._assemble_basic(container, _indent)

    def _assemble_basic(self, container, _indent=''):

        res, _indent = self._assemble_loop_condition(container, _indent)

        # symbol
        res += self.symbol.assemble(container, _indent,
                                    at_begin=True, top_level=True)

        # equate sign
        res += ' = '

        # expression
        res += self._assemble_expression(container, _indent) + _NL

        return res

    def _assemble_set_attribute(self, container, attr, _indent=''):

        _attribute_dict = {
            'up': 'set_upper_bound',
            'lo': 'set_lower_bound',
            'fx': 'fix',
            'l': 'set_start_value'
        }

        res, _indent = self._assemble_loop_condition(container, _indent)

        # symbol
        symbol = self.symbol.assemble(container, _indent,
                                    at_begin=True, top_level=True)

        # set attribute
        # l: active level
        # if attr == 'l':
        #    res += f'{symbol} = '
        #    res += self._assemble_expression(container, _indent) + _NL
        # else:
        res += _attribute_dict[attr] + f'({symbol}, '
        # expression
        res += self._assemble_expression(container, _indent)
        res += ')' + _NL

        return res

    def _assemble_loop_condition(self, container, _indent):

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
        # if build_loop:
        #     for (_i, _s) in _set_dict.items():
                # res += _indent + f'for {_i} in {_s}:' + _NL
                # _indent += '\t'

        # conditional lines
        if self.condition:

            res += _indent + 'if '

            c = self.condition.children[0]
            try:
                res += c.assemble(container, _indent, top_level=True)
                res += ':' + _NL
            except Exception as e:
                msg = "Error while trying to assemble the condition of the assignment statement."
                logger.error(msg)
                raise e
            _indent += '\t'

        return res, _indent

    def _assemble_expression(self, container, _indent):
        res = ''
        if isinstance(self.expression, (int, float)):
            res += str(self.expression)
        else:
            try:
                res += self.expression.assemble(container, _indent, top_level=True)
            except Exception as e:
                msg = "Error while trying to assemble the expression."
                logger.error(msg)
                raise e

        return res


class Definition(BasicElement):
    """
    Definition of set, parameter, scalar, variable, equation, table, or alias.
    """

    description = None
    equation = None
    symbol_ref = []

    def __init__(self, symbol: Symbol, description, data, meta, type=None):

        self.symbol, self.description, self.data = symbol, description, data
        if type:
            self.type = type

        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

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

        data = ', '.join([f'"{set_member}"' for set_member in data])

        res = f"m_{symbol_name} = [{data}]" # , ordered=True"
        if doc:
            res += f" # {doc}"
        res += _NL

        return res

    def _assemble_scalar(self):
        symbol_name = self.symbol.name
        data = self.data
        doc = self.description

        # make all parameters mutable to handle potential update later
        res = f"{symbol_name} = "
        if data:
            if isinstance(data, list):
                res += str(data[0])
            else:
                res += str(data)
        # res += ")" 
        if doc:
            res += f" # {doc} "

        res += _NL
        return res

    def _assemble_parameter(self):
        symbol_name = self.symbol.name
        data = self.data
        doc = self.description

        # update the data structure
        # if isinstance(data, list):
        #     data = {k: v for (k, v) in data}

        # res = _PREFIX + f"{symbol_name} = Param("
        if data:
            res = f"m_{symbol_name} = Dict({data})" + _NL
        else:
            res = ""
            # add index
            if hasattr(self.symbol, 'index_list') and self.symbol.index_list:
                for i, _idx in enumerate(self.symbol.index_list):
                    if _idx == '*':
                        if data:
                            _tmp_list = []
                            for k in data:
                                if k[i] not in _tmp_list:
                                    _tmp_list.append(k[i])
                            res += f"[i in {_tmp_list}] "
                    else:
                        res += f"[i in {_idx.upper()}]"
            # res += f" in Parameter(i)"

            # data
            if data:
                # when scalar is declared as parameter
                if len(data) == 1 and isinstance(data, list):
                    res += f", start = {data[0]}"
                else:
                    res += f", start = {data}"
            # doc
            res += ")" 
            if doc:
                res += f" # {doc}"
            res += _NL
        return res

    def _assemble_variable(self, domain, container):

        symbol_name = self.symbol.name
        doc = self.description
        data = self.data

        # before assembling, check if the declaration is to update domain
        if symbol_name in container.variable:
            if domain == 'b':
                res = f'set_binary({symbol_name})'
            elif domain == 'p':
                res = f'set_lower_bound({symbol_name}, 0.0)'
            else:
                res = f'unset_binary({symbol_name})'
                res += f'delete_lower_bound({symbol_name})'
            return res + _NL
        else:


            # update the data structure
            if isinstance(data, list):
                data = {k: v for (k, v) in data}

            res = f"@variable(m, {symbol_name}, "

            _tmp_res = []
            # add index
            if hasattr(self.symbol, 'index_list') and self.symbol.index_list:
                for _idx in self.symbol.index_list:
                    _tmp_res.append(_PREFIX + f"{_idx.upper()}")
            # domain
            if domain == 'b':
                _tmp_res.append("Bin")
            elif domain == 'p':
                _tmp_res.append("lower_bound = 0")
            else:
                pass

            if data:
                _tmp_res.append(f"start = {data}")

            res += ", ".join(_tmp_res) + ")"
            if doc:
                res += f" # {doc}" 
            res += _NL

            return res


# class SymbolId(BasicElement):
#     """
#     The class for symbol IDs.
#     """

#     def __init__(self, sid):
#         logger.debug("Creating Symbol ID {}".format(sid))
#         self.sid = str(sid)

#     def __str__(self):
#         return self.sid

#     def __repr__(self):
#         return '*{sid}*'.format(sid=self.sid)


class SpecialIndex(BasicElement):
    """
    The class for special index, including lead, lag, circular_lead, and
    circular_lag.
    """

    def __init__(self, idx, type, value):

        self.index = idx
        self.type = type
        self.value = value

    def assemble(self, container, _indent='', **kwargs):

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


