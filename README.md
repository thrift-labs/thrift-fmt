# thrift-fmt
thrift formatter

the parser is https://github.com/alingse/thrift-parser

## Usage

### install

```bash
pip install thrift-fmt
```
### format files

single file

```bash
thrift-fmt mythrift.thrift
```

```bash
thrift-fmt mythrift.thrift -w
```

or directory (this will overwrite the origin file, please keep in track)

```bash
thrift-fmt -d ./thrift_files
```

or more options see help

```bash
thrift-fmt --help
```

## Use in Code

use `ThriftData` parse from file / stdin / str

use `ThriftFormatter` or `PureThriftFormatter` format the data

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

1. suppoort keep the comment
2. patch the required field
3. align the fields comment
4. format only single field

### TODO

1. support function blank line count
2. fix //a comment
3. support Enum field
4. better code
5. other language ?

# LICENSE

some thrift files in fixtures thrift was copy from https://github.com/apache/thrift/blob/master/tutorial/ , The Apache LICENSE

the Thrift.g4 in thrift-parser package was copy from https://github.com/antlr/grammars-v4
