# thrift-fmt
thrift formatter

## NOTE

等不及有空实现 https://github.com/alingse/thrift-parser 了,

打算先用 ptsd https://github.com/wickman/ptsd 来做一版

实在是看到公司一些文件乱七八糟的

## TODO

1. 单文件解析
2. 定义格式 空格/换行/注释
3. 支持 include?
4. 封装成 python package
5. struct 依赖排序(生成 python 代码会有依赖问题)
6. 补充 optional/required
7. 校正类型
8. 兼容注释
```bash
python simple.py tutorial/tutorial.thrift
```

### ptsd 不足

1. comment 丢失
2. default 值丢失
3. optional required 丢失
4. extends 后面的是一个 <object>
5. 非逗号 + 2 space tab 风格

## LICENSE

tutorial 目录从 https://github.com/apache/thrift/blob/master/tutorial/ 中 copy 过来

是 Apache 证书的
