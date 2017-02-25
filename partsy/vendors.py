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
    name = 'reichelt'

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

            return VendorItem(cls.name, order_no, name)


VENDORS = {ReicheltVendor.name: ReicheltVendor}
