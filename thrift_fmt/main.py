import click

from .core import ThriftData


@click.command()
@click.argument('fin', type=click.Path(exists=True, file_okay=True))
@click.argument('fout', type=click.Path(file_okay=True, writable=True))
def main(fout, fin):
    data = ThriftData.from_file(fin)
    fmt_data = data.format()
    fmt_data.dump(fout)
