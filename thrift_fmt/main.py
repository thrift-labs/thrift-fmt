import click
import io
import pathlib
import sys

from .core import ThriftData, ThriftFormatter


@click.command()
@click.option('-d', '--dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True),)
@click.option('-w', '--write', is_flag=True,
    help='Write to file instead of stdout, default true when dir was set')
@click.argument('file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False), required=False)
def main(write, dir, file):
    if not dir and not file:
        click.Abort()
    if file:
        data = ThriftData.from_file(file)
        fmt = ThriftFormatter(data)
        fmt.patch()
        if write:
            with io.open(file, 'w') as f:
                fmt.format(f)
        else:
            fmt.format(sys.stdout)
    else:
        for file in pathlib.Path(dir).glob('*.thrift'):
            data = ThriftData.from_file(file)
            fmt = ThriftFormatter(data)
            fmt.patch()
            with io.open(file, 'w') as f:
                fmt.format(f)
