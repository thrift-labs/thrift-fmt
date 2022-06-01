from importlib.resources import path
import os
import glob

from thrift_fmt.core import ThriftData, PureThriftFormatter, ThriftFormatter

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def run_fmt(file, patch=True):
    fin = os.path.abspath(os.path.join(TEST_DIR, '../fixtures/', file))
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data)
    fmt.option(comment=True, patch=True, indent=4)
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
    assert len(out)  > 0


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
    fin = os.path.abspath(os.path.join(TEST_DIR, '../fixtures/', file))
    data = ThriftData.from_file(fin)

    parts = []
    for node in data.document.children:
        out = PureThriftFormatter().format_node(node)
        parts.append(out)
        print(out)

    assert parts[0] == 'include "shared.thrift"'
    assert parts[1] == 'include "shared2.thrift"'
    assert parts[2] == '''struct Xtruct2 {
    1: required i8 byte_thing,
    2: required Xtruct struct_thing,
    3: required i32 i32_thing,
}'''

