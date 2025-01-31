from lark import Tree
from .basic import _PREFIX, logger, BasicElement
from .util import find_alias

class FuncExpression(BasicElement):

    def __init__(self, operator, operands, meta):

        self.operator = operator
        self.operands = operands
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        math_func_dict = {
            'fn_abs': 'abs',
            'fn_arccos': 'acos',
            'fn_arcsin': 'asin',
            'fn_arctan': 'atan',
            'fn_ceil': 'ceil',
            'fn_cos': 'cos',
            'fn_cosh': 'cosh',
            'fn_floor': 'floor',
            'fn_sin': 'sin',
            'fn_sinh': 'sinh',
            'fn_tan': 'tan',
            'fn_tanh': 'tanh',
            'fn_log': 'log',
            'fn_log10': 'log10',
        }

        o = self.operands

        if self.operator.data in math_func_dict:
            container.required_packages.add('math')
            res = math_func_dict[self.operator.data] + '('
            if isinstance(o, list):
                for _o in o:
                    if isinstance(_o, (int, float)):
                        res += str(_o)
                    else:
                        res += _o.assemble(container, _indent)
            else:
                res += o.assemble(container, _indent)
            res += ')'
        elif self.operator.data == 'fn_card':
            res = f'len({_PREFIX + o.name.upper()})'
        elif self.operator.data == 'fn_power':
            res = '('
            if isinstance(o[0], (int, float)):
                res += str(o[0])
            else:
                res += o[0].assemble(container, _indent)
            res += ') ** '
            if isinstance(o[1], (int, float)):
                res += str(o[1])
            else:
                res += o[1].assemble(container, _indent)
        elif self.operator.data == 'fn_sqrt':
            res = '('
            if isinstance(o, (int, float)):
                res += str(o)
            else:
                res += o.assemble(container, _indent)
            res += ') ** 0.5'
        elif self.operator.data == 'fn_sqr':
            res = '('
            if isinstance(o, (int, float)):
                res += str(o)
            else:
                res += o.assemble(container, _indent)
            res += ') ** 2'
        elif self.operator.data == 'fn_ord':
            res = f'list({_PREFIX + o.name.upper()}).index({o.name}) + 1'
        elif self.operator.data == 'fn_log2':
            res = 'log('
            for _o in o:
                if isinstance(_o, (int, float)):
                    res += str(_o)
                else:
                    res += _o.assemble(container, _indent)
            res += ') / log(2)'
        elif self.operator.data == 'fn_errorf':
            container.required_packages.add('math')
            res = f'(1 + math.erf(({o.assemble(container, _indent)}) / math.sqrt(2))) / 2'
        elif self.operator.data == 'fn_sqrt':
            res = f'({o.assemble(container, _indent)}) ** 0.5'
        elif self.operator.data == 'fn_round':
            if isinstance(o, list):
                res = f'round({o[0].assemble(container, _indent)}, {o[1]})'
            else:  # decimal not given
                res = f'round({o[0].assemble(container, _indent)})'
        elif self.operator.data == 'fn_sameas':
            op_0 = o[0]
            op_1 = o[1]

            if isinstance(op_0, (str, float, int)):
                res = str(op_0)
            else:
                res = op_0.assemble(container, _indent)

            res += ' == '
            if isinstance(op_1, (str, float, int)):
                res += str(op_1)
            else:
                res += op_1.assemble(container, _indent)
        elif self.operator.data == 'fn_max':
            res = 'max('
            res += ', '.join([_o.assemble(container, _indent) for _o in o])
            res += ')'
        else:
            msg = "The operator has not been implemented: "
            msg += self.operator.data
            raise NotImplementedError(msg)

        if self.minus:
            res = '- ' + res

        if self.negate:
            res = 'not ' + res

        return res


class BinaryExpression(BasicElement):

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

    def assemble(self, container, _indent='', top_level=False, **kwargs):

        res = ''

        if not top_level:
            # add parenthesis around the expression
            res += '('

        if self.minus:
            res += '- '

        if isinstance(self.operand_1, (int, float)):
            res += str(self.operand_1)
        else:
            try:
                res += self.operand_1.assemble(container, _indent, top_level=self.operator in self.top_level_operator)
            except Exception as e:
                msg = "Error while trying to assemble operand 1 in the binary expression."
                logger.error(msg)
                raise e

        if isinstance(self.operator, Tree):
            try:
                res += ' ' + self.operator_dict[self.operator.data] + ' '
            except:
                raise NotImplementedError
        else:
            raise NotImplementedError

        if isinstance(self.operand_2, (int, float)):
            res += str(self.operand_2)
        else:
            try:
                res += self.operand_2.assemble(container, _indent, top_level=self.operator in self.top_level_operator)
            except Exception as e:
                msg = "Error while trying to assemble operand 2 in the binary expression."
                logger.error(msg)
                raise e

        if not top_level:
            # add parenthesis around the expression
            res += ')'

        return res


class ArithmeticExpression(BasicElement):

    top_level_operator = ['+', '-']

    def __init__(self, operand_1, operator, operand_2):

        self.operand_1 = operand_1
        self.operator = operator
        self.operand_2 = operand_2

    def assemble(self, container, _indent='', top_level=False, **kwargs):

        res = ''

        if not top_level:
            # add parenthesis around the expression
            res += '('

        if self.minus:
            res += '- '

        if isinstance(self.operand_1, (int, float)):
            res += str(self.operand_1)
        else:
            try:
                res += self.operand_1.assemble(container, _indent, top_level=self.operator in self.top_level_operator)
            except Exception as e:
                msg = "Error while trying to assemble operand 1 in the binary expression."
                logger.error(msg)
                raise e

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
        else:
            try:
                res += self.operand_2.assemble(container, _indent, top_level=self.operator in self.top_level_operator)
            except Exception as e:
                msg = "Error while trying to assemble operand 1 in the binary expression."
                logger.error(msg)
                raise e

        if not top_level:
            # add parenthesis around the expression
            res += ')'

        return res


class ConditionalExpression(BasicElement):

    def __init__(self, expression, condition, meta):
        self.expression = expression
        self.condition = condition
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent, **kwargs):
        raise NotImplementedError


class IndexedExpression(BasicElement):

    def __init__(self, idx, exp, condition):

        self.idx = idx
        self.exp = exp
        self.condition = condition


class SumExpression(IndexedExpression, BasicElement):

    def assemble(self, container, _indent='', **kwargs):

        if self.minus:
            res = '- '
        else:
            res = ''

        res += 'sum('

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the sum expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        if self.condition:
            res += ' if '
            if isinstance(self.condition, (int, float)):
                res += str(self.condition)
            else:
                res += self.condition.assemble(container, _indent)
        res += ')'

        return res


class ProdExpression(IndexedExpression, BasicElement):

    def assemble(self, container, _indent='', **kwargs):

        if self.minus:
            res = '- '
        else:
            res = ''

        res += 'math.prod('

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the product expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        if self.condition:
            res += ' if '
            if isinstance(self.condition, (int, float)):
                res += str(self.condition)
            else:
                res += self.condition.assemble(container, _indent)
        res += ')'
        container.required_packages.add("math") # needed for math.prod()

        return res


class SetMaxExpression(IndexedExpression, BasicElement):

    def assemble(self, container, _indent='', **kwargs):

        # set global variable for adding .value suffix in symbols
        global value_suffix
        value_suffix = True

        if self.minus:
            res = '- '
        else:
            res = ''

        res += 'max(['

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the set-max expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        if self.condition:
            res += ' if '
            if isinstance(self.condition, (int, float)):
                res += str(self.condition)
            else:
                res += self.condition.assemble(container, _indent)
        res += ')'

        res += '])'

        value_suffix = False

        return res


class SetMinExpression(IndexedExpression, BasicElement):

    def assemble(self, container, _indent='', **kwargs):

        # set global variable for adding .value suffix in symbols
        global value_suffix
        value_suffix = True

        if self.minus:
            res = '- '
        else:
            res = ''

        res += 'min(['

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the set-min expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        if self.condition:
            res += ' if '
            if isinstance(self.condition, (int, float)):
                res += str(self.condition)
            else:
                res += self.condition.assemble(container, _indent)
        res += ')'

        res += '])'

        value_suffix = False

        return res
