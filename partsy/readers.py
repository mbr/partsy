class Item(object):
    def __init__(self, **kwargs):
        self.props = kwargs

    def __repr__(self):
        return 'Item({})'.format(', '.join('{}={!r}'.format(*i)
                                           for i in self.props.items()))


class KiCadReader(object):
    def handle_row(self, row):
        i = Item(designator=row[1],
                 footprint=row[2],
                 qty=int(row[3]),
                 symbol=row[4], )

        return i
