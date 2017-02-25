from collections import OrderedDict
import re

from voluptuous import Schema, Required
from voluptuous.humanize import validate_with_humanized_errors
import yaml

RULE = Schema({'footprint': str, 'symbol': str})

ARTICLE = Schema({Required('name'): str,
                  'manufacturer': str,
                  'mpart_no': str,
                  'ignore': bool,
                  'matches': [RULE],
                  'vendor': {str: str}})

ARTICLES = Schema([ARTICLE])


def ordered_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(OrderedDict, ordered_dict_representer)


class Rule(object):
    def __init__(self, conditions, condition_strings):
        self.conditions = conditions
        self.condition_strings = condition_strings

    def match(self, item):
        for field, exp in self.conditions.items():
            val = item.props.get(field)

            if val is None:
                return False

            if not exp.match(val):
                return False

        return True

    @classmethod
    def from_raw(cls, condition_strings):
        return cls(
            {field: re.compile(regex + '$')
             for field, regex in condition_strings.items()}, condition_strings)

    def to_dict(self):
        return self.condition_strings


class Article(object):
    @classmethod
    def from_db(cls, raw):
        a = cls()

        a.name = raw.get('name')
        a.manufacturer = raw.get('manufacturer')
        a.mpart_no = raw.get('mpart_no')
        a.ignore = raw.get('ignore', None)
        a.rules = [Rule.from_raw(m) for m in raw['matches']]
        a.vendors = raw.get('vendor', {})

        return a

    @classmethod
    def from_vendor_item(cls, vitem, symbol, footprint):
        a = cls()

        a.name = vitem.name
        a.manufacturer = None
        a.mpart_no = None
        a.ignore = None
        a.rules = [Rule.from_raw({'symbol': symbol, 'footprint': footprint, })]
        a.vendors = {vitem.vendor: vitem.order_no}

        return a

    def match(self, item):
        # in any rule matches, the article can fill the required item
        for rule in self.rules:
            if rule.match(item):
                return True

        return False

    def to_dict(self):
        od = OrderedDict()

        for k in ['name', 'manufacturer', 'mpart_no', 'ignore']:
            v = getattr(self, k, None)
            if v is not None:
                od[k] = v

        if self.rules:
            od['matches'] = [r.to_dict() for r in self.rules]

        if self.vendors:
            od['vendor'] = self.vendors

        return od

    def __str__(self):
        s = '<'

        if self.manufacturer:
            s += '{}, '.format(self.manufacturer)
        if self.mpart_no:
            s += '{}, '.format(self.mpart_no)

        s += '{}>'.format(self.name)

        return s


class Database(object):
    def __init__(self, articles):
        self.articles = articles

    def add_article(self, article):
        self.articles.append(article)

    @classmethod
    def load(cls, src):
        articles = yaml.safe_load(src)

        # validate
        validated = validate_with_humanized_errors(articles, ARTICLES)

        # instantiate
        rules = [Article.from_db(a) for a in validated]
        return cls(rules)

    def dump(self):
        buf = yaml.dump(
            [art.to_dict() for art in self.articles],
            default_flow_style=False,
            width=1024)

        # silly hack for more readable db
        return buf.replace('\n- ', '\n\n- ')

    def match(self, item):
        for article in self.articles:
            if article.match(item):
                return article
