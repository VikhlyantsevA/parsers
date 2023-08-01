from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from urllib.parse import urljoin
from dotenv import dotenv_values
from hashlib import md5
import os
import re

from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from orm_tables import Categories, ItemsInfo


def element_exists(self, by, value):
    try:
        self.find_element(by, value)
    except NoSuchElementException:
        return False
    return True

def get_with_reload(self, url):
    try:
        self.get(url)
    except TimeoutException:
        self.refresh()

WebDriver.element_exists = element_exists
WebDriver.get_with_reload = get_with_reload
WebElement.element_exists = element_exists


class CitilinkParser:

    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        config = dotenv_values(env_path)
        user_agent = config.get("USER_AGENT")
        pg_username = config.get("PG_USERNAME")
        pg_password = config.get("PG_PASSWORD")
        pg_host = config.get("PG_HOST")
        pg_port = config.get("PG_PORT")
        database = 'citilink'

        pg_engine = create_engine(f"postgresql://{pg_username}:{pg_password}@{pg_host}:{pg_port}/{database}", echo=False)
        Session = sessionmaker(bind=pg_engine)
        self.session = Session()

        options = Options()
        options.add_argument("start-maximized")
        driver_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'drivers', 'chromedriver'))
        service = Service(driver_dir)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(20)

        self.base_url = "https://www.citilink.ru"
        self.endpoint = "/catalog/"
        self.start_url = urljoin(self.base_url, self.endpoint)
        self.headers = {"User-Agent": user_agent}

    def __del__(self):
        self.driver.close()
        self.session.close()

    def run_parser(self):
        self.driver.get_with_reload(self.start_url)
        self.parse_catalog()

    def parse_catalog(self):
        catalog_items = self.driver.find_elements(By.XPATH, "//div[@class='CatalogLayout__item-title-wrapper']")
        categories_url = dict()
        for catalog_item in catalog_items:
            category_title = catalog_item.find_element(By.XPATH, ".//span[@class='CatalogLayout__category-title']") \
                .text \
                .strip()
            category_id = md5(category_title.encode('utf-8')).hexdigest()
            self.save_to_db(dict(category_id=category_id,
                                 category_name=category_title,
                                 parent_id=None))

            subcategories = catalog_item.find_elements(By.XPATH, ".//li[contains(@class,'CatalogLayout__children-item')]")
            for subcategory in subcategories:
                subcategory_url = self.get_abs_url(subcategory.find_element(By.XPATH, "./a").get_attribute("href"))
                subcategory_title = subcategory.find_element(By.XPATH, "./a").get_attribute("text").strip()
                subcategory_id = md5(f"{category_title}_{subcategory_title}".encode('utf-8')).hexdigest()
                categories_url[subcategory_id] = subcategory_url
                self.save_to_db(dict(category_id=subcategory_id,
                                     category_name=subcategory_title,
                                     parent_id=category_id))

        for category_id, category_url in categories_url.items():
            self.driver.get_with_reload(category_url)
            self.parse_items_info(category_id=category_id)

    def parse_items_info(self, **kwargs):
        category_id = kwargs.get("category_id")

        items_cards = self.driver.find_elements(By.XPATH, "//div[@data-meta-name='SnippetProductHorizontalLayout']")
        for item_card in items_cards:
            item_name = item_card.find_element(By.XPATH, ".//a/text()/..").text
            item_code = re.findall(r"Код товара:\s(\d+)",
                                   item_card.find_element(By.XPATH, ".//span[contains(text(), 'Код товара:')]").text)[0]
            id = md5(f"{item_code}_{item_name}".encode("utf-8")).hexdigest()
            item_url = self.get_abs_url(item_card.find_element(By.XPATH, ".//a/text()/..").get_attribute("href"))
            item_rate_xpath = ".//div[@data-meta-name='MetaInfo_rating']"
            item_rate = None
            if item_card.element_exists(By.XPATH, item_rate_xpath):
                item_rate = item_card.find_element(By.XPATH, item_rate_xpath).text
            item_price = None
            item_currency = None
            if item_card.element_exists(By.XPATH, ".//span[@data-meta-price]"):
                item_price = float(item_card.find_element(By.XPATH, ".//span[@data-meta-price]/span[1]")
                                   .text
                                   .replace(" ", ""))
                item_currency = item_card.find_element(By.XPATH, ".//span[@data-meta-price]/span[2]").text
            item_category_id = category_id

            self.save_to_db(dict(item_id=id,
                                 item_name=item_name,
                                 item_code=item_code,
                                 item_url=item_url,
                                 item_rate=item_rate,
                                 item_price=item_price,
                                 item_currency=item_currency,
                                 item_category_id=item_category_id))

        next_page = self.get_abs_url(self.driver.find_element(By.XPATH, "//a[@data-meta-name='PageLink__page-page-next']")
                                     .get_attribute("href"))
        if next_page:
            self.driver.get(next_page)
            self.parse_items_info(category_id=category_id)

    def save_to_db(self, item: dict):
        # in categories_fields key is local item key, value is a corresponding column name in table Categories
        categories_fields = {'category_id': 'id', 'category_name': 'name', 'parent_id': 'parent_id'}
        categories_info = {v: item.get(k) for k, v in categories_fields.items() if item.get(k)}
        # in items_fields key is local item key, value is a corresponding column name in table ItemsInfo
        items_fields = {'item_id': 'id',
                        'item_name': 'name',
                        'item_code': 'code',
                        'item_url': 'item_url',
                        'item_rate': 'rate',
                        'item_price': 'price',
                        'item_currency': 'currency',
                        'item_category_id': 'category_id'}
        items_info = {v: item.get(k) for k, v in items_fields.items() if item.get(k)}

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
    cl = CitilinkParser()
    cl.run_parser()
