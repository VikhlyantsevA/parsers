from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from instaparser.spiders.insta import InstaSpider

if __name__ == '__main__':
    configure_logging()
    settings = get_project_settings()
    runner = CrawlerRunner(settings, users=['soh.y4w00', 'cutezkitten', 'mycatsardor'])
    runner.crawl(InstaSpider)
    reactor.run()
