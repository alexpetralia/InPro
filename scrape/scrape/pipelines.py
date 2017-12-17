# -*- coding: utf-8 -*-

import pymongo
import os

from scrape.spiders import EmpireSpider, FlippaSpider

class ItemPipeline(object):

    def __init__(self):

        host = os.environ.get('MONGO_URL', 'localhost')
        self.client = pymongo.MongoClient(host, 27017)

    def open_spider(self, spider):
        """Passes database object upon opening a new spider"""
        if isinstance(spider, EmpireSpider):
            spider.listings_db = self.client['data']['empireflippers_listings']
            spider.details_db = self.client['data']['empireflippers_details']
        if isinstance(spider, FlippaSpider):
            spider.listings_db = self.client['data']['flippa_listings']

    def process_item(self, item, spider):

        type_, data = item['type'], item['data']
        if type_ == 'listing':
            spider.listings_db.insert_one(data)
        elif type_ == 'detail':
            spider.details_db.insert_one(data)

        return item
