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
@click.option('--no-patch', is_flag=True,
    help='not patch thrift file')
@click.argument('file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False), required=False)
def main(dir, write, no_patch, file):
    if not dir and not file:
        click.Abort()

    if file:
        files = [file]
    else:
        files = pathlib.Path(dir).glob('*.thrift')
        write = True

    patch = not no_patch
    for file in files:
        data = ThriftData.from_file(file)
        fmt = ThriftFormatter(data)
        if patch:
            fmt.patch()
        out = io.StringIO()
        fmt.format(out)

        if write:
            with io.open(file, 'w') as f:
                f.write(out.getvalue())
        else:
            print(out.getvalue())
