# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from itemadapter import ItemAdapter

from my_lib.mongodb_operator import MongodbOperator

class InstaparserPipeline:
    def __init__(self):
        self.m_utils = MongodbOperator()

    def process_item(self, item, spider):
        if item.get('user_info'):
            self.m_utils.save_documents('insta', 'users', [item.get('user_info')])

        # Extract followers_id and following_id and making pairs with user_id
        if item.get('followers_id'):
            users_connections = [{'user_id': item.get('user_id'), 'subscriber_id': follower_id}
                                for follower_id in item.get('followers_id')]
            self.m_utils.save_documents('insta', 'users_connections', users_connections)

        if item.get('following_id'):
            users_connections = [{'user_id': following_id, 'follower_id': item.get('user_id')}
                          for following_id in item.get('following_id')]
            self.m_utils.save_documents('insta', 'followers', users_connections)
        return item
