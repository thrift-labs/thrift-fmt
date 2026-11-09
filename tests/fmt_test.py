import os
import glob
import shutil

import pytest

from click.testing import CliRunner
from thrift_fmt.main import main

from thrift_parser import ThriftData
from thrift_fmt import PureThriftFormatter, ThriftFormatter, Option

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def run_fmt(file, patch=True):
    fin = os.path.abspath(os.path.join(TEST_DIR, 'fixtures', file))
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data)
    opt = Option(keep_comment=True, patch_required=True, patch_sep=True, indent=4, align_assign=False)
    if not patch:
        opt.disble_patch()
    fmt.option(opt)
    return fmt.format()


def test_simple():
    out = run_fmt('simple.thrift', patch=True)
    print(out)
    assert len(out) > 0
    assert out.count('\n') > 0


def test_complex():
    out = run_fmt('tutorial.thrift', patch=True)
    print(out)
    assert len(out) > 0


def test_thrift_test():
    out = run_fmt('ThriftTest.thrift')
    print(out)
    assert len(out) > 0


def test_AnnotationTest():
    out = run_fmt('AnnotationTest.thrift')
    print(out)
    assert len(out) > 0


def test_all():
    files = glob.glob('./fixtures/*.thrift')
    for file in files:
        file = file.split('/')[-1]
        run_fmt(file)
        run_fmt(file, patch=False)


def test_only_part():
    file = 'simple.thrift'
    fin = os.path.abspath(os.path.join(TEST_DIR, 'fixtures', file))
    data = ThriftData.from_file(fin)

    parts = []
    for node in data.document.children:
        out = PureThriftFormatter().format_node(node)
        parts.append(out)

    assert parts[0] == 'include "shared.thrift"'
    assert parts[1] == 'include "shared2.thrift"'
    assert parts[2] == '''struct Xtruct2 {
    1: required i8 byte_thing,
    2: required Xtruct struct_thing,
    3: required i32 i32_thing,
}'''


def test_all_part():
    file = 'simple.thrift'
    fin = os.path.abspath(os.path.join(TEST_DIR, 'fixtures', file))
    data = ThriftData.from_file(fin)

    # test walk
    all_outs = []

    def run_each(node):
        out = PureThriftFormatter().format_node(node)
        all_outs.append(out)

    PureThriftFormatter.walk_node(data.document, run_each)
    for i, out in enumerate(all_outs):
        print(i, out)

    assert len(all_outs) == 241


def test_from_string():
    data = '''
    include    "shared.thrift"   // a
    // work info
    struct Work {
    1: i32 num1 = 0,
        2: required i32 num2, // num2 for
        3: Operation op, // op is Operation
        4: optional string comment,
        5: map<string,list<string>> tags, //hello
    }
    '''

    # thrift = ThriftData.from_file('simple.thrift')
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=False))
    out = fmt.format()
    print(out)
    assert out == '''
include "shared.thrift" // a

// work info
struct Work {
    1: required i32 num1 = 0,
    2: required i32 num2,                       // num2 for
    3: required Operation op,                   // op is Operation
    4: optional string comment,
    5: required map<string, list<string>> tags, //hello
}'''.strip()

    # or only a single node
    header = PureThriftFormatter().format_node(thrift.document.children[0])
    assert header == 'include "shared.thrift"'


def test_field_assign_align():
    data = '''
struct Work {
1: i32 number_a = 0, // hello
2: required i32 num2 = 1,//xyz
}
'''

    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True))
    out = fmt.format()
    assert out == '''struct Work {
    1: required i32 number_a = 0, // hello
    2: required i32 num2     = 1, //xyz
}'''


def test_field_assign_align_for_enum():
    data = '''
enum Numberz
{
  ONE = 1,
  TWO,
  THREE,
  FIVE = 5,
  SIX,
  EIGHT = 8
}
'''

    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, indent=2))
    out = fmt.format()
    assert out == '''enum Numberz {
  ONE   = 1,
  TWO,
  THREE,
  FIVE  = 5,
  SIX,
  EIGHT = 8,
}'''


def test_field_assign_align_with_complex():
    data = '''enum NUM {
            ONE =1,
            SEVEN = 7,
            ELEVLEN
        }
    '''

    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, indent=4, patch_required=False, patch_sep=False))
    out = fmt.format()
    assert out == '''enum NUM {
    ONE     = 1,
    SEVEN   = 7,
    ELEVLEN
}'''


def test_field_assign_align_with_complex2():
    data = '''enum NUM {
            ONE =1,
            SEVEN = 7,
            ELEVLEN
        }
    '''

    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, indent=4, patch_sep=False))
    out = fmt.format()
    assert out == '''enum NUM {
    ONE     = 1,
    SEVEN   = 7,
    ELEVLEN
}'''


def test_field_align_with_calc():
    data = '''
struct Work {
1: i32 number_a = 0, // hello
2: required i32 num2 = 1,//xyz
}
'''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, align_field=True, indent=4, patch_required=False))
    out = fmt.format()
    print(out)
    assert out == '''
struct Work {
    1:          i32 number_a = 0, // hello
    2: required i32 num2     = 1, //xyz
}
'''.strip()


def test_field_align_with_calc_complex():
    data = '''
struct Work {
1: i32 number_a = 0, // hello
2: required i32 num2 = 1,//xyz
3: list<i32> num3 = [1, 2, 3],// num3
11: string str_b = "hello-world"
}
'''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, align_field=True, indent=4, patch_required=False, patch_sep=True))
    out = fmt.format()
    print(out)
    assert out == '''
struct Work {
    1:           i32       number_a = 0            , // hello
    2:  required i32       num2     = 1            , //xyz
    3:           list<i32> num3     = [ 1, 2, 3 ]  , // num3
    11:          string    str_b    = "hello-world",
}
'''.strip()


def test_field_align_with_calc_complex_with_patch():
    data = '''
struct Work {
1: i32 number_a = 0, // hello
2: required i32 num2 = 1,//xyz
3: list<i32> num3 = [1, 2, 3],// num3
11: string str_b = "hello-world"
}
'''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, align_field=True, indent=4, patch_required=True, patch_sep=True))
    out = fmt.format()
    print(out)
    assert out == '''
struct Work {
    1:  required i32       number_a = 0            , // hello
    2:  required i32       num2     = 1            , //xyz
    3:  required list<i32> num3     = [ 1, 2, 3 ]  , // num3
    11: required string    str_b    = "hello-world",
}
'''.strip()


def test_field_align_with_enum():
    data = '''
enum NUM {
    ONE     = 1,
    SEVEN   = 7,
    ELEVLEN    ,
}'''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(align_assign=True, align_field=True, indent=4, patch_required=True, patch_sep=True))
    out = fmt.format()
    print(out)
    assert out.strip() == '''
enum NUM {
    ONE     = 1,
    SEVEN   = 7,
    ELEVLEN    ,
}
'''.strip()


def test_without_patch_align_assign():
    data = '''
    struct Response {
    } // hello
    senum SENUMS {
    }
    struct Param {
        1: i64 num,
    }
    service Hello {
    void ping(),
    void pong()
    }
    // comment
    '''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(keep_comment=False, align_assign=True).disble_patch())
    out = fmt.format()
    print(out)
    assert out.strip() == '''
struct Response {
}

struct Param {
    1: i64 num,
}

service Hello {
    void ping(),
    void pong()
}
'''.strip()

def test_without_patch_align_field():
    data = '''
    struct Response {
    } // hello
    senum SENUMS {
    }
    struct Param {
        1: i64 num,
    }
    service Hello {
    void ping(),
    void pong()
    }
    // comment
    '''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(keep_comment=False, align_field=True).disble_patch())
    out = fmt.format()
    print(out)
    assert out.strip() == '''
struct Response {
}

struct Param {
    1: i64 num,
}

service Hello {
    void ping(),
    void pong()
}
'''.strip()

def test_with_empty():
    data = ''' '''
    thrift = ThriftData.from_str(data)
    fmt = ThriftFormatter(thrift)
    fmt.option(Option(keep_comment=False).disble_align().disble_patch())
    out = fmt.format()
    print(out)
    assert out.strip() == ''''''.strip()

def test_with_click(tmp_path, monkeypatch):
    shutil.copytree(os.path.join(TEST_DIR, 'fixtures'), tmp_path / 'tests' / 'fixtures')
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    args_list = [
        [
            '-i 4',
            '--remove-comment',
            '--patch-required',
            '--patch-sep',
            '--align-assign',
            '-r',
            './'
        ],
        [
            '-i 4',
            '--no-patch',
            '--no-align',
            './'
        ],
        [
            '-i 4',
            '--no-patch',
            '--no-align',
            '-w',
            './tests/fixtures/simple.thrift',
        ],
        [
            '-i 4',
            '--no-patch',
            '--no-align',
            './tests/fixtures/simple.thrift',
        ],
    ]

    for args in args_list:
        result = runner.invoke(main, args)
        assert result.exit_code == 0


def format_text(source, option=None):
    fmt = ThriftFormatter(ThriftData.from_str(source))
    fmt.option(option if option is not None else Option(separate_base_fields=True))
    return fmt.format()


@pytest.mark.parametrize('field_type,name', [
    ('Base', 'Base'),
    ('base.Base', 'Base'),
    ('common.meta.Base', 'Base'),
    ('BaseResp', 'BaseResp'),
    ('base.BaseResp', 'BaseResp'),
])
@pytest.mark.parametrize('option', [
    Option(separate_base_fields=True),
    Option(align_field=True, indent=2, separate_base_fields=True),
    Option(align_assign=False, separate_base_fields=True),
    Option(keep_comment=False, separate_base_fields=True).disble_align().disble_patch(),
])
def test_base_field_separator(field_type, name, option):
    source = '''struct ArbitraryName {
    1: optional string Name,
    42: optional %s %s,
}''' % (field_type, name)
    out = format_text(source, option)
    lines = out.splitlines()
    assert len(lines) == 5
    assert lines[2] == ''
    assert lines[3].strip().endswith('%s,' % name)
    assert format_text(out, option) == out


@pytest.mark.parametrize('blank_lines', ['', '\n', '\n\n\n'])
def test_base_field_normalizes_blank_lines(blank_lines):
    source = 'struct ExampleReq {\n1: string Name,\n%s255: base.Base Base,\n}' % blank_lines
    assert format_text(source) == '''struct ExampleReq {
    1: required string Name,

    255: required base.Base Base,
}'''


@pytest.mark.parametrize('field', ['base.Base Base', 'base.BaseResp BaseResp'])
@pytest.mark.parametrize('following_field', ['', '\n1: optional string Name,'])
def test_first_or_only_base_field(field, following_field):
    out = format_text('struct Example {\n255: optional %s,%s\n}' % (field, following_field))
    assert '\n\n' not in out
    assert out.splitlines()[1] == '    255: optional %s,' % field


@pytest.mark.parametrize('patch', [True, False])
def test_only_base_field_with_leading_comments(patch):
    option = Option(separate_base_fields=True)
    if not patch:
        option.disble_patch()
    out = format_text('struct Example {\n/* Common metadata */\n\n255: optional base.Base Base,\n}', option)
    assert out == '''struct Example {
    /* Common metadata */
    255: optional base.Base Base,
}'''
    assert format_text(out, option) == out


@pytest.mark.parametrize('field', [
    'string Base',
    'base.Base OtherName',
    'base.Base BaseResp',
    'base.BaseResp Base',
    'base.Base base',
    'list<base.Base> Base',
])
def test_non_metadata_fields_are_not_separated(field):
    out = format_text('struct Example {\n1: string Name,\n255: %s,\n}' % field)
    assert '\n\n' not in out


@pytest.mark.parametrize('kind', ['union', 'exception'])
def test_base_separator_only_applies_to_structs(kind):
    out = format_text('%s Example {\n1: string Name,\n255: base.Base Base,\n}' % kind)
    assert '\n\n' not in out


@pytest.mark.parametrize('comment', [
    '// Common metadata',
    '// Common metadata\n// Request context',
    '/* Common metadata */',
    '/* Common\nmetadata */',
    '/* Common metadata */\n/* Request context */',
])
@pytest.mark.parametrize('patch_sep', [True, False])
@pytest.mark.parametrize('gap', ['', '\n\n'])
def test_base_separator_precedes_leading_comments(comment, patch_sep, gap):
    source = '''struct ExampleReq {
1: optional string Name, // Business field
%s%s
255: optional base.Base Base // Metadata field
}''' % (comment, gap)
    option = Option(align_assign=False, patch_sep=patch_sep, separate_base_fields=True)
    out = format_text(source, option)
    expected_comments = '\n'.join('    ' + line if i == 0 or line.startswith(('//', '/*')) else line
                                  for i, line in enumerate(comment.splitlines()))
    assert out == '''struct ExampleReq {
    1: optional string Name,%s// Business field

%s
    255: optional base.Base Base%s // Metadata field
}''' % ('      ' if patch_sep else '     ', expected_comments, ',' if patch_sep else '')
    assert format_text(out, option) == out


@pytest.mark.parametrize('comment', ['// Common metadata', '/* Common metadata */'])
def test_only_base_field_with_leading_comment(comment):
    out = format_text('struct Example {\n%s\n\n255: base.Base Base\n}' % comment)
    assert out == '''struct Example {
    %s
    255: required base.Base Base,
}''' % comment
    assert format_text(out) == out


def test_base_separator_with_comments_removed():
    source = '''struct ExampleReq {
1: optional string Name, // Business field
// Common metadata
255: optional base.Base Base,
}'''
    out = format_text(source, Option(keep_comment=False, separate_base_fields=True))
    assert out == '''struct ExampleReq {
    1: optional string Name,

    255: optional base.Base Base,
}'''


def test_base_separator_for_single_struct_formatting():
    thrift = ThriftData.from_str('struct ExampleResp {1: bool OK, 255: base.BaseResp BaseResp}')
    node = thrift.document.children[0].children[0]
    fmt = PureThriftFormatter()
    fmt.option(Option(separate_base_fields=True))
    assert fmt.format_node(node) == '''struct ExampleResp {
    1: bool OK,

    255: base.BaseResp BaseResp
}'''


def test_base_separator_does_not_apply_to_service_parameters():
    out = format_text('service Example {void call(1: string Name, 2: base.Base Base)}')
    assert out == '''service Example {
    void call(1: string Name, 2: base.Base Base),
}'''


def test_base_separator_cli(tmp_path):
    thrift_file = tmp_path / 'example.thrift'
    thrift_file.write_text('struct ExampleReq {1: string Name, 255: base.Base Base}')
    result = CliRunner().invoke(main, ['--separate-base-fields', '-w', str(thrift_file)])
    assert result.exit_code == 0, result.output
    out = thrift_file.read_text()
    assert out.strip() == '''struct ExampleReq {
    1: required string Name,

    255: required base.Base Base,
}'''
    result = CliRunner().invoke(main, ['--separate-base-fields', '-w', str(thrift_file)])
    assert result.exit_code == 0, result.output
    assert thrift_file.read_text() == out


@pytest.mark.parametrize('field', ['base.Base Base', 'base.BaseResp BaseResp'])
@pytest.mark.parametrize('option', [None, Option(separate_base_fields=False)])
def test_base_separator_disabled(field, option):
    fmt = ThriftFormatter(ThriftData.from_str('struct Example {1: string Name, 255: %s}' % field))
    if option is not None:
        fmt.option(option)
    assert fmt.format() == '''struct Example {
    1: required string Name,
    255: required %s,
}''' % field


def test_base_separator_disabled_preserves_comment_formatting():
    source = 'struct Example {\n/* Common metadata */\n\n255: base.Base Base\n}'
    out = format_text(source, Option(separate_base_fields=False))
    assert out == '''struct Example {

    /* Common metadata */

    255: required base.Base Base,
}'''


def test_base_separator_cli_default_is_disabled(tmp_path):
    thrift_file = tmp_path / 'example.thrift'
    thrift_file.write_text('struct ExampleReq {1: string Name, 255: base.Base Base}')
    result = CliRunner().invoke(main, [str(thrift_file)])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == '''struct ExampleReq {
    1: required string Name,
    255: required base.Base Base,
}'''
