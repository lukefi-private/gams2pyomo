
from lark import Lark
import os
from .transformer import GAMSTransformer
import logging

logger = logging.getLogger('gams_translator')
logging.basicConfig(level=logging.WARNING)

dirname = os.path.dirname(__file__)
grammar = os.path.join(dirname, 'gams.lark')


with open(grammar, 'r') as in_file:
    text = in_file.read()
    lark_gams = Lark(text, propagate_positions=True)


class GAMSTranslator():

    def __init__(self, file):

        if isinstance(file, str):
            self.file = open(file, 'r')
        else:
            self.file = file

        self.text = self.file.read()

        # store the file name
        if isinstance(file, str):
            self.f_name = file.split('/')[-1]
        else:
            self.f_name = ''

        self.preprocess()

    def preprocess(self):
        """
        Preprocess the text.
        """

        lines = self.text.split('\n')

        # remove the first-line comments (as they lack `\n` and cannot be parsed by lark)
        while len(lines[0]) > 0 and lines[0][0] == '*':
            lines.pop(0)

        self.text = '\n'.join(lines)

    def parse_comments(self, parse_comment=False):
        """
        Parse the single-line comments prior to the main parsing step.

        Single-line comment pattern: `*` at line beginning.

        The ones in the comment blocks are neglected as those will be parsed.
        """

        lines = self.text.split('\n')

        comments = []

        comment_block = False
        for i, l in enumerate(lines):

            if len(l) >= 7 and '$ontext' in l.lower():
                comment_block = True
            if len(l) >= 8 and '$offtext' in l.lower():
                comment_block = False

            if not comment_block and len(l) > 0 and l[0] == '*':
                # store line number and comment contents
                comments.append((i, l[1:]))

        # try to parse the comments in case they are executable
        if parse_comment:

            _transformer = GAMSTransformer()
            _transformer._with_head = False

            new_comments = []
            for comment in comments:
                try:
                    _parse_tree = lark_gams.parse(comment[1])
                    res = _transformer.transform(_parse_tree)
                    # remove the extra `\n` in the end
                    res = res[:-1]
                    new_comments.append((comment[0], res))
                except Exception:
                    new_comments.append(comment)
            comments = new_comments

        return comments

    def parse(self):
        return lark_gams.parse(self.text)

    def transform(self):

        comments = self.parse_comments(parse_comment=True)

        parse_tree = lark_gams.parse(self.text)
        transformer = GAMSTransformer()
        transformer.import_comments(comments)
        transformer.import_f_name(self.f_name)

        res = transformer.transform(parse_tree)
        return res
