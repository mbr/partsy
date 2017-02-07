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


class Rule(object):
    def __init__(self, conditions):
        self.conditions = conditions

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
        return cls({field: re.compile(regex + '$')
                    for field, regex in condition_strings.items()})


class Article(object):
    def __init__(self, raw):
        self.name = raw['name']
        self.ignore = raw.get('ignore', False)
        self.rules = [Rule.from_raw(m) for m in raw['matches']]
        self.vendors = raw.get('vendor', {})

    def match(self, item):
        # in any rule matches, the article can fill the required item
        for rule in self.rules:
            if rule.match(item):
                return True

        return False


class Database(object):
    def __init__(self, articles):
        self.articles = articles

    @classmethod
    def load(cls, src):
        articles = yaml.load(src)

        # validate
        validated = validate_with_humanized_errors(articles, ARTICLES)

        # instantiate
        rules = [Article(a) for a in validated]
        return cls(rules)

    def match(self, item):
        for article in self.articles:
            if article.match(item):
                return article
