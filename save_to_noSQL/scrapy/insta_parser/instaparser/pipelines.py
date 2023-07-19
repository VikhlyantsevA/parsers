# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter
# from pymongo.errors import DuplicateKeyError
# from pymongo import MongoClient

from my_lib.mongodb_operator import MongodbOperator

class InstaparserPipeline:
    def __init__(self):
        self.m_utils = MongodbOperator()
        # client = MongoClient('localhost', 27017)
        # self.mongobase = client.insta
        # self.followers_coll = self.mongobase['followers']
        # self.users_coll = self.mongobase['users']

    def process_item(self, item, spider):
        print()
        # Запись инфо о пользователях в users_coll
        item_dict = dict(item)
        user_info = item_dict.get('user_info')
        followers_info = item_dict.get('followers_info', [])
        following_info = item_dict.get('following_info', [])
        self.m_utils.save_documents('insta', 'users', [user_info, *followers_info, *following_info])
        # self.write_to_db(self.users_coll, user_info, *followers_info, *following_info)

        # Запись инфо о подписчиках пользователя в followers_coll
        if followers_info:
            user_links = [{'user_id': user_info['user_id'], 'follower_id': str(follower['user_id'])}
                          for follower in followers_info]
            self.m_utils.save_documents('insta', 'followers', user_links)
            # self.write_to_db(self.followers_coll, *user_links)

        if following_info:
            user_links = [{'user_id': str(following['user_id']), 'follower_id': user_info['user_id']}
                          for following in following_info]
            self.m_utils.save_documents('insta', 'followers', user_links)
            # self.write_to_db(self.followers_coll, *user_links)
        return item

    # def write_to_db(self, collection, *args):
    #     data = args
    #     for document in data:
    #         if not document:
    #             continue
    #
    #         document['_id'] = hash_struct(document)
    #         try:
    #             collection.insert_one(document)
    #         except DuplicateKeyError:
    #             print(f"Document with key {document['_id']} already exists.")
