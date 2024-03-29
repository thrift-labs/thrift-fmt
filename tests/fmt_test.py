import os
import glob

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

def test_with_click():
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
