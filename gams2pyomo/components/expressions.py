from lark import Tree
from .basic import _PREFIX, logger
from .util import find_alias

class FuncExpression():

    def __init__(self, operator, operands):

        self.operator = operator
        self.operands = operands

    def assemble(self, container, _indent='', **kwargs):

        o = self.operands
        if self.operator.data == 'fn_card':
            res = f'len({_PREFIX + o.name.upper()})'
        elif self.operator.data == 'fn_ord':
            res = f'list({_PREFIX + o.name.upper()}).index({o.name}) + 1'
        elif self.operator.data == 'fn_errorf':
            res = f'(1 + math.erf(({o.assemble(container, _indent)}) / math.sqrt(2))) / 2'
        elif self.operator.data == 'fn_sqrt':
            res = f'({o.assemble(container, _indent)}) ** 0.5'
        elif self.operator.data == 'fn_abs':
            res = f'abs({o.assemble(container, _indent)})'
        elif self.operator.data == 'fn_round':
            if isinstance(o, list):
                res = f'round({o[0].assemble(container, _indent)}, {o[1]})'
            else:  # decimal not given
                res = f'round({o[0].assemble(container, _indent)})'
        elif self.operator.data == 'fn_sameas':
            op_0 = self.operands[0]
            op_1 = self.operands[1]

            if isinstance(op_0, (str, float, int)):
                res = str(op_0)
            else:
                res = op_0.assemble(container, _indent)

            res += ' == '
            if isinstance(op_1, (str, float, int)):
                res += str(op_1)
            else:
                res += op_1.assemble(container, _indent)

            return res
        else:
            msg = "The operator has not been implemented: "
            msg += self.operator.data
            raise NotImplementedError(msg)

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

    def assemble(self, container, _indent='', top_level=False, **kwargs):

        res = ''

        if not top_level:
            # add parenthesis around the expression
            res += '('

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


class ArithmeticExpression():

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


class ConditionalExpression():

    def __init__(self, expression, condition):
        self.expression = expression
        self.condition = condition


class IndexedExpression():

    def __init__(self, idx, exp):

        self.idx = idx
        self.exp = exp


class SumExpression(IndexedExpression):

    def assemble(self, container, _indent='', **kwargs):
        res = 'sum('

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the sum expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'
        res += ')'

        return res


class SetMaxExpression(IndexedExpression):

    def assemble(self, container, _indent='', **kwargs):

        # set global variable for adding .value suffix in symbols
        global value_suffix
        value_suffix = True

        res = 'max(['

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the set-max expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        res += '])'

        value_suffix = False

        return res


class SetMinExpression(IndexedExpression):

    def assemble(self, container, _indent='', **kwargs):

        # set global variable for adding .value suffix in symbols
        global value_suffix
        value_suffix = True

        res = 'min(['

        try:
            res += self.exp.assemble(container, _indent)
        except Exception as e:
            msg = "Error while trying to assemble the set-min expression."
            logger.error(msg)
            raise e

        for _idx in self.idx:
            _idx = find_alias(_idx, container)
            res += f' for {_idx} in {_PREFIX + _idx.upper()}'

        res += '])'

        value_suffix = False

        return res
