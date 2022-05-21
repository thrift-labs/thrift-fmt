import sys
import typing

from antlr4.InputStream import InputStream
from antlr4.FileStream import FileStream
from antlr4.StdinStream import StdinStream
from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl

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
        self._last_nodes = []

    def format(self, out: typing.TextIO):
        self._out = out
        self._last_nodes = []
        self._newline_c = 0
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

    def push_tokens(self, children, join=' '):
        for i, child in enumerate(children):
            if i > 0:
                self.push(join)
            self.push_token(child)

    def push_token(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)
        if node.symbol.type == ThriftParser.EOF:
            return
        self.push(node.symbol.text)

    def process_node(self, node):
        method_name = node.__class__.__name__.split('.')[-1]
        if hasattr(self, method_name):
            getattr(self, method_name)(node)
            self._last_nodes.push(node)
        else:
            print(type(node))
            #import pdb
            #pdb.set_trace()

    def iter_children(self, node, join='\n'):
        for i, child in enumerate(node.children):
            if i > 0:
                if join == '\n':
                    self._newline()
                else:
                    self.push(join)
            self.process_node(child)

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        self.push_token(node)

    def DocumentContext(self, node):
        self.push('# fmt by thrift-fmt')
        self._newline()
        self.iter_children(node)
        self._newline()

    def HeaderContext(self, node):
        self.iter_children(node)
        self._newline()

    def Include_Context(self, node):
        self.iter_children_line(node)

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

    def Field_typeContext(self, node):
        self.process_node(node.children[0])

    def Base_typeContext(self, node):
        self.process_node(node.children[0])
        if len(node.children) > 1:
            self.process_node(node.children[1])

    def Real_base_typeContext(self, node):
        self.push_token(node.children[0])

    def iter_children_line(self, node):
        self.iter_children(node, join=' ')

    def Const_ruleContext(self, node):
        self.iter_children_line(node)
        self._newline()

    Const_valueContext = iter_children_line
    IntegerContext = iter_children_line
    Container_typeContext = iter_children_line
    Map_typeContext = iter_children_line
    Const_mapContext = iter_children_line
    Const_map_entryContext = iter_children_line

    def List_separatorContext(self, node):
        self.push_token(node.children[0])

    def Enum_ruleContext(self, node):
        pass

'''
Cpp_includeContext


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

Container_typeContext
Map_typeContext
Set_typeContext
List_typeContext
Cpp_typeContext


Const_listContext
Const_map_entryContext
Const_mapContext
List_separatorContext
Real_base_typeContext
'''
