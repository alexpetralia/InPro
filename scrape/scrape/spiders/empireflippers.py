import json
import logging
import scrapy

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

class EmpireSpider(scrapy.Spider):

    name = 'empireflippers'

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

        # Pull .json items
        first_batch = extract_json(split[1], 23)
        second_batch = extract_json(split[2], 23)
        all_items = first_batch + second_batch

        # Iterate over item
        for item in all_items[:]:
            url = 'https://empireflippers.com/listing/{}'
            # yield response.follow(url=url.format(item['listing_id']),
            #                       callback=self.parse_detail)

            yield item

            # TODO: not persisting

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        # import pdb; pdb.set_trace();

    def parse_detail(self, response):
        """Parses an internet property detail page"""
        print 'got here to {}'.format(response.url)
        yield {'url': response.url}
