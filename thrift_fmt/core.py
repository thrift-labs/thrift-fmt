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

    def format(self, out: typing.TextIO):
        self._out = out
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

    def push_token(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)
        if node.symbol.type == ThriftParser.EOF:
            return
        self.push(node.symbol.text)

    def process_node(self, node):
        if not isinstance(node, TerminalNodeImpl):
            # add parent
            for child in node.children:
                child.parent = node

        method_name = node.__class__.__name__.split('.')[-1]
        fn = getattr(self, method_name, self._inline_Context)
        fn(node)

    def get_repeat_children(self, nodes, cls):
        children = []
        for i, child in enumerate(nodes):
            if not isinstance(child, cls):
                return children, nodes[i:]
            children.append(child)
        return children, []

    def is_EOF(self, node):
        return isinstance(node, TerminalNodeImpl) and node.symbol.type == ThriftParser.EOF

    def _block_nodes(self, nodes, indent=''):
        last_node = None
        for i, node in enumerate(nodes):
            if self.is_EOF(node):
                break

            if isinstance(node, (ThriftParser.HeaderContext, ThriftParser.DefinitionContext)):
                node = node.children[0]
            if i > 0:
                # TODO: skip struct/enum/senum/service
                if node.__class__ != last_node.__class__:
                    self._newline(2)
                else:
                    self._newline()

            self.push(indent)
            self.process_node(node)
            last_node = node

    def _inline_nodes(self, nodes):
        for i, node in enumerate(nodes):
            if i > 0:
                self.push(' ')
            self.process_node(node)

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        self.push_token(node)

    def DocumentContext(self, node):
        self.push('# fmt by thrift-fmt')
        self._newline()
        self._block_nodes(node.children)
        self._newline()

    def HeaderContext(self, node):
        assert False

    def DefinitionContext(self, node):
        assert False

    def _inline_Context(self, node):
        self._inline_nodes(node.children)

    def _inline_Context_type_annotation(self, node):
        if len(node.children) == 0:
            return
        if not isinstance(node.children[-1], ThriftParser.Type_annotationContext):
            self._inline_Context(node)
        else:
            self._inline_nodes(node.children[:-1])
            self.process_node(node.children[-1])

    Include_Context = _inline_Context
    Namespace_Context = _inline_Context_type_annotation
    Typedef_Context = _inline_Context_type_annotation
    Base_typeContext = _inline_Context_type_annotation
    Field_typeContext = _inline_Context
    Real_base_typeContext = _inline_Context
    Const_ruleContext = _inline_Context
    Const_valueContext = _inline_Context
    IntegerContext = _inline_Context
    Container_typeContext = _inline_Context
    Map_typeContext = _inline_Context
    Const_mapContext = _inline_Context
    Const_map_entryContext = _inline_Context
    List_separatorContext = _inline_Context
    Enum_fieldContext = _inline_Context

    def Enum_ruleContext(self, node):
        self._inline_nodes(node.children[:3])
        self._newline()
        fields, left = self.get_repeat_children(node.children[3:], ThriftParser.Enum_fieldContext)
        self._block_nodes(fields, indent=' '*4)
        self._newline()
        # TODO: type_annotation
        self._inline_nodes(left)

    def Struct_Context(self, node):
        self._inline_nodes(node.children[:3])
        self._newline()
        #import pdb
        #pdb.set_trace()
        fields, left = self.get_repeat_children(node.children[3:], ThriftParser.FieldContext)
        self._block_nodes(fields, indent=' '*4)
        self._newline()
        self._inline_nodes(left)

'''
SenumContext
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
