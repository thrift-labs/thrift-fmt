# thrift-fmt
thrift formatter

the parser is https://github.com/alingse/thrift-parser

# Usage

### install

```bash
pip install thrift-fmt
```
### run

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

```python
from thrift_fmt import ThriftFormatter, PureThriftFormatter
from thrift_parser import ThriftData

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

## LICENSE

fixtures 中部分thrift 是来自于 https://github.com/apache/thrift/blob/master/tutorial/
是 Apache 证书的

thrift-parser 中使用的 Thrift.g4 是来自于 https://github.com/antlr/grammars-v4
