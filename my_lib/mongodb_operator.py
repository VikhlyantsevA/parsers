from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient
from typing import List, Dict
from pprint import pprint

from my_lib.utils import hash_struct


class MongodbOperator:
    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)

    def save_documents(self, database, collection, data: List[Dict]):
        db = self.client[database]
        collection = db[collection]
        for document in data:
            document_id = hash_struct(document)
            try:
                collection.insert_one({'_id': document_id, **document})
            except DuplicateKeyError:
                print(f'Document with key {document_id} already exists.')

    def show_documents(self, database, collection, filters: dict = {}):
        db = self.client[database]
        collection = db[collection]
        for document in collection.find(filters):
            pprint(document, indent=2)
