# thrift-fmt

Thrift Formatter

Can be used as command line tool `thrift-fmt` and python sdk `thrift_fmt`

The parser is thrift-parser https://github.com/alingse/thrift-parser

## Usage
### install

```bash
pip install thrift-fmt
```

### format files

Format single file and print to stdout

```bash
thrift-fmt mythrift.thrift
```

Format and overwrite the origin file
```bash
thrift-fmt -w mythrift.thrift
```

Format a directory, this will overwrite the origin file, please keep in track

```bash
thrift-fmt -r ./thrift_files
```

## Use in Code

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
