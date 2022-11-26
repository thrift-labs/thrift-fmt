import click
import io
import pathlib
from typing import Optional

from .core import ThriftData, ThriftFormatter, Option


@click.command()
@click.option(
    '-d', '--dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    '-w', '--write', is_flag=True,
    help='Write to file instead of stdout, default true when dir was set')
@click.option(
    '-i', '--indent', type=click.IntRange(min=0), default=None,
    help='sub field indent of struct/enum/service/union/exception, default {}'.format(Option.DEFAULT_INDENT))
@click.option(
    '--no-patch', is_flag=True, help='disable field patch about comma and required flag')
@click.option(
    '--remove-comment', is_flag=True, help='remove all comment')
@click.option(
    '--no-assign-align', is_flag=True, help='disable field assign align')
@click.argument(
    'file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False), required=False)
def main(dir, write: Optional[bool], indent: Optional[int], no_patch: Optional[bool], remove_comment: Optional[bool], no_assign_align: Optional[bool], file):
    if not dir and not file:
        raise click.ClickException('thrift file or dir is required')

    if file:
        files = [file]
    else:
        files = pathlib.Path(dir).glob('*.thrift')
        write = True

    option = Option(
        patch=not no_patch,
        comment=not remove_comment,
        indent=indent,
        assign_align=not no_assign_align)

    for file in files:
        data = ThriftData.from_file(file)
        fmt = ThriftFormatter(data)
        fmt.option(option)
        output = fmt.format()

        if write:
            with io.open(file, 'w') as f:
                f.write(output)
        else:
            print(output)
