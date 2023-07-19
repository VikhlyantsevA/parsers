"""
Parser to get data from hh.ru and superjob.ru.
Runner gets:
    - list of requests text into `vacancies` field;
    - region of vacancy posting into `region` field (corresponds to region search button);
    - limit for number of pages to be parsed into `limit` field.
Data collects into Documents and saves into MongoDB collections (hh and superjob according to names of scrapy spiders).
Fields of the Document:
    _id - unique identifier of the Document (Documents with same _id are saved only once into MongoDB collection);
    position - vacancy name;
    resume_url - url to get full vacancy info;
    employer_info - dictionary with employer info collected within:
        `employer` - employer name,
        `employer_url` - link to employer page at hh.ru/superjob.ru).
    salary_info - dictionary with parsed salary info within:
        `min_salary` - maximum salary level,
        `max_salary` - minimum salary level,
        `currency` - currency type,
        `payment_frequency` - monthly, yearly, for watch etc.,
        `tax` - net or gross.
    website_url - website base url used for parsing (either hh.ru or superjob.ru)
    published_at - date when vacancy was posted
    experience - experience requirements for the position
    location_info - employer location info collected withing the dictionary:
        `region` - location of employer (region where job is for),
        `metrostation` - list of nearest metrostations,
        `address` - full address.
    key_skills - list of required key skills
    is_remote - shows if job remote or not
"""
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


from jobparser.spiders.hh import HhSpider
from jobparser.spiders.superjob import SuperjobSpider

if __name__ == '__main__':
    configure_logging()
    settings = get_project_settings()
    runner = CrawlerRunner(settings)
    runner.crawl(HhSpider,
                 vacancies=['data engineer'],
                 regions=["Санкт-Петербург", "Москва"],
                 limit=10)

    runner.crawl(SuperjobSpider,
                 vacancies=['аналитик'],
                 regions=["Санкт-Петербург", "Москва"],
                 limit=10)

    d = runner.join()
    d.addBoth(lambda x: reactor.stop())

    reactor.run()
