"""Module dedicated to functions that assist other functions.

E.g. decorators, checking cooldowns, etc.
"""

from datetime import datetime, timedelta

import requests
import telegram.error
from telegram import TelegramError, Update
from telegram.ext import CallbackContext, run_async

from constants import DEV, INDIVIDUAL_USER_DELAY
from maindoomer import BOT, LOGGER
from maindoomer.sqlcommands import run_query


# Get known chats
KNOWNCHATS = []
KNOWNCHATSDB = run_query('SELECT chat_id from chattable')
KNOWNCHATS += [entry[0] for entry in KNOWNCHATSDB]
# Get knownusers
KNOWNUSERS = {}
KNOWNUSERSDB = run_query('SELECT user_id, chat_id FROM userdata')
for entry in KNOWNUSERSDB:
    if entry[1] not in KNOWNUSERS:
        KNOWNUSERS[entry[1]] = []
    KNOWNUSERS[entry[1]] += [entry[0]]


def command_antispam_passed(func):
    """Check if the user is spamming.

    Delay of INDIVIDUAL_USER_DELAY minute(s) for individual user commands, changeable.
    """
    def executor(update: Update, *args, **kwargs):
        store_data(update)
        # Check for cooldown
        from constants import INDIVIDUAL_USER_DELAY
        if check_cooldown(update, 'lastcommandreply', INDIVIDUAL_USER_DELAY):
            try:
                func(update, *args, **kwargs)
            except (telegram.error.BadRequest,
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ReadTimeout):
                reset_command_cooldown(update)

    return executor


def check_if_group_chat(func):
    """Check if the chat is a group chat."""
    def executor(update: Update, *args, **kwargs):
        if update.effective_message.chat.type == 'private':
            BOT.send_message(chat_id=update.effective_chat.id,
                             text='Это только для групп.')
        else:
            func(update, *args, **kwargs)

    return executor


def rights_check(func):
    """Check if the user has enough rights.

    Enough rights are defined as creator or administrator or developer.
    """
    def executor(update: Update, *args, **kwargs):
        store_data(update)
        rank = BOT.get_chat_member(chat_id=update.effective_message.chat_id,
                                   user_id=update.effective_user.id).status
        permitted = ['creator', 'administrator']
        if rank in permitted or update.effective_user.id == DEV:
            func(update, *args, **kwargs)
        else:
            informthepleb(update)

    return executor


def check_if_dev(func):
    """Check if user is the developer."""
    def executor(update: Update, *args, **kwargs):
        if update.effective_user.id == DEV:
            func(update, *args, **kwargs)

    return executor


@run_async
def store_chat_data(update: Update):
    """Store chat data."""
    global KNOWNCHATS
    if update.effective_chat.id not in KNOWNCHATS:
        # Create chat data
        run_query(
            'INSERT OR IGNORE INTO chattable (chat_id, chat_name) VALUES (?, ?)',
            (update.effective_chat.id,
             BOT.get_chat(chat_id=update.effective_chat.id).title)
        )
        KNOWNCHATS += [update.effective_chat.id]


@run_async
def store_user_data(update: Update):
    """Add user data to the userdata table of the database."""
    global KNOWNUSERS
    # Create chat entry
    if update.effective_chat.id not in KNOWNUSERS:
        KNOWNUSERS[update.effective_chat.id] = []
    if update.effective_user.id not in KNOWNUSERS[update.effective_chat.id]:
        # Get all user data
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        firstname = update.effective_user.first_name
        lastname = update.effective_user.last_name if update.effective_user.last_name else ''
        username = update.effective_user.username if update.effective_user.username else ''
        # Try to get the chat name
        try:
            chatname = BOT.get_chat(
                chat_id=update.effective_message.chat_id).title
        except:
            chatname = ''
        # Try to get the chat link
        try:
            chatlink = "t.me/" + update.effective_message.chat.username
        except:
            chatlink = 'private'
        usable_data = []
        usable_variable = []
        # Prepare data for SQL
        for data in (
                (user_id, 'user_id'),
                (chat_id, 'chat_id'),
                (firstname, 'firstname'),
                (lastname, 'lastname'),
                (username, 'username'),
                (chatname, 'chatname'),
                (chatlink, 'chatlink')):
            if data[0]:
                usable_data += [data[0]]
                usable_variable += [data[1]]
        # Store the user data
        run_query(
            f"""INSERT OR IGNORE INTO userdata {tuple(usable_variable)} VALUES
            ({','.join('?'*len(usable_data))})""", tuple(usable_data)
        )
        KNOWNUSERS[update.effective_chat.id] += [user_id]


@run_async
def store_data(update: Update):
    """Store chat and user data."""
    store_user_data(update)
    store_chat_data(update)


def check_cooldown(update: Update, whattocheck, cooldown):
    """Check cooldown of command, error.

    Whattocheck should be the sql column name.
    """
    def _give_command_error():
        """Give command cooldown error, if the user still spams, delete his message."""
        nonlocal update
        # Check if the error was given
        if run_query(
                'SELECT errorgiven from cooldowns WHERE chat_id=(?) and user_id=(?)',
                (update.effective_chat.id, update.effective_user.id)
        )[0][0] == 0:
            # If it wasn't, give the time remaining and update the flag.
            time_remaining = str(
                (barriertime - message_time)).split('.')[0][3:]
            BOT.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.effective_message.message_id,
                text=(f'До команды осталось {time_remaining} (ММ:СС). '
                      f'Пока не прошёл откат, я буду удалять твои команды, '
                      'если у меня есть на это права.')
            )
            run_query(
                'UPDATE cooldowns SET errorgiven=1 WHERE chat_id=(?) AND user_id=(?)',
                (update.effective_chat.id, user_id)
            )
        # If it was, try to delete the message
        else:
            try:
                BOT.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=update.effective_message.message_id
                )
            except TelegramError:
                pass

    if update.effective_message.chat.type == 'private':
        return True
    # Add exceptions for some users
    user_id = update.effective_user.id
    if run_query(
            'SELECT * FROM exceptions WHERE user_id=(?)', (user_id,)):
        for chatexcused in run_query(
                'SELECT chat_id FROM exceptions WHERE user_id=(?)', (user_id,)):
            # 1 is global
            if chatexcused[0] in [update.effective_chat.id, 1]:
                return True
    message_time = datetime.now()
    # Find last instance
    lastinstance = run_query(
        f'SELECT {whattocheck} FROM cooldowns WHERE chat_id=(?) AND user_id=(?)',
        (update.effective_chat.id, user_id)
    )
    # If there was a last one
    if lastinstance:
        lasttime = lastinstance[0][0]
        # Check if the cooldown has passed
        barriertime = datetime.fromisoformat(lasttime) + \
            timedelta(seconds=cooldown)
        if message_time > barriertime:
            # If it did, update table, return True
            run_query(
                f'UPDATE cooldowns SET {whattocheck}=(?), errorgiven=0 '
                f'WHERE chat_id=(?) AND user_id=(?)',
                (message_time, update.effective_chat.id, user_id)
            )
            return True
        # If it didn't return False and give an error
        _give_command_error()
        return False
    # If there was none, create entry and return True
    run_query(
        f'INSERT OR IGNORE INTO cooldowns (user_id, chat_id, firstname, {whattocheck})'
        'VALUES (?, ?, ?, ?)', (user_id, update.effective_chat.id,
                                update.effective_user.first_name, message_time)
    )
    run_query(
        f'UPDATE cooldowns SET {whattocheck}=(?) WHERE user_id=(?) AND chat_id=(?)',
        (message_time, user_id, update.effective_chat.id)
    )
    return True


@run_async
def informthepleb(update: Update):
    """If was not called by admin/creator/dev, inform the user that he is a pleb."""
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text='Пошёл нахуй, ты не админ.'
    )


@run_async
def callbackhandler(update: Update, context: CallbackContext):
    """Handle callbacks for admins."""
    rank = BOT.get_chat_member(chat_id=update.effective_chat.id,
                               user_id=update.effective_user.id).status
    permitted = ['creator', 'administrator']
    if rank not in permitted and update.effective_chat.type != 'private':
        return
    if update.callback_query.data in ['legal', 'illegal']:
        lolitype = 0 if update.callback_query.data == 'legal' else 1
        run_query(
            'UPDATE chattable SET loliNSFW=(?) WHERE chat_id=(?)',
            (lolitype, update.effective_chat.id)
        )
        currentstate = 'Теперь контент '
        currentstate += '***SFW***.' if lolitype == 0 else '***NSFW***.'
        BOT.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id
        )
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text=currentstate,
            reply_to_message_id=update.effective_message.reply_to_message.message_id,
            disable_notification=True,
            parse_mode='Markdown'
        )


@run_async
def error_callback(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    LOGGER.warning('Error "%s" caused by update "%s"', context.error, update)


@run_async
def ping(context: CallbackContext):
    """Ping a chat to show that the bot is working and is online."""
    from constants import PING_CHANNEL
    BOT.send_message(
        chat_id=PING_CHANNEL,
        text='ping...',
        disable_notification=True
    )


@run_async
def reset_command_cooldown(update: Update):
    """Reset the user command cooldown."""
    run_query(
        'UPDATE cooldowns SET lastcommandreply=(?) WHERE '
        'chat_id=(?) AND user_id=(?)',
        (datetime.now() - timedelta(seconds=INDIVIDUAL_USER_DELAY),
         update.effective_chat.id, update.effective_user.id)
    )
