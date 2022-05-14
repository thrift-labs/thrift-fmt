import click


@click.command()
def main():
    click.echo('thrift-fmt format thrift files in one style')
