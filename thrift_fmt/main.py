import click
import glob
import pathlib
import sys

from .core import ThriftData, ThriftFormatter


@click.command()
@click.argument('input', type=click.Path(exists=True, file_okay=True, dir_okay=True))
def main(input=None):
    fin = pathlib.Path(input)
    if fin.is_file():
        data = ThriftData.from_file(fin)
        fmt = ThriftFormatter(data)
        fmt.patch()
        fmt.format(sys.stdout)
    else:
        for file in fin.glob('*.thrift'):
            data = ThriftData.from_file(file)
            fmt = ThriftFormatter(data)
            fmt.patch()
            fmt.format(sys.stdout)
