#!/usr/bin/python3

import csv
import re
import sys

import click
import yaml


class DbError(Exception):
    def __init__(self, line_no, msg):
        exc_msg = 'db line {}: {}'.format(line_no, msg)
        super(DbError, self).__init__(exc_msg)
        self.line_no = line_no


class Article(object):
    @property
    def footprint_re(self):
        if not self.footprint:
            return None

        regex = getattr(self, 'footprint_re', None)

        if not regex:
            regex = re.compile(self.footprint)
            self.footprint_re = regex

        return regex

    def __init__(self, name):
        self.name = name

    def match(self, item):
        regexps = []

        if self.footprint_re:
            regexps.append()
            self.footprint_re

        return False


class Db(object):
    # @classmethod
    # def load(cls, src):
    #     articles = []

    #     for idx, line in enumerate(iter(src)):
    #         if not line.strip():
    #             continue

    #         if line.lstrip().startswith('#'):
    #             continue

    #         if not line.endswith('\n'):
    #             raise DbError(idx, 'missing newline at EOF')

    #         if len(line) < 3:
    #             raise DbError(idx, 'line too short')

    #         cmd, space, rem = line[0], line[1], line[2:]

    #         if space != ' ':
    #             raise DbError(idx, 'expected single command follow by space')

    #         if cmd != 'A' and not articles:
    #             raise DbError(idx, 'first command must be article command')

    #         if cmd == 'A':
    #             articles.append(Article(rem))
    #         elif cmd == 'F':
    #             articles[-1].footprint = rem
    #         elif cmd == 'S':
    #             articles[-1].symbol = rem
    #         else:
    #             raise DbError(idx, 'unknown command: {}'.format(cmd))

    #         obj = cls()

    #         obj.articles = articles

    #         return obj

    def __init__(self, articles):
        self.articles = articles

    @classmethod
    def load(cls, src):
        articles = yaml.load(src)
        db = cls(articles)
        return db

    def match(self, item):
        for article in self.articles:
            if article.match(item):
                return article


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


@click.group(help='PartY: Lookup order numbers for parts')
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
              default='party.yaml',
              help='Parts database file')
def test(input, input_format, db_file):
    # read database
    with open(db_file) as db_inp:
        db = Db.load(db_inp)

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
