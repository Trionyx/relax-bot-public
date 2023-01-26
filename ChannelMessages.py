import configparser
import json
import asyncio
from datetime import date, datetime
import logging as log

import bot_db_handler
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)


# some functions to parse json date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)

log.basicConfig(filename='debug.log',
                format='%(filename)s -- %(asctime)s -- %(message)s',
                level=log.INFO,
                datefmt='%m/%d/%Y %I:%M:%S %p'
                )


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)


async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if await client.is_user_authorized() == False:
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    my_channel = config['Telegram']['channel_link']

    offset_id = 0  # if offset_id != 0: messge id which will be the first parsed. Next messages will be parsed descending
    limit = 100  # how many messages parse at one attempt (don't change if not necessary)
    all_messages = []
    old_messages = []  # temp - for old "json" approach
    total_messages = 0
    total_count_limit = 0  # How many messages we should parse by default
                           # Number of this limit calculates later / if 0: parse all msgs

    last_message_id = bot_db_handler.lastmsg_id()  # getting last message id for DB
    log.debug(f'Last message ID = {last_message_id}')
    print(f'Last message ID = {last_message_id}')

    while True:
        print("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        log.debug("Current Offset ID is:", offset_id, "; Total Messages:", total_messages)
        history = await client(GetHistoryRequest(
            peer=my_channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=last_message_id,  # add -1 to not leaving json empty
            hash=0
        ))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            all_messages.append(message.to_dict())
        offset_id = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    with open('channel_messages.json', 'w') as outfile:
        json.dump(all_messages, outfile, cls=DateTimeEncoder)
    try:
        bot_db_handler.message_save(all_messages)  # save new messages into DB
    except:
        print(f'No new messages (DB saving exception)')
        log.debug(f'DB save exception. No new messages?')


def client_loop():
    with client:
        client.loop.run_until_complete(main(phone))

