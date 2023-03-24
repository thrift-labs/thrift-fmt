from __future__ import annotations
import copy
import io
import typing
from typing import List, Optional, Callable, Tuple, Dict

from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl
from antlr4.tree.Tree import ParseTree

from thrift_parser import ThriftData
from thrift_parser.ThriftParser import ThriftParser


FAKE_FIELD_REQ_TYPE: int = 21  # copy from thrirft_parser. generate by antlr4
FAKE_SEP_TOKEN_TEXT: str = ','  # fake separator token, we use comma


class Option:
    DEFAULT_INDENT: int = 4

    def __init__(self, patch_sep: bool = True, patch_required: bool = True,
                 keep_comment: bool = True, indent: Optional[int] = None,
                 align_assign: bool = True, align_field: bool = False):

        self.patch_sep: bool = patch_sep
        self.patch_required: bool = patch_required

        self.keep_comment: bool = keep_comment
        self.indent: int = self.DEFAULT_INDENT
        if indent and indent > 0:
            self.indent = indent

        self.align_assign: bool = align_assign
        self.align_field: bool = align_field

    def disble_patch(self) -> Option:
        self.patch_required = False
        self.patch_sep = False
        return self

    def disble_align(self) -> Option:
        self.align_field = False
        self.align_assign = False
        return self

    @property
    def is_align(self):
        return self.align_field or self.align_assign


class PureThriftFormatter:

    def __init__(self):
        self._option: Option = Option()

        self._out: io.StringIO = io.StringIO()
        self._newline_c: int = 0
        self._indent_s: str = ''

    def option(self, option: Option):
        self._option = option

    def format_node(self, node: ParseTree) -> str:
        self._out: io.StringIO = io.StringIO()
        self._newline_c: int = 0
        self._indent_s: str = ''

        self.process_node(node)
        return self._out.getvalue()

    def _push(self, text: str):
        if self._newline_c > 0:
            self._out.write('\n' * self._newline_c)
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
        nodes: List[ParseTree] = [root]
        while nodes:
            node: ParseTree = nodes.pop(0)
            fn(node)
            if not isinstance(node, TerminalNodeImpl):
                for child in node.children:
                    child.parent = node
                    nodes.append(child)

    @staticmethod
    def _split_repeat_children(nodes: List[ParseTree], cls: typing.Type[ParseTree]) \
            -> Tuple[List[ParseTree], List[ParseTree]]:
        children: List[ParseTree] = []
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

    @staticmethod
    def _get_parent(node: ParseTree):
        if hasattr(node, 'parent'):
            return node.parent
        return None

    def _block_nodes(self, nodes: List[ParseTree], indent: str = ''):
        last_node = None
        for i, node in enumerate(nodes):
            if isinstance(node, (ThriftParser.HeaderContext, ThriftParser.DefinitionContext)):
                node = node.children[0]

            self.before_block_node(node)
            if i > 0:
                if node.__class__ != last_node.__class__ or self._is_newline_node(node):
                    self._newline(2)
                else:
                    self._newline()

            self._indent(indent)
            self.process_node(node)
            self.after_block_node(node)
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
    def gen_subblocks_Context(start: int, field_class: typing.Type[ParseTree]):
        def fn(self: PureThriftFormatter, node: ParseTree):
            self._inline_nodes(node.children[:start])
            self._newline()

            subblocks, left_nodes = self._split_repeat_children(node.children[start:], field_class)
            self.before_subblocks(subblocks)
            self._block_nodes(subblocks, indent=' ' * self._option.indent)
            self.after_subblocks(subblocks)

            self._newline()
            self._inline_nodes(left_nodes)
        return fn

    _gen_inline_Context = gen_inline_Context.__func__
    _gen_subblocks_Context = gen_subblocks_Context.__func__

    def before_subblocks(self, _: List[ParseTree]):
        pass

    def after_subblocks(self, _: List[ParseTree]):
        pass

    def before_block_node(self, _: ParseTree):
        pass

    def after_block_node(self, _: ParseTree):
        pass

    def before_process_node(self, _: ParseTree):
        pass

    def after_process_node(self, _: ParseTree):
        pass

    def process_node(self, node: ParseTree):
        if not isinstance(node, TerminalNodeImpl):
            for child in node.children:
                child.parent = node

        method_name: str = node.__class__.__name__.split('.')[-1]
        fn: Optional[Callable[[ParseTree], None]] = getattr(self, method_name, None)
        assert fn
        self.before_process_node(node)
        fn(node)
        self.after_process_node(node)

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)
        if self._is_EOF(node):
            return

        # add indent for the first real token
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
    # (xxx, xxx)
    _tuple_tight_inline = _gen_inline_Context(
        tight_fn=lambda i, n:
            PureThriftFormatter._is_token(n, '(')
            or PureThriftFormatter._is_token(n, ')')
            or PureThriftFormatter._is_token(n.parent.children[i-1], '(')
            or isinstance(n, ThriftParser.List_separatorContext)
    )
    Function_Context = _tuple_tight_inline
    OnewayContext = _gen_inline_Context()
    Function_typeContext = _gen_inline_Context()
    Throws_listContext = _tuple_tight_inline
    Type_annotationsContext = _tuple_tight_inline
    Type_annotationContext = _tuple_tight_inline
    Annotation_valueContext = _gen_inline_Context()

    def ServiceContext(self, node: ThriftParser.ServiceContext):
        fn = self.gen_subblocks_Context(3, ThriftParser.Function_Context)
        if self._is_token(node.children[2], 'extends'):
            fn = self.gen_subblocks_Context(5, ThriftParser.Function_Context)
        return fn(self, node)

    def SenumContext(self, _: ThriftParser.SenumContext):
        # deprecated
        pass


class ThriftFormatter(PureThriftFormatter):
    def __init__(self, data: ThriftData):
        super().__init__()

        self._data: ThriftData = data
        self._document: ThriftParser.DocumentContext = data.document

        self._last_token_index: int = -1

        self._field_comment_padding: int = 0
        self._field_align_assign_padding: int = 0
        self._field_align_padding_map: Dict[str, int] = {}

    def format(self) -> str:
        self._patch()
        return self.format_node(self._document)

    def _patch(self):
        if self._option.patch_required:
            self.walk_node(self._document, self._patch_field_req)

        if self._option.patch_sep:
            self.walk_node(self._document, self._patch_field_list_separator)
            self.walk_node(self._document, self._patch_remove_last_list_separator)

    @staticmethod
    def _patch_field_req(node: ParseTree):
        if not isinstance(node, ThriftParser.FieldContext):
            return

        if isinstance(PureThriftFormatter._get_parent(node),
                      (ThriftParser.Function_Context, ThriftParser.Throws_listContext)):
            return

        if not node.children:
            return

        i: int = 0
        for i, child in enumerate(node.children):
            if isinstance(child, ThriftParser.Field_reqContext):
                return
            if isinstance(child, ThriftParser.Field_typeContext):
                break

        fake_token = CommonToken()
        fake_token.type = FAKE_FIELD_REQ_TYPE
        fake_token.text = 'required'
        fake_token.is_fake = True
        fake_node = TerminalNodeImpl(fake_token)
        fake_req = ThriftParser.Field_reqContext(parser=node.parser)
        fake_req.children = [fake_node]
        # patch
        node.children.insert(i, fake_req)

    @staticmethod
    def _patch_field_list_separator(node: ParseTree):
        if not isinstance(node, (ThriftParser.Enum_fieldContext,
                                 ThriftParser.FieldContext,
                                 ThriftParser.Function_Context)):
            return

        tail = node.children[-1]
        if isinstance(tail, ThriftParser.List_separatorContext):
            tail.children[0].symbol.text = FAKE_SEP_TOKEN_TEXT
            return

        fake_token = CommonToken()
        fake_token.text = FAKE_SEP_TOKEN_TEXT
        fake_token.is_fake = True
        fake_node = TerminalNodeImpl(fake_token)
        fake_ctx = ThriftParser.List_separatorContext(parser=node.parser)
        fake_ctx.children = [fake_node]
        node.children.append(fake_ctx)

    @staticmethod
    def _patch_remove_last_list_separator(node: ParseTree):
        is_inline_field = isinstance(node, ThriftParser.FieldContext) and \
            isinstance(PureThriftFormatter._get_parent(node),
                       (ThriftParser.Function_Context, ThriftParser.Throws_listContext))
        is_inline_node = isinstance(node, ThriftParser.Type_annotationContext)

        if is_inline_field or is_inline_node:
            ThriftFormatter._remove_last_list_separator(node)

    @staticmethod
    def _remove_last_list_separator(node: ParseTree):
        parent = PureThriftFormatter._get_parent(node)
        if not parent:
            return

        is_last = False
        brothers = parent.children
        for i, child in enumerate(brothers):
            if child is node and i < len(brothers) - 1:
                if not isinstance(brothers[i + 1], child.__class__):
                    is_last = True
                    break

        if is_last and isinstance(node.children[-1], ThriftParser.List_separatorContext):
            node.children.pop()

    @staticmethod
    def _is_field_or_enum_field(node: ParseTree | None):
        return isinstance(node, (ThriftParser.FieldContext, ThriftParser.Enum_fieldContext))

    @staticmethod
    def _calc_subblocks_comment_padding(subblocks: List[ParseTree]):
        padding: int = 0
        for subblock in subblocks:
            padding = max(padding, len(PureThriftFormatter().format_node(subblock)))

        if padding > 0:
            return padding + 1
        return 0

    # align by assign
    @staticmethod
    def _split_field_by_assign(node: ParseTree):
        '''
          split field to [left, right] by assgin
          field: '1: required i32 number_a = 0,' -->
                left:  '1: required i32 number_a'
                right: '= 0,'
        '''
        assert ThriftFormatter._is_field_or_enum_field(node)
        left: ParseTree = copy.copy(node)
        right: ParseTree = copy.copy(node)

        i: int = 0
        current_is_left: bool = True
        for i, child in enumerate(node.children):
            if PureThriftFormatter._is_token(child, '=') or \
                    isinstance(child, ThriftParser.List_separatorContext):
                current_is_left = False
                break

        if current_is_left:
            i += 1

        left.children = node.children[:i]
        right.children = node.children[i:]
        return left, right

    @staticmethod
    def _calc_field_align_assign_padding(subblocks: List[ParseTree]) -> Tuple[int, int]:
        '''
            field: '1: required i32 number_a = 0,'
            assign_padding:   max(left) + 1
            comment_padding:  max(left) + max(right) [+ 1]
        '''
        if not subblocks or not ThriftFormatter._is_field_or_enum_field(subblocks[0]):
            return (0, 0)

        left_max_size: int = 0
        right_max_size: int = 0
        for subblock in subblocks:
            left, right = ThriftFormatter._split_field_by_assign(subblock)
            left_max_size = max(left_max_size, len(PureThriftFormatter().format_node(left)))
            right_max_size = max(right_max_size, len(PureThriftFormatter().format_node(right)))

        assign_padding: int = left_max_size + 1  # add an extra space for assgin
        comment_padding: int = assign_padding + right_max_size + 1  # add an extra space for next
        # if right part is only a comma, it should tight with the left, so remove an extra space
        #   case 1 --> "1: bool a = true," ---> "1: bool a" + " " + "= true,"
        #   case 2 --> "2: bool b," ---> "2: bool b" + "" + ","
        if right_max_size <= 1:
            comment_padding -= 1
        return assign_padding, comment_padding

    @staticmethod
    def _get_field_child_name(node: ParseTree) -> str:
        if PureThriftFormatter._is_token(node, '='):
            return '='
        return node.__class__.__name__

    @staticmethod
    def _calc_field_align_padding_map(subblocks: List[ParseTree]) -> Tuple[Dict[str, int], int]:
        if not subblocks or not ThriftFormatter._is_field_or_enum_field(subblocks[0]):
            return {}, 0

        sep_class = str(ThriftParser.List_separatorContext.__name__)
        name_levels: Dict[str, int] = {}
        for subblock in subblocks:
            for i in range(len(subblock.children)-1):
                a = ThriftFormatter._get_field_child_name(subblock.children[i])
                b = ThriftFormatter._get_field_child_name(subblock.children[i+1])
                if a not in name_levels:
                    name_levels[a] = 0
                if b not in name_levels:
                    name_levels[b] = 0
                name_levels[b] = max(name_levels[b], name_levels[a] + 1)

        # 检查 levles 连续
        if max(name_levels.values()) + 1 != len(name_levels):
            return {}, 0

        level_length: Dict[int, int] = {}
        for subblock in subblocks:
            for child in subblock.children:
                level = name_levels[ThriftFormatter._get_field_child_name(child)]
                length = len(PureThriftFormatter().format_node(child))
                level_length[level] = max(level_length.get(level, 0), length)

        level_padding: Dict[int, int] = {}
        for level in level_length:
            if level == name_levels.get(sep_class):
                level_padding[level] = level - 1  # separator should tight with left. so remove one
            else:
                level_padding[level] = level

            for i in range(0, level):
                level_padding[level] += level_length[i]

        padding: Dict[str, int] = {}
        for name, level in name_levels.items():
            padding[name] = level_padding[level]

        comment_padding: int = len(level_length)  # add n-1 and an extra space
        for _, length in level_length.items():
            comment_padding += length
        if sep_class in padding:
            comment_padding -= 1

        return padding, comment_padding

    def _get_current_line(self) -> str:
        if self._newline_c > 0:
            return ''
        cur = self._out.getvalue().rsplit('\n', 1)[-1]
        return cur

    def _padding(self, padding: int, pad: str = ' '):
        if padding <= 0:
            return
        cur = self._get_current_line()
        padding = padding - len(cur)
        if padding > 0:
            self._append(pad * padding)

    def _add_indent_padding(self, padding: int):
        if padding > 0:
            return padding + self._option.indent
        return 0

    def _padding_align(self, node: TerminalNodeImpl):
        if not self._is_field_or_enum_field(self._get_parent(node)):
            return

        if self._option.align_field:
            if self._field_align_padding_map:
                child_name: str = self._get_field_child_name(node)
                padding: int = self._field_align_padding_map.get(child_name, 0)
                self._padding(padding, ' ')
        if self._option.align_assign:
            if self._is_token(node, '='):
                self._padding(self._field_align_assign_padding, ' ')

    def before_subblocks(self, subblocks: List[ParseTree]):
        # subblocks : [Function] | [Field] | [Enum_Field]
        if self._option.is_align:
            if self._option.align_field:
                padding_map, comment_padding = self._calc_field_align_padding_map(subblocks)
                self._field_align_padding_map = {key: self._add_indent_padding(value) for key, value in padding_map.items()}
                self._field_comment_padding: int = self._add_indent_padding(comment_padding)

            elif self._option.align_assign:
                # assign align && comment
                assign_padding, comment_padding = self._calc_field_align_assign_padding(subblocks)
                self._field_align_assign_padding: int = self._add_indent_padding(assign_padding)
                self._field_comment_padding: int = self._add_indent_padding(comment_padding)

        # clac for comment
        if self._option.keep_comment and self._field_comment_padding == 0:
            padding: int = self._calc_subblocks_comment_padding(subblocks)
            self._field_comment_padding: int = self._add_indent_padding(padding)

    def after_subblocks(self, _: List[ParseTree]):
        self._field_align_assign_padding: int = 0
        self._field_comment_padding: int = 0
        self._field_align_padding_map: Dict[str, int] = {}

    def after_block_node(self, _: ParseTree):
        self._tail_comment()

    def before_process_node(self, node: ParseTree):
        if self._option.is_align:
            self._padding_align(node)

    def _line_comments(self, node: TerminalNodeImpl):
        if not self._option.keep_comment:
            return

        if hasattr(node.symbol, 'is_fake') and node.symbol.is_fake:
            return

        token_index: int = node.symbol.tokenIndex
        comments: List[CommonToken] = []
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

        self._last_token_index: int = node.symbol.tokenIndex

    def _tail_comment(self):
        if not self._option.keep_comment:
            return

        if self._last_token_index == -1:
            return

        last_token: CommonToken = self._data.tokens[self._last_token_index]
        comments: List[CommonToken] = []
        for token in self._data.tokens[self._last_token_index + 1:]:
            if token.line != last_token.line:
                break
            if token.channel != 2:
                continue
            comments.append(token)

        assert len(comments) <= 1
        if comments:
            if self._field_comment_padding:
                self._padding(self._field_comment_padding, ' ')
            else:
                self._append(' ')  # add space
            self._append(comments[0].text.strip())
            self._push('')
            self._last_token_index: int = comments[0].tokenIndex

    def TerminalNodeImpl(self, node: TerminalNodeImpl):
        assert isinstance(node, TerminalNodeImpl)

        # add tail comment before a new line
        if self._newline_c > 0:
            self._tail_comment()

        # add abrove comments
        self._line_comments(node)

        super().TerminalNodeImpl(node)
