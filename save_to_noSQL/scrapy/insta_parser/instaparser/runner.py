"""
Web parser to get data from IG.
Runner gets:
    - list of users names into `users` field to get their info (photos, followers, followings, etc.).
Data collects into Documents and saves into MongoDB collections (`users` with users detailed info and
`users_connections` with friendship links of users).
Fields of the Documents:
    for `users` collection:
        _id - unique identifier of the Document (Documents with same _id are saved only once into MongoDB collection);
        user_id - user unique identifier;
        username - user login name;
        full_name - full name mentioned when signed up;
        profile_pic_url_hd - url to profile picture in high quality.
    for `users_connections` collection:
        _id - unique identifier of the Document (Documents with same _id are saved only once into MongoDB collection);
        user_id - user unique identifier;
        subscriber_id - subscriber (friend of user with user_id) unique identifier.
"""
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from instaparser.spiders.insta import InstaSpider

if __name__ == '__main__':
    configure_logging()
    settings = get_project_settings()
    runner = CrawlerRunner(settings)
    runner.crawl(InstaSpider, users=['cutezkitten', 'mycatsardor'])
    reactor.run()
