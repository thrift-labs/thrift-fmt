import io
import os

from thrift_fmt.core import ThriftData, ThriftFormatter

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def run_fmt(file, patch=True):
    fin = os.path.abspath(os.path.join(TEST_DIR, '../fixtures/', file))
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data.document)
    if patch:
        fmt.patch()

    out = io.StringIO()
    fmt.format(out)
    return out.getvalue()


def test_simple():
    out = run_fmt('simple.thrift', patch=True)
    print(out)
    assert len(out) == 50
    assert out.count('\n') == 3


def test_complex():
    out = run_fmt('tutorial.thrift', patch=True)
    print(out)
    assert len(out) == 831


def test_thrift_test():
    out = run_fmt('ThriftTest.thrift')
    print(out)
    assert len(out) == 5444


def test_AnnotationTest():
    out = run_fmt('AnnotationTest.thrift')
    print(out)
    assert len(out) == 1223
