"""
Python script to run data collection from hh.ru website.
"""
from dotenv import dotenv_values

from my_lib.parsers.html.hh_parser import HHParser

if __name__ == '__main__':
    config = dotenv_values('.env')
    user_agent = config.get('USER_AGENT')

    search_params = [
        ('area', 1),
        ('employment', 'full'),
        ('experience', 'between1And3'),
        ('schedule', 'remote'),
        ('search_field', 'name'),
        ('search_field', 'company_name'),
        ('search_field', 'description'),
        ('text', 'data engineer'),
        ('items_on_page', 20)
    ]

    hh_parser = HHParser(user_agent)
    hh_parser.parse_data(search_params, limit=5)


    search_params = list(map(lambda x: x if x[0] != 'experience' else (x[0], 'between3And6'), search_params))

    hh_parser = HHParser(user_agent)
    hh_parser.parse_data(search_params, limit=5)
