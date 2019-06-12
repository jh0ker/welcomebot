"""
Authors (telegrams) - @doitforgachi, @dovaogedot
"""

import logging
import random
from html import escape

import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

bot = Bot("832751678:AAFZo70Y2icygBFO9CU_I4TeJFa_WONfANU")


def help(update, context):
    """Help message"""
    help_text = (
        "Пример команды для бота: /help@random_welcome_bot\n"
        "[ ] в самой команде не использовать.\n"
        "/help - Это меню;\n"
        "/echo [сообщение]- Получить ответ своим же сообщением;\n"
        "/myiq - Мой IQ (0 - 200);\n"
        "/muhdick - Длина моего шланга (0 - 25);\n"
        "/cat - Случайное фото котика;\n"
        "/dog - Случайное фото собачки;\n"
        "/dadjoke - Случайная dad joke;\n"
        "\n"
        "Генераторы чисел:\n"
        "/flip - Бросить монетку (Орёл или Решка);\n"
        "/random [число1] [число2] - Случайное число в выбранном диапазоне, включая концы;"
    )
    bot.send_message(chat_id=update.message.chat_id,
                     text=help_text,
                     reply_to_message_id=update.message.message_id)


def welcome_user(update, context):
    """Welcome message for the user"""
    # Get the message, id, user information.
    logger.info('%s joined to chat %d (%s)'
                % (escape(update.message.new_chat_members[0].first_name),
                   update.message.chat.id,
                   escape(update.message.chat.title)))
    # Generate a reply
    reply_end = random.choice(['Имя, Фамилия. Изображения ног НИ В КОЕМ СЛУЧАЕ не кидать.', 'Имя, Фамилия, фото ног.'])
    reply = (f"Приветствуем вас в Думерском Чате, {update.message.new_chat_members[0].first_name}!\n"
             f"С вас {reply_end}")
    bot.send_message(chat_id=update.message.chat_id,
                     text=reply,
                     reply_to_message_id=update.message.message_id)


def welcome_bot(update, context):
    """Welcome message for a bot"""
    pass


def empty_message(update, context):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    # someone entered chat
    if update.message.new_chat_members is not None:
        # update was added to a group chat
        if update.message.new_chat_members[0].is_bot is True:
            return
        # Another user joined the chat
        else:
            return welcome_user(update, context)


def echo(update, context):
    """Echo back the message"""
    return_echo = update.message.text[6:]
    bot.send_message(chat_id=update.message.chat_id,
                     text=return_echo,
                     reply_to_message_id=update.message.message_id)


def flip(update, context):
    """Flip a Coin"""
    flip_outcome = random.choice(['Орёл!', 'Решка!'])
    bot.send_message(chat_id=update.message.chat_id,
                     text=flip_outcome,
                     reply_to_message_id=update.message.message_id)


def myiq(update, context):
    """Return IQ level (0-200)"""
    iq_level = update.message.chat_id % 201
    if iq_level < 85:
        message = f"Твой уровень IQ {iq_level}. Грустно за тебя, братишка. (0 - 200)"
    elif 85 <= iq_level <= 115:
        message = f"Твой уровень IQ {iq_level}. Ты норми, братишка. (0 - 200)"
    elif 115 < iq_level <= 125:
        message = f"Твой уровень IQ {iq_level}. Ты умный, братишка! (0 - 200)"
    else:
        message = f"Твой уровень IQ {iq_level}. Ты гений, братишка! (0 - 200)"
    bot.send_message(chat_id=update.message.chat_id,
                     text=message,
                     reply_to_message_id=update.message.message_id)


def muhdick(update, context):
    """Return dick size in cm (0-25)"""
    muh_dick = update.message.chat_id % 26
    if muh_dick == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text='У тебя нет члена (0 см) \U0001F62C! (0 - 25)',
                         reply_to_message_id=update.message.message_id)
    elif 1 <= muh_dick <= 11:
        bot.send_photo(chat_id=update.message.chat_id,
                       photo='https://st2.depositphotos.com/1525321/9473/i/950/depositphotos_94736512-stock-photo'
                             '-funny-weak-man-lifting-biceps.jpg',
                       caption=f"Длина твоего стручка {muh_dick} см \U0001F923! (0 - 25)",
                       reply_to_message_id=update.message.message_id)
    elif 12 <= muh_dick <= 17:
        print(type(update.message))
        bot.send_message(chat_id=update.message.chat_id,
                         reply_to_message_id=update.message.message_id,
                         text=f"Длина твоей палочки {muh_dick} см! (0 - 25)")
    else:
        bot.send_photo(chat_id=update.message.chat_id,
                       photo='https://www.thewrap.com//images/2013/11/SharayHayesExhibits-300.jpg',
                       reply_to_message_id=update.message.message_id,
                       caption=f"Длина твоего шланга {muh_dick} см! (0 - 25)")


def randomnumber(update, context):
    """Return a random number between two integers"""
    args = update.message.text[13:].split()
    if len(args) == 2:
        try:
            arg1, arg2 = int(args[0]), int(args[1])
            generated_number = random.randint(arg1, arg2)
            bot.send_message(chat_id=update.message.chat_id,
                             text=f"Выпало {generated_number}.",
                             reply_to_message_id=update.message.message_id)
        except ValueError:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Аргументы неверны. Должны быть два числа.',
                             reply_to_message_id=update.message.message_id)
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text='Неверное использование команды.\n'
                              'Пример: /randomnumber 10 25',
                         reply_to_message_id=update.message.message_id)


def dog(update, context):
    """Get a random dog image"""
    while True:
        response = requests.get('https://random.dog/woof.json').json()
        if 'mp4' not in response['url']:
            break
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=response['url'],
                   reply_to_message_id=update.message.message_id, )


def cat(update, context):
    """Get a random cat image"""
    response = requests.get('http://aws.random.cat/meow').json()
    bot.send_photo(chat_id=update.message.chat_id,
                   photo=response['file'],
                   reply_to_message_id=update.message.message_id)


def dadjoke(update, context):
    """Get a random dad joke"""
    response = requests.get('https://icanhazdadjoke.com/')
    soup = BeautifulSoup(response.text, "lxml")
    joke = str(soup.find_all('meta')[-5])[15:][:-30]
    bot.send_message(chat_id=update.message.chat_id,
                     reply_to_message_id=update.message.message_id,
                     text=joke)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    TOKEN = environ.get("TG_BOT_TOKEN")

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
    dp.add_handler(CommandHandler("dog", dog))
    dp.add_handler(CommandHandler("cat", cat))
    dp.add_handler(CommandHandler("dadjoke", dadjoke))

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
