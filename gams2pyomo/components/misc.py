from .basic import _NL, _PREFIX, logger

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


class Alias():
    def __init__(self, aliases, meta):

        self.aliases = aliases
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):
        # return f"aliases.append({self.aliases})" + _NL
        # no return for alias; aliases are directly transformed in other steps
        return ''


class Display():
    def __init__(self, symbols, meta):
        self.symbols = symbols
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        prefix = _PREFIX
        if 'last_solved_model' in globals():
            global last_solved_model
            prefix = 'm_' + last_solved_model + '.'

        _tmp_res = []
        for symbol in self.symbols:

            if symbol.index_list:
                raise NotImplementedError
            elif symbol.suffix:
                # activity level
                if symbol.suffix == 'l':
                    _res = symbol.name
                    _res = prefix + _res + '.pprint()' + _NL
                else:
                    logger.warn(f"Not supported suffix type for display: '.{symbol.suffix}'")
                    continue
            else:
                _res = symbol.assemble(container, _indent) + '.pprint()' + _NL

            _tmp_res.append(_indent + _res)

        res = ''.join(_tmp_res)

        return res


class Option():

    def __init__(self, name, value, meta):

        self.name = name.lower()
        self.value = value
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        # TODO: filter out certain irrelevant options
        _irrelevant_options = [
            'limrow', 'limcol'
        ]
        if self.name in _irrelevant_options:
            return ''

        container.add_option(self.name, self.value)

        return ''

        # if isinstance(self.value, str):
        #     # add quote to mark it as string
        #     v_string = f"'{self.value}'"
        # else:
        #     v_string = f"{self.value}"
        # return f"options['{self.name}'] = {v_string}" + _NL


class Macro():

    def __init__(self, option, args, meta):
        self.option, self.args = option, args
        self.lines = (meta.line, meta.end_line)

    def assemble(self, container, _indent='', **kwargs):

        if self.option == 'title':
            global model_title
            model_title = self.args
            return ''
        else:
            return NotImplementedError(f"The dollar control option '{self.option}' is not translated.")
