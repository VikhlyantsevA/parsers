"""
Script to login to mail.ru, parse data from upcoming emails and save it into database.
"""
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver

from dotenv import dotenv_values
from pprint import pprint
import string
import time
import os
import re

from my_lib.mongodb_operator import MongodbOperator



def element_exists(self, by, value):
    try:
        self.find_element(by, value)
    except NoSuchElementException:
        return False
    return True

WebDriver.element_exists = element_exists

if __name__ == '__main__':
    config = dotenv_values('.env')
    login = config.get("MAIL_LOGIN")
    password = config.get("MAIL_PASSWORD")

    m_utils = MongodbOperator()

    options = Options()
    options.add_argument("start-maximized")

    driver_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'drivers', 'chromedriver'))
    service = Service(driver_dir)
    with webdriver.Chrome(service=service, options=options) as driver:
        driver.implicitly_wait(20)

        driver.get("https://mail.ru/")
        driver.find_element(By.XPATH, "//button[contains(@class, 'resplash-btn_primary')]").click()

        iframe = driver.find_element(By.XPATH, "//iframe[contains(@class, 'iframe')]")
        driver.switch_to.frame(iframe)

        username_fieled = driver.find_element(By.NAME, "username")
        username_fieled.send_keys(login)
        username_fieled.send_keys(Keys.ENTER)


        password_fieled = driver.find_element(By.NAME, "password")
        password_fieled.send_keys(password)
        password_fieled.send_keys(Keys.ENTER)

        security_checkup_xpath = "//div[@data-test-id='security-checkup']//div[@data-test-id='expansion-panel-cross']"
        if driver.element_exists(By.XPATH, security_checkup_xpath):
            driver.find_element(By.XPATH, security_checkup_xpath).click()

        all_mail_links = set()
        prev_last_mail_link = None
        limit = 5 # mails parsing breaker (number of page to stop at). Set `limit = None` for non-stop parsing.
        page = 1
        print('Start mails links collection (scrolling)')

        while True:
            print(f'Page {page}')
            time.sleep(1)
            mails = driver.find_elements(By.XPATH, "//a[contains(@class,'llc')]")
            mail_links = [mail.get_attribute('href') for mail in mails]
            curr_last_mail_link = mail_links[-1]
            # Check if the oldest email was reached or not.
            if curr_last_mail_link == prev_last_mail_link:
                break

            all_mail_links.update(mail_links)

            actions = ActionChains(driver)
            actions.move_to_element(mails[-1])
            actions.perform()

            prev_last_mail_link = curr_last_mail_link
            page += 1

            if limit:
                if page > limit:
                    print('Mails scrolling was completed')
                    break

        time.sleep(10)
        # Mails opening and data parsing
        print('Start mails data parsing')
        for i, mail_link in enumerate(all_mail_links, start=1):
            print(f'Mail {i}')
            driver.get(mail_link)
            sender = driver.find_element(By.XPATH, "//div[@class='letter__author']//span[contains(@class, 'letter-contact')]").text
            sender_email = driver.find_element(By.XPATH, "//div[@class='letter__author']//span[contains(@class, 'letter-contact')]").get_attribute(
                "title")
            sent_at = driver.find_element(By.XPATH, "//div[@class='letter__date']").text
            mail_topic = driver.find_element(By.XPATH, "//div[@class='thread__header']//*[@class='thread-subject']").text
            mail_content = driver.find_element(By.XPATH, "//div[@class ='letter__body']").get_attribute("innerText")
            if mail_content:
                mail_content = re.sub(r'([{}])+'.format(string.whitespace), r'\1',
                       re.sub(r'(\xa0|\u200b)', '', mail_content)) \
                    .strip(string.whitespace).replace('\t', ' ')

            mail_data = [{
                'sender': sender,
                'sender_email': sender_email,
                'sent_at': sent_at,
                'mail_topic': mail_topic,
                'mail_content': mail_content
            }]

            pprint(mail_data)
            print('Start saving data to database')
            m_utils.save_documents('mails', 'mail_ru', mail_data)
            print('Writing to database was successfully completed')

        m_utils.show_documents('mails', 'mail_ru')
