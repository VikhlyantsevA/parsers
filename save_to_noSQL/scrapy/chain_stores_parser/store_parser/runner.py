"""
Web parser to get data from chain stores (now just one spider for castorama.ru).
Runner gets:
    - dictionary of url arguments gor request into `url_args` field;
    - limit for number of pages to be parsed into `limit` field.
Parser simulates search request for castorama.ru, get items pages, save their info and photos.
Data collects into Documents and saves into MongoDB collections (castorama according to name of scrapy spider).
Photos are saved into `photos` folder in root directory of the project. For each item subfolder is created.
Fields of the Document:
    _id - unique identifier of the Document (Documents with same _id are saved only once into MongoDB collection);
    name - name of the product;
    item_code - item unique code from chain store (included into subfolder name in `photos` directory);
    product_url - link to product page;
    price_items - dictionary with price items of product (`price` and `currency` field now);
    photos_info - dictionary with photos saving path, url and hashcode;
    params - characteristics of product.
"""
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from store_parser.spiders.castorama import CastoramaSpider

if __name__ == '__main__':
    configure_logging()
    settings = get_project_settings()
    runner = CrawlerRunner(settings)

    runner.crawl(CastoramaSpider,
                 url_args={'q': 'смесители'})

    d = runner.join()
    d.addBoth(lambda x: reactor.stop())

    reactor.run()
