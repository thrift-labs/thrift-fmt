import io
import os
import sys

from thrift_fmt.core import ThriftData, ThriftFormatter

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_load_data():
    fin = os.path.abspath(os.path.join(TEST_DIR, '../fixtures/simple.thrift'))
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data.document)
    out = io.StringIO()
    fmt.format(out)
    print(out.getvalue())
    assert len(out.getvalue()) == 70
