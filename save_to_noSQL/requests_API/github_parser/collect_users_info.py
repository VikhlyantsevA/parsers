"""
Python script to parse data from API and save it to MongoDB database.
Full users info data is saved to collection users_info collection.
Selective users repo info is saved into users_repos collection.
"""
import os

from my_lib.parsers.api.github_parser import GithubApiParser
from my_lib.mongodb_operator import MongodbOperator


if __name__ == '__main__':
    env_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
    gh_parser = GithubApiParser(env_file=env_file)
    mongo = MongodbOperator()
    # Pagination breaker
    breaker = 2
    params = {
        'per_page': 100,
        'since': 0
    }

    page = 1
    while True:
        print(f'Page {page} of users_info.')
        users_info = gh_parser.get_response('/users', params=params)
        if not users_info:
            print('No info on this page. Stop flicking up.')
            break

        print(f'Start getting users_repos info.')
        for i, user_info in enumerate(users_info, 1):
            print(f'Get data about user: {i} of {len(users_info)}.')
            # Writing to MongoDB to collection users_info
            mongo.save_documents('github_api', 'users_info', [user_info])

            username = user_info['login']
            repos_info_all = gh_parser.get_response(f'/users/{username}/repos')

            repos_info_cut = [{'allow_forking': repo.get('allow_forking'),
                               'html_url': repo.get('html_url'),
                               'language': repo.get('language'),
                               'private': repo.get('private'),
                               'pushed_at': repo.get('pushed_at')} for repo in repos_info_all]
            repos_info = {
                'login': username,
                'repos_num': len(repos_info_cut),
                'repos_info': repos_info_cut
            }
            # Writing to MongoDB to collection users_repos
            mongo.save_documents('github_api', 'users_repos', [repos_info])
        params['since'] = max(map(lambda x: x.get('id'), users_info))
        page += 1
        if breaker:
            if page > breaker:
                print('Breaker limit exceeded. Stop flicking up.')
                break
