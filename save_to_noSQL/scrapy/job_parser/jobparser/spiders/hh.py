import scrapy
from scrapy.http import HtmlResponse
from urllib.parse import urljoin, urlencode


from jobparser.items import JobparserItem


class HhSpider(scrapy.Spider):
    name = 'hh'
    allowed_domains = ['hh.ru']

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.base_url = 'https://izhevsk.hh.ru'
        endpoint = '/search/vacancy'
        self.start_urls = []
        self.page = 1
        self.limit = kwargs.get('limit')
        regions = kwargs.get('regions')
        vacancies = kwargs.get('vacancies')

        area_codes = {"Москва": 1, "Санкт-Петербург": 2}
        for vacancy in vacancies:
            for region in regions:
                search_params = [
                    ('area', area_codes[region]),
                    ('search_field', 'name'),
                    ('search_field', 'company_name'),
                    ('search_field', 'description'),
                    ('text', vacancy),
                    ('items_on_page', 20),
                    ('no_magic', 'true'),
                    ('L_save_area', 'true')
                ]
                url = f"{urljoin(self.base_url, endpoint)}?{urlencode(search_params)}"
                self.start_urls.append(url)

    def parse(self, response: HtmlResponse):
        rel_next_page = response.xpath("//a[@data-qa='pager-next']/@href").get()
        self.page += 1
        if rel_next_page and (self.page <= self.limit if self.limit else True):
            next_page = urljoin(self.base_url, rel_next_page)
            yield response.follow(next_page, callback=self.parse)

        vacancy_windows = response.xpath("//div[@class='vacancy-serp-item__layout']")
        for window in vacancy_windows:
            position = window.xpath(".//a[@data-qa='serp-item__title']/text()").getall()
            resume_url = window.xpath(".//a[@data-qa='serp-item__title']/@href").get()
            employer = window.xpath(".//a[@data-qa='vacancy-serp__vacancy-employer']/text()").getall()
            employer_url = window.xpath(".//a[@data-qa='vacancy-serp__vacancy-employer']/@href").get()
            experience = window.xpath(".//div[@data-qa='vacancy-serp__vacancy-work-experience']/text()").get()
            region = window.xpath(".//div[@data-qa='vacancy-serp__vacancy-address']/text()").get()
            salary_info = window.xpath(".//span[@data-qa='vacancy-serp__vacancy-compensation']/text()").getall()
            is_remote = window.xpath(".//div[@data-qa='vacancy-label-remote-work-schedule']//text()").get()
            website_url = self.base_url

            item = dict(
                position=position,
                resume_url=resume_url,
                employer=employer,
                employer_url=employer_url,
                region=region,
                salary_info=salary_info,
                website_url=website_url,
                experience=experience,
                is_remote=is_remote
            )
            yield response.follow(resume_url, callback=self.parse_resume_data, cb_kwargs={"item": item})

    def parse_resume_data(self, response: HtmlResponse, **kwargs):
        item = kwargs.get("item")
        published_at = response.xpath("//p[contains(@class, 'vacancy-creation-time')]//text()").getall()
        metrostation = response.xpath("//span[@data-qa='vacancy-view-raw-address']//span[@class='metro-station']/text()").getall()
        address = response.xpath("//div[@class='vacancy-description']//span[@data-qa='vacancy-view-raw-address']/text()").getall()
        key_skills = response.xpath("//div[@class='bloko-tag-list']//text()").getall()
        yield JobparserItem(**item,
                            published_at=published_at,
                            metrostation=metrostation,
                            address=address,
                            key_skills=key_skills)
