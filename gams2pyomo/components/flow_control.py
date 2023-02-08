from typing import List
from .basic import Assignment, _NL, _PREFIX, logger
from .expressions import BinaryExpression
from .util import gams_arange

class ElseIfStatement():
    def __init__(self, condition, statement):

        self.condition = condition
        self.statement = statement

        # Tree.__init__(self, data, children, meta=meta)

    def assemble(self, container, _indent='', **kwargs):
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

    def __init__(self, condition, statement, elif_st: List[ElseIfStatement], else_statement, meta):
        self.condition, self.statement, self.elif_st, self.else_statement = condition, statement, elif_st, else_statement
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

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
            else:
                raise NotImplementedError

        # elif
        if self.elif_st:
            # reduce indent level
            _indent = (len(_indent) - 1) * '\t'
            for s in self.elif_st:
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
                else:
                    raise NotImplementedError
            ...

        return res


class LoopStatement():
    def __init__(self, index_item: str, conditional, statements, meta):

        self.index_item, self.conditional, self.statements = index_item, conditional, statements
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

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
        for s in self.statements:
            # TODO: add a list of all assemble-able statement classes
            if isinstance(s, (Assignment, LoopStatement, BreakStatement, ContinueStatement)):
                res += s.assemble(container, _indent)
            elif isinstance(s, str):
                res += _indent + s + _NL
            else:
                raise NotImplementedError

        return res


class RepeatStatement():
    def __init__(self, conditional, statements, meta):

        self.conditional, self.statements = conditional, statements
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        # start line
        res = _indent + 'while True:' + _NL
        # increase indent
        _indent += '\t'

        # statement(s)
        for s in self.statements:
            try:
                res += s.assemble(container, _indent)
            except Exception as e:
                msg = "An error occurred during the transformation step. Program terminates.\n"
                msg += f"Step: Transforming for loop, statement: {s}"
                logger.error(msg)
                raise e

        # conditional lines
        res += _indent + 'if '

        c = self.conditional
        if isinstance(c, BinaryExpression):
            res += c.assemble(container, _indent, top_level=True)
            res += ': break' + _NL
        else:
            raise NotImplementedError

        return res


class WhileStatement():
    def __init__(self, conditional, statements, meta):

        self.conditional, self.statements = conditional, statements
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        # start line
        res = _indent + 'while '

        c = self.conditional
        if isinstance(c, BinaryExpression):
            res += c.assemble(container, _indent, top_level=True)
            res += ':' + _NL
        else:
            raise NotImplementedError
        # increase indent
        _indent += '\t'

        # statement(s)
        for s in self.statements:
            try:
                res += s.assemble(container, _indent)
            except Exception as e:
                msg = "An error occurred during the transformation step. Program terminates.\n"
                msg += f"Step: Transforming for loop, statement: {s}"
                logger.error(msg)
                raise e

        return res


class ForStatement():
    def __init__(self, symbol, start_n, end_n, step, statements, meta):

        for_list = gams_arange(start_n, end_n, step)

        self.for_list = for_list

        self.symbol, self.statements = symbol, statements

        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        _idx = self.symbol.name

        res = ''

        # loop lines
        res += _indent + f'for {_idx} in {self.for_list}:' + _NL
        # increase indent
        _indent += '\t'

        # statement(s)
        for s in self.statements:
            try:
                res += s.assemble(container, _indent)
            except Exception as e:
                msg = "An error occurred during the transformation step. Program terminates.\n"
                msg += f"Step: Transforming for loop, statement: {s}"
                logger.error(msg)
                raise e

        return res


class BreakStatement():
    def __init__(self, meta, conditional):
        self.conditional = conditional
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):
        res = ''

        if self.conditional:
            res += _indent + 'if ' + self.conditional.assemble(container, _indent) + ":" + _NL
            _indent += '\t'

        res += _indent + 'break' + _NL

        return res


class ContinueStatement():
    def __init__(self, meta, conditional):
        self.conditional = conditional
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):
        res = ''

        if self.conditional:
            res += _indent + 'if ' + self.conditional.assemble(container, _indent) + ":" + _NL
            _indent += '\t'

        res += _indent + 'continue' + _NL

        return res


class AbortStatement():
    def __init__(self, descriptions, meta):
        self.descriptions = descriptions
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):
        res = ''
        for d in self.descriptions:
            res += _indent + f"raise ValueError('{d}')" + _NL
        return res

