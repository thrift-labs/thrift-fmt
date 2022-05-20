import io
import click
import sys

from .core import ThriftData, ThriftFormatter


@click.command()
@click.argument('fin', type=click.Path(exists=True, file_okay=True))
@click.argument('fout', type=click.Path(file_okay=True, writable=True))
def main(fout, fin):
    data = ThriftData.from_file(fin)
    fmt = ThriftFormatter(data.document)
    fmt.format(sys.stdout)
    #with io.open(fout, 'w', encoding='utf8') as f:
        #fmt.format(f)
