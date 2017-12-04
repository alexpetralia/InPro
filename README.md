## Objective

InPro scrapes financial information from internet property brokerages and stores the data in a local database. Valuation analyses, visualizations and alerting can be performed on the scraped data.


## Data sources

* https://empireflippers.com/
* https://flippa.com/
* https://feinternational.com/buy-a-website/


## Requirements

* Analytics: Sharpe ratios, multiples (eg. P/E), moment calculations (eg. standard deviation, skewness, kurtosis)
* Visualization: time series, distributions by a given dimension (eg. industry, vintage, etc.)
* Alerting: new internet properties generate email reports if they are potential opportunities


## Technical stack

#### Backend services
* Deployment: docker
* Scraping: (a) scrapy scripers and (b) ad hoc scripts using requests
* Database: postgres
* Proxy server: nginx
* Web framework: django via uWSGI

#### Frontend
* Templating: django templates
* CSS framework: bootstrap 3
* Visualizaton: Charts.js

## Deployment

1. Build tools: Install docker & docker-compose
2. Build: `sudo docker-compose up -d`
3. Start services: `sudo docker-compose start`


## Next steps

1. Set up dockerized containers for services (nginx, django, scrapy, postgres)
2. Write the crawlers
3. Exploratory data analysis - is there anything actually useful here?
4. Build a GUI via django
