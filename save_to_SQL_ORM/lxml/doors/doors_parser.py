"""
Parser to get data from kinlong.ru.
There was a class DoorsParser made to get data from website.
Data collects into `items` of dict type and saves into postgres with help of sqlalchemy.
File `orm_tables.py` to create tables is attached. Descriptions of tables classes within.
Fields of `items`:
    For `categories` table:
        id - unique identifier of product category (md5-hash);
        name - name of product category;
        parent_id - identifier of product parent category (md5-hash);
    For `items_info` table:
        id - unique identifier of item (md5-hash);
        item_name - name of product;
        item_code - item article (code);
        item_url - url to item page with full description;
        price - item price;
        currency - item price currency;
        category_id - item category id (the last child in chain of categories links).
Still in progress...
"""
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from urllib.parse import urljoin
from dotenv import dotenv_values
from requests import Response
from hashlib import md5
from lxml import html
import requests
import asyncio
import re
import os

from orm_tables import Categories, ItemsInfo


class DoorsParser:

    def __init__(self):
        database = 'doors'
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        config = dotenv_values(env_path)
        pg_username = config.get("PG_USERNAME")
        pg_password = config.get("PG_PASSWORD")
        pg_host = config.get("PG_HOST")
        pg_port = config.get("PG_PORT")
        user_agent = config.get("USER_AGENT")
        headers = {"User-Agent": user_agent}
        self.base_url = "https://kinlong.ru/"
        self.start_url = self.base_url
        pg_engine = create_engine(f"postgresql://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{database}",
                                  echo=False)
        Session = sessionmaker(bind=pg_engine)
        self.session = Session()

    def __del__(self):
        self.session.close()

    def run_parser(self):
        start_url_response = requests.get(self.start_url, headers=self.headers)
        return self.save_to_db(start_url_response)

    async def parse_items_info(self, response: Response, **kwargs):
        category_id = kwargs.get("category_id")
        items_dom = html.document_fromstring(response.text)

        next_page = items_dom.xpath("//li[@class='next']/a/@href")
        if next_page:
            next_page_response = requests.get(next_page[0], headers=self.headers)
            self.parse_items_info(next_page_response,
                                  category_id=category_id)

        items = items_dom.xpath("//div[contains(@class, 'product')]")
        for item in items:
            item_name = item.xpath(".//div[@class='name']/a/text()")
            item_code = re.match(r"Артикул:\s*(\w+)\s*[|]", item.xpath(".//div[contains(@class, 'articul')]/text()"))
            item_url = self.get_abs_url(item.xpath(".//div[@class='name']/a/@href"))
            id = md5(f"{item_code}_{item_name}".encode("utf-8")).hexdigest()
            price = float(item.xpath(".//div[@class='price']/span[1]/text()").replace(" ", ""))
            currency = item.xpath(".//div[@class='price']/span[2]/text()")
            category_id = category_id
            yield dict(item_id=id,
                       item_name=item_name,
                       item_code=item_code,
                       item_url=item_url,
                       item_price=price,
                       item_currency=currency,
                       item_category_id=category_id)

    async def parse_categories(self, response: Response, **kwargs):
        category_id = kwargs["category_id"]
        category_dom = html.document_fromstring(response.text)
        category_items = category_dom.xpath("//div[@id='section']")
        for category_item in category_items:
            subcategory_title = category_item.xpath(".//div[@class='name']/text()")[0].strip()
            subcategory_id = md5(f"{category_id}_{subcategory_title}".encode('utf-8')).hexdigest()
            subcategory_url = self.get_abs_url(category_item.xpath("./a/@href")[0])
            yield dict(category_id=subcategory_id, category_name=subcategory_title, parent_id=category_id)

            subcategory_url_response = requests.get(subcategory_url, headers=self.headers)
            async for item in self.parse_items_info(subcategory_url_response, category_id=subcategory_id):
                yield item

    async def parse_catalog(self, response: Response):
        catalog_dom = html.document_fromstring(response.text)
        catalog_items = catalog_dom.xpath("//ul[@class='catalog_index']//a")
        for catalog_item in catalog_items:
            category_title = "".join(catalog_item.xpath(".//span[@class='name']/text()"))
            category_id = md5(category_title.encode('utf-8')).hexdigest()
            category_url = self.get_abs_url(catalog_item.xpath("./@href"))
            yield dict(category_id=category_id, category_name=category_title, parent_id=None)

            category_url_response = requests.get(category_url, headers=self.headers)
            async for item in self.parse_categories(category_url_response, category_id=category_id):
                yield item

    async def save_to_db(self, response: Response):
        categories_info = None
        items_info = None
        async for item in self.parse_catalog(response):
            # in categories_fields key is local item key, value is a corresponding column name in table Categories
            categories_fields = {'category_id': 'id', 'category_name': 'name', 'parent_id': 'parent_id'}
            categories_info = {v: item.get(k) for k, v in categories_fields.items() if item.get(k)}
            # in items_fields key is local item key, value is a corresponding column name in table ItemsInfo
            items_fields = {'item': 'id',
                            'item_name': 'item_name',
                            'item_code': 'item_code',
                            'item_url': 'item_url',
                            'item_price': 'price',
                            'item_currency': 'currency',
                            'item_category_id': 'category_id'}
            items_info = {v: item.get(k) for k, v in items_fields.items() if item.get(k)}
        # Writing to tables Categories and ItemsInfo with sqlalchemy
        if categories_info:
            self.session.execute(insert(Categories)
                                 .values(categories_info)
                                 .on_conflict_do_nothing())
            self.session.commit()

        if items_info:
            self.session.execute(insert(ItemsInfo)
                                 .values(items_info)
                                 .on_conflict_do_nothing())
            self.session.commit()

    def get_abs_url(self, url):
        return urljoin(self.base_url, url) if url.startswith("/") else url


if __name__ == '__main__':
    dr = DoorsParser()
    asyncio.run(dr.run_parser())

