"""
This file focused on DB functions

TODO implement noSQL injection avoidance
Searching keyword: pymongo how to sanitize the input
Useful topic: https://stackoverflow.com/questions/14672046/pymongo-orm-injection-sanitizing-input
"""

import configparser
import logging as log
import pymongo
from pymongo import MongoClient

import json  # temp

# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
cluster_link = config['MongoDB']['cluster_link']

cluster = MongoClient(cluster_link)  # cluster link taken from config.ini
db = cluster["relax_bot_db"]
collection = db["user_settings"]
idea_collection = db["user_ideas"]
msg_collection = db["messages"]

# logging settings
log.basicConfig(filename='debug.log',
                format='%(filename)s -- %(asctime)s -- %(message)s',
                level=log.INFO,
                datefmt='%m/%d/%Y %I:%M:%S %p'
                )


def db_id_counter():
    last_db_post = collection.find_one(
        {'$query': {}, '$orderby': {'_id': -1}})  # find post with highest id in DB to increase counter
    last_db_id = last_db_post['_id']  # assign highes id to variable
    print(f'last_db_id: {last_db_id}')
    log.info(f'last_db_id: {last_db_id}')
    db_id_generator = last_db_id + 1  # increasing counter
    return db_id_generator  # we need this to use generator number in ofther functions


def newkeyword(user_newkeyword, user_id):
    db_id_generator = db_id_counter()  # returning new generated id
    searching_keyword = user_newkeyword
    post = {"_id": db_id_generator, "user_id": user_id, "searching_keyword": searching_keyword}
    collection.insert_one(post)
    print(f'Слово: "{searching_keyword}" добавлено в БД')
    log.info(f'Слово: "{searching_keyword}" добавлено в БД')


def mysearch(user_id):
    mysearch_list = []
    user_db_posts = collection.find({'user_id': user_id})
    for post in user_db_posts:
        mysearch_list.append(post['searching_keyword'])
    with open('temp.json', 'w') as outfile:
        json.dump(mysearch_list, outfile)
        print("JSON saved")

    # TODO add input logic below as bot command in tg_bot
    # user_request = input()
    # if user_request == "newkeyword":
    #     newkeyword()
    # elif user_request == "removekeyword":
    #     removekeyword()


def removekeyword(user_remove_keyword, user_id):
    '''
    Remove keyword from DB and save error message in JSON
    We use JSON here to not import logging module (not sure if it's a right decision)
    TODO replace json logs to actual logging module and transfer db_msg with "return"
    '''
    user_search_list = {}
    with open('temp.json', 'r') as outfile:
        user_search_list = json.load(outfile)
    if user_search_list.count(user_remove_keyword) < 1:
        db_msg = f'Слова: "{user_remove_keyword}" нет в поиске, введите новое или /exit для выхода'
        with open('errors.json', 'w') as errfile:
            json.dump(db_msg, errfile)
            print("no keyword ERR JSON saved")
    else:
        collection.delete_one({"user_id": user_id, "searching_keyword": user_remove_keyword})
        db_msg = f'Слово: "{user_remove_keyword}" удалено из поиска'
        with open('errors.json', 'w') as errfile:
            json.dump(db_msg, errfile)
            print("try db_msg JSON saved")


def useridea(user_idea, username, user_id):
    """
    Save user idea into DB to read it later
    """
    post = {"username": username, "user_id": user_id, "user_idea": user_idea}
    idea_collection.insert_one(post)


def main_search():
    parse_dict = {}
    all_posts = collection.find({})
    for post in all_posts:
        parse_dict.update({post['searching_keyword']: post['user_id']})
    return parse_dict


def message_save(all_messages):
    """
    Save new messages from chat into DB
    :param all_messages: dictionary with all new messages
    :return: How many messages have been added
    """
    single_message = {}
    db_import = []
    msgs_added = 0
    for messages in all_messages:
        _id = messages['id']
        channel_id = messages['peer_id']['channel_id']
        date = messages['date']
        message = messages['message']
        try:
            from_id = messages['from_id']['user_id']
        except:
            from_id = messages['from_id']['channel_id']
        single_message = {"_id": _id, "channel_id": channel_id, "date": date, "message": message, "from_id": from_id}
        db_import.append(single_message)
        msgs_added += 1
    msg_collection.insert_many(db_import)
    return msgs_added


def lastmsg_id():
    last_message = msg_collection.find_one(sort=[("_id", -1)])
    last_message_id = last_message['_id']
    return last_message_id


def message_search(keyword, last_message_id):
    """
    search by a single keyword

    :param keyword: keyword we should search in DB
    :param last_message_id: id to search only in last messages
    :return: list of found messages with message_id
    """
    searched_messages = []
    for messages in msg_collection.find(sort=[("_id", -1)]):  # search by descending order
        if int(messages['_id']) < int(last_message_id):  # preventing message repetition
            '''
            Options here:
            1. Check if message with current id has been sent. Save sent msg id in config file (PROBLEM - 
                if we need to send this msg to many users? Should we save also user id? But if we have 1k user send list?)
            2. Add DB flag in user setting post with last msg id sent to him (Too many DB requests)
            3. Add msg sent log and check if msg has been sent in log file (SENDLOG, user_id, msg_id)
            4. Add variable in loop cycle with last sent msg_id (OK)
            5. Create new temp file with last sent msg_id and user_id (SENDLOG file?)
            '''
            break
        if messages['message'].find(keyword) > 0:  # find if position of first symbol > 0
            searched_messages.append((messages['_id'], messages['message']))  # Add message with key to list
    return searched_messages


def allmessages_search(keyword):
    """
    Debugging function, useful for looking at data structure
    Will be handful in future bot features
    Search by single keyword

    :param keyword: what keyword we should search in DB
    """
    searched_messages = {}
    counter = 0
    for messages in msg_collection.find(sort=[("_id", -1)]):  # search by descending order
        if messages['message'].find(keyword) >= 0:
            print(messages)
            counter += 1
        if counter == 10:
            print('break')
            break
