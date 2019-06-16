"""
Authors (telegrams) - @doitforgachi, @dovaogedot
"""

import datetime
import logging
import random
import re
from os import environ

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

# Bot initiatlization
TOKEN = environ.get("TG_BOT_TOKEN")
bot = Bot(TOKEN)

# Antispammer variables
spam_counter = {}
ANTISPAMMER_EXCEPTIONS = {
    255295801: "doitforricardo",
    413327053: "comradesanya",
    205762941: "dovaogedot",
    }

# Delays in minutes for the bot
INDIVIDUAL_USER_DELAY = 1
ERROR_DELAY = 1
CHAT_DELAY = 10


def help(update, context):
    """Help message"""
    if antispammer(update):
        help_text = (
            "Пример команды для бота: /help@random_welcome_bot\n"
            "[ ] в самой команде не использовать.\n"
            "/help - Это меню;\n"
            "/cat - Случайное фото котика;\n"
            "/dog - Случайное фото собачки;\n"
            "/image [тематика] - Случайное фото. Можно задать тематику на английском;\n"
            "/dadjoke - Случайная шутка бати;\n"
            "\n"
            "Генераторы чисел:\n"
            "/myiq - Мой IQ (0 - 200);\n"
            "/muhdick - Длина моего шланга (0 - 25);\n"
            "/flip - Бросить монетку (Орёл или Решка);\n"
            "/randomnumber [число1] [число2] - Случайное число в выбранном диапазоне, включая концы;\n"
            "\n"
            "Дополнительная информация:\n"
            "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
            "2. Кулдаун бота на любые команды 1 минута.\n"
            "3. Кулдаун на каждую команду 10 минуту для индивидуального пользователя.\n"
            "4. Ошибка о кулдауне даётся минимум через каждую 1 минуту."
        )
        bot.send_message(chat_id=update.message.chat_id,
                         text=help_text,
                         reply_to_message_id=update.message.message_id)


def welcomer(update, context):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    # A bot entered the chat
    if update.message.new_chat_members[0].is_bot:
        bot.send_message(chat_id=update.message.chat_id,
                         text="УХОДИ, НАМ БОЛЬШЕ БОТОВ НЕ НАДО. БАН ЕМУ.",
                         reply_to_message_id=update.message.message_id)
    # Another user joined the chat
    else:
        reply = (f"Приветствуем вас в Думерском Чате, {update.message.new_chat_members[0].first_name}!\n"
                 f"По традициям группы, с вас Имя, Фамилия, Фото ног.")
        bot.send_message(chat_id=update.message.chat_id,
                         text=reply,
                         reply_to_message_id=update.message.message_id)


def farewell(update, context):
    """Goodbye message"""
    # A a bot was removed
    if update.message.left_chat_member.is_bot:
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"{update.message.left_chat_member.first_name}'a убили, красиво. Уважаю.",
                         reply_to_message_id=update.message.message_id)


def reply_to_text(update, context):
    """Replies to regular text messages"""
    # Handle the word doomer if the message is not edited
    if update.message is not None:
        # Find the word start
        doomer_word_start = update.message.text.lower().find('думер')
        if doomer_word_start != -1:
            # Get the word with symbol, strip symbols using re and send the reply
            word_with_symbols = update.message.text.lower()[doomer_word_start:].replace('думер', 'хуюмер').split()[0]
            reply = re.sub(r'[^\w]', '', word_with_symbols).strip('01234556789')
            bot.send_message(chat_id=update.message.chat_id,
                             text=reply,
                             reply_to_message_id=update.message.message_id)


def flip(update, context):
    """Flip a Coin"""
    if antispammer(update):
        flip_outcome = random.choice(['Орёл!', 'Решка!'])
        bot.send_message(chat_id=update.message.chat_id,
                         text=flip_outcome,
                         reply_to_message_id=update.message.message_id)


def myiq(update, context):
    """Return IQ level (0-200)"""
    if antispammer(update):
        iq_level = random.randint(0, 200)
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
    if antispammer(update):
        muh_dick = random.randint(0, 25)
        if muh_dick == 0:
            reply = f"У тебя нет члена (0 см) \U0001F62C! Ты евнух, братишка. (0 - 25)"
        elif 1 <= muh_dick <= 11:
            reply = f"Длина твоего стручка {muh_dick} см \U0001F923! (0 - 25)"
        elif 12 <= muh_dick <= 17:
            reply = f"Длина твоей палочки {muh_dick} см! (0 - 25)"
        else:
            reply = f"Длина твоего шланга {muh_dick} см! (0 - 25)"
        bot.send_message(chat_id=update.message.chat_id,
                         text=reply,
                         reply_to_message_id=update.message.message_id)


def randomnumber(update, context):
    """Return a random number between two integers"""
    if antispammer(update):
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
    # Go to a website with a json, that contains a link, pass the link to the bot, let the server download the
    # image/video/gif
    if antispammer(update):
        response = requests.get('https://random.dog/woof.json').json()
        if 'mp4' in response['url']:
            bot.send_video(chat_id=update.message.chat_id,
                           video=response['url'],
                           reply_to_message_id=update.message.message_id)
        elif 'gif' in response['url']:
            bot.send_animation(chat_id=update.message.chat_id,
                               animation=response['url'],
                               reply_to_message_id=update.message.message_id)
        else:
            bot.send_photo(chat_id=update.message.chat_id,
                           photo=response['url'],
                           reply_to_message_id=update.message.message_id)


def cat(update, context):
    """Get a random cat image"""
    # Go to a website with a json, that contains a link, pass the link to the bot, let the server download the image
    if antispammer(update):
        response = requests.get('http://aws.random.cat/meow').json()
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=response['file'],
                       reply_to_message_id=update.message.message_id)


def image(update, context):
    """Create a command for random images"""

    def image_unsplash(user_request, update):
        """Function that gets random images from unsplash.com"""
        # Create a user request
        user_request = ','.join(user_request)
        # Ask the server
        response = requests.get(f'https://source.unsplash.com/500x700/?{user_request}')
        # Reply the response with the photo
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=response.url,
                       reply_to_message_id=update.message.message_id)

    def image_pixabay(user_request, update):
        """Function that gets random images from pixabay.com"""
        # Create a user request
        user_request = '+'.join(user_request)
        # Request the server for the dictionary with links to images
        response = requests.get('https://pixabay.com/api/',
                                params={
                                    'key': '12793256-08bafec09c832951d5d3366f1',
                                    'q': user_request,
                                    "safesearch": "false",
                                    "lang": "en"
                                    }).json()
        # If there are hits, reply with photo
        if response['totalHits'] != 0:
            photo = random.choice(response['hits'])['largeImageURL']
            bot.send_photo(chat_id=update.message.chat_id,
                           photo=photo,
                           reply_to_message_id=update.message.message_id)
        # If no hits, give an error
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text='Фото по запросу не найдено.',
                             reply_to_message_id=update.message.message_id)

    if antispammer(update):
        # Get user request, remove the bot command
        user_request = update.message.text.split()
        user_request.pop(0)
        # Use a random source
        if random.randint(0, 1) == 0:
            image_pixabay(user_request, update)
        else:
            image_unsplash(user_request, update)


def dadjoke(update, context):
    """Get a random dad joke"""
    if antispammer(update):
        # Retrieve the website source, find the joke in the code.
        response = requests.get('https://icanhazdadjoke.com/')
        soup = BeautifulSoup(response.text, "lxml")
        joke = str(soup.find_all('meta')[-5])[15:][:-30]
        bot.send_message(chat_id=update.message.chat_id,
                         reply_to_message_id=update.message.message_id,
                         text=joke)


def antispammer(update):
    """
    Check if the user is spamming
    Delay of 1 minute for all commands toward the bot
    Delay of 10 minutes for individual user commands, changeable.
    """
    # Get the time now to compare to previous messages
    message_time = datetime.datetime.now()
    # Add exception for the bot developer to be able to run tests
    if update.message.from_user.id in ANTISPAMMER_EXCEPTIONS:
        return True
    # Create a holder for errors
    error_message = ''
    # If the chat has been encountered before, go into its info, otherwise create chat info in spam_counter
    if update.message.chat_id in spam_counter:
        # First check if there is a chat cooldown (1 minute)
        if message_time > (spam_counter[update.message.chat_id]['last_chat_message']
                           + datetime.timedelta(minutes=INDIVIDUAL_USER_DELAY)):
            spam_counter[update.message.chat_id]['last_chat_message'] = message_time
            chat_cooldown = False
        else:
            error_message += "Бот отвечает на команды пользователей минимум через каждую 1 минуту.\n"
            chat_cooldown = True

        # Next check if there is a user cooldown (10 minute)
        if update.message.from_user.id in spam_counter[update.message.chat_id]:
            if message_time > (spam_counter[update.message.chat_id][update.message.from_user.id]
                               + datetime.timedelta(minutes=CHAT_DELAY)):
                spam_counter[update.message.chat_id][update.message.from_user.id] = message_time
                user_cooldown = False
            else:
                error_message += "Ответ индивидуальным пользователям на команды минимум через каждые 10 минут.\n"
                user_cooldown = True
        else:
            spam_counter[update.message.chat_id][update.message.from_user.id] = message_time
            user_cooldown = False
    else:
        spam_counter[update.message.chat_id] = {}
        spam_counter[update.message.chat_id]['last_chat_message'] = message_time
        spam_counter[update.message.chat_id][update.message.from_user.id] = message_time
        return True

    # If there is no user cooldown or a chat cooldown, return True to allow the commands to run
    if not chat_cooldown and not user_cooldown:
        return True
    else:
        # Give error at minimum every 1 minute
        if 'last_error' in spam_counter[update.message.chat_id]:
            if message_time > (spam_counter[update.message.chat_id][update.message.from_user.id]
                               + datetime.timedelta(minutes=ERROR_DELAY)):
                spam_counter[update.message.chat_id]['last_error'] = message_time
                bot.send_message(chat_id=update.message.chat_id,
                                 reply_to_message_id=update.message.message_id,
                                 text=error_message + "Эта ошибка тоже появляется минимум каждую 1 минуту.\n")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             reply_to_message_id=update.message.message_id,
                             text=error_message + "Эта ошибка тоже появляется минимум каждую 1 минуту.\n")
            spam_counter[update.message.chat_id]['last_error'] = message_time
        return False


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("flip", flip))
    dispatcher.add_handler(CommandHandler("myiq", myiq))
    dispatcher.add_handler(CommandHandler("muhdick", muhdick))
    dispatcher.add_handler(CommandHandler("randomnumber", randomnumber))
    dispatcher.add_handler(CommandHandler("dog", dog))
    dispatcher.add_handler(CommandHandler("cat", cat))
    dispatcher.add_handler(CommandHandler("image", image))
    dispatcher.add_handler(CommandHandler("dadjoke", dadjoke))

    # add message handlers
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcomer))
    dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, farewell))
    dispatcher.add_handler(MessageHandler(Filters.text, reply_to_text))

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
