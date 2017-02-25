import html
import re

import requests


class VendorItem(object):
    def __init__(self, vendor, order_no, name, price=None):
        self.vendor = vendor
        self.order_no = order_no
        self.name = name
        self.price = price

    def __str__(self):
        return '<{}:{} {!r}>'.format(self.vendor, self.order_no, self.name)


class ReicheltVendor(object):
    NAME = 'reichelt'

    @classmethod
    def retrieve_item(cls, order_no):
        # reichelt markup is a grade-A mess. just shoot in the dark for the
        # first thing that looks like an article #

        resp = requests.post(
            'https://www.reichelt.de/index.html?ACTION=446&LA=446',
            data={'SEARCH': order_no})
        resp.raise_for_status()

        ms = re.findall('ARTICLE=([A-Z0-9-_]+)', resp.text)

        if ms:
            # actual article page
            article_page = requests.get('https://www.reichelt.de/?ARTICLE=' +
                                        ms[0])
            article_page.raise_for_status()

            name_span = re.findall('<span itemprop="name">(.*?)</span>',
                                   article_page.text)[0]

            name = html.unescape(name_span)

            return VendorItem(cls.NAME, order_no, name)


class FarnellVendor(object):

    NAME = 'farnell'

    API_ENDPOINT = 'http://api.element14.com//catalog/products'

    REGION = 'uk.farnell.com'

    # example key from the docs, because why not?
    API_KEY = 'gd8n8b2kxqw6jq5mutsbrvur'

    @classmethod
    def retrieve_item(cls, order_no):

        # import logging

        # logging.basicConfig()
        # logging.getLogger().setLevel(logging.DEBUG)
        # requests_log = logging.getLogger("requests.packages.urllib3")
        # requests_log.setLevel(logging.DEBUG)
        # requests_log.propagate = True

        params = {
            'term': 'id:' + order_no,
            'storeInfo.id': cls.REGION,
            'resultsSettings.offset': '0',
            'resultsSettings.numberOfResults': '1',
            'resultsSettings.refinements.filters': '',
            'resultsSettings.responseGroup': 'small',
            'callInfo.omitXmlSchema': 'false',
            'callInfo.callback': '',
            'callInfo.responseDataFormat': 'json',
            'callinfo.apiKey': cls.API_KEY,
        }

        resp = requests.get(cls.API_ENDPOINT, params=params)

        # while not insane, the farnell api is pretty bad. errors will be
        # returned on a 200, with a "code" entry in the resulting dict
        resp.raise_for_status()

        data = resp.json()

        assert 'error' not in data

        prod = data['premierFarnellPartNumberReturn']['products'][0]

        return VendorItem(cls.NAME, order_no, prod['displayName'])


VENDORS = {v.NAME: v for v in (ReicheltVendor, FarnellVendor)}
