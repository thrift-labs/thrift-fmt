import io
import pathlib
from typing import Optional, List

import click

from .core import ThriftData, ThriftFormatter, Option


@click.command()
@click.option(
    '-i', '--indent', show_default=True, type=click.IntRange(min=0), default=Option.DEFAULT_INDENT,
    help='sub field indent of struct/enum/service/union/exception')
@click.option(
    '--remove-comment', is_flag=True, default=False, help='remove all comment')
@click.option(
    '--patch-required', is_flag=True, show_default=True, default=True, help='patch field\'s missed required flag')
@click.option(
    '--patch-sep', is_flag=True, show_default=True, default=True, help='patch the separator in struct/enum/service/union/exception (default use comma)')
@click.option(
    '--align-field', is_flag=True, show_default=True, default=False, help='align by field\'s each part (in struct/enum/union/exception)')
@click.option(
    '--align-assign', is_flag=True, show_default=True, default=True, help='align by field\'s assign `=` (in struct/enum/union/exception)')
@click.option(
    '--no-patch', is_flag=True, default=False, help='disable all --patch-xx flag')
@click.option(
    '--no-align', is_flag=True, default=False, help='disable all --align-xx flag')
@click.option(
    '-r', '--recursive', is_flag=True, default=False, help='If `path` is dir, will recursive format all thrift files')
@click.option(
    '-w', '--write', is_flag=True,
    help='If `path` is file, will write to file instead of stdout. default true when `path` is a dir')
@click.argument(
    'path',
    type=click.Path(exists=True, file_okay=True, dir_okay=True), required=True)
def main(indent: Optional[int], remove_comment: Optional[bool],
         patch_required: Optional[bool], patch_sep: Optional[bool],
         align_field: Optional[bool], align_assign: Optional[bool],
         no_patch: Optional[bool], no_align: Optional[bool],
         recursive: Optional[bool], write: Optional[bool],
         path: str):

    files: List[str] = []

    p = pathlib.Path(path)
    if p.is_file():
        files = [p]
    elif p.is_dir():
        if recursive:
            files = p.glob('**/*.thrift')
        else:
            files = p.glob('*.thrift')
        write = True
    else:
        raise click.ClickException('path must be file or dir')

    option = Option(
        patch_sep=patch_sep,
        patch_required=patch_required,
        keep_comment=not remove_comment,
        indent=indent,
        align_assign=align_assign,
        align_field=align_field)

    if no_patch:
        option.disble_patch()
    if no_align:
        option.disble_align()

    for file in files:
        data = ThriftData.from_file(file)
        fmt = ThriftFormatter(data)
        fmt.option(option)
        output = fmt.format()

        if write:
            with io.open(file, 'w', encoding='utf8') as f:
                f.write(output)
        else:
            print(output)
