#!/usr/bin/python3

import sys

import click

from .database import Database
from .readers import READERS
from .vendors import VENDORS
from .writers import FarnellWriter


def exit_err(msg):
    click.echo(msg, err=True)
    sys.exit(1)


@click.group(help='partsy: Lookup order numbers for parts')
def cli():
    pass


@cli.command('lookup',
             help='Look-up parts in database, outputting order numbers')
@click.option('--input',
              '-i',
              type=click.File(),
              default=sys.stdin,
              help='Input file (default: stdin)')
@click.option('--input-format',
              '-I',
              type=click.Choice(['auto'] + list(sorted(READERS.keys()))),
              default='auto',
              help='Input format.')
@click.option('--output',
              '-o',
              type=click.File(mode='w'),
              default=sys.stdout,
              help='Output file (default: stdout)')
@click.option('--output-format',
              '-O',
              type=click.Choice(['auto', 'farnell']),
              default='farnell',
              help='Output format.')
@click.option('--db',
              '-D',
              'db_file',
              type=click.Path(readable=True),
              default='partsy.yaml',
              help='Parts database file')
@click.option('--qty', '-q', type=int, default=1, help='Quantity')
def lookup(input, input_format, output, output_format, db_file, qty):
    # read database
    with open(db_file) as db_inp:
        db = Database.load(db_inp)

    buffered = input.read()

    if input_format == 'auto':
        for cand in READERS.values():
            reader = cand.try_handle(buffered)
            if reader:
                break

        if not reader:
            exit_err('Cannot determine input format')
    else:
        reader = READERS[input_format].try_handle(buffered)
        if not reader:
            exit_err('Input data not valid for input format {}'.format(
                input_format))

    # determine output format
    if output_format == 'auto':
        output_format = 'farnell'

    # collected all items, now look them up in the database
    unmatched = False
    paired = []
    for item in reader.iter_items():
        article = db.match(item)

        if not article:
            click.echo('Not matched: {}'.format(item), err=True)
            unmatched = True

        if unmatched or article.ignore:
            continue

        # multiply quantities
        item.props['qty'] *= qty

        paired.append((item, article))

    if unmatched:
        exit_err('Has unmatched items')

    # now output
    if output_format == 'farnell':
        writer = FarnellWriter(output)
    else:
        exit_err('Cannot determine output format')

    # print each article
    for item, article in paired:
        writer.output_article(item, article)


@cli.command('vendor')
@click.argument('vendor')
@click.argument('order_no')
def lookup_vendor_item(vendor, order_no):
    click.echo(VENDORS[vendor].retrieve_item(order_no))


if __name__ == '__main__':
    cli()
