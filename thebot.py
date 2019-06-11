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

from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def help(update, context):
    """Help message"""
    help_text = (
        "/echo - Получить ответ своим же сообщением;\n"
        "/help - Это меню;\n"
        "\n"
        "Генераторы чисел:\n"
        "/flip - Бросить монетку (Орёл или Решка);\n"
        "/myiq - Мой IQ (0 - 200);\n"
        "/muhdick - Длина моего шланга (0 - 25);\n"
        "/random - Случайное число в выбранном диапазоне, включая концы."
                 )
    context.bot.send_message(chat_id=update.message.chat_id, text=help_text)


def welcome(update, context):
    """Welcome message for the user"""
    # Get the message, id, user information.
    message = update.message
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
    print(update.message)

    # someone entered chat
    if update.message.new_chat_members is not None:
        # update was added to a group chat
        if update.message.new_chat_members[0].is_bot is True:
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


def myiq(update, context):
    """Return IQ level (0-200)"""
    iq_level = random.randint(0, 200)
    if iq_level < 85:
        message = f"Твой уровень IQ {iq_level}. Грустно за тебя, братишка. (0 - 200)"
    elif 85 <= iq_level <= 115:
        message = f"Твой уровень IQ {iq_level}. Ты норми, братишка. (0 - 200)"
    elif 115 < iq_level <= 125:
        message = f"Твой уровень IQ {iq_level}. Ты умный, братишка! (0 - 200)"
    else:
        message = f"Твой уровень IQ {iq_level}. Ты гений, братишка! (0 - 200)"
    context.bot.send_message(chat_id=update.message.chat_id, text=message)


def muhdick(update, context):
    """Return dick size in cm (0-25)"""
    muh_dick = random.randint(0, 25)
    if muh_dick == 0:
        context.bot.send_message(chat_id=update.message.chat_id, text='У тебя нет члена (0), хаха! (0 - 25)')
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Длина твоего шланга {muh_dick} см! (0 - 25)")

def randomnumber(update, context):
    """Return a random number between two integers"""
    args = update.message.text[13:].split()
    if len(args) == 2:
        try:
            arg1, arg2 = int(args[0]), int(args[1])
            generated_number = random.randint(arg1, arg2)
            context.bot.send_message(chat_id=update.message.chat_id, text=f"Выпало {generated_number}.")
        except ValueError:
            context.bot.send_message(chat_id=update.message.chat_id, text='Аргументы неверны. Должны быть два числа.')
    else:
        pass

def image(update, context):
    """Return an image"""
    # TODO - Make a random image from imgur using their API.
    link = 'https://imgur.com/gallery/F4IKheK'
    context.bot.send_message(chat_id=update.message.chat_id, text=link)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # TODO - fix a bug when additional bots break the commands of this bot
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    TOKEN = ""
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("echo", echo))
    dp.add_handler(CommandHandler("flip", flip))
    dp.add_handler(CommandHandler("myiq", myiq))
    dp.add_handler(CommandHandler("muhdick", muhdick))
    dp.add_handler(CommandHandler("randomnumber", randomnumber))

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
