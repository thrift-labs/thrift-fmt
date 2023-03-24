# thrift-fmt

Thrift Formatter

![Github Actions](https://github.com/thrift-labs/thrift-fmt/workflows/Python%20package/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/thrift-fmt?logo=python&logoColor=%23cccccc)](https://pypi.org/project/thrift-fmt)
[![codecov](https://codecov.io/gh/thrift-labs/thrift-fmt/branch/master/graph/badge.svg?token=0R6PGQ57WQ)](https://codecov.io/gh/thrift-labs/thrift-fmt)
[![Downloads](https://pepy.tech/badge/thrift-fmt/week)](https://pepy.tech/project/thrift-fmt)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

can be used as command line tool `thrift-fmt` and python sdk `thrift_fmt`

use thrift-parser https://github.com/thrift-labs/thrift-parser as parser

## Usage
### Install

```bash
pip install thrift-fmt
```

### Format files

format single file and print to stdout

```bash
thrift-fmt mythrift.thrift
```

format and overwrite the origin file
```bash
thrift-fmt -w mythrift.thrift
```

format a directory, this will overwrite the origin file, please keep in track

```bash
thrift-fmt -r ./thrift_files
```

## Feature

1. keep and align all comments
2. patch list separator
3. patch missed field's `required` flag
4. align by the field's assign (like go)
5. align by each field's part
6. Format only part of the parsed thrift

example
```thrift
struct Work {
    1: required i32 number_a = 0, // hello
    2: optional i32 num2     = 1, // xyz
}
```

align by each field's part
```thrift
struct Work {
    1:  required i32       number_a = 0            , // hello
    2:  required i32       num2     = 1            , // xyz
    3:  required list<i32> num3     = [ 1, 2, 3 ]  , // num3
    11: required string    str_b    = "hello-world",
}
```

## Use as sdk

use `thrift_parser.ThriftData` to parse from file or str

use `ThriftFormatter` or `PureThriftFormatter` format the parsed thrift data.

```python
from thrift_fmt import ThriftFormatter, PureThriftFormatter
from thrift_parser import ThriftData

origin = '''
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

thrift = ThriftData.from_str(data)
out = ThriftFormatter(thrift).format()
assert out == '''
include "shared.thrift" // a

// work info
struct Work {
    1: required i32 num1 = 0,
    2: required i32 num2,                       // num2 for
    3: required Operation op,                   // op is Operation
    4: optional string comment,
    5: required map<string, list<string>> tags, //hello
}
'''.strip()

# or only a single node
header = PureThriftFormatter().format_node(thrift.document.children[0])
assert header == 'include "shared.thrift"'
```


### TODO

1. better code
2. support function default add new line
3. support indent for /* */ multi line comment
4. support tight map/list define ?
5. any other feature ?

## Dev

```bash
pdm install

pdm run pytest

pdm build

pdm run thrift-fmt --help
```
# LICENSE

some thrift files in fixtures thrift was copy from https://github.com/apache/thrift/blob/master/tutorial/ , The Apache LICENSE

the Thrift.g4 in thrift-parser package was copy from https://github.com/antlr/grammars-v4
