from pprint import pprint
import argparse
import json
import os

from my_lib.parsers.api.github_parser import GithubApiParser


def get_abs_path(path_):
    if not path_:
        return None
    return os.path.expanduser(path_) if path_.startswith('~') else os.path.abspath(path_)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='''
        CLI. Take users names (login) as arguments, print their repositories info or save it into json-file
        '''
    )

    arg_parser.add_argument('-env_file',
                            type=str,
                            required=True,
                            help='Path to env-file with credentials.')

    arg_parser.add_argument('-path',
                            type=str,
                            required=False,
                            help='Path to folder for result saving. If hasn\'t not choosen, then print to screen used.')

    arg_parser.add_argument('usernames',
                            type=str,
                            nargs='+',
                            help='Names of users to show info from.')

    args = arg_parser.parse_args()
    env_file = get_abs_path(args.env_file)
    path_to_save = get_abs_path(args.path)
    usernames = args.usernames

    gh_parser = GithubApiParser(env_file=env_file)

    if not os.path.exists(path_to_save):
        os.mkdir(path_to_save)

    try:
        fw = None
        if path_to_save:
            fw = open(os.path.join(path_to_save, 'github_users_repos.json'), 'w', encoding='utf-8')
        for username in usernames:
            repos_info = gh_parser.get_response(f'/users/{username}/repos')
            repo_names = [repo['html_url'] for repo in repos_info]
            output = {
                'login': username,
                'repos_num': len(repo_names),
                'repos_urls': repo_names
            }
            if path_to_save:
                json.dump(output, fw, ensure_ascii=False, indent=2)
            else:
                pprint(output)
                print()
    except Exception as ex:
        print(ex)
    finally:
        if fw:
            fw.close()
