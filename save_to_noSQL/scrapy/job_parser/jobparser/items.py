# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobparserItem(scrapy.Item):
    # define the fields for your item here like:
    position = scrapy.Field()
    resume_url = scrapy.Field()
    employer_info = scrapy.Field()
    employer = scrapy.Field()
    employer_url = scrapy.Field()
    salary_info = scrapy.Field()
    website_url = scrapy.Field()
    published_at = scrapy.Field()
    experience = scrapy.Field()
    region = scrapy.Field()
    metrostation = scrapy.Field()
    address = scrapy.Field()
    location_info = scrapy.Field()
    key_skills = scrapy.Field()
    is_remote = scrapy.Field()
    _id = scrapy.Field()
