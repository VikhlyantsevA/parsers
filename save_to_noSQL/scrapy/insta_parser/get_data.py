"""
Python script to get user followers info.
"""
from pymongo import MongoClient
from pprint import pprint

from my_lib.utils import hash_struct

if __name__ == '__main__':
    client = MongoClient('localhost', 27017)
    mongobase = client.insta

    # Find friends of user with `username`
    username = 'mycatsardor'

    # Make join of `users` info and `users_connections` and get `subscriber_info` of user with `username`.
    user_followers = mongobase['users_connections'] \
        .aggregate([{'$lookup': {'from': 'users',
                                 'localField': 'user_id',
                                 'foreignField': 'user_id',
                                 'as': 'user_info'}},
            {'$unwind': '$user_info'},
            {"$addFields": {'subscriber_id': {"$toString": "$subscriber_id"}}},
            {'$lookup': {'from': 'users',
                         'localField': 'subscriber_id',
                         'foreignField': 'user_id',
                         'as': 'subscriber_info'}},
            {'$unwind': '$subscriber_info'},
            {'$match': {'user_info.username': username}},
            {'$project': {'_id': 0, 'subscriber_info': 1}}
        ])

    # Make hash of target subscriber_info and get only unique docs.
    # Duplicates may appear because different profile pictures links may be gotten for one user.
    # So that there will be 2 or more documents for one user.
    # PS: Make document creation time to filter the newest one
    user_followers_info = dict()
    for doc in user_followers:
        hash = hash_struct(dict(doc['subscriber_info']))
        user_followers_info[hash] = doc['subscriber_info']

    pprint(list(user_followers_info.values()))
