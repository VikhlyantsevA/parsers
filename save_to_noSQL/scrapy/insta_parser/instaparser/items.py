# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    user_info = scrapy.Field()
    user_id = scrapy.Field()
    following_id = scrapy.Field()
    followers_id = scrapy.Field()
    _id = scrapy.Field()

