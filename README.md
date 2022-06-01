# thrift-fmt
thrift formatter

# Usage

### install

```bash
pip install thrift-fmt
```
### run

```bash
thrift-fmt mythrift.thrift

thrift-fmt mythrift.thrift -w

thrift-fmt -d ./thrift_files -w

thrift-fmt -d ./thrift_files -w --no-patch --remove-comment

thrift-fmt --help
```

parser https://github.com/alingse/thrift-parser

## Use in Code

```python
from thrift_fmt import ThriftFormatter, PureThriftFormatter
from thrift_parser import ThriftData

data = ThriftData.from_file('simple.thrift')
# format one thrift file
out = ThriftFormatter(data).format()

# only a single node
PureThriftFormatter().format_node(data.document.children[2])
```

## LICENSE

fixtures 中部分thrift 是来自于 https://github.com/apache/thrift/blob/master/tutorial/
是 Apache 证书的

thrift-parser 中使用的 Thrift.g4 是来自于 https://github.com/antlr/grammars-v4
