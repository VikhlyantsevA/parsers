"""
Python script to show vacancies with salary more than given value.
"""
from pymongo import MongoClient
from pprint import pprint

if __name__ == '__main__':
    client = MongoClient('localhost', 27017)
    db = client['vacancies']
    hh = db.hh

    salary_wanted = 100000.0
    currency = '₽'


    filters = {
        'salary_info.currency': currency,
        '$or': [
            {'salary_info.min_salary': None, 'salary_info.max_salary': {'$gte': salary_wanted}},
            {'salary_info.min_salary': {'$lte': salary_wanted}, 'salary_info.max_salary': None},
            {'salary_info.min_salary': {'$lte': salary_wanted}, 'salary_info.max_salary': {'$gte': salary_wanted}}
        ]
    }

    for document in hh.find(filters):
        pprint(document, indent=2)
