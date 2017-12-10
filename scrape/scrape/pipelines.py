# -*- coding: utf-8 -*-

import pymongo

from scrape.spiders.empireflippers import EmpireSpider

class ItemPipeline(object):

    def __init__(self):

        self.client = pymongo.MongoClient('localhost', 27017)

    def open_spider(self, spider):
        """Passes database object upon opening a new spider"""
        if isinstance(spider, EmpireSpider):
            spider.listings_db = self.client['data']['empireflippers_listings']
            spider.details_db = self.client['data']['empireflippers_details']

    def process_item(self, item, spider):

        type_, data = item['type'], item['data']
        if type_ == 'listing':
            spider.listings_db.insert_one(data)
        elif type_ == 'detail':
            spider.details_db.insert_one(data)

        return item
