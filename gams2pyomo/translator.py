"""
This is the main translator module. It defines the main GAMSTranslator class
for major interactions.
"""

import logging
import logging.config
import os
from lark import Lark, UnexpectedCharacters
from .transformer import GAMSTransformer

logging.config.fileConfig('gams2pyomo/config.ini', disable_existing_loggers=False)
logger = logging.getLogger('gams_translator')
logger.setLevel(logging.WARNING)

grammar = os.path.join(os.path.dirname(__file__), 'gams.lark')


with open(grammar, 'r', encoding="utf8") as in_file:
    text = in_file.read()
    lark_gams = Lark(text, propagate_positions=True)


class GAMSTranslator():

    def __init__(self, file):

        if isinstance(file, str):
            self.file = open(file, 'r', encoding="utf8")
        else:
            self.file = file

        self.text = self.file.read()

        # store the file name
        if isinstance(file, str):
            self.f_name = file.split('/')[-1]
        else:
            self.f_name = ''

        self._preprocess()

    def _preprocess(self):
        """
        Preprocess the text.
        """

        logger.info("Preprocessing the text...")

        lines = self.text.split('\n')

        # remove the first-line comments (as they lack `\n` and cannot be parsed by lark)
        while len(lines[0]) > 0 and lines[0][0] == '*':
            lines.pop(0)

        self.text = '\n'.join(lines)

        logger.info("Done.")

    def parse_comments(self, translate_comment=False):
        """
        Parse the single-line comments prior to the main parsing step.

        Single-line comment pattern: `*` at line beginning.

        The ones in the comment blocks are neglected as those will be parsed.
        """

        logger.info("Parsing comments...")

        lines = self.text.split('\n')

        comments = []

        comment_block = False
        for i, line in enumerate(lines):

            if len(line) >= 7 and '$ontext' in line.lower():
                comment_block = True
            if len(line) >= 8 and '$offtext' in line.lower():
                comment_block = False

            if not comment_block and len(line) > 0 and line[0] == '*':
                # store line number and comment contents
                comments.append((i, line[1:]))

        # try to parse the comments in case they are executable
        if translate_comment:
            logger.info("Potential code in comment will be translated.")

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

        logger.info("Done.")

        return comments

    def parse(self):
        """
        Parse the GAMS code.

        Returns:
            Tree: the resulting Lark Tree.
        """

        logger.info("Parsing the text...")
        try:
            res = lark_gams.parse(self.text)
        except UnexpectedCharacters as e:
            logger.error("An error occurred during the parsing step. Program terminates.")
            raise e
        logger.info("Done.")
        return res

    def translate(self, translate_comment=True):
        """Translate the GAMS code into Python-Pyomo code.

        Args:
            parse_comment (bool, optional): _description_. Defaults to True.

        Returns:
            _type_: _description_
        """

        logger.info("Translating the GAMS code...")

        # extract comments
        comments = self.parse_comments(translate_comment=translate_comment)

        # parse into tree
        parse_tree = lark_gams.parse(self.text)

        transformer = GAMSTransformer()
        transformer.import_comments(comments)
        transformer.import_f_name(self.f_name)
        # transform
        res = transformer.transform(parse_tree)

        logger.info("Done.")

        return res
