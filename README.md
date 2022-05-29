# thrift-fmt
thrift formatter

## Usage

### install

```bash
pip install thrift-fmt
```

### run

```bash
thrift-fmt xx.thrift

thrift-fmt xx.thrift xx.out.thrift
```

parser https://github.com/alingse/thrift-parser

## TODO

1. 支持控制 patch 与否
2. 支持 -w 回写
3. 支持目录

## LICENSE

fixtures 中部分thrift 是来自于 https://github.com/apache/thrift/blob/master/tutorial/
是 Apache 证书的

thrift-parser 中使用的 Thrift.g4 是来自于 https://github.com/antlr/grammars-v4
