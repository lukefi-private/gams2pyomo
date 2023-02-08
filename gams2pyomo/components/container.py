
from .basic import Definition, ModelDefinition

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

