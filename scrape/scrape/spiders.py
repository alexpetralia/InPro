from functools import partial
import json
import pandas as pd
import pymongo
import scrapy
import re

# Helper functions

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

def js_wrap(df):
    """Converts dataframe to json object"""
    return df.to_dict(orient='records')

# User defined classes

class XML(object):

    def __init__(self, response):
        """Initialize a scrapy response
        `params`
            response (scrapy.http.response.html.HtmlResponse)
        """
        self.response = response

    def _extract_objs(self, attr, str_, values, xpath_root):
        """Private method"""
        xpath = ("//{}[contains(concat(' ', normalize-space(@{}), ' ')"
                 ", ' {} ')]{}".format(xpath_root, attr, str_, values))
        objs = self.response.xpath(xpath).extract()
        return objs, xpath

    def extract(self, str_, attr='class', debug=False,
                xpath_root='*', values='/text()'):
        """Extracts text of an element given its class
        `params`
            str_ (str): the class identifer of the element
            attr (str): the attribute to search
            debug (bool): print interim transformations
            xpath_root (str): how deep to look into the xpath
            values (str): underlying values in xpath to capture
        `returns`
            (str): the text of the element
        """
        objs, xpath = self._extract_objs(attr, str_, values=values,
                                         xpath_root=xpath_root)
        text_objs = [obj for obj in objs if obj.strip() != '']

        if debug:
            print("Xpath:", xpath)
            print("Objects:", objs)
            print("Text objects:", text_objs)

        if text_objs:
            first = text_objs[0].strip()
            return first.replace('\n', '').replace('  ', ' ')
        else:
            return ''

    def extract_tbl(self, str_, attr='class', n=1,
                    debug=False, xpath_root='*'):
        """Extracts an HTML and dumps into pandas dataframe
        `params`
            root (str): how deep to look into the xpath
            str_ (str): the class identifer of the element
            attr (str): the attribute to search
            n (int): table number given this xpath match
            debug (bool): print interim transformations
        `returns`
            (pd.DataFrame): dataframe of data
        """
        objs, xpath = self._extract_objs(attr, str_, values='',
                                         xpath_root=xpath_root)
        if debug:
            print("Xpath:", xpath)
            print("Objects", objs)

        if objs:
            try:
                table_html = objs[n - 1].replace('\n', '')
            except IndexError:
                return pd.DataFrame()

            return pd.read_html(table_html, flavor='bs4')[0]

        return pd.DataFrame()

# Spiders

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
        headers = {
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                           '(KHTML, like Gecko) Chrome/60.0.3112.78'
                           'Safari/537.36'),
            'referer': 'https://empireflippers.com/'
        }
        yield scrapy.Request(url='https://empireflippers.com/marketplace/',
                             headers=headers,
                             callback=self.parse_main)

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
        for item in all_items:
            # Generate metadata
            url = 'https://empireflippers.com/listing/{}'
            item['url'] = url.format(item['listing_id'])
            item['source'] = self.name

            # Follow detail page
            if item['listing_id'] not in detail_ids:
                yield response.follow(
                    url=item['url'],
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

class FlippaSpider(scrapy.Spider):

    name = 'flippa'

    def __init__(self):
        """Constructor. Database is initialized in the associated Pipeline"""
        self.BASE_URL = 'https://flippa.com'
        self.post_id_regex = r'^https://flippa.com/(\d+)-.*$'
        self.listings_db = None
        self.existing_posts = self.get_posts()

    def get_posts(self):
        """Gets listing posts which already exist in the collection
        `returns`
            (list[str]): list of post IDs
        """
        client = pymongo.MongoClient('localhost', 27017)
        collection = client['data']['flippa_listings']
        posts = collection.find({})
        return [post['post_id'] for post in posts]

    def start_requests(self):
        """Build request messages"""
        login = 'https://flippa.com/login'
        yield scrapy.Request(url=login, callback=self.login)

    def login(self, response):
        """Logins into Flippa"""
        yield scrapy.FormRequest.from_response(
            response,
            formxpath='//*[@id="new_login_form"]',
            formdata={
                'email': 'alex.petralia@gmail.com',
                'password': 'scrapy123',
            },
            callback=self.after_login
        )

    def after_login(self, response):
        """Action to perform after login"""
        listings_url = 'https://flippa.com/websites/all'
        yield scrapy.Request(url=listings_url, callback=self.parse_main)

    def parse_main(self, response):
        """Parses the main marketplace page"""
        xpath_listings_box = "//*[@class='ListingResults___listingResults']"
        listings_box = response.xpath(xpath_listings_box)
        links = listings_box.xpath('.//a/@href')

        # Parse each listing from listings page
        for link in links:
            url = link.extract()

            post_id = re.findall(self.post_id_regex, url)[0]
            if post_id in self.existing_posts:
                continue

            yield scrapy.Request(url=url, callback=self.parse_detail)

        # Paginate
        next_page_xml = XML(response).extract('Pagination___nextLink',
                                              values='')
        next_page_href = re.findall(r'.*href=\"(.*?)\"', next_page_xml)
        if next_page_href:
            yield response.follow(url=self.BASE_URL + next_page_href[0],
                                  callback=self.parse_main)

    def parse_detail(self, response):
        """Parses listing detail page"""
        xml = XML(response)

        # Metadata
        post_id = re.findall(self.post_id_regex, response.url)[0]
        url = response.url
        source = self.name

        # At a glance
        name = xml.extract('ListingHero-propertyIdentifierLink')
        summary = xml.extract('Listing-listingSummary')
        seller = xml.extract('SellerNameOnListing', 'context')
        listing_status = xml.extract('ListingStatus-auctionTime--bidBox')
        seller_tx_value = xml.extract('UserProfile-transactionsSummary')
        site_type = xml.extract('site_type', 'id')
        platform = xml.extract('platform', 'id')
        site_age = xml.extract('site_age', 'id')

        # Traffic
        pg_session = xml.extract('pages_/_session', 'id')
        pg_duration = xml.extract('avg._session_duration', 'id')
        pg_bounce = xml.extract('bounce_rate', 'id')
        traffic = xml.extract_tbl('Listing-trafficTable')
        if not traffic.empty:
            traffic.columns = ['date', 'uniques', 'views']

        # Traffic sub data
        xp = "table/preceding-sibling::h4[contains(text(), '{}')]//..//*"
        channels = xml.extract_tbl('Table Table--bordered', n=2,
                                   xpath_root=xp.format('Top Channels'))
        if not channels.empty:
            channels.columns = ['channels', 'views', 'pct_of_total']
        countries = xml.extract_tbl('Table Table--bordered', n=3,
                                    xpath_root=xp.format('Top Countries'))
        if not countries.empty:
            countries.columns = ['country', 'views']

        # Financials
        deep_xpath = "div[@class='Panel-section' and " \
                     ".//h2[contains(text(), '{}')]]//*"
        fin_xpath = deep_xpath.format('Financials')
        fin = xml.extract_tbl('Table Table--bordered', xpath_root=fin_xpath)
        if not fin.empty:
            fin.columns = ['date', 'revenue', 'costs', 'profit']

        # Site info
        info = pd.DataFrame()
        for n in range(1, 4):
            tbl = xml.extract_tbl('Table--siteInfo', n=n)
            info = info.append(tbl)
        if not info.empty:
            info.columns = ['field', 'value']
            info['field'] = info['field'].str.replace('?', '').str.strip()

        js = {
            'type': 'listing',
            'data': {
                'post_id': post_id,
                'url': url,
                'source': source,
                'name': name,
                'summary': summary,
                'seller': seller,
                'listing_status': listing_status,
                'seller_tx_value': seller_tx_value,
                'site_type': site_type,
                'platform': platform,
                'site_age': site_age,
                'traffic': {
                    'pg_session': pg_session,
                    'pg_duration': pg_duration,
                    'pg_bounce': pg_bounce,
                    'metrics': js_wrap(traffic),
                    'channels': js_wrap(channels),
                    'countries': js_wrap(countries)
                },
                'financials': js_wrap(fin),
                'site_info': js_wrap(info),
            }
        }

        yield js

        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
