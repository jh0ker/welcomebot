"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import random
from html import escape
import requests

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def help(update, context):
    """Help message"""
    help_text = "/flip - Бросить монетку (Орёл или Решка);" \
                "/echo - Получить ответ своим же сообщением;" \
                ""
    context.bot.send_message(chat_id=update.message.chat_id, text=help_text)

def welcome(update, context):
    """Welcome message for the user"""
    # Get the message, id, user information.
    message = update.message
    print(message)
    chat_id = message.chat.id
    logger.info('%s joined to chat %d (%s)'
                % (escape(message.new_chat_members[0].first_name),
                   chat_id,
                   escape(message.chat.title)))
    # Generate a reply
    reply_end = random.choice(['Имя, Фамилия. Изображения ног НИ В КОЕМ СЛУЧАЕ не кидать.', 'Имя, Фамилия, фото ног.'])
    reply = (f"Приветствуем вас в Думерском Чате, {message.new_chat_members[0].first_name}!\n"
             f"С вас {reply_end}")
    context.bot.send_message(chat_id=update.message.chat_id, text=reply)

def empty_message(update, context):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    BOTNAME = "random_welcome_bot"

    print(update.message)
    # someone entered chat
    if update.message.new_chat_members is not None:
        # update was added to a group chat
        if update.message.new_chat_members[0].username == BOTNAME:
            return
        # Another user joined the chat
        else:
            return welcome(update, context)


def echo(update, context):
    """Echo back the message"""
    return_echo = update.message.text[6:]
    context.bot.send_message(chat_id=update.message.chat_id, text=return_echo)


def flip(update, context):
    """Start message"""
    flip_outcome = random.choice(['Орёл!', 'Решка!'])
    context.bot.send_message(chat_id=update.message.chat_id, text=flip_outcome)

def image(update,context):
    """Return an image"""
    link = 'https://imgur.com/gallery/F4IKheK'
    context.bot.send_message(chat_id=update.message.chat_id, text=link)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    TOKEN = ""
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("welcome", welcome))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("echo", echo))
    dp.add_handler(CommandHandler("flip", flip))
    dp.add_handler(CommandHandler("random", random))

    # add welcomer
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, empty_message))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
