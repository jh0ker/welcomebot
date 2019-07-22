"""
Authors (telegrams) - @doitforgachi, @dovaogedot
"""

import datetime
import logging
import random
from os import environ

import requests
from telegram import Bot, TelegramError
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot initialization
TOKEN = "824227677:AAEXWiwnYPI3M6cZ1MTN2_pzmCdOpGqW6ic"
bot = Bot(TOKEN)

# Antispammer variables
SPAM_COUNTER = {}
ANTISPAMMER_EXCEPTIONS = {
    255295801: "doitforricardo",
    413327053: "comradesanya",
    205762941: "dovaogedot",
    185500059: "melancholiak",
}

# Delays in minutes for the bot
CHAT_DELAY = 1
INDIVIDUAL_USER_DELAY = 10
ERROR_DELAY = 1

# Bot ID
BOT_ID = 705781870

# Request timeout time in seconds
REQUEST_TIMEOUT = 1.2


def help(update, context):
    """Help message"""
    if antispammer_check_passed(update):
        help_text = (
            "Пример команды для бота: /help@random_welcome_bot\n"
            "[ ] в самой команде не использовать.\n"
            "/help - Это меню;\n"
            "/cat - Случайное фото котика;\n"
            "/dog - Случайное фото собачки;\n"
            "/dadjoke - Случайная шутка бати;\n"
            "/slap - Кого-то унизить (надо ответить жертве, чтобы бот понял кого бить);\n"
            "\n"
            "Генераторы чисел:\n"
            "/myiq - Мой IQ (1 - 200);\n"
            "/muhdick - Длина моего шланга (1 - 25);\n"
            "/flip - Бросить монетку (Орёл или Решка);\n"
            "\n"
            "Дополнительная информация:\n"
            "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
            f"2. Кулдаун бота на любые команды {CHAT_DELAY} минута.\n"
            f"3. Кулдаун на каждую команду {INDIVIDUAL_USER_DELAY} минуту для "
            f"индивидуального пользователя.\n"
            f"4. Ошибка о кулдауне даётся минимум через каждую {ERROR_DELAY} минуту. "
            f"Спам удаляется.\n"
        )
        _send_message(update, help_text)


def rules(update, context):
    """Reply to the user with the rules of the chat"""
    reply_text = ("1. Не быть зумером, не сообщать зумерам о думском клубе;\n"
                  "2. Всяк сюда входящий, с того фото ножек;\n"
                  "3. Никаких гей-гифок;\n"
                  "4. За спам - ноги;\n"
                  "5. Думерскую историю рассказать;\n")
    _send_message(update, reply_text)


def welcomer(update, context):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    # A bot entered the chat, and not this bot
    if update.message.new_chat_members[0].is_bot and \
            update.message.new_chat_members[0].id != BOT_ID:
        reply_text = "Уходи, нам больше ботов не надо."
    # This bot joined the chat
    elif update.message.new_chat_members[0].id == BOT_ID:
        reply_text = "Думер бот в чате. Для помощи используйте /help."
    # Another user joined the chat
    else:
        new_member = update.message.new_chat_members[0].first_name
        reply_text = (f"Приветствуем вас в Думерском Чате, {new_member}!\n"
                      f"По традициям группы, с вас фото своих ног.\n")
    _send_message(update, reply_text)


def farewell(update, context):
    """Goodbye message"""
    # A a bot was removed
    if update.message.left_chat_member.is_bot:
        _send_message(
            update, f"{update.message.left_chat_member.first_name}'a убили, красиво. Уважаю.")


def reply_to_text(update, context):
    """Replies to regular text messages
    Думер > Земляночка > """
    if update.message is not None:
        # Handle the word doomer
        if _doomer_word_handler(update)[0]:
            _send_message(update, _doomer_word_handler(update)[1])
        # Handle землянoчкy
        elif _anprim_word_handler(update):
            bot.send_photo(chat_id=update.message.chat_id,
                           photo='http://masterokblog.ru/wp-content/uploads/0_1e5f5d_b67a598d_XXL.jpg',
                           caption='Эх, жить бы подальше от общества как анприм и там думить...',
                           reply_to_message_id=update.message.message_id)


def _doomer_word_handler(update):
    # Make the preparations with variations of the word with latin letters
    variations_with_latin_letters = [
        'думер', 'дyмер', 'дyмeр', 'дyмep', 'думeр', 'думep', 'думеp'
    ]
    doomer_word_start = None
    # Check if any of the variations are in the text, if there are break
    for variation in variations_with_latin_letters:
        position = update.message.text.lower().find(variation)
        if position != -1:
            found_word = variation
            doomer_word_start = position
            break
    # If any of the variations have been found, give a reply
    if doomer_word_start is not None:
        # Find the word in the message, get the word and all adjacent symbol
        word_with_symbols = \
            update.message.text.lower()[doomer_word_start:].replace(
                found_word, 'хуюмер').split()[0]
        reply_word = ''
        # Get only the word, until any number or non alpha symbol is encountered
        for i in word_with_symbols:
            if i.isalpha():
                reply_word += i
            else:
                break
        # Return the reply word
        return (True, reply_word)
    else:
        return (False, )


def _anprim_word_handler(update):
    """Image of earth hut"""
    variations = ['земляночку бы', 'земляночкy бы', 'землянoчку бы', 'зeмляночку бы',
                  'землянoчкy бы', 'зeмляночкy бы', 'зeмлянoчку бы', 'зeмлянoчкy бы']
    for variation in variations:
        if variation in update.message.text.lower():
            return True


def flip(update, context):
    """Flip a Coin"""
    if antispammer_check_passed(update):
        _send_message(update, random.choice(['Орёл!', 'Решка!']))


def myiq(update, context):
    """Return IQ level (1 - 200)"""
    if antispammer_check_passed(update):
        iq_level = random.randint(1, 200)
        reply_text = f"Твой уровень IQ {iq_level}. "
        if iq_level < 85:
            reply_text += "Грустно за тебя, братишка. (1 - 200)"
        elif 85 <= iq_level <= 115:
            reply_text += "Ты норми, братишка. (1 - 200)"
        elif 115 < iq_level <= 125:
            reply_text += "Ты умный, братишка! (1 - 200)"
        else:
            reply_text += "Ты гений, братишка! (1 - 200)"
        _send_message(update, reply_text)


def muhdick(update, context):
    """Return dick size in cm (1 - 25)"""
    if antispammer_check_passed(update):
        muh_dick = random.randint(1, 25)
        reply_text = f"Длина твоей палочки {muh_dick} см! "
        if 1 <= muh_dick <= 11:
            reply_text += "\U0001F92D "
        elif 21 <= muh_dick <= 25:
            reply_text += "\U0001F631 "
        reply_text += "(1 - 25)"
        _send_message(update, reply_text)


def dog(update, context):
    """Get a random dog image"""
    # Go to a website with a json, that contains a link, pass the link to the bot,
    # let the server download the image/video/gif
    if antispammer_check_passed(update):
        try:
            response = requests.get(
                'https://random.dog/woof.json', timeout=REQUEST_TIMEOUT).json()
            # Get the file extension of the file
            file_extension = response['url'].split('.')[-1]
            # Depending on the file extension, use the proper bot method
            if 'mp4' in file_extension:
                bot.send_video(chat_id=update.message.chat_id,
                               video=response['url'],
                               reply_to_message_id=update.message.message_id)
            elif 'gif' in file_extension:
                bot.send_animation(chat_id=update.message.chat_id,
                                   animation=response['url'],
                                   reply_to_message_id=update.message.message_id)
            else:
                bot.send_photo(chat_id=update.message.chat_id,
                               photo=response['url'],
                               reply_to_message_id=update.message.message_id)
        except requests.exceptions.ReadTimeout:
            _send_message(update, 'Думер умер на пути к серверу.')


def cat(update, context):
    """Get a random cat image"""
    # Go to a website with a json, that contains a link, pass the link to the bot,
    # let the server download the image
    if antispammer_check_passed(update):
        try:
            response = requests.get(
                'http://aws.random.cat/meow', timeout=REQUEST_TIMEOUT).json()
            bot.send_photo(chat_id=update.message.chat_id,
                           photo=response['file'],
                           reply_to_message_id=update.message.message_id)
        except requests.exceptions.ReadTimeout:
            _send_message(update, 'Думер умер на пути к серверу.')


def dadjoke(update, context):
    """Get a random dad joke"""
    if antispammer_check_passed(update):
        # Retrieve the website source, find the joke in the code.
        headers = {
            'Accept': 'application/json',
        }
        try:
            response = requests.get(
                'https://icanhazdadjoke.com/', headers=headers, timeout=REQUEST_TIMEOUT).json()
            _send_message(update, response['joke'])
        except requests.exceptions.ReadTimeout:
            _send_message(update, 'Думер умер на пути к серверу.')


def slap(update, context):
    """Slap with random item"""
    if antispammer_check_passed(update):
        # List the items that the target will be slapped with
        action_items = {
            'ударил': ['писюном', 'бутылкой', 'carasiqueом'],
            'обтер лицо': ['яйцами'],
            'пукнул': ['в лицо'],
            'резнул': ['заточкой'],
            'дал': ['пощечину'],
        }
        # Check if the user has indicated the target by making his message a reply
        if update.message.reply_to_message is None:
            reply_text = ('Кого унижать то будем? '
                          'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
        else:
            # Generate the answer + create the reply using markdown. Use weighted actions.
            weighted_keys = []
            for action, items in action_items.items():
                weighted_keys += [action] * len(items)
            action = random.choice(weighted_keys)
            reply_text = f"[{update.message.from_user.first_name}](tg://user?id={update.message.from_user.id}) {action} " \
                f"[{update.message.reply_to_message.from_user.first_name}](tg://user?id={update.message.reply_to_message.from_user.id}) " \
                f"{random.choice(action_items[action])}."
        _send_message(update, reply_text, parse_mode='Markdown')


def antispammer_check_passed(update):
    """
    Check if the user is spamming
    Delay of CHAT_DELAY minute(s) for all commands toward the bot
    Delay of INDIVIDUAL_USER_DELAY minute(s) for individual user commands, changeable.
    """
    # Turn off antispam for private conversations
    if update.message.chat.type == 'private':
        return True
    # Add exception for the bot developer to be able to run tests
    if update.message.from_user.id in ANTISPAMMER_EXCEPTIONS:
        return True
    # Get the time now to compare to previous messages
    message_time = datetime.datetime.now()
    # Create a holder for errors
    error_message = ''
    # If the chat has been encountered before, go into its info,
    # otherwise create chat info in SPAM_COUNTER
    if update.message.chat_id in SPAM_COUNTER:
        # First check if there is a chat cooldown (1 minute)
        if message_time > (SPAM_COUNTER[update.message.chat_id]['last_chat_message']
                           + datetime.timedelta(minutes=CHAT_DELAY)):
            SPAM_COUNTER[update.message.chat_id]['last_chat_message'] = message_time
            chat_cooldown = False
        else:
            error_message += \
                f"Бот отвечает на команды пользователей минимум через каждую {CHAT_DELAY} минуту.\n"
            chat_cooldown = True

        # Next check if there is a user cooldown (INDIVIDUAL_USER_DELAY minute)
        if update.message.from_user.id in SPAM_COUNTER[update.message.chat_id]:
            if message_time > (SPAM_COUNTER[update.message.chat_id][update.message.from_user.id]
                               + datetime.timedelta(minutes=INDIVIDUAL_USER_DELAY)):
                SPAM_COUNTER[update.message.chat_id][update.message.from_user.id] = message_time
                user_cooldown = False
            else:
                error_message += \
                    f"Ответ индивидуальным пользователям на команды минимум через каждые {INDIVIDUAL_USER_DELAY} минут.\n"
                user_cooldown = True
        else:
            if not chat_cooldown:
                SPAM_COUNTER[update.message.chat_id][update.message.from_user.id] = message_time
            user_cooldown = False
    else:
        SPAM_COUNTER[update.message.chat_id] = {}
        SPAM_COUNTER[update.message.chat_id]['last_chat_message'] = message_time
        SPAM_COUNTER[update.message.chat_id][update.message.from_user.id] = message_time
        return True

    # If there is no user cooldown or a chat cooldown, return True to allow the commands to run
    if not chat_cooldown and not user_cooldown:
        return True
    # Give error at minimum every 1 minute (ERROR_DELAY)
    if 'last_error' in SPAM_COUNTER[update.message.chat_id]:
        if message_time > (SPAM_COUNTER[update.message.chat_id]['last_error']
                           + datetime.timedelta(minutes=ERROR_DELAY)):
            SPAM_COUNTER[update.message.chat_id]['last_error'] = message_time
            error_message += (f"Эта ошибка тоже появляется минимум каждую {ERROR_DELAY} минуту.\n"
                              f"Запросы во время кулдауна ошибки будут удаляться.")
            _send_message(update, error_message)
        else:
            _try_to_delete_message(update)
    else:
        error_message += (f"Эта ошибка тоже появляется минимум каждую {ERROR_DELAY} минуту.\n"
                          f"Запросы во время кулдауна ошибки будут удаляться.")
        _send_message(update, error_message)
        SPAM_COUNTER[update.message.chat_id]['last_error'] = message_time
    return False


def _try_to_delete_message(update):
    """Try to delete user message using admin rights. If no rights, pass."""
    try:
        bot.delete_message(chat_id=update.message.chat_id,
                           message_id=update.message.message_id)
    except TelegramError:
        pass


def _send_message(update, text: str, parse_mode: str = None):
    """Shortener of replies"""
    bot.send_message(chat_id=update.message.chat_id,
                     text=text,
                     reply_to_message_id=update.message.message_id,
                     parse_mode=parse_mode)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Error "%s" caused by update "%s"', context.error, update)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("flip", flip))
    dispatcher.add_handler(CommandHandler("myiq", myiq))
    dispatcher.add_handler(CommandHandler("muhdick", muhdick))
    dispatcher.add_handler(CommandHandler("dog", dog))
    dispatcher.add_handler(CommandHandler("cat", cat))
    dispatcher.add_handler(CommandHandler("dadjoke", dadjoke))
    dispatcher.add_handler(CommandHandler("slap", slap))
    dispatcher.add_handler(CommandHandler("rules", rules))

    # add message handlers
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, welcomer))
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.left_chat_member, farewell))
    dispatcher.add_handler(MessageHandler(
        Filters.text, reply_to_text))

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
