from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from scrapy.exceptions import CloseSpider
from scrapy.http import HtmlResponse
import scrapy
from urllib.parse import urlencode
from csv import DictReader
import configparser
import random
import time
import re
import os

from instaparser.settings import INSTA_CONFIG_PATH, PROJECT_ROOT
from instaparser.items import InstaparserItem


def element_exists(self, by, value):
    try:
        self.find_element(by, value)
    except NoSuchElementException:
        return False
    return True

WebDriver.element_exists = element_exists


class InstaSpider(scrapy.Spider):
    name = 'insta'
    allowed_domains = ['instagram.com']

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.start_urls = ['https://www.instagram.com/']
        self.to_parse_users = kwargs.get('users')

        self.user_info_api_link = 'https://www.instagram.com/api/v1/users/web_profile_info/?{user_info_attrs}'
        self.following_api_link = 'https://www.instagram.com/api/v1/friendships/{user_id}/following/?{following_attrs}'
        self.followers_api_link = 'https://www.instagram.com/api/v1/friendships/{user_id}/followers/?{followers_attrs}'


    def start_requests(self):
        if not self.start_urls and hasattr(self, 'start_url'):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)")
        for start_url in self.start_urls:
            yield scrapy.Request(
                start_url,
                cookies=self.login(start_url),
                dont_filter=True
            )


    def login(self, start_url):
        options = Options()
        options.add_argument("start-maximized")
        service = Service(os.path.join(PROJECT_ROOT, "drivers", "chromedriver"))

        with webdriver.Chrome(service=service, options=options) as driver:
            driver.implicitly_wait(1)
            wait = WebDriverWait(driver, 16, poll_frequency=2)

            driver.get(start_url)
            # Accept cookies using
            cookie_button_xpath = "//div[@role='dialog']//button[text()='Allow all cookies']"
            if driver.element_exists(By.XPATH, cookie_button_xpath):
                driver.find_element(By.XPATH, cookie_button_xpath).click()
                wait.until(EC.invisibility_of_element((By.XPATH, cookie_button_xpath)))

            config = configparser.ConfigParser()
            config.read(INSTA_CONFIG_PATH)
            login_info = config['login_info']

            # Try to login without cookies first. If fail login with existing one only
            login_attempts = 2
            login_page = driver.current_url

            for i in range(1, login_attempts + 1):
                if i == login_attempts:
                    cookies_filepath = os.path.join(PROJECT_ROOT, 'insta_cookies.csv')
                    if not os.path.exists(cookies_filepath):
                        raise CloseSpider("There is no cookies file. Logging failed. Try again later.")
                    # If login was failed with given cookies, then try to reuse existing cookies.
                    # After that get and exchange csrf-token.
                    new_cookies = [*self.get_cookies_values('insta_cookies.csv'), self.get_csrftoken(driver)]
                    driver.delete_all_cookies()
                    for cookie in new_cookies:
                        driver.add_cookie(cookie)

                wait.until(EC.element_to_be_clickable((By.XPATH, '//form[@id="loginForm"]//input[@name="username"]'))) \
                    .send_keys(login_info.get('USERNAME'))

                wait.until(EC.element_to_be_clickable((By.XPATH, '//form[@id="loginForm"]//input[@name="password"]'))) \
                    .send_keys(login_info.get('PASSWORD'))

                # Delay before authentication (to prevent blocking)
                self.random_sleep(1.0, 5.0)

                wait.until(EC.element_to_be_clickable((By.XPATH, "//form[@id='loginForm']//button[@type='submit']"))).click()

                try:
                    wait.until_not(EC.url_to_be(login_page))
                    break
                except TimeoutException:
                    if i == login_attempts:
                        raise CloseSpider("Logging failed. Try again later.")
                    print("TimeoutException. Can't login. Trying again with verified cookies.")
                    driver.refresh()

            # Push the button of saving data push-notification
            save_login_xpath = "//button[text()='Save Info']"
            if driver.element_exists(By.XPATH, save_login_xpath):
                wait.until(EC.element_to_be_clickable((By.XPATH, save_login_xpath))).click()

            # Push the button of "show/don't show notifications" push-notification
            not_show_notifications_xpath = "//div[@role='dialog']//button[text()='Not Now']"
            if driver.element_exists(By.XPATH, not_show_notifications_xpath):
                wait.until(EC.element_to_be_clickable((By.XPATH, not_show_notifications_xpath))).click()

            return driver.get_cookies().copy()


    def parse(self, response: HtmlResponse):
        cookies = response.request.cookies.copy()
        for username in self.to_parse_users:
            user_info_attrs = {'username': username}
            user_info_link = self.user_info_api_link.format(user_info_attrs=urlencode(user_info_attrs))
            yield response.follow(user_info_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_info,
                                  cookies=cookies,
                                  cb_kwargs={'username': username,
                                             'cookies': cookies,
                                             'recursive': True})


    def parse_user_info(self, response: HtmlResponse, **kwargs):
        j_body = response.json()
        user_id = j_body.get('data').get('user').get('id')
        username = kwargs.get('username')
        full_name = j_body.get('data').get('user').get('full_name')
        profile_pic_url_hd = j_body.get('data').get('user').get('profile_pic_url_hd')
        user_info = {'user_id': user_id,
                     'username': username,
                     'full_name': full_name,
                     'profile_pic_url_hd': profile_pic_url_hd}

        yield InstaparserItem(user_info=user_info)

        if kwargs.get('recursive'):
            following_attrs = {'count': 12}
            user_following_link = self.following_api_link.format(user_id=user_id, following_attrs=urlencode(following_attrs))

            yield response.follow(user_following_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_following,
                                  cookies=kwargs['cookies'].copy(),
                                  cb_kwargs={'user_id': user_id,
                                             'following_attrs': following_attrs.copy(),
                                             **kwargs.copy()})

            followers_attrs = {'count': 12, 'search_surface': 'follow_list_page'}
            user_followers_link = self.followers_api_link.format(user_id=user_id, followers_attrs=urlencode(followers_attrs))

            yield response.follow(user_followers_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_followers,
                                  cookies=kwargs['cookies'].copy(),
                                  cb_kwargs={'user_id': user_id,
                                             'followers_attrs': followers_attrs.copy(),
                                             **kwargs.copy()})


    def parse_user_following(self, response: HtmlResponse, **kwargs):
        j_body = response.json()
        for user in j_body.get('users'):
            username = user.get('username')
            user_info_attrs = {'username': username}
            user_info_link = self.user_info_api_link.format(user_info_attrs=urlencode(user_info_attrs))
            yield response.follow(user_info_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_info,
                                  cookies=kwargs['cookies'].copy(),
                                  cb_kwargs={'username': username,
                                             'cookies': kwargs['cookies'].copy(),
                                             'recursive': False})
        following_id = [user.get('pk') for user in j_body.get('users')]
        next_max_id = j_body.get('next_max_id')
        if next_max_id:
            new_kwargs = kwargs.copy()
            new_kwargs['following_attrs']['max_id'] = next_max_id
            user_following_link = self.following_api_link \
                .format(user_id=kwargs['user_id'], following_attrs=urlencode(new_kwargs['following_attrs']))

            yield response.follow(user_following_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_following,
                                  cookies=new_kwargs['cookies'],
                                  cb_kwargs=new_kwargs)

        yield InstaparserItem(user_id=kwargs['user_id'],
                              following_id=following_id)


    def parse_user_followers(self, response: HtmlResponse, **kwargs):
        j_body = response.json()
        for user in j_body.get('users'):
            username = user.get('username')
            user_info_attrs = {'username': username}
            user_info_link = self.user_info_api_link.format(user_info_attrs=urlencode(user_info_attrs))
            yield response.follow(user_info_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_info,
                                  cookies=kwargs['cookies'].copy(),
                                  cb_kwargs={'username': username,
                                             'cookies': kwargs['cookies'].copy(),
                                             'recursive': False})
        followers_id = [user.get('pk') for user in j_body.get('users')]
        next_max_id = j_body.get('next_max_id')
        if next_max_id:
            new_kwargs = kwargs.copy()
            new_kwargs['followers_attrs']['max_id'] = next_max_id
            user_followers_link = self.followers_api_link \
                .format(user_id=kwargs['user_id'], followers_attrs=urlencode(new_kwargs['followers_attrs']))

            yield response.follow(user_followers_link,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  callback=self.parse_user_followers,
                                  cookies=new_kwargs['cookies'],
                                  cb_kwargs=new_kwargs)

        yield InstaparserItem(user_id=kwargs['user_id'],
                              followers_id=followers_id)


    def get_cookies_values(self, file):
        with open(file, encoding='utf-8-sig') as f:
            dict_reader = DictReader(f)
            list_of_dicts = list(dict_reader)
        return list_of_dicts


    def get_csrftoken(self, driver):
        page_reloads = 2
        for i in range(page_reloads):
            csrf_token = driver.get_cookie('csrftoken')
            if csrf_token:
                return csrf_token.copy()
            if i == page_reloads - 1:
                # Get csrf-token from html-code of webpage
                csrf_token = self.get_csrftoken_from_html(driver.page_source)
                if not csrf_token:
                    raise CloseSpider("There is no csrf token found. Can't login.")
            else:
                # Sometimes webpage refresh is required to get csrf-token
                driver.refresh()
        return csrf_token


    def get_csrftoken_from_html(self, text):
        '''Get csrf-token for authentication'''
        csrf_token_value = re.search(r'"csrf_token"\s*:\s*"(?P<token>\w+)"', text).group('token')
        return {'name': 'csrftoken', 'value': csrf_token_value, 'domain': '.instagram.com'}


    def random_sleep(self, min_time: float, max_time: float):
        '''Generates float delay value from range'''
        precision_rev = 10 ** max(len(str(min_time).split('.')[1]), len(str(max_time).split('.')[1]))
        time.sleep(random.randint(min_time * precision_rev, max_time * precision_rev) / precision_rev)
