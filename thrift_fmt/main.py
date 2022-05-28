import io
import click
import sys

from .core import ThriftData, ThriftFormatter


@click.command()
@click.argument('fin', type=click.Path(exists=True, file_okay=True))
@click.argument('fout', type=click.Path(file_okay=True, writable=True), required=False)
def main(fout=None, fin=None):
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data)
    fmt.patch()

    if fout is None:
        fmt.format(sys.stdout)
    else:
        with io.open(fout, 'w', encoding='utf8') as f:
            fmt.format(f)
