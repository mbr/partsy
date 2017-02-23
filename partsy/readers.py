import csv


class Reader(object):
    @classmethod
    def try_handle(cls, buf):
        raise NotImplementedError()


class Item(object):
    def __init__(self, **kwargs):
        self.props = kwargs

    def __repr__(self):
        return 'Item({})'.format(', '.join('{}={!r}'.format(*i)
                                           for i in self.props.items()))


class KiCadReader(Reader):
    def __init__(self, row_iter):
        self.row_iter = row_iter

    @classmethod
    def try_handle(cls, buf):
        try:
            inp = csv.reader(buf.splitlines())
            rows = iter(inp)
            header = next(rows)

            if header[:6] == ['Id', 'Designator', 'Package', 'Quantity',
                              'Designation', 'Supplier and ref']:
                return cls(rows)
        except Exception:
            return None

    def iter_items(self):
        for row in self.row_iter:
            yield Item(designator=row[1],
                       footprint=row[2],
                       qty=int(row[3]),
                       symbol=row[4], )


READERS = {'kicad': KiCadReader, }
