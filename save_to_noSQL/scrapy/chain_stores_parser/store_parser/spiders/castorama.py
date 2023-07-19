from store_parser.items import StoreParserItem
from scrapy.http import HtmlResponse
from scrapy.loader import ItemLoader
from urllib.parse import urlencode, urljoin
import scrapy

class CastoramaSpider(scrapy.Spider):
    name = 'castorama'
    allowed_domains = ['castorama.ru']

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.base_url = 'https://castorama.ru'
        self.endpoint = '/catalogsearch/result/'
        self.page = 1
        self.limit = kwargs.get('limit')
        self.start_urls = [f"{urljoin(self.base_url, self.endpoint)}?{urlencode(kwargs.get('url_args'))}"]

    def parse(self, response: HtmlResponse):
        next_page = response.xpath("//a[@class='next i-next']/@href").get()
        self.page += 1
        if next_page and (self.page <= self.limit if self.limit else True):
            next_page = urljoin(self.base_url, next_page) if next_page.startswith('/') else next_page
            yield response.follow(next_page, callback=self.parse)

        items_links = response.xpath("//a[contains(@class, 'product-card__name')]")
        for link in items_links:
            yield response.follow(link, callback=self.parse_ads)

    def parse_ads(self, response: HtmlResponse):
        loader = ItemLoader(item=StoreParserItem(), response=response)
        loader.add_xpath("name", "//h1[contains(@class, 'product-essential__name')]/text()")
        loader.add_xpath("item_code", "//div[@class='product-essential__sku']//span/text()")
        price_items = response.xpath("//div[contains(@class, 'add-to-cart__price')]/div[not(contains(@class, 'scrollbar-margin'))]//span[@class='price']//text()")
        loader.add_xpath("price_items", "//div[contains(@class, 'add-to-cart__price')]/div[not(contains(@class, 'scrollbar-margin'))]//span[@class='price']//text()")
        loader.add_xpath("photos_url", "//div[contains(@class, 'product-media__top-slider')]//@data-src")
        loader.add_value("product_url", response.url)
        loader.add_value("store_homepage", self.base_url)

        params_table_xpath = "//div[contains(@class, 'product-block')]//dl[contains(@class, 'specs-table')]"
        loader.add_xpath("params_names", f"{params_table_xpath}/dt/span[contains(@class, 'specs-table__attribute-name')]/text()")
        loader.add_xpath("params_values", f"{params_table_xpath}/dd[contains(@class, 'specs-table__attribute-value ')]/text()")

        yield loader.load_item()
