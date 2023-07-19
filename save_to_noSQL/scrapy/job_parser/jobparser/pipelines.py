# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from urllib.parse import urljoin
from datetime import datetime
import unicodedata
import dateparser
import regex
import re

from my_lib.mongodb_operator import MongodbOperator

class JobparserPipeline:
    def __init__(self):
        self.m_utils = MongodbOperator()


    def process_item(self, item, spider):
        item['position'] = self.process_position(item['position'])

        item['salary_info'] = self.process_salary(item['salary_info']) if item['salary_info'] else None

        item['published_at'] = self.process_date(spider.name, item['published_at']) if item['published_at'] else None

        item['location_info'] = self.process_location_info(region=item['region'],
                                                           metrostation=item['metrostation'],
                                                           address=item['address'])

        item['employer_info'] = self.process_employer_info(spider.name,
                                                           website_url=item['website_url'],
                                                           employer=item['employer'],
                                                           employer_url=item['employer_url'])

        item['key_skills'] = self.process_skills(item['key_skills']) if item['key_skills'] else None
        item['is_remote'] = True if item['is_remote'] else False

        del item['employer'], item['employer_url'], item['region'], item['metrostation'], item['address']

        self.m_utils.save_documents('vacancies_scrapy', spider.name, [dict(item)])
        return item


    def process_salary(self, salary_info: str):
        salary_info = re.sub(r'(\d)\s(\d)',
                             r'\1\2',
                             re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', ''.join(salary_info)).strip()))

        pattern_1 = regex.compile(r'(?:з/п\sне\sуказана)|(?:По\sдоговорённости)')

        pattern_2 = regex.compile('(?:(?P<min_salary>\d+)\s?[—–-]\s?)?'
                               '(?P<max_salary>\d+)\s'
                               '(?P<currency>[a-zа-яё]+|\p{Sc})\.?\s?'
                               '(?:(?P<net>на\sруки)|(?P<gross>до\sвычета\sналогов))?\s?'
                               '(?:/\s?(?P<payment_frequency>\w.*))?',
                               regex.I | regex.X)

        pattern_3 = regex.compile('(?:от\s(?P<min_salary>\d+)\s)?'
                               '(?:до\s(?P<max_salary>\d+)\s)?'
                               '(?P<currency>([a-zа-яё]+|\p{Sc}))\.?\s?'
                               '(?:(?P<net>на\sруки)|(?P<gross>до\sвычета\sналогов))?\s?'
                               '(?:/\s?(?P<payment_frequency>\w.*))?',
                               regex.I | regex.X)


        patterns = [pattern_1, pattern_2, pattern_3]
        for i, pattern in enumerate(patterns):
            match = pattern.fullmatch(salary_info)
            if match:
                salary_info = match.groupdict()
                break
            if i == len(patterns) - 1:
                raise Exception(f"Unknown pattern.\nSalary info:{salary_info}")

        res = {
            'min_salary': salary_info.get('min_salary'),
            'max_salary': salary_info.get('max_salary'),
            'currency': salary_info.get('currency'),
            'tax': 'net' if salary_info.get('net') else 'gross' if salary_info.get('gross') else None,
            'payment_frequency': salary_info.get('payment_frequency')
        }
        if not any(res.values()):
            return None
        return res


    def process_date(self, spider_name: str, published_at: str):
        if spider_name == 'hh':
            published_at = ''.join(published_at)
        published_at = unicodedata.normalize('NFKC', published_at).strip().lower()

        if spider_name == 'hh':
            # Usually pattern of published_at at hh.ru is 'Vacansy was published at <published_at_str> in <location>' or just '<published_at_str>'
            pattern = re.compile(r'[a-zа-яё\s]*(?P<published_at_str>\d{1,2}\s[a-zа-яё]+\s\d{4}).*')
            day_, month_, year_ = pattern.fullmatch(published_at)['published_at_str'].split(' ')
            published_at = f'{int(day_):02d} {month_.lower()} {year_}'
        # For spider_name == 'superjob' there is no pre-treatment required

        date_formats = ['%d %B %Y %H:%M', '%d %B', '%d %B %Y']
        published_at_dt = dateparser.parse(published_at, date_formats=date_formats, languages=['ru'])
        if not published_at_dt:
            raise Exception("Unknown date format")
        return datetime.strftime(published_at_dt, '%Y-%m-%d')


    def process_location_info(self, **kwargs):
        region = kwargs.get('region')
        metrostation = kwargs.get('metrostation')
        address = kwargs.get('address')
        metrostation = list(set(metrostation)) if metrostation else None
        address = re.sub(r'(,\s*)+', r', ', ''.join(address)) if address else None

        return dict(region=region, metrostation=metrostation, address=address)


    def process_employer_info(self, spider_name, **kwargs):
        website_url = kwargs.get('website_url')
        employer = kwargs.get('employer')
        employer_url = kwargs.get('employer_url')
        if employer:
            if spider_name == 'hh':
                employer = ''.join(employer)
            employer = unicodedata.normalize('NFKC', employer).strip()
        if employer_url:
            employer_url = urljoin(website_url, employer_url) if employer_url.startswith('/') else employer_url

        return dict(employer=employer, employer_url=employer_url)


    def process_position(self, position):
        return unicodedata.normalize('NFKC', ''.join(position)).strip()

    def process_skills(self, key_skills):
        return [unicodedata.normalize('NFKC', skill).strip() for skill in key_skills]
