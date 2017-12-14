import requests
import pymongo
from bs4 import BeautifulSoup

def clean(element, under=False):
    """Given a bs4 element tag, extract the text and clean it
    `params`
        element (bs4.element.Tag)
        under (bool): replace spaces with underscores
    `returns`
        text (str): cleaned text
    """
    text = element.get_text().strip().replace('\n', '').replace('\t', '')
    return text if not under else text.replace(' ', '_')

def extract(listing):
    """Given a listing, extract the quantitative data
    `params`
        listing (bs4.element.Tag): the listing
    `returns`
        (dict)
    """
    dict_ = {}

    # Get title, URL and source
    header = listing.findAll('h2', attrs={'class': 'listing-title'})[0]
    dict_['url'] = header.findAll('a')[0]['href']
    dict_['title'] = clean(header)
    dict_['source'] = 'fei'

    # Get stats
    stats = ('yearly-revenue', 'yearly-profit', 'asking-price')
    base = 'class*="listing-overview-item-'
    for stat in stats:
        key = listing.select('dt[{}title-{}"]'.format(base, stat))[0]
        value = listing.select('dd[{}-{}"]'.format(base, stat))[0]
        dict_[clean(key, under=True).lower()] = clean(value)

    return dict_

def main():
    """Main thread"""
    # Initialize database
    client = pymongo.MongoClient('localhost', 27017)
    C = client['data']['fei_listings']
    query = C.find({})
    existing = [x['title'] for x in query]

    # Scrape webpage
    response = requests.get('https://feinternational.com/buy-a-website/')
    soup = BeautifulSoup(response.text, 'html5lib')
    listings = soup.findAll('div', attrs={'class': 'listing'})

    # Write data
    for listing in listings:
        data = extract(listing)
        if data['title'] not in existing:
            print("Writing {}..".format(data))
            C.insert_one(data)

if __name__ == '__main__':

    main()
