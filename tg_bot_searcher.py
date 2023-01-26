import time
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter

import telebot
import configparser
from telebot import types

import ChannelMessages
import bot_db_handler
import sendlog

# LOG ROTATION SYSTEM
# reference: https://stackoverflow.com/questions/43947206/automatically-delete-old-python-log-files

# get named logger
log = logging.getLogger(__name__)
# create handler
handler = TimedRotatingFileHandler(filename='debug.log', when='D', interval=1, backupCount=90, encoding='utf-8',
                                                                                                        delay=False)
# create formatter and add to handler
formatter = Formatter(fmt='%(filename)s -- %(asctime)s -- %(message)s')
handler.setFormatter(formatter)
# add the handler to named logger
log.addHandler(handler)
# set the logging level
log.setLevel(logging.INFO)

config = configparser.ConfigParser()
config.read("config.ini")
bot_key = config['TgBot']['bot_key']
debug_mod = int(config['Debug']['debug_mod'])

bot = telebot.TeleBot(bot_key, parse_mode=None)

'''
Algorythm:
1. Every 2 min bot exec main() func
2. main() parses fresh messages from channel and save it to JSON using ChannelMessages.py
3. main() connect to DB and call all searched keys with user_ids as dictionary
4. Search FOR all keys in fresh messages
5. IF key was found, msg to connected user with link to these msg
'''


def main():
    # tmp - read how many times we'll connect to DB
    db_connections = 0  # tmp

    # Call parsing telethone ChannelMessages script
    last_message_id = bot_db_handler.lastmsg_id()
    db_connections += 1  # tmp

    ChannelMessages.client_loop()  # TODO test this carefully  # parse new messages from chat
    parse_dict = bot_db_handler.main_search()  # pulling all searching keywords from DB
    db_connections += 1  # tmp

    for searching_post in parse_dict.items():  # searching with every keyword in fresh DB dictionary
        searching_keyword = searching_post[0]
        searcher_userid = searching_post[1]
        if searching_keyword != '':  # Ignore user blank searches (Rare bug)
            db_messages = bot_db_handler.message_search(searching_keyword, last_message_id)
            db_connections += 1  # tmp

            for messages in db_messages:
                cycle_message = messages[1]  # Open each message text in cycle
                if cycle_message.find(searching_keyword) >= 0:
                    '''
                    1. if keyword was found, ".find" method return his starting position, if not = -1
                    '''
                    # check if debug mod is turned on to not spam users if bugs appears
                    if debug_mod == 1:
                        searcher_userid = 207230922
                        print(f'===DEBUG MOD ON===')
                        log.info(f'===DEBUG MOD ON===')

                    searching_msgid = messages[0]

                    # check if message has not been sent
                    if not sendlog.read(searcher_userid, searching_msgid):
                        mess = f"Найдено сообщение c поисковым словом: {searching_keyword}\n" \
                               f"https://t.me/batumi_together_chat/{str(searching_msgid)}"
                        print(mess)
                        log.info(mess)

                        # this "try" prevents crash if user block bot
                        try:
                            bot.send_message(searcher_userid, mess, parse_mode=None)
                            print(f'user: {searcher_userid} just received message\n-----------------------------------')
                            log.info(f'user: {searcher_userid} just received message\n--------------------------------')
                        except:
                            print(f'Send message exception. Might be bot blocked by user')
                            log.info(f'Send message exception. Might be bot blocked by user')
                        sendlog.save(searcher_userid, searching_msgid)  # store msg info in sendlog

                    else:
                        print(f'Message has already been sent')
                        log.info(f'Message has already been sent')

    print(f'DB connections during session: {db_connections}')  # tmp
    log.info(f'DB connections during session: {db_connections}')


sleep_cycle = 0  # tmp
while True:
    main()
    # 2 min sleeping then cycle main function
    time.sleep(120)  # default = 120 sec here (5 for testing)
    sleep_cycle += 1  # tmp
    log.info(f'sleep cycle: {sleep_cycle}')
    print(f'sleep cycle: {sleep_cycle}')  # tmp
    if debug_mod == 1:
        log.info(f'===DEBUG MOD ON===')
        print(f'===DEBUG MOD ON===')

