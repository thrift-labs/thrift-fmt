from antlr4.InputStream import InputStream
from antlr4.FileStream import FileStream
from antlr4.StdinStream import StdinStream


from thrift_parser import parse


class ThriftData(object):

    def __init__(self, input_stream: InputStream):
        self._input_stream = input_stream

        lexer, tokens, parser, document = parse(input_stream)
        self._lexer = lexer
        self._tokens = tokens
        self._parser = parser
        self._document = document

    @classmethod
    def from_file(cls, file: str):
        input_stream = FileStream(file, encoding='utf8')
        return ThriftData(input_stream)

    @classmethod
    def from_stdin(cls):
        input_stream = StdinStream(encoding='utf8')
        return ThriftData(input_stream)

    def format(self):
        # TODO: return
        return self

    def dump(self, file: str):
        return
