# Если нет файла с куками то предусмотреть пропуск одной попытки в методе login (сразу вызов ошибки)
from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient('localhost', 27017)
    mongobase = client.insta

    username = 'soh.y4w00'

    # У пользователя могли поменяться картинка, имя, но id остается.
    # Если правилами Instagram предусмотрены только уникальные имена, то len(user_id) = 1
    user_followers = mongobase['followers'] \
        .aggregate([
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': 'user_id',
                    'as': 'user_info'
                }
            },
            {
                '$unwind': '$user_info'
            },
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'follower_id',
                    'foreignField': 'user_id',
                    'as': 'follower_info'
                }
            },
            {
                '$unwind': '$follower_info'
            },
            {'$match': {'user_info.username': username}},
            {'$project': {'_id': 0, 'follower_info': {'username': 1}}}
        ])

    user_followers_list = set([document['follower_info']['username'] for document in user_followers])
    print(user_followers_list)

    user_followings = mongobase['followers'] \
        .aggregate([
        {
            '$lookup': {
                'from': 'users',
                'localField': 'user_id',
                'foreignField': 'user_id',
                'as': 'user_info'
            }
        },
        {
            '$unwind': '$user_info'
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'follower_id',
                'foreignField': 'user_id',
                'as': 'follower_info'
            }
        },
        {
            '$unwind': '$follower_info'
        },
        {'$match': {'follower_info.username': username}},
        {'$project': {'_id': 0, 'user_info': {'username': 1}}}
    ])

    user_followings_list = set([document['user_info']['username'] for document in user_followings])
    print(user_followings_list)

    # Проверка (можно при парсинге данных оставить только данного пользователя чтобы ускорить процесс)
    print(len(user_followings_list))
    print(len(user_followers_list))

