import sys
import typing

from antlr4.InputStream import InputStream
from antlr4.FileStream import FileStream
from antlr4.StdinStream import StdinStream
from antlr4.Token import CommonToken

from thrift_parser import parse
from thrift_parser.ThriftParser import ThriftParser


class ThriftData(object):

    def __init__(self, input_stream: InputStream):
        _, tokens, _, document = parse(input_stream)
        self._tokens = tokens.tokens
        self.document = document

    @classmethod
    def from_file(cls, file: str):
        input_stream = FileStream(file, encoding='utf8')
        return ThriftData(input_stream)

    @classmethod
    def from_stdin(cls):
        input_stream = StdinStream(encoding='utf8')
        return ThriftData(input_stream)


class ThriftFormatter(object):
    def __init__(self, document):
        self._document = document
        self._out = sys.stdout

    def format(self, out: typing.TextIO):
        self._out = out
        self.process_node(self._document)

    def _newline(self):
        self._out.write('\n')

    def process_node(self, node):
        if isinstance(node, ThriftParser.DocumentContext):
            self.on_document(node)
        elif isinstance(node, ThriftParser.HeaderContext):
            self.on_header(node)
        elif isinstance(node, ThriftParser.Include_Context):
            self.on_include(node)

    def on_document(self, node):
        self._out.write('# fmt by thrift-fmt\n')
        for child in node.children:
            self.process_node(child)
        self._newline()

    def on_header(self, node):
        for child in node.children:
            self.process_node(child)
            self._newline()

    def on_include(self, node):
        _, value = node.children
        self._out.write('include {}'.format(value.symbol.text))
