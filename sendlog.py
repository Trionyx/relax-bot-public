"""
Sendlog module for storing logs of sent messages and similar logic

save last sent msg_id with user_id and time, remove if time more than 7 days
"""
import json
import time


def save(searcher_userid, searching_msgid):
    """
    Save info of last sent message

    :param searcher_userid: TG id of user who received message
    :param searching_msgid: sent message id
    """
    last_message = {  # place send data in dict
        "searcher_userid": searcher_userid,
        "searching_msgid": searching_msgid,
        "date": time.time()
    }

    # save if file is not empty
    try:
        with open('sendlog.json', 'r') as infile:
            json_log = json.load(infile)
            json_log = remove(json_log)  # remove messages older than a week
            json_log.append(last_message)
        with open('sendlog.json', 'w') as outfile:
            json.dump(json_log, outfile)

    # save if file is empty
    except:
        print(f'JSON log file is empty, passing open stage')
        with open('sendlog.json', 'w') as outfile:
            json_log = [last_message]
            json.dump(json_log, outfile)


def remove(json_log):
    """
    Remove messages if they are older than 604800 seconds (week)

    :param json_log: All messages from json file in list format
    :return: list without old messages
    """
    new_list = []
    for message in json_log:
        if (time.time() - message["date"]) < 604800:  # should be 604800 (week)
            new_list.append(message)
    return new_list


def read(searcher_userid, searching_msgid):
    """
    Read sednlog file and check if current message has been sent to current user

    :param searcher_userid: TG id of user who received message
    :param searching_msgid: sent message id
    :return: True if message has been sent, False if message hasn't been sent
    """
    with open('sendlog.json', 'r') as outfile:
        json_log = json.load(outfile)
        for message in json_log:
            if message["searcher_userid"] == searcher_userid and message["searching_msgid"] == searching_msgid:
                return True
                break

        return False
