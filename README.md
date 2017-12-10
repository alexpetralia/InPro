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
* <s>Database: postgres</s>
* Database: MongoDB (due to schemaless nature of source data)
* Proxy server: nginx
* Web framework: django via uWSGI

#### Frontend
* Templating: django templates
* CSS framework: bootstrap 3
* Visualizaton: Charts.js

## Deployment

1. Build tools: Install docker & docker-compose
2. Build: `sudo docker-compose up` (in a tmux window)

* Changes to the docker-compose.yaml file force a rebuild of the images, use: `sudo docker-compose up -d --build <image>`
* Never use `sudo docker-compose down` unless you want to destroy docker images. Instead use `sudo docker-compose stop`

## Next steps

1. <s>Set up dockerized containers for services (nginx, django, scrapy, postgres)</s>
2. Write the crawlers
3. Exploratory data analysis - is there anything actually useful here?
4. Build a GUI via django
