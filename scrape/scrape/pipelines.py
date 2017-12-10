# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo

class EmpireFlippersPipeline(object):

    def __init__(self):

        client = pymongo.MongoClient('localhost', 27017)
        self.collection = client['data']['empireflippers_listings']

    def process_item(self, item, spider):

        # self.collection.insert_one(item)
        # key = {'listing_id': item['listing_id']}
        # self.collection.update_one(key, {'$set': item}, upsert=True)

        return item
