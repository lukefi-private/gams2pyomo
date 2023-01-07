
from lark import Lark
import os
from .transformer import TreeToModel
import logging

logger = logging.getLogger('gams_parser')

dirname = os.path.dirname(__file__)
grammar = os.path.join(dirname, 'grammar/gams.lark')


with open(grammar, 'r') as in_file:
    text = in_file.read()
    lark_gams = Lark(text, propagate_positions=True)


class GamsParser():

    def __init__(self, file):

        if isinstance(file, str):
            self.file = open(file, 'r')
        else:
            self.file = file

        self.text = self.file.read()

    def parse(self):
        return lark_gams.parse(self.text)

    def transform(self):
        parse_tree = lark_gams.parse(self.text)
        res = TreeToModel().transform(parse_tree)
        # res.cross_reference()
        # res.reference_lines(self.text)
        return res
