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
        self._newline_c = 0

    def format(self, out: typing.TextIO):
        self._out = out
        self.process_node(self._document)

    def push(self, text):
        if not text:
            return
        self._out.write(text)
        self._newline_c = 0

    def _newline(self, repeat=1):
        diff = repeat - self._newline_c
        if diff <= 0:
            return
        self._out.write('\n'*diff)
        self._newline_c += diff

    def push_tokens(self, children):
        tokens = [child.symbol.text for child in children]
        self.push(' '.join(tokens))

    def process_node(self, node):
        method_name = node.__class__.__name__.split('.')[-1]
        if hasattr(self, method_name):
            getattr(self, method_name)(node)

    def iter_children(self, node):
        for child in node.children:
            self.process_node(child)
            self._newline()

    def DocumentContext(self, node):
        self.push('# fmt by thrift-fmt')
        self._newline()
        self.iter_children(node)
        self._newline()

    def HeaderContext(self, node):
        self.iter_children(node)
        self._newline(2)

    def Include_Context(self, node):
        _, value = node.children
        self.push('include {}'.format(value.symbol.text))

    def Namespace_Context(self, node):
        self._newline(2)
        self.push_tokens(node.children[:3])
        if len(node.children) > 3:
            self.process_node(node.children[3])
        self._newline()

    def DefinitionContext(self, node):
        self.iter_children(node)

    def Typedef_Context(self, node):
        self.push('typedef ')
        self.process_node(node.children[1])
        self.push(' ')
        self.push(node.children[2].symbol.text)

        if len(node.children) > 3:
            self.process_node(node.children[3])
        self._newline()

'''
Cpp_includeContext
DefinitionContext
Const_ruleContext

Enum_ruleContext
Enum_fieldContext
SenumContext
Struct_Context
Union_Context
ExceptionContext
ServiceContext
FieldContext
Field_idContext
Field_reqContext
Function_Context
OnewayContext
Function_typeContext
Throws_listContext
Type_annotationsContext
Type_annotationContext
Annotation_valueContext
Field_typeContext
Base_typeContext
Container_typeContext
Map_typeContext
Set_typeContext
List_typeContext
Cpp_typeContext
Const_valueContext
IntegerContext
Const_listContext
Const_map_entryContext
Const_mapContext
List_separatorContext
Real_base_typeContext
'''
