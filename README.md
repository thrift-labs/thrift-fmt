# thrift-fmt
thrift formatter

## Usage

install

```
pip install thrift-fmt
```

```
thrift-fmt xx.thrift
```

parser https://github.com/alingse/thrift-parser

## TODO

[x] 1. 单文件解析
[x] 2. 定义格式 空格/换行/注释
[x] 3. 支持 include?
[x] 4. 封装成 python package
5. struct 依赖排序(生成 python 代码会有依赖问题)
[x] 6. 补充 optional/required
[x] 7. 校正类型
8. 兼容注释

## LICENSE

fixtures 中部分thrift 是来自于 https://github.com/apache/thrift/blob/master/tutorial/
是 Apache 证书的

thrift-parser 中使用的 Thrift.g4 是来自于 https://github.com/antlr/grammars-v4