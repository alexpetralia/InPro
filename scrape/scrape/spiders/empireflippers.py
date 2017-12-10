from functools import partial
import json
import logging
import scrapy
import re

def extract_json(str_, st, end=-1):
    """Takes a string and returns a dict object
    `params`
        str_ (str): the string to parse
        st (int): what index to start at
        end (int): what index to end at
    `returns`
        (dict): the extracted .json object
    """
    val = str_[st:end]
    return json.loads(val)

def create_key(*attrs):
    """Creates a unique string key from many attributes"""
    attrs = [str(attr) for attr in attrs]
    return '|'.join(attrs)

class EmpireSpider(scrapy.Spider):

    name = 'empireflippers'

    def __init__(self):
        """Constructor. Database is initialized in the associated Pipeline"""
        self.listings_db = None
        self.details_db = None

    def fetch_all_listing_keys(self):
        """Gets all listings so as not to scrape already stored ones"""
        items = self.listings_db.find({})
        keys = [create_key(x['post_id'], x['listing_id']) for x in items]
        return keys

    def fetch_all_detail_ids(self):
        """Get all stored detail pages so as not to fetch twice"""
        items = self.details_db.find({})
        detail_ids = [x['listing_id'] for x in items]
        return detail_ids

    def start_requests(self):
        """Build request messages"""
        start_urls = ['https://empireflippers.com/marketplace/']
        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse_main)

    def parse_main(self, response):
        """Parses the main marketplace page"""
        # Parse HTML
        items = response.xpath("//script[contains(text(), 'for_sale_list')]")
        split = items.extract_first().split("\n")

        # Check existing
        listing_keys = self.fetch_all_listing_keys()
        detail_ids = self.fetch_all_detail_ids()

        # Pull .json items
        first_batch = extract_json(split[1], 23)
        second_batch = extract_json(split[2], 23)
        all_items = first_batch + second_batch

        # Iterate over items
        for item in all_items[:300]:
            # Follow detail page
            if item['listing_id'] not in detail_ids:
                url = 'https://empireflippers.com/listing/{}'
                yield response.follow(
                    url=url.format(item['listing_id']),
                    callback=partial(self.parse_detail, item['listing_id'])
                )

            # Persist listing if it doesn't already exist
            key = create_key(item['post_id'], item['listing_id'])
            if key not in listing_keys:
                yield {'type': 'listing', 'data': item}

    def parse_detail(self, listing_id, response):
        """Parses an internet property detail page"""
        # Pull data from JavaScript
        js = response.xpath("//script[contains(text(), 'updateCanvas()')]")
        js = js.extract_first().replace('\n', '')

        # Extract metrics
        data = {}
        for field in ('Revenue', 'Profit', 'Pageviews'):
            regex = r"{}\', ([\d\.\,]*)\]".format(field)
            series = re.findall(regex, js)
            if series:
                data[field] = series[0].split(',')

        # Extract date fields
        dt_regex = r"ticks = \[([\d\"\-\,]*)\];"
        dates = re.findall(dt_regex, js)
        dates = [x.replace('"', '') for x in dates[0].split(',')]
        data['Dates'] = dates

        # Prepare object
        obj = {
            'type': 'detail',
            'data': {
                'listing_id': listing_id,
                'data': data
            }
        }

        yield obj

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
