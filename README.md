# thrift-fmt
thrift formatter

the parser is https://github.com/alingse/thrift-parser

## Usage

```bash
thrift-fmt mythrift.thrift
```

```bash
thrift-fmt --help
```

### install

```bash
pip install thrift-fmt
```
### format files

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
thrift-fmt -d ./thrift_files
```

## Use in Code

use `ThriftData` parse from file / stdin / str

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

1. suppoort keep and align the comment
2. auto patch list separator and field's `required` flag
3. align the field's assign
4. support format part of the thrift parsed result

example
```
struct Work {
    1: required i32 number_a = 0, // hello
    2: optional i32 num2     = 1, // xyz
}
```

### TODO

1. support function blank line count
2. fix //a comment
3. better code
4. other language ?
5. support function default add new line, function remove list sep
6. support indent for /* */ multi line comment
7. support tight map/list define ?
8. any other featur ?

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
