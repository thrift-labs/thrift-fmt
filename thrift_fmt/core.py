from __future__ import annotations
import copy
import io
import typing
from typing import List, Optional, Callable, Tuple

from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl
from antlr4.tree.Tree import ParseTree

from thrift_parser import ThriftData
from thrift_parser.ThriftParser import ThriftParser


class Option(object):
    DEFAULT_INDENT: int = 4

    def __init__(self, patch :bool = True, comment :bool = True, indent :Optional[int] = None, assign_align: bool=False):
        self.patch: bool = patch
        self.comment: bool = comment
        self.indent: int = self.DEFAULT_INDENT
        if indent and indent > 0:
            self.indent = indent
        self.assign_align: bool = assign_align

class PureThriftFormatter(object):

    def __init__(self):
        self._option : Option = Option()

        self._newline_c: int = 0
        self._indent_s: str = ''

    def option(self, option: Option):
        self._option = option

    def format_node(self, node: ParseTree):
        self._out: io.StringIO = io.StringIO()
        self._newline_c = 0
        self._indent_s = ''

        self.process_node(node)
        return self._out.getvalue()

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

    def _indent(self, indent: str = ''):
        self._indent_s = indent

    @staticmethod
    def walk_node(root: ParseTree, fn: Callable[[ParseTree], None]):
        nodes = [root]
        while nodes:
            node = nodes.pop(0)
            fn(node)
            if not isinstance(node, TerminalNodeImpl):
                for child in node.children:
                    child.parent = node
                    nodes.append(child)

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
            ThriftParser.Exception_Context,
            ThriftParser.ServiceContext,
        ))

    def after_block_node_hook(self, _: ParseTree):
        pass

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
            self.after_block_node_hook(node)
            last_node = node

    def _inline_nodes(self, nodes: List[ParseTree], join: str = ' '):
        for i, node in enumerate(nodes):
            if i > 0:
                self._push(join)
            self.process_node(node)

    @staticmethod
    def gen_inline_Context(
            join: str = ' ',
            tight_fn: Optional[Callable[[int, ParseTree], bool]] = None):
        def fn(self: PureThriftFormatter, node: ParseTree):
            for i, child in enumerate(node.children):
                if i > 0 and len(join) > 0:
                    if not tight_fn or not tight_fn(i, child):
                        self._push(join)
                self.process_node(child)
        return fn

    @staticmethod
    def gen_subblocks_Context(start: int, field_class: typing.Type):
        def fn(self: PureThriftFormatter, node: ParseTree):
            self._inline_nodes(node.children[:start])
            self._newline()
            subblocks, left = self._get_repeat_children(node.children[start:], field_class)

            self.before_subblocks_hook(subblocks)
            self._block_nodes(subblocks, indent=' ' * self._option.indent)
            self.after_subblocks_hook(subblocks)

            self._newline()
            self._inline_nodes(left)
        return fn

    _gen_inline_Context = gen_inline_Context.__func__
    _gen_subblocks_Context = gen_subblocks_Context.__func__

    def before_subblocks_hook(self, _: List[ParseTree]):
        pass

    def after_subblocks_hook(self, _: List[ParseTree]):
        pass

    def process_node(self, node: ParseTree):
        if not isinstance(node, TerminalNodeImpl):
            for child in node.children:
                child.parent = node

        method_name = node.__class__.__name__.split('.')[-1]
        fn = getattr(self, method_name, None)
        assert fn
        fn(node)

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)
        if self._is_EOF(node):
            return

        # add indent
        if self._indent_s:
            self._push(self._indent_s)
            self._indent_s = ''

        self._push(node.symbol.text)

    def DocumentContext(self, node: ThriftParser.DocumentContext):
        self._block_nodes(node.children)

    def HeaderContext(self, node: ThriftParser.HeaderContext):
        self.process_node(node.children[0])

    def DefinitionContext(self, node: ThriftParser.DefinitionContext):
        self.process_node(node.children[0])

    Include_Context = _gen_inline_Context()
    Namespace_Context = _gen_inline_Context()
    Typedef_Context = _gen_inline_Context()
    Base_typeContext = _gen_inline_Context()
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
    Field_typeContext = _gen_inline_Context()
    Map_typeContext = _gen_inline_Context(
        tight_fn=lambda i, n: not PureThriftFormatter._is_token(n.parent.children[i-1], ','))
    Const_listContext = _gen_inline_Context(
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    Enum_ruleContext = _gen_subblocks_Context(3, ThriftParser.Enum_fieldContext)
    Struct_Context = _gen_subblocks_Context(3, ThriftParser.FieldContext)
    Union_Context = _gen_subblocks_Context(3, ThriftParser.FieldContext)
    Exception_Context = _gen_subblocks_Context(3, ThriftParser.FieldContext)
    Enum_fieldContext = _gen_inline_Context(
        join=' ',
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    FieldContext = _gen_inline_Context(
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    Function_Context = _gen_inline_Context(
        tight_fn=lambda i, n:
            PureThriftFormatter._is_token(n, '(') or
            PureThriftFormatter._is_token(n, ')') or
            PureThriftFormatter._is_token(n.parent.children[i-1], '(') or
            isinstance(n, ThriftParser.List_separatorContext)
    )
    OnewayContext = _gen_inline_Context()
    Function_typeContext = _gen_inline_Context()
    Throws_listContext = _gen_inline_Context(
        tight_fn=lambda i, n:
            PureThriftFormatter._is_token(n, '(') or
            PureThriftFormatter._is_token(n, ')') or
            PureThriftFormatter._is_token(n.parent.children[i-1], '(') or
            isinstance(n, ThriftParser.List_separatorContext)
    )
    Type_annotationsContext = _gen_inline_Context()
    Type_annotationContext = _gen_inline_Context(
        tight_fn=lambda _, n: isinstance(n, ThriftParser.List_separatorContext))
    Annotation_valueContext = _gen_inline_Context()

    def ServiceContext(self, node: ThriftParser.ServiceContext):
        fn = self.gen_subblocks_Context(3, ThriftParser.Function_Context)
        if self._is_token(node.children[2], 'extends'):
            fn = self.gen_subblocks_Context(5, ThriftParser.Function_Context)
        return fn(self, node)

    def SenumContext(self, node: ThriftParser.SenumContext):
        # deprecated
        pass


class ThriftFormatter(PureThriftFormatter):
    def __init__(self, data: ThriftData):
        super().__init__()

        self._data: ThriftData = data
        self._document: ThriftParser.DocumentContext = data.document

        self._field_assign_padding: int = 0
        self._field_comment_padding: int = 0
        self._last_token_index: int = -1

    def format(self) -> str:
        if self._option.patch:
            self.patch()

        return self.format_node(self._document)

    def patch(self):
        self._document.parent = None
        self.walk_node(self._document, self._patch_field_req)
        self.walk_node(self._document, self._patch_field_list_separator)
        self.walk_node(self._document, self._patch_remove_last_list_separator)

    @staticmethod
    def _patch_field_req(node: ParseTree):
        if not isinstance(node, ThriftParser.FieldContext):
            return
        if isinstance(node.parent, (ThriftParser.Function_Context, ThriftParser.Throws_listContext)):
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

    @staticmethod
    def _patch_field_list_separator(node: ParseTree):
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

    @staticmethod
    def _remove_last_list_separator(node: ParseTree):
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

    @staticmethod
    def _is_field_or_enum_field(node: ParseTree):
        return isinstance(node, (ThriftParser.FieldContext, ThriftParser.Enum_fieldContext))

    @staticmethod
    def _split_field_define_assign(node: ParseTree):
        '''
          split field to [left, right]
          field: '1: required i32 number_a = 0,'
          left:  '1: required i32 number_a'
          right: '= 0,'
        '''
        assert ThriftFormatter._is_field_or_enum_field(node)
        left = copy.copy(node)
        right = copy.copy(node)

        i = 0
        for i, child in enumerate(node.children):
            if ThriftFormatter._is_token(child, '='):
                break

        left.children = node.children[:i]
        right.children = node.children[i:]
        return left, right

    def _calc_subblocks_padding(self, subblocks: List[ParseTree]) -> Tuple[int, int]:
        if not subblocks:
            return 0, 0

        # only field is FieldContext or Enum_fieldContext
        if self._option.assign_align and self._is_field_or_enum_field(subblocks[0]):
            '''
                field: '1: required i32 number_a = 0,'
                assign_padding:    field.index('=')
                comment_padding:  max(assign) + max(left)
            '''
            left_max_size = 0
            right_max_size = 0
            for field in subblocks:
                left, right = self._split_field_define_assign(field)
                left_size = len(PureThriftFormatter().format_node(left))
                right_size = len(PureThriftFormatter().format_node(right))

                left_max_size = max(left_max_size, left_size)
                right_max_size = max(right_max_size, right_size)

            # add extra space
            assign_padding = left_max_size + 1
            comment_padding = left_max_size + 1 + right_max_size
        else:
            assign_padding = 0
            comment_padding = 0
            for subblock in subblocks:
                subblock_size = len(PureThriftFormatter().format_node(subblock))
                comment_padding = max(comment_padding, subblock_size)

        return assign_padding, comment_padding

    def before_subblocks_hook(self, subblocks: List[ParseTree]):
        # subblocks : [ Function ] | [ Field]

        # calculate the subblocks's padding
        assign_padding, comment_padding = self._calc_subblocks_padding(subblocks)
        if assign_padding > 0:
            self._field_assign_padding = assign_padding + self._option.indent
        if comment_padding > 0:
            self._field_comment_padding = comment_padding + self._option.indent

    def after_subblocks_hook(self, _: List[ParseTree]):
        self._field_assign_padding = 0
        self._field_comment_padding = 0

    def after_block_node_hook(self, _: ParseTree):
        self._tail_comment()

    def _get_current_line(self):
        cur = self._out.getvalue().rsplit('\n', 1)[-1]
        return cur

    def _padding(self, padding: int, pad: str=' '):
        if padding <= 0:
            return
        cur = self._get_current_line()
        padding = padding - len(cur)
        if padding > 0:
            self._append(pad * padding)

    def _line_comments(self, node: TerminalNodeImpl):
        if not self._option.comment:
            return

        if hasattr(node.symbol, 'is_fake') and node.symbol.is_fake:
            return

        token_index = node.symbol.tokenIndex
        comments = []
        for token in self._data.tokens[self._last_token_index + 1:]:
            if token.channel != 2:
                continue
            if self._last_token_index < token.tokenIndex < token_index:
                comments.append(token)

        for token in comments:
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
        if not self._option.comment:
            return

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
            self._padding(self._field_comment_padding, ' ')
            self._append(' ')
            self._append(comments[0].text.strip())
            self._push('')
            self._last_token_index = comments[0].tokenIndex

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)

        # add tail comment before a new line
        if self._newline_c > 0:
            self._tail_comment()

        # add abrove comments
        self._line_comments(node)

        # add field assign padding
        if self._option.assign_align and self._is_field_or_enum_field(node.parent) and self._is_token(node, '='):
            self._padding(self._field_assign_padding, ' ')

        super().TerminalNodeImpl(node)
