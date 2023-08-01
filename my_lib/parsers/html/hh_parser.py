from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup as bs
import re

from my_lib.parsers.html.website_parser import WebsiteParser
from my_lib.mongodb_operator import MongodbOperator

class HHParser(WebsiteParser):
    """
    A class to get vacancies data from hh.ru website.
    ...

    Attributes
    ----------
    user_agent : str
        user-agent field fro browser for request headers.
    base_url : str
        Website base url. Default = 'https://hh.ru'
    endpoint : str
        Vacancies search page endpoint. Default = '/search/vacancy'

    Methods
    -------
    parse_data(search_params, limit, **kwargs):
        Get vacancy info from hh.ru according to search request.
        search_params : List[Tuple]
            Search query parameters (filters).
        limit : int
            Number of pages for parsing to stop at.
    """
    def __init__(self,
                 user_agent: str,
                 base_url: str = 'https://hh.ru',
                 endpoint: str = '/search/vacancy'):
        self._headers = {'User-Agent': user_agent}
        self._base_url = base_url
        self._endpoint = endpoint
        self.m_utils = MongodbOperator()

    def parse_data(self, search_params: list, limit: int = None, **kwargs):
        max_retries = kwargs.get('max_retries', 8)
        headers = kwargs.get('headers', self._headers)
        url = f"{urljoin(self._base_url, self._endpoint)}?{urlencode(search_params)}"
        limit = limit if limit else None
        page = 1
        vacancy_num = 1
        print(f'Start new parsing. Getting data from: {url}')
        while True:
            print(f'\nPage {page}')
            page_res = list()
            search_page_resp = self.get_response(url=url, max_retries=max_retries, headers=headers)

            search_page_dom = bs(search_page_resp.text, 'html.parser')
            resume_windows = search_page_dom.find_all('div', {'class': 'vacancy-serp-item__layout'})
            for resume in resume_windows:
                title = resume.find('a', {'data-qa': 'serp-item__title'})
                if not title:
                    continue
                position = title.getText()
                resume_url = title['href']
                employer_info = resume.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
                employer = employer_info.getText().replace('\xa0', ' ')
                employer_url = urljoin(self._base_url, employer_info['href'])
                experience = resume.find('div', {'data-qa': 'vacancy-serp__vacancy-work-experience'}).getText()

                region = resume.find('div', {'data-qa': 'vacancy-serp__vacancy-address'})\
                    .find(text=True, recursive=False)\
                    .replace('\xa0', ' ')

                salary_info = resume.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
                if salary_info:
                    salary_info_text = salary_info.getText().replace('\u202f', '').replace(' ', '')
                    pattern_1 = re.compile('(?:(?P<min_salary>\d+)–)?(?P<max_salary>\d+)(?P<currency>\D+)')
                    pattern_2 = re.compile('(?:от(?P<min_salary>\d+))?(?:до(?P<max_salary>\d+))?(?P<currency>\D+)',
                                           re.I | re.X)
                    patterns = [pattern_1, pattern_2]
                    for i, pattern in enumerate(patterns):
                        match = pattern.match(salary_info_text)
                        if match:
                            salary_info = {k: (v if not v else float(v) if v.isnumeric() else v.lower()) for k, v in
                                           match.groupdict().items()}
                            break
                        elif not match and i == len(patterns) - 1:
                            raise Exception(f"There is a new pattern.\nSalaries info (text):{salary_info_text}")



                resume_page_resp = self.get_response(url=resume_url, max_retries=max_retries, headers=headers)
                resume_page_dom = bs(resume_page_resp.text, 'html.parser')
                location_info = resume_page_dom.find('span', {'data-qa': 'vacancy-view-raw-address'})
                metrostation = None
                address = None
                if location_info:
                    metrostation = list(set([el.getText() for el in location_info.find_all('span', {'class': 'metro-station'})]))
                    metrostation = metrostation if metrostation else None
                    address = re.sub(r'(,\s*)+', r', ', ''.join(location_info.find_all(text=True, recursive=False)))

                key_skills_info = resume_page_dom.find('div', {'class': 'bloko-tag-list'})
                key_skills = key_skills_info.getText(separator=',').split(',') if key_skills_info else None


                page_res.append({
                    'position': position,
                    'key_skills': key_skills,
                    'region': region,
                    'metrostation': metrostation,
                    'address': address,
                    'salary_info': salary_info,
                    'experience': experience,
                    'resume_url': resume_url,
                    'employer': employer,
                    'employer_url': employer_url,
                    'search_url': url
                })

                print(f'{vacancy_num} vacancy was parsed.')

                vacancy_num += 1

            print(f'Saving data from {page} page.')
            self.m_utils.save_documents('vacancies', 'hh', page_res)
            if limit:
                if page >= limit:
                    break

            next_page = search_page_dom.find('a', {'class': 'bloko-button', 'data-qa': 'pager-next'})
            if not next_page:
                break

            url = urljoin(self._base_url, next_page['href'])
            page += 1
        print('<<<<<<<<<< Finished >>>>>>>>>>', end='\n\n\n')
