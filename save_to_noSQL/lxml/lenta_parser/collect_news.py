"""
1. Написать приложение, которое собирает основные новости с сайта на выбор:
   - news.mail.ru;
   - lenta.ru;
   - yandex-новости.

   Структура данных должна содержать:
   - название источника;
   - наименование новости;
   - ссылку на новость;
   - дату публикации.

   > Для парсинга использовать XPath
2. Сложить собранные новости в БД
"""
from urllib.parse import urljoin, urlparse
from dotenv import dotenv_values
from datetime import datetime
from lxml import html
import requests
import locale
import re

from my_lib.mongodb_operator import MongodbOperator


if __name__ == '__main__':
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    m_utils = MongodbOperator()
    config = dotenv_values('.env')
    user_agent = config.get('USER_AGENT')

    base_url = 'https://lenta.ru/'
    headers = {'User-Agent': user_agent}
    news_response = requests.get(base_url, headers=headers)
    news_dom = html.document_fromstring(news_response.content, parser=html.HTMLParser(encoding='utf-8'))

    news_list = list()
    topnews_cards = news_dom.xpath('//div[contains(@class, "topnews")]//a[contains(@class, "card")]')
    for news_card in topnews_cards:
        news_url_raw = news_card.xpath('./@href')[0]
        news_url = urljoin(base_url, news_url_raw) if news_url_raw.startswith('/') else news_url_raw

        parsed_url = urlparse(news_url)
        hostname = parsed_url.hostname
        protocol = parsed_url.scheme
        source = f'{protocol}://{hostname}/'

        title = news_card.xpath('.//*[contains(@class, "title")]/text()')[0]

        date_info = news_card.xpath('.//time[contains(@class, "card")]/text()')
        created_at = None
        if date_info:
            date_info = date_info[0].replace(' ', '').split(',')
            date_ = datetime.strptime(date_info[1], '%d%B%Y') if len(date_info) > 1 else datetime.now().date()
            time_ = datetime.strptime(date_info[0], '%H:%M').time()
            created_at = datetime.strftime(datetime.combine(date_, time_), '%Y-%m-%d %H:%M')

        article_response = requests.get(news_url, headers=headers)
        article_dom = html.document_fromstring(article_response.content, parser=html.HTMLParser(encoding='utf-8'))
        if hostname == 'lenta.ru':
            article_text_xpath = '//div[contains(@class, "topic-page") and contains(@class, "_news")]//div[contains(@class, "topic-body__content")]//text()'
        elif hostname == 'moslenta.ru':
            article_text_xpath = '//article[not(contains(@class, "disabled"))]//div[@data-qa="topic-card"]//div[contains(@class, "text")]//text()'
        else:
            raise Exception(f'Unknown source: {source}')
        article_text = re.sub(r'\s+', ' ', ' '.join(article_dom.xpath(article_text_xpath)))

        data = {
            'source': source,
            'news_url': news_url,
            'title': title,
            'created_at': created_at,
            'article_text': article_text
        }

        news_list.append(data)

    m_utils.save_documents('lenta_news', 'topnews', news_list)

    # Print all written to lenta_news.topnews  documents
    m_utils.show_documents('lenta_news', 'topnews')