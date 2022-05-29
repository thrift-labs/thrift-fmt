from __future__ import annotations
import typing
from typing import List, Optional, Callable, Tuple

from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl
from antlr4.tree.Tree import ParseTree


from thrift_parser import ThriftData
from thrift_parser.ThriftParser import ThriftParser


class ThriftFormatter(object):
    def __init__(self, data: ThriftData):
        self._data: ThriftData = data
        self._document: ThriftParser.DocumentContext = data.document
        self._newline_c: int = 0
        self._indent_s: str = ''
        self._last_token_index: int = -1

    def format(self, out: typing.TextIO):
        self._out = out
        self._newline_c = 0
        self._indent_s = ''
        self._last_token_index = -1

        self.process_node(self._document)

    def _push(self, text: str):
        if self._newline_c > 0:
            self._out.write('\n'*self._newline_c)
            self._newline_c = 0
        self._out.write(text)

    def _append(self, text: str):
        self._out.write(text)

    def _newline(self, repeat: int = 1):
        diff = repeat - self._newline_c
        if diff <= 0:
            return
        self._newline_c += diff

    def _indent(self, indent=''):
        self._indent_s = indent

    def patch(self):
        self._walk(self._patch_field_req)
        self._walk(self._patch_field_list_separator)
        self._walk(self._patch_remove_last_list_separator)

    def _walk(self, fn: Callable[[ParseTree], None]):
        self._document.parent = None
        nodes = [self._document]
        while nodes:
            node = nodes.pop(0)
            fn(node)
            if not isinstance(node, TerminalNodeImpl):
                for child in node.children:
                    child.parent = node
                    nodes.append(child)

    def _patch_field_req(self, node: ParseTree):
        if not isinstance(node, ThriftParser.FieldContext):
            return
        if isinstance(node.parent, ThriftParser.Function_Context):
            return

        for i, child in enumerate(node.children):
            if isinstance(child, ThriftParser.Field_reqContext):
                return
            if isinstance(child, ThriftParser.Field_typeContext):
                break

        fake_token = CommonToken()
        fake_token.type = 21
        fake_token.text = 'required'
        fake_token.is_fake = True
        fake_node = TerminalNodeImpl(fake_token)
        fake_req = ThriftParser.Field_reqContext(parser=node.parser)
        fake_req.children = [fake_node]
        # patch
        node.children.insert(i, fake_req)

    def _patch_field_list_separator(self, node: ParseTree):
        classes = (
            ThriftParser.Enum_fieldContext,
            ThriftParser.FieldContext,
            ThriftParser.Function_Context,
        )
        if not isinstance(node, classes):
            return

        tail = node.children[-1]
        if isinstance(tail, ThriftParser.List_separatorContext):
            tail.children[0].symbol.text = ','
            return

        fake_token = CommonToken()
        fake_token.text = ','
        fake_token.is_fake = True
        fake_node = TerminalNodeImpl(fake_token)
        fake_ctx = ThriftParser.List_separatorContext(parser=node.parser)
        fake_ctx.children = [fake_node]
        node.children.append(fake_ctx)

    def _patch_remove_last_list_separator(self, node: ParseTree):
        is_inline_field = isinstance(node, ThriftParser.FieldContext) and \
            isinstance(node.parent, (ThriftParser.Function_Context, ThriftParser.Throws_listContext))
        is_inline_node = isinstance(node, ThriftParser.Type_annotationContext)

        if is_inline_field or is_inline_node:
            self._remove_last_list_separator(node)

    def _remove_last_list_separator(self, node: ParseTree):
        if not node.parent:
            return

        is_last = False
        brothers = node.parent.children
        for i, child in enumerate(brothers):
            if child is node and i < len(brothers) - 1:
                if not isinstance(brothers[i + 1], child.__class__):
                    is_last = True
                    break

        if is_last and isinstance(node.children[-1], ThriftParser.List_separatorContext):
            node.children.pop()

    def _line_comments(self, node: TerminalNodeImpl):
        if hasattr(node.symbol, 'is_fake') and node.symbol.is_fake:
            return

        token_index = node.symbol.tokenIndex
        comments = []
        for token in self._data.tokens[self._last_token_index + 1:]:
            if token.channel != 2:
                continue
            if self._last_token_index < token.tokenIndex < token_index:
                comments.append(token)

        for i, token in enumerate(comments):
            if token.tokenIndex > 0 and token.type == ThriftParser.ML_COMMENT:
                self._newline(2)

            if self._indent_s:
                self._push(self._indent_s)
            self._push(token.text.strip())

            is_tight: bool = token.type == ThriftParser.SL_COMMENT \
                or self._is_EOF(node) \
                or 0 < node.symbol.line - (token.text.count('\n') + token.line) <= 1
            if is_tight:
                self._newline()
            else:
                self._newline(2)

        self._last_token_index = node.symbol.tokenIndex

    def _tail_comment(self):
        if self._last_token_index == -1:
            return

        last_token = self._data.tokens[self._last_token_index]
        comments = []
        for token in self._data.tokens[self._last_token_index + 1:]:
            if token.line != last_token.line:
                break
            if token.channel != 2:
                continue
            comments.append(token)

        assert len(comments) <= 1
        if comments:
            self._append(' ')
            self._append(comments[0].text.strip())
            self._push('')
            self._last_token_index = comments[0].tokenIndex

    def process_node(self, node: ParseTree):
        if not isinstance(node, TerminalNodeImpl):
            for child in node.children:
                child.parent = node

        method_name = node.__class__.__name__.split('.')[-1]
        fn = getattr(self, method_name, None)
        assert fn
        fn(node)

    @staticmethod
    def _get_repeat_children(nodes: List[ParseTree], cls: typing.Type[ParseTree]) \
            -> Tuple[List[ParseTree], List[ParseTree]]:
        children:  List[ParseTree] = []
        for i, child in enumerate(nodes):
            if not isinstance(child, cls):
                return children, nodes[i:]
            children.append(child)
        return children, []

    @staticmethod
    def _is_EOF(node: ParseTree):
        return isinstance(node, TerminalNodeImpl) and node.symbol.type == ThriftParser.EOF

    @staticmethod
    def _is_token(node: ParseTree, text: str):
        return isinstance(node, TerminalNodeImpl) and node.symbol.text == text

    @staticmethod
    def _is_newline_node(node: ParseTree):
        return isinstance(node, (
            ThriftParser.Enum_ruleContext,
            ThriftParser.Struct_Context,
            ThriftParser.Union_Context,
            ThriftParser.ExceptionContext,
            ThriftParser.ServiceContext,
        ))

    def _block_nodes(self, nodes: List[ParseTree], indent: str = ''):
        last_node = None
        for i, node in enumerate(nodes):
            if isinstance(node, (ThriftParser.HeaderContext, ThriftParser.DefinitionContext)):
                node = node.children[0]

            if i > 0:
                if node.__class__ != last_node.__class__ or self._is_newline_node(node):
                    self._newline(2)
                else:
                    self._newline()

            self._indent(indent)
            self.process_node(node)
            last_node = node

    def _inline_nodes(self, nodes: List[ParseTree], join: str = ' '):
        for i, node in enumerate(nodes):
            if i > 0:
                self._push(join)
            self.process_node(node)

    @staticmethod
    def _gen_inline_Context(
            join: str = ' ',
            tight_fn: Optional[Callable[[int, ParseTree], bool]] = None):
        def fn(self, node: ParseTree):
            for i, child in enumerate(node.children):
                if i > 0 and len(join) > 0:
                    if not tight_fn or not tight_fn(i, child):
                        self._push(join)
                self.process_node(child)
        return fn

    @staticmethod
    def _gen_subfields_Context(start: int, field_class: typing.Type):
        def fn(self, node: ParseTree):
            self._inline_nodes(node.children[:start])
            self._newline()
            fields, left = self._get_repeat_children(node.children[start:], field_class)
            self._block_nodes(fields, indent=' '*4)
            self._newline()
            self._inline_nodes(left)
        return fn

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)

        # add tail comment before a new line
        if self._newline_c > 0:
            self._tail_comment()

        # add abrove comments
        self._line_comments(node)

        if self._is_EOF(node):
            return

        # add indent
        if self._indent_s:
            self._push(self._indent_s)
            self._indent_s = ''

        self._push(node.symbol.text)

    def DocumentContext(self, node: ThriftParser.DocumentContext):
        self._block_nodes(node.children)

    Type_ruleContext = _gen_inline_Context(join='')
    Const_ruleContext = _gen_inline_Context(join='')
    Enum_fieldContext = _gen_inline_Context(join='')
    Field_ruleContext = _gen_inline_Context(join='')
    Type_ruleContext = _gen_inline_Context(join='')
    Type_annotationContext = _gen_inline_Context(join='')
    Type_idContext = _gen_inline_Context(join='')
    Type_listContext = _gen_inline_Context(join='')
    Type_mapContext = _gen_inline_Context(join='')
    Type_setContext = _gen_inline_Context(join='')
    Type_baseContext = _gen_inline_Context(join='')
    Type_identifierContext = _gen_inline_Context(join='')
    Include_Context = _gen_inline_Context()
    Namespace_Context = _gen_inline_Context()
    Typedef_Context = _gen_inline_Context()
    Base_typeContext = _gen_inline_Context()
    Field_typeContext = _gen_inline_Context()
    Real_base_typeContext = _gen_inline_Context()
    Const_ruleContext = _gen_inline_Context()
    Const_valueContext = _gen_inline_Context()
    IntegerContext = _gen_inline_Context()
    Container_typeContext = _gen_inline_Context(join='')
    Set_typeContext = _gen_inline_Context(join='')
    List_typeContext = _gen_inline_Context(join='')
    Cpp_typeContext = _gen_inline_Context()
    Const_mapContext = _gen_inline_Context()
    Const_map_entryContext = _gen_inline_Context()
    List_separatorContext = _gen_inline_Context()
    Field_idContext = _gen_inline_Context(join='')
    Field_reqContext = _gen_inline_Context()
    Map_typeContext = _gen_inline_Context(
        tight_fn=lambda i, n: not ThriftFormatter._is_token(n.parent.children[i-1], ','))
    Const_listContext = _gen_inline_Context(
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    Enum_ruleContext = _gen_subfields_Context(3, ThriftParser.Enum_fieldContext)
    Struct_Context = _gen_subfields_Context(3, ThriftParser.FieldContext)
    Union_Context = _gen_subfields_Context(3, ThriftParser.FieldContext)
    ExceptionContext = _gen_subfields_Context(3, ThriftParser.FieldContext)
    FieldContext = _gen_inline_Context(
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    Function_Context = _gen_inline_Context(
        tight_fn=lambda i, n:
            ThriftFormatter._is_token(n, '(') or
            ThriftFormatter._is_token(n, ')') or
            ThriftFormatter._is_token(n.parent.children[i-1], '(') or
            isinstance(n, ThriftParser.List_separatorContext)
    )
    OnewayContext = _gen_inline_Context()
    Function_typeContext = _gen_inline_Context()
    Throws_listContext = _gen_inline_Context()
    Type_annotationsContext = _gen_inline_Context()
    Type_annotationContext = _gen_inline_Context(
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    Annotation_valueContext = _gen_inline_Context()

    def ServiceContext(self, node: ThriftParser.ServiceContext):
        fn = self._gen_subfields_Context(3, ThriftParser.Function_Context)
        if isinstance(node.children[2], TerminalNodeImpl):
            if node.children[2].symbol.text == 'extends':
                fn = self._gen_subfields_Context(5, ThriftParser.Function_Context)

        return fn(self, node)

    def SenumContext(self, node: ThriftParser.SenumContext):
        # deprecated
        pass
