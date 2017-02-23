#!/usr/bin/python3

import csv
import sys

import click

from .database import Database


class PartyError(Exception):
    pass


class MissingOrderNo(PartyError):
    pass


class KiCadReader(object):
    def handle_row(self, row):
        i = Item(designator=row[1],
                 footprint=row[2],
                 qty=int(row[3]),
                 symbol=row[4], )

        return i


class FarnellWriter(object):
    def __init__(self, outstream):
        self.writer = csv.writer(outstream)
        self.writer.writerow(('Part Number', 'Quantity'))

    def output_article(self, item, article):
        if 'farnell' not in article.vendors:
            raise MissingOrderNo('Article {} has no Farnell Order#'.format(
                item))

        self.writer.writerow((article.vendors['farnell'], item.props['qty']))


class Item(object):
    def __init__(self, **kwargs):
        self.props = kwargs

    def __repr__(self):
        return 'Item({})'.format(', '.join('{}={!r}'.format(*i)
                                           for i in self.props.items()))


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
              type=click.Choice(['auto', 'kicad']),
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
def test(input, input_format, output, output_format, db_file, qty):
    # read database
    with open(db_file) as db_inp:
        db = Database.load(db_inp)

    inp = csv.reader(input)

    rows = iter(inp)
    header = next(rows)

    # determine input format
    if input_format == 'auto':
        if header[:6] == ['Id', 'Designator', 'Package', 'Quantity',
                          'Designation', 'Supplier and ref']:
            input_format = 'kicad'
        else:
            exit_err('Cannot determine input format')

    if input_format == 'kicad':
        reader = KiCadReader()

    # determine output format
    if output_format == 'auto':
        output_format = 'farnell'

    items = []
    for row in rows:
        items.append(reader.handle_row(row))

    # collected all items, now look them up in the database
    unmatched = False
    paired = []
    for item in items:
        article = db.match(item)

        if not article:
            click.echo('Not matched: {}'.format(item), err=True)
            unmatched = True

        if article.ignore:
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


if __name__ == '__main__':
    cli()
