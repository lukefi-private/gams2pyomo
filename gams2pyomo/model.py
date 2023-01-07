from lark import Tree
from lark.tree import Meta
from .util import sequence_set
import logging

logger = logging.getLogger('gams_parser.model')
logging.basicConfig(level=logging.WARNING)


class Model(object):
    """The class for storing optimization models from GAMS code.

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

        self.statements = []

    def append(self, statement):
        """
        Append a statement into the tree. This records the given statements in order.
        """
        self.statements.append(statement)

    def __add__(self, other):
        """Combine two models.

        Args:
            other (Model): The other model.

        Returns:
            Model: The combined model.
        """

        model = Model()

        for s in self.symbols:
            model.symbols[s] = self.symbols[s]+other.symbols[s]

        model.equation_defs = self.equation_defs+other.equation_defs
        model.assignments = self.assignments+other.assignments
        model.model_defs = self.model_defs+other.model_defs
        model.solve = self.solve+other.solve

        return model

    def add_equation(self, e):
        """Add equations to the model.

        Args:
            e (Tree): The equation definition.
        """

        eqn_def = EquationDefinition()
        eqn_def.symbol = Symbol(e.children[0])
        eqn_def.meta = e.meta
        for s in e.find_data('symbol_name'):
            logger.debug('Found symbol ref: {}'.format(s))
            eqn_def.symbol_ref.append(s)
        self.equation_defs.append(eqn_def)

    def add_assignment(self, a):
        self.assignments.append(a)

    def add_model(self, m):
        self.model_defs.append(m)

    def add_solve(self, s):
        self.solve.append(s)

    # def add_alias(self, s):
    #     self.alias.append(s)

    def add_symbol(self, e):

        if not e.symbol_type:
            raise Exception('Symbol does not have a type!')
        elif e.symbol_type not in self.symbols:
            raise Exception('Symbol type not found')

        self.symbols[e.symbol_type].append(e)
        # logger.info("Symbol[{type}]={name} added to model".format(
        #     name=e.symbol.name, type=e.symbol_type))

    def add_option(self, o):
        try:
            self.options[o[0]] = float(o[1])
        except ValueError:
            self.options[o[0]] = o[1]

    def add_if(self, s):
        self.if_statement.append(s)

    def add_loop(self, s):
        self.loop_statement.append(s)

    def add_abort(self, s):
        self.abort_statement.append(s)

    def add_display(self, s):
        self.display.append(s)

    def set(self):
        return self.symbols['set']

    def parameter(self):
        return self.symbols['parameter']

    def equation(self):
        return self.symbols['equation']

    def variable(self):
        return self.symbols['variable']

    def scalar(self):
        return self.symbols['scalar']

    def symbol(self):
        """Returns the symbols.
        """
        for i in self.symbols:
            for j in self.symbols[i]:
                yield j

    def cross_reference(self):
        # TODO: what is this for?
        # TODO: this looks quite inefficient

        logger.debug("Cross referencing...")

        for i in self.symbols['equation']:
            for j in self.equation_defs:
                if i.symbol == j.symbol:
                    logger.debug('CR Match')
                    i.equation = j
                    i.symbol_ref = j.symbol_ref

    def reference_lines(self, text):
        """???
        TODO: summarize the function of this
        """

        lines = text.splitlines()

        for s in self.symbol():

            logger.debug("Reference line for symbol {}".format(s))

            line = s.meta.line - 1

            end_line = s.meta.end_line

            text = ["\n".join(lines[line:end_line])]

            if s.equation:

                text.insert(0, "*** Symbol Definition ***\n\n")
                text.append("\n\n*** Equation Definition ***\n\n")

                line = s.equation.meta.line-1
                end_line = s.equation.meta.end_line

                text.append("\n".join(lines[line:end_line]))

            s.text = "".join(text)

        for a in self.assignments:
            logger.debug("Reference line for assignment {}".format(a))
            line = a.meta.line-1
            end_line = a.meta.end_line
            text = ["\n".join(lines[line:end_line])]
            a.text = "".join(text)

    def __repr__(self):
        output = ["** model **", "\nsymbols:"]
        for i in self.symbols:
            if len(self.symbols[i]) > 0:
                output.append("n_{name}={num}".format(
                    name=i, num=len(self.symbols[i])))
        if len(self.assignments) > 0:
            output.append("\nn_assignments={num}".format(
                num=len(self.assignments)))

        for m in self.model_defs:
            output.append("\n{}".format(m))

        for s in self.solve:
            output.append("\n{}".format(s))

        output.append("\n** end model **")
        return " ".join(output)


class EquationDefinition():

    def __init__(self):
        # TODO IS THIS ENOUGH??? equation sign, lhs, rhs, ...
        self.symbol = None
        self.meta = None
        self.symbol_ref = []


class ModelDefinition(Tree):
    """
    The class for defined optimization models in the GAMS code. A single .gms
    file can define multiple optimization models.

    NOTE: This and the following classes are subclasses of Tree such that the
    tree structure can be maintained when transformed.
    """

    def __init__(self, data, children, meta=None):

        # NOTE The order of the children corresponds to the order of each
        # terminal in the rules.
        # first child: model name
        self.name = children[0]
        # following children: equations
        self.equations = children[1:]

        # reserve tree structure
        Tree.__init__(self, data, children, meta=meta)

    def __repr__(self):
        return "<model={} eqn={}>".format(self.name, ",".join([str(e) for e in self.equations]))


class SolveStatement(Tree):
    """
    The class for "solve" statement in the GAMS code.
    """

    def __init__(self, data, children, meta=None):

        # TODO: should it be called .name? or .m_name?
        self.name = children[0]

        for c in children:

            # get sense
            if isinstance(c, Tree) and c.data == 'sense_min':
                self.sense = 'min'
            elif isinstance(c, Tree) and c.data == 'sense_max':
                self.sense = 'max'

            # objective variable
            elif isinstance(c, SymbolName):
                self.obj = c

            # model types
            else:
                self.model_type = c


            # else:
            #     # TODO: a hierarchy of loggers
            #     logger.warning("[solve definition] Child not recognized.")

        Tree.__init__(self, data, children, meta=meta)

    def __repr__(self):
        return "-> solve model={name} {sense} {obj}".format(name=self.name, sense=self.sense, obj=self.obj)


class Assignment(Tree):
    """
    The class for assignment statement.
    """

    def __init__(self, data, children, meta=None):


        refs = set()
        for s in children:
            if isinstance(s, SymbolName):
                refs.add(s.name)
            elif isinstance(s, Tree):
                for s in s.find_data('symbol_name'):
                    refs.add(s.name)
        # store symbols
        self.symbol_refs = list(refs)

        self.symbol = Symbol(children[0])

        self.conditional = None

        if len(children) == 2:
            self.expression = children[1]
        else:  # len == 3
            self.conditional = children[1]
            self.expression = children[2]

        Tree.__init__(self, data, children, meta=meta)

    def __repr__(self):
        return "<assignment n_symbols={num}>".format(num=len(self.symbol_refs))

    def assemble(self):

        # LHS
        res = self.symbol.assemble()

        res += ' = '

        # RHS
        for c in self.children:
            try:
                res += c.assemble()
            except:
                res += str(c.value)
        return ''


class SymbolName(Tree):
    """
    The class for symbol names.
    """

    def __init__(self, data, children, meta=None):
        self.name = children[0]
        Tree.__init__(self, data, children, meta=meta)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "__{name}__".format(name=self.name)


class IndexList(Tree):

    symbol_type = None
    symbol = None
    description = None
    data = None
    equation = None
    symbol_ref = []

    """
    The class for lists of indices.
    """
    def items(self):
        return [s.name for s in self.children]

    def __repr__(self):
        return "({items})".format(items=",".join([str(c) for c in self.children]))

    def assemble(self):
        if self.symbol_type == 'alias':
            return self._assemble_alias()
        else:
            return ''

    def _assemble_alias(self):
        res = f'alias.append({[c.name.upper() for c in self.children]})\n'
        return res


class Data(Tree):
    """
    The class for GAMS data.
    """
    # def __init__(self, args):
    #     logger.debug("BUILD Data {}".format(args))
    #     self.data = args

    def __repr__(self):
        return "<data block len={length}>".format(length=len(self.data))

    def to_dict(self):

        res = {}

        for child in self.children:

            _idx = child.children[0].children[0].value
            try:
                _idx = int(_idx)
            except ValueError:
                pass

            _value = child.children[1]

            res[_idx] = _value

        return res


class Definition():
    """
    Definition of set, parameter, scalar, variable, equation, table, or alias.
    """

    symbol_type = None
    symbol = None
    description = None
    data = None
    equation = None
    symbol_ref = []

    def __init__(self, args, meta):

        # logger.debug("Build Definition: {}".format(args))
        self._meta = meta

        # TODO: apply this structure to other classes
        for a in args:
            # symbol
            if isinstance(a, Tree) and a.data == 'symbol':
                self.symbol = Symbol(a)
                self.meta.line = a.meta.line
                self.meta.end_line = a.meta.end_line
                self.meta.empty = False
            # description
            elif isinstance(a, Tree) and a.data == "description":
                self.description = "".join(a.children).strip("'")
                self.meta.end_line = a.end_line
            # data
            elif isinstance(a, Tree) and a.data == "data":
                self.data = Data(a.data, a.children, a.meta)
                self.meta.end_line = a.end_line

    @property
    def meta(self):
        if self._meta is None:
            self._meta = Meta()
        return self._meta

    def __repr__(self):
        output = []
        if self.symbol_type:
            output.append('[{}]'.format(self.symbol_type))
        output.append('{}'.format(self.symbol))
        if self.description:
            output.append('"{}"'.format(self.description))
        if self.data:
            output.append('{}'.format(self.data))
        return " ".join(output)

    def assemble(self):

        if self.symbol_type == 'set':
            return self._assemble_set()
        elif self.symbol_type == 'scalar':
            return self._assemble_scalar()
        elif self.symbol_type == 'parameter':
            return self._assemble_parameter()
        else:
            return ''

    def _assemble_set(self):

        if self.data.children[0].data == 'symbol_range':
            _idx_1, _idx_2 = str(self.data.children[0].children[0]), str(self.data.children[0].children[1])
            _tmp_set = sequence_set(_idx_1, _idx_2)
            _doc = self.description
            _symbol = self.symbol.name.upper()
            res = f"m.{_symbol} = Set(initialize={_tmp_set}, doc={_doc})\n"
            return res
        else:
            # TODO deal with other situation
            return ''

    def _assemble_scalar(self):
        _doc = self.description
        _symbol = self.symbol.name
        _data = self.data

        res = f"m.{_symbol} = Param("
        if _data:
            res += f"initialize={_data.children[0]}"
        if _doc:
            if _data:
                res += ", "
            res += f"doc={_doc}"
        res += ")\n"
        return res

    def _assemble_parameter(self):
        _doc = self.description
        _symbol = self.symbol.name
        _data = self.data

        res = f"m.{_symbol} = Param("

        # add index
        if hasattr(self.symbol, 'index_list') and self.symbol.index_list:
            for _idx in self.symbol.index_list:
                res += f"m.{_idx.upper()}, "
        if _data:
            res += f"initialize={_data.to_dict()}"
        if _doc:
            if _data:
                res += ", "
            res += f"doc={_doc}"
        res += ")\n"
        return res



class Symbol():
    """
    The class for symbols.
    """

    symbol_name = None
    index_list = None
    index = None

    def __init__(self, tree: Tree):

        if tree.data != 'symbol':
            raise Exception("Not a symbol def")

        info = tree.children

        self.name = info[0].name

        logger.debug("Creating Symbol: {}".format(self.name))

        if len(info) > 1:
            if info[1].data == 'index_list':
                if info[1].children[0].data == 'symbol_element':
                    self.index = info[1]
                    try:
                        self.index = self.index
                    except ValueError:
                        pass
                else:
                    self.index_list = info[1].items()
            else:  # TODO what if there is suffix
                pass

    def assemble(self):
        res = ''

        res += self.name
        if self.index:
            res += f'[{self.index}]'

        return res

    def __eq__(self, other):
        return self.name == other.name

    def __repr__(self):
        if self.index_list:
            return '__{symbol_name}{index_list}__'.format(symbol_name=self.name, index_list=self.index_list)
        else:
            return '__{symbol_name}__'.format(symbol_name=self.name)


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


class IfStatement(Tree):
    """
    The class for if statement.
    """

    def __init__(self, data, children, meta=None):

        self.condition = children[0]

        self.statement = []
        self.elif_statement = []
        self.else_statement = []

        for child in children[1:]:
            if child.data == 'elseif_statement':
                self.elif_statement.append(ElseIfStatement(child.data, child.children, child.meta))
            elif child.data == 'else_statement':
                self.else_statement.append(child)
            # elif child.data == 'statement':
            else:
                self.statement.append(child)
            # else:
            #     raise Exception('IfStatement: Unexpected children!')

        Tree.__init__(self, data, children, meta=meta)

class ElseIfStatement(Tree):
    def __init__(self, data, children, meta=None):

        self.condition = children[0]
        self.statement = children[1:]

        Tree.__init__(self, data, children, meta=meta)

class LoopStatement(Tree):
    def __init__(self, data, children, meta=None):

        self.index_item = children[0]

        self.condition = None
        self.statement = []

        for child in children[1:]:
            if child.data == 'conditional':
                self.condition = child
            else:
                self.statement.append(child)

        Tree.__init__(self, data, children, meta=meta)

class AbortStatement(Tree):
    def __init__(self, data, children, meta=None):

        Tree.__init__(self, data, children, meta=meta)

# class Alias(Tree):
#     def __init__(self, children, meta=None):

#         Tree.__init__(self, 'alias', children, meta=meta)

class Display(Tree):
    def __init__(self, children, meta=None):

        Tree.__init__(self, 'display', children, meta=meta)

class Option(Tree):

    def __init__(self, children, meta=None):

        self.name = str(children[0])
        v = children[1]
        try:
            v = int(v)
        except ValueError:
            try:
                v = float(v)
            except ValueError:
                pass
        self.value = v

        Tree.__init__(self, 'option_setting', children, meta=meta)

    def assemble(self):
        if isinstance(self.value, str):
            v_string = f"'{self.value}'"
        else:
            v_string = f"{self.value}"
        return f"options.append(('{self.name}', {v_string}))\n"