#!/usr/bin/python3

import csv
import sys

import click

from .database import Database


class KiCadHandler(object):
    def handle_row(self, row):
        i = Item(designator=row[1],
                 footprint=row[2],
                 qty=row[3],
                 symbol=row[4], )

        return i


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
@click.option('--db',
              '-D',
              'db_file',
              type=click.Path(readable=True),
              default='partsy.yaml',
              help='Parts database file')
def test(input, input_format, db_file):
    # read database
    with open(db_file) as db_inp:
        db = Database.load(db_inp)

    print(db)

    inp = csv.reader(input)

    rows = iter(inp)
    header = next(rows)

    if input_format == 'auto':
        if header[:6] == ['Id', 'Designator', 'Package', 'Quantity',
                          'Designation', 'Supplier and ref']:
            input_format = 'kicad'
        else:
            exit_err('Cannot determine input format')

    if input_format == 'kicad':
        handler_in = KiCadHandler()

    items = []
    for row in rows:
        items.append(handler_in.handle_row(row))

    # collected all items, now look them up in the database
    for item in items:
        article = db.match(item)

        if not article:
            click.echo('Not matched: {}'.format(item))


if __name__ == '__main__':
    cli()
