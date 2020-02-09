"""Module dedicated to functions that assist other functions.

E.g. decorators, checking cooldowns, etc.
"""

from datetime import datetime, timedelta

import telegram.error
from telegram import Update, Message
from telegram.ext import CallbackContext, run_async

from main import LOGGER
from main.database import *
from main.constants import DEVS, INDIVIDUAL_USER_DELAY, PING_CHANNEL


class ResetError(Exception):
    """Error made to be able to reset cooldowns when needed by raising the error."""
    pass


def antispam_passed(func):
    """Check if the user is spamming in a group."""
    def executor(update: Update, context: CallbackContext, *args, **kwargs):
        if update.message.chat.type != 'private':
            record_data(update)
            # Check for cooldown
            if not cooldown(update, context):
                try:
                    func(update, context, *args, **kwargs)
                    set_cooldown(update, True)
                except telegram.error.BadRequest as crit:
                    LOGGER.error(crit)
                    set_cooldown(update, False)
                except ResetError:
                    set_cooldown(update, False)
        else:
            func(update, context, *args, **kwargs)

    return executor


def check_if_group_chat(func) -> None:
    """Check if the chat is a group chat."""
    def executor(update: Update, context: CallbackContext, *args, **kwargs):
        if update.message.chat.type == 'private':
            update.message.reply_text('Эта команда только для групп.')
        else:
            func(update, context, *args, **kwargs)

    return executor


def admin_priv(update: Update, context: CallbackContext) -> bool:
    """Check if the user has enough rights.

    Enough rights are defined as the administrator or the developer.
    """
    admins = [u.user for u in context.bot.get_chat_administrators(
        update.message.chat.id)]
    if update.message.from_user in admins or \
            update.message.from_user.id in DEVS:
        return True
    return False


@run_async
@db_session
def record_data(update: Update) -> None:
    """Store chat and user data."""
    # Don't record private chats
    if update.message.chat.type == 'private':
        return
    # Record the chat
    if not Chats.exists(id=update.message.chat.id):
        Chats(id=update.message.chat.id,
              title=update.message.chat.title or 'Private',
              link=update.message.chat.link or 'Private')
    # Get the users involved
    users = [update.message.from_user]
    if update.message.reply_to_message is not None:
        users.append(update.message.reply_to_message.from_user)
    # Record the users and scores
    for data in users:
        if not Users.exists(id=data.id):
            Users(id=data.id,
                  full_name=data.full_name,
                  username=data.username or 'Unknown',
                  link=data.link or 'Unknown')
        if not User_Stats.exists(user_id=Users[data.id],
                                 chat_id=Chats[update.message.chat.id]):
            User_Stats(user_id=Users[data.id],
                       chat_id=Chats[update.message.chat.id])
        if not Options.exists(chat_id=Chats[update.message.chat.id]):
            Options(chat_id=Chats[update.message.chat.id])
        if not Cooldowns.exists(user_id=Users[data.id],
                                chat_id=Chats[update.message.chat.id]):
            Cooldowns(user_id=Users[data.id],
                      chat_id=Chats[update.message.chat.id])


@db_session
def cooldown(update: Update, context: CallbackContext) -> bool:
    """Check if there is a cooldown for the user."""
    # No cooldown for admins and developer
    if admin_priv(update, context):
        return False
    sender = update.message.from_user
    # No cooldown for immune
    if User_Stats[Users[sender.id], Chats[update.message.chat.id]].exception:
        return False
    # If cooldown existed for regular users
    last_command = Cooldowns[Users[sender.id],
                             Chats[update.message.chat.id]].last_command
    error_sent = Cooldowns[Users[sender.id],
                           Chats[update.message.chat.id]].error_sent
    chat_cooldown = Options[Chats[update.message.chat.id]].cooldown
    # Do
    if last_command is None or \
            last_command + timedelta(minutes=chat_cooldown) < datetime.now():
        Cooldowns[Users[sender.id],
                  Chats[update.message.chat.id]].error_sent = 0
        return False
    # Don't do
    if not error_sent:
        remaining = last_command + \
            timedelta(minutes=chat_cooldown) - datetime.now()
        update.message.reply_text(
            (f'До вашей следующей команды {remaining.seconds} секунд.\n'
                'Ошибку на задержку даю только один раз, запоминай.')
        )
        Cooldowns[Users[sender.id],
                  Chats[update.message.chat.id]].error_sent = 1
    return True


@db_session
def set_cooldown(update: Update, success: bool) -> None:
    """Set cooldown for the user."""
    if success:
        to_set = datetime.now()
    else:
        to_set = datetime.now() - \
            timedelta(minutes=Options[Chats[update.message.chat.id]].cooldown)
    Cooldowns[Users[update.message.from_user.id],
              Chats[update.message.chat.id]].last_command = to_set


@run_async
def error_callback(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    LOGGER.warning('Error "%s" caused by update "%s"', context.error, update)


@run_async
def ping(context: CallbackContext) -> Message:
    """Ping a chat to show that the bot is working and is online."""
    context.bot.send_message(
        chat_id=PING_CHANNEL,
        text='ping...',
        disable_notification=True
    )
