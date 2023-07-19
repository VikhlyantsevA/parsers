# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    user_info = scrapy.Field()
    following_info = scrapy.Field()
    followers_info = scrapy.Field()
    _id = scrapy.Field()

