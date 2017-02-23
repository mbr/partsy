import csv


class PartsyError(Exception):
    pass


class MissingOrderNo(PartsyError):
    pass


class FarnellWriter(object):
    def __init__(self, outstream):
        self.writer = csv.writer(outstream)
        self.writer.writerow(('Part Number', 'Quantity'))

    def output_article(self, item, article):
        if 'farnell' not in article.vendors:
            raise MissingOrderNo('Article {} has no Farnell Order#'.format(
                item))

        self.writer.writerow((article.vendors['farnell'], item.props['qty']))
