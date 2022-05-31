import os
import glob

from thrift_fmt.core import ThriftData, ThriftFormatter

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def run_fmt(file, patch=True):
    fin = os.path.abspath(os.path.join(TEST_DIR, '../fixtures/', file))
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data)
    if patch:
        fmt.patch()
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
