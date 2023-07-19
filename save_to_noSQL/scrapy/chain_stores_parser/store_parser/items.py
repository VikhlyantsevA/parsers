# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from itemloaders.processors import Compose, MapCompose, TakeFirst
import scrapy
import string

def treat_price_items(value):
    value = value.translate({ord(x): '' for x in string.whitespace})
    return int(value) if value.isdigit() else value


class StoreParserItem(scrapy.Item):
    name = scrapy.Field(input_processor=MapCompose(lambda x: x.strip()), output_processor=TakeFirst())
    item_code = scrapy.Field(output_processor=TakeFirst())
    product_url = scrapy.Field(output_processor=TakeFirst())
    price_items = scrapy.Field(input_processor=MapCompose(treat_price_items))
    photos_url = scrapy.Field()
    photos_info = scrapy.Field()
    params_names = scrapy.Field(input_processor=MapCompose(lambda x: x.strip()))
    params_values = scrapy.Field(input_processor=MapCompose(lambda x: x.strip()))
    params = scrapy.Field()
    store_homepage = scrapy.Field(output_processor=TakeFirst())
    _id = scrapy.Field()
