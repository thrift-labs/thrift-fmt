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
        fn = getattr(self, method_name, None)
        print(type(node))
        assert fn
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

    def is_newline_node(self, node):
        return isinstance(node,
            (ThriftParser.Enum_ruleContext,
            ThriftParser.Struct_Context,
            ThriftParser.Union_Context,
            ThriftParser.ExceptionContext,
            ThriftParser.ServiceContext,
        ))

    def _block_nodes(self, nodes, indent=''):
        last_node = None
        for i, node in enumerate(nodes):
            if self.is_EOF(node):
                break

            if isinstance(node, (ThriftParser.HeaderContext, ThriftParser.DefinitionContext)):
                node = node.children[0]
            if i > 0:
                if node.__class__ != last_node.__class__ or self.is_newline_node(node):
                    self._newline(2)
                else:
                    self._newline()

            self.push(indent)
            self.process_node(node)
            last_node = node

    def _inline_nodes(self, nodes, join=' '):
        for i, node in enumerate(nodes):
            if i > 0:
                self.push(join)
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
    Set_typeContext = _inline_Context
    List_typeContext = _inline_Context
    Cpp_typeContext = _inline_Context
    Const_listContext = _inline_Context
    Const_mapContext = _inline_Context
    Const_map_entryContext = _inline_Context
    List_separatorContext = _inline_Context
    Enum_fieldContext = _inline_Context

    def _gen_subfields_Context(_, start, field_class):
        def _subfields_Context(self, node):
            self._inline_nodes(node.children[:start])
            self._newline()
            fields, left = self.get_repeat_children(node.children[start:], field_class)
            self._block_nodes(fields, indent=' '*4)
            self._newline()
            self._inline_nodes(left)
        return _subfields_Context

    Enum_ruleContext = _gen_subfields_Context(None, 3, ThriftParser.Enum_fieldContext)
    Struct_Context = _gen_subfields_Context(None, 3, ThriftParser.FieldContext)
    Union_Context = _gen_subfields_Context(None, 3, ThriftParser.FieldContext)
    ExceptionContext = _gen_subfields_Context(None, 3, ThriftParser.FieldContext)
    #SenumContext = _gen_subfields_Context(None, 3, ThriftParser.FieldContext)

    def SenumContext(self, node):
        # TODO: add more rule
        pass

    FieldContext = _inline_Context  # TODO
    Field_idContext = _inline_Context
    Field_reqContext = _inline_Context

    def Field_idContext(self, node):
        self._inline_nodes(node.children, join='')

    def ServiceContext(self, node):
        fn = self._gen_subfields_Context(3, ThriftParser.Function_Context)
        if isinstance(node.children[2], TerminalNodeImpl):
            if node.children[2].symbol.text == 'extends':
                fn = self._gen_subfields_Context(5, ThriftParser.Function_Context)

        return fn(self, node)

    Function_Context = _inline_Context
    OnewayContext = _inline_Context
    Function_typeContext = _inline_Context
    Throws_listContext = _inline_Context
    Type_annotationsContext = _inline_Context
    Type_annotationContext = _inline_Context
    Annotation_valueContext = _inline_Context
