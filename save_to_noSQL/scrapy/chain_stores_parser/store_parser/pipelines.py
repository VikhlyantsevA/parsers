# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from urllib.parse import urlencode, urljoin
from scrapy.utils.python import to_bytes
from transliterate import translit
import hashlib
import string

from my_lib.mongodb_operator import MongodbOperator

class StoreParserPipeline:
    def __init__(self):
        self.m_utils = MongodbOperator()

    def process_item(self, item, spider):
        item['price_items'] = self.process_price(item.get('price_items')) if item.get('price_items') else None
        item['params'] = dict(zip(item['params_names'], item['params_values']))

        del item['params_names'], item['params_values'], item['store_homepage']

        self.m_utils.save_documents('stores_scrapy', spider.name, [dict(item)])
        return item

    def process_price(self, price_items):
        res = dict()
        res['price'], res['currency'], *other = filter(None, price_items)
        return res

class StorePhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item.get('photos_url'):
            for img_url in item['photos_url']:
                img_url = urljoin(item['store_homepage'], img_url) if img_url.startswith('/') else img_url
                try:
                    yield scrapy.Request(img_url)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        item['photos_info'] = [{k:v for k, v in item_[1].items() if k in ["url", "path", "checksum"]}
                               for item_ in results if item_[0]]
        del item['photos_url']
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        if item and info.spider:
            # reversed - translit from target language to source
            folder_name = translit(item['name'], reversed=True) \
                .translate({ord(x): '' for x in string.punctuation}) \
                .replace(' ', '_')
            folder_prefix = item["item_code"] if item["item_code"] else ''
            return f'{info.spider.name}/{folder_prefix}_{folder_name}/{image_guid}.jpg'

