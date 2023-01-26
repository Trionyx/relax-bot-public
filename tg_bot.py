import json
import logging as log

import telebot
import configparser
from telebot import types

import bot_db_handler


log.basicConfig(filename='debug.log',
                format='%(filename)s -- %(asctime)s -- %(message)s',
                level=log.INFO,
                datefmt='%m/%d/%Y %I:%M:%S %p'
                )


#################################################
#                    BOT BODY                   #
#################################################

def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)
            log.info(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")
bot_key = config['TgBot']['bot_key']
logpass = config['Logsecurity']['logpass']

bot = telebot.TeleBot(bot_key, parse_mode=None)
bot.set_update_listener(listener)  # register listener


#################################################
#               START   COMMAND                 #
#################################################

@bot.message_handler(commands=['start'])
def start(message):

    mess = """
    Бот мониторит чат за вас и уведомляет когда появилось искомое слово
(Если не хотите пропустить #го, то добавьте "#го" в поиск)
!Бот на стадии разработки!
    
    Список команд:
    /start - Вызвать меню бота
    /newsearch - Добавить слово для поиска
    /mysearch - Ваши поисковые слова
    /removesearch - Удалить поисковую фразу из списка
    /sendidea - Отправить идею разработчику
    
    /help - Пример настройки поиска
    /charisma_buff - Баф харизмы
    """
    bot.send_message(message.chat.id, mess, parse_mode=None )
    print(message.chat.id)
    log.info(message.chat.id)
    print(message.from_user.username)
    log.info(message.from_user.username)


#################################################
#               NEWSEARCH COMMAND               #
#################################################

@bot.message_handler(commands=['newsearch'])  # Add new search keyword
def bot_newkeyword(message):
    """
    Ask user for keywords, parse his id, save info in db
    """
    msg = bot.send_message(message.chat.id, f'Напишите пожалуйста новое слово для поиска или нажмите /exit для отмены')
    bot.register_next_step_handler(msg, process_newkeyword)


def process_newkeyword(message):  # bot_newkeyword next step
    user_id = message.from_user.id
    user_newkeyword = message.text

    if user_newkeyword != "/exit":
        bot_db_handler.newkeyword(user_newkeyword, user_id)  # Send info to DB handler
        bot.send_message(message.chat.id, f'Слово [{user_newkeyword}] сохранено', parse_mode=None)
    else:
        bot.send_message(message.chat.id, f'Добавление поискового слова отменено', parse_mode=None)

    # TODO send user keywords from 'mysearch' here


#################################################
#               MYSEACH COMMAND                 #
#################################################

@bot.message_handler(commands=['mysearch'])  # Show user his searching keywords
def bot_mysearch(message):
    user_id = message.from_user.id
    user_search_list = {}
    bot_db_handler.mysearch(user_id)  # send user id to DB handler
    with open('temp.json', 'r') as outfile:
        user_search_list = json.load(outfile)  # Put json_temp file into variable
    print(f'user_search_list from tg_bot {user_search_list}')  # temp
    log.info(f'user_search_list from tg_bot {user_search_list}')
    markup = telebot.types.InlineKeyboardMarkup()
    markup.width = 2
    markup.add(telebot.types.InlineKeyboardButton(text='Удалить слова из списка', callback_data='remove_keywords'))
    markup.add(telebot.types.InlineKeyboardButton(text='Добавить слова', callback_data='add_keywords'))
    markup.add(telebot.types.InlineKeyboardButton(text='Закончить', callback_data='exit_btn'))
    msg = bot.send_message(
        message.chat.id,
        f'Ваши поисковые слова: {user_search_list}', # uncomment this for buttons: \nЧто хотите сделать далее?',
        parse_mode=None,
        #  reply_markup=markup  # uncomment this for buttons
    )
#  TODO finish block with buttons below to make next step more handy
#
#     bot.register_next_step_handler(msg, process_mysearch)
#
# def process_mysearch(message):
#     if not message.text.startswith('/'):
#         bot.send_message(message.chat.id, 'Нажмите одну из кнопок')
#         bot_mysearch(message)
#
# @bot.callback_query_handler(func=lambda call: True)  # call: "command" in call.data)
# def callback_query(call):
#     if call.data == "remove_keywords":
#         bot_newkeyword(message)  # TODO - message argument doesn't hand over to bot_newkeyword() function,
#                                  #  so 'message' name not defined error [!Use temp file!]
#     if call.data == "add_keywords":
#         bot_removesearch(message)
#     if call.data == "exit_btn":
#         start(message)


#################################################
#           REMOVESEARCH COMMAND                #
#################################################

@bot.message_handler(commands=['removesearch'])  # Remove user searching keywords
def bot_removesearch(message):
    user_id = message.from_user.id
    user_search_list = {}
    bot_db_handler.mysearch(user_id)  # send user id to DB handler
    with open('temp.json', 'r') as outfile:
        user_search_list = json.load(outfile)  # Put json_temp file into variable

    # -- code below for showing users keywords as buttons --
    # markup = telebot.types.InlineKeyboardMarkup()
    # markup.width = 2
    # for user_keyword in user_search_list:
    #     markup.add(telebot.types.InlineKeyboardButton(
    #     text=user_keyword,
    #     callback_data=f'user_keyword_{user_search_list.index(user_keyword)}'))
    msg = bot.send_message(
        message.chat.id,
        f'Ваши поисковые слова: {user_search_list}\n'
        f'Отправьте мне по одному, какие из слов хотите удалить?\n'
        f'Или отправьте /exit для выхода',
        parse_mode=None,
        # reply_markup=markup  # for buttons inline
    )
    bot.register_next_step_handler(msg, process_removesearch)


def process_removesearch(message):  # reading users keyword for removing and remove it from DB if exists
    user_id = message.from_user.id
    user_remove_keyword = message.text

    if user_remove_keyword != "/exit":
        bot_db_handler.removekeyword(user_remove_keyword, user_id)  # Send info to DB handler
        with open('errors.json', 'r') as errfile:
            db_msg = json.load(errfile)  # Put db_error json file into variable
        print(f'db_msg: {db_msg}')
        log.info(f'db_msg: {db_msg}')
        bot.send_message(message.chat.id, db_msg, parse_mode=None)
        bot_removesearch(message)
    else:
        bot.send_message(message.chat.id, f'Удаление поискового слова отменено', parse_mode=None)


# TODO finish buttons processing
# def callback_query(call):  # Process next step of removing with buttons
#     for user_keyword_index in call.data:
#         print(user_keyword_index)


#################################################
#               HELP COMMAND                    #
#################################################


@bot.message_handler(commands=['help'])  # Explanation of how bot works
def help_message(message):
    """
    Information for better understanding
    """
    msg = '''Для начала поиска выберите команду /newsearch и добавьте поисковое слово, например "#го"
    
Бот начнет сканировать свежие сообщения и пришлет уведомление когда в чате появится нужное слово

Можно добавить различные слова в зависимости от того, какие активности интересуют и что не хотели бы пропустить
Например: "пляж", "волейбол" и т.д.

Поисковые слова чувствительны к большим/маленьким буквам: "пляж" и "Пляж" для бота разные слова

Чтобы посмотреть добавленные слова, нажмите /mysearch в меню /start

Чтобы удалить слова: /removesearch
    '''
    log_command(message)
    bot.send_message(message.chat.id, msg)


#################################################
#               SENDIDEA COMMAND                #
#################################################

@bot.message_handler(commands=['sendidea'])  # Button for users to send idea
def sendidea_text(message):
    msg = bot.send_message(message.chat.id, f'Напишите пожалуйста вашу идею в чат')
    bot.register_next_step_handler(msg, process_user_idea)

def process_user_idea(message):  # sendidea_text next step
    """
    Get user idea and save it in DB
    """
    user_idea = message.text
    username = message.from_user.username
    user_id = message.from_user.id
    bot_db_handler.useridea(user_idea, username, user_id)
    bot.send_message(message.chat.id, f'Идея [{user_idea}] отправлена разработчику', parse_mode=None)

#################################################
#                     LOGGER                    #
#################################################


@bot.message_handler(commands=['log'])
def log_entry(message):
    """
    Check if user == admin and ask password
    """
    if message.from_user.id == 207230922:
        msg = bot.send_message(message.chat.id, f'drowssap')
        bot.register_next_step_handler(msg, log_outfile)
    else:
        msg = f'DebugError: [Errno 22] Invalid argument: 97a65d1633f5c, line 28962'
        bot.send_message(message.chat.id, msg, parse_mode=None)


def log_outfile(message):
    """
    Send debug.log file from server to admin if password is correct
    """
    if message.text == logpass:  # read password variable from config file
        bot.send_message(message.chat.id, "Files incoming")
        logfile = open('debug.log', 'rb')
        bot.send_document(message.chat.id, logfile)
    else:
        msg = f'DebugError: [Errno 22] Invalid argument: 97a65d1633f5c, line 28962'
        bot.send_message(message.chat.id, msg, parse_mode=None)


#################################################
#               CHARISMA BUFF                   #
#################################################


@bot.message_handler(commands=['charisma_buff'])  # Fun-video button
def charismabuff(message):
    """
    Fun function
    """
    video = open('charisma_buff_full.mp4', 'rb')
    bot.send_video(message.chat.id, video)
    bot.send_video(message.chat.id, "FILEID")


def log_command(message):
    log.info(f'Command {message.text} has been received. Chat data: {message.chat}')


bot.polling(none_stop=True)
