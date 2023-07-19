import time

import scrapy
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from urllib.parse import urljoin, urlparse
from scrapy.http import HtmlResponse
import os.path

from jobparser.settings import PROJECT_ROOT
from jobparser.items import JobparserItem


class SuperjobSpider(scrapy.Spider):
    name = 'superjob'
    allowed_domains = ['superjob.ru']

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        home_page = 'http://superjob.ru'
        self.start_urls = []
        self.page = 1
        self.limit = kwargs.get('limit')
        regions = kwargs.get('regions')
        vacancies = kwargs.get('vacancies')

        options = Options()
        options.add_argument("start-maximized")
        service = Service(os.path.join(PROJECT_ROOT, "drivers", "chromedriver"))

        # Get urls for search start pages
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.implicitly_wait(1)
            wait = WebDriverWait(driver, 30)

            for vacancy in vacancies:
                for region in regions:
                    driver.get(home_page)

                    # Click cookie use acception button
                    try:
                        driver.find_element(By.XPATH, '//button[contains(@class, "f-test-button-Soglasen")]').click()
                    except NoSuchElementException:
                        pass

                    # Choose required region
                    # Click region button
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//form[@action="/vacancy/search/"]//span[@role="button"]'))) \
                        .click()
                    # Clean regions checkbox list
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "f-test-button-Ochistit")]'))) \
                        .click()
                    # Type required region for filtering
                    wait.until(EC.presence_of_element_located((By.XPATH, '//input[@name="geo"]'))).send_keys(region)
                    # Tick filtered region from list
                    wait.until(EC.element_to_be_clickable((By.XPATH, f'//label//span[contains(text(), "{region}")]'))) \
                        .click()

                    wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "f-test-button-Primenit")]'))) \
                        .click()
                    start_url = driver.current_url

                    # Enter vacancy
                    wait.until(EC.invisibility_of_element_located((By.ID, 'headerLocationGeoCurtain')))
                    driver.find_element(By.XPATH, '//input[@name="keywords"]').send_keys(vacancy, Keys.ENTER)

                    wait.until_not(EC.url_to_be(start_url))
                    time.sleep(2)
                    self.start_urls.append(driver.current_url)

    def parse(self, response: HtmlResponse):
        next_page = response.xpath('//a[contains(@class, "f-test-link-Dalshe")]').get()
        self.page += 1
        if next_page and (self.page <= self.limit if self.limit else True):
            yield response.follow(next_page, callback=self.parse)

        start_url_parsed = urlparse(response.url)
        base_url = f"{start_url_parsed.scheme}://{start_url_parsed.hostname}"
        job_items = response.xpath("//div[contains(@class, 'f-test-vacancy-item')]")
        for job_item in job_items:
            position = job_item.xpath(".//span[not(contains(@class, 'vacancy-item-company-name'))]/a//text()").getall()
            resume_url = job_item.xpath(".//span[not(contains(@class, 'vacancy-item-company-name'))]/a/@href").get()
            resume_url = urljoin(base_url, resume_url) if resume_url.startswith('/') else resume_url
            employer = job_item.xpath(".//span[contains(@class, 'vacancy-item-company-name')]/a/text()").get()
            employer_url = job_item.xpath(".//span[contains(@class, 'vacancy-item-company-name')]/a/@href").get()
            region = job_item.xpath(".//span[contains(@class, 'f-test-text-company-item-location')]//div/text()").get()
            salary_info = job_item.xpath(".//div[contains(@class, 'f-test-text-company-item-salary')]//text()").getall()
            is_remote = job_item.xpath(".//span[contains(@class, 'f-test-badge') and text() = 'Удаленная работа']/text()").get()
            website_url = base_url
            published_at = job_item.xpath(".//div/span/text()").get()

            item = dict(
                position=position,
                resume_url=resume_url,
                employer=employer,
                employer_url=employer_url,
                region=region,
                salary_info=salary_info,
                is_remote=is_remote,
                website_url=website_url,
                published_at=published_at
            )
            yield response.follow(resume_url, callback=self.parse_resume_data, cb_kwargs={"item": item})


    def parse_resume_data(self, response: HtmlResponse, **kwargs):
        item = kwargs.get("item")
        experience = response.xpath("//div/span[contains(text(), 'Опыт')]/text()").get()
        metrostation = response.xpath("//div[contains(@class, 'f-test-address')]/div[2]//span[not(.//svg)]//text()").getall()
        address = response.xpath("//div[contains(@class, 'f-test-address')]/div[1]//span//text()").getall()
        key_skills = None
        yield JobparserItem(**item,
                            experience=experience,
                            metrostation=metrostation,
                            address=address,
                            key_skills=key_skills)
