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
    def __init__(self, raw):
        self.name = raw.get('name')
        self.manufacturer = raw.get('manufacturer')
        self.mpart_no = raw.get('mpart_no')
        self.ignore = raw.get('ignore', None)
        self.rules = [Rule.from_raw(m) for m in raw['matches']]
        self.vendors = raw.get('vendor', {})

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


class Database(object):
    def __init__(self, articles):
        self.articles = articles

    @classmethod
    def load(cls, src):
        articles = yaml.safe_load(src)

        # validate
        validated = validate_with_humanized_errors(articles, ARTICLES)

        # instantiate
        rules = [Article(a) for a in validated]
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
