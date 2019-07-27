"""
Authors (telegrams) - @doitforgachi, @dovaogedot
"""

import datetime
import logging
import pickle
import random
from os import environ
from time import sleep

import requests
from telegram import Bot
from telegram import TelegramError
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

# Import huts, slaps
from huts import HUTS
from slaps import SLAPS


# Enable logging into file
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename='logs.log')
LOGGER = logging.getLogger(__name__)

# Import list of muted people, if fails to import, create a new list and log the error
try:
    with open('muted.py', 'rb') as muted_storer:
        MUTED = pickle.load(muted_storer)
except (EOFError, FileNotFoundError) as error:
    LOGGER.error(error)
    MUTED = {}

# Bot initialization
TOKEN = environ.get("TG_BOT_TOKEN")
BOT = Bot(TOKEN)

# Antispammer variables
SPAM_COUNTER = {}
DEVELOPER_ID = 255295801
ANTISPAM_EXCEPTIONS = {
    DEVELOPER_ID: "doitforricardo",
    413327053: "comradesanya",
    205762941: "dovaogedot",
    185500059: "melancholiak",
    }

# Delays in seconds for the BOT
CHAT_DELAY = 1 * 60  # One minute
INDIVIDUAL_USER_DELAY = 10 * 60  # Ten minutes
INDIVIDUAL_REPLY_DELAY = 5 * 60  # Five minutes
ERROR_DELAY = 1 * 60  # One minute

# Request timeout time in seconds
REQUEST_TIMEOUT = 1.2


def start(update, context):
    """Send out a start message"""
    _send_reply(update, 'Думер бот в чате. Для списка функций используйте /help.')


def help(update, context):
    """Help message"""
    if _command_antispam_passed(update):
        help_text = (
            f"<b>Пример команды для бота:</b> /help@{BOT.username}\n"
            "/help - Это меню;\n"
            "/cat - Случайное фото котика;\n"
            "/dog - Случайное фото собачки;\n"
            "/dadjoke - Случайная шутка бати;\n"
            "/slap - Кого-то унизить (надо ответить жертве, чтобы бот понял кого бить);\n"
            "/duel - Устроить дуэль (надо ответить тому, чтобыс кем будет дуэль)\n"
            "/rules - Правила думерского чата;\n"
            "\n"
            "<b>Генераторы чисел:</b>\n"
            "/myiq - Мой IQ (1 - 200);\n"
            "/muhdick - Длина моего шланга (1 - 25);\n"
            "/flip - Бросить монетку (Орёл/Решка);\n"
            "\n"
            "<b>Дополнительная информация:</b>\n"
            "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
            f"2. Кулдаун бота на любые команды {CHAT_DELAY // 60} минута.\n"
            f"3. Кулдаун на каждую команду {INDIVIDUAL_USER_DELAY // 60} минуту для "
            f"индивидуального пользователя.\n"
            f"4. Ошибка о кулдауне даётся минимум через каждую {ERROR_DELAY // 60} минуту. "
            f"Спам команд во время кд удаляется.\n"
        )
        _send_reply(update, help_text, parse_mode='HTML')


def rules(update, context):
    """Reply to the user with the rules of the chat"""
    if _command_antispam_passed(update):
        reply_text = ("1. Не быть зумером, не сообщать зумерам о думском клубе;\n"
                      "2. Всяк сюда входящий, с того фото своих ножек;\n"
                      "3. Никаких гей-гифок;\n"
                      "4. За спам - фото своих ног;\n"
                      "5. Думерскую историю рассказать;\n")
        _send_reply(update, reply_text)


def welcomer(update, context):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    # A BOT entered the chat, and not this BOT
    if update.message.new_chat_members[0].is_bot and \
            update.message.new_chat_members[0].id != BOT.id:
        reply_text = f"Уходи, {update.message.new_chat_members[0].first_name}, нам больше ботов не надо."
    # This BOT joined the chat
    elif update.message.new_chat_members[0].id == BOT.id:
        reply_text = "Думер бот в чате. Для списка функций используйте /help."
    # Another user joined the chat
    else:
        new_member = update.message.new_chat_members[0].first_name
        reply_text = (f"Приветствуем вас в Думерском Чате, {new_member}!\n"
                      f"По традициям группы, с вас фото своих ног.\n")
    _send_reply(update, reply_text)


def farewell(update, context):
    """Goodbye message"""
    # A a BOT was removed
    if update.message.left_chat_member.is_bot:
        _send_reply(
            update, f"{update.message.left_chat_member.first_name}'a убили, красиво, уважаю.")


def message_filter(update, context):
    """Replies to all messages
    Думер > Земляночка > """
    if update.message is not None:
        # If user is in the muted list, delete his message unless he is in exceptions
        # to avoid possible self-mutes
        if update.message.chat_id in MUTED:
            if update.message.from_user.id in MUTED[update.message.chat_id] and \
                    update.message.from_user.id not in ANTISPAM_EXCEPTIONS:
                _try_to_delete_message(update)
        # Handle the word doomer
        elif _doomer_word_handler(update)[0]:
            if _text_antispam_passed(update):
                _send_reply(update, _doomer_word_handler(update)[1])
        # Handle землянoчкy
        elif _anprim_word_handler(update):
            if _text_antispam_passed(update):
                BOT.send_photo(chat_id=update.message.chat_id,
                               photo=random.choice(HUTS),
                               caption='Эх, жить бы подальше от общества как анприм и там думить..',
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
    # If the word is not found, return False
    return (False,)


def _anprim_word_handler(update):
    """Image of earth hut"""
    variations = ['земляночку бы', 'земляночкy бы', 'землянoчку бы', 'зeмляночку бы',
                  'землянoчкy бы', 'зeмляночкy бы', 'зeмлянoчку бы', 'зeмлянoчкy бы']
    # If the word is found, return true
    for variation in variations:
        if variation in update.message.text.lower():
            return True
    # If the word is not found, return false
    return False


def flip(update, context):
    """Flip a Coin"""
    if _command_antispam_passed(update):
        _send_reply(update, random.choice(['Орёл!', 'Решка!']))


def myiq(update, context):
    """Return IQ level (1 - 200)"""
    if _command_antispam_passed(update):
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
        _send_reply(update, reply_text)


def muhdick(update, context):
    """Return dick size in cm (1 - 25)"""
    if _command_antispam_passed(update):
        muh_dick = random.randint(1, 25)
        reply_text = f"Длина твоей палочки {muh_dick} см! "
        if 1 <= muh_dick <= 11:
            reply_text += "\U0001F92D "
        elif 21 <= muh_dick <= 25:
            reply_text += "\U0001F631 "
        reply_text += "(1 - 25)"
        _send_reply(update, reply_text)


def dog(update, context):
    """Get a random dog image"""
    # Go to a website with a json, that contains a link, pass the link to the BOT,
    # let the server download the image/video/gif
    if _command_antispam_passed(update):
        try:
            response = requests.get(
                'https://random.dog/woof.json', timeout=REQUEST_TIMEOUT).json()
            # Get the file extension of the file
            file_extension = response['url'].split('.')[-1]
            # Depending on the file extension, use the proper BOT method
            if 'mp4' in file_extension:
                BOT.send_video(chat_id=update.message.chat_id,
                               video=response['url'],
                               reply_to_message_id=update.message.message_id)
            elif 'gif' in file_extension:
                BOT.send_animation(chat_id=update.message.chat_id,
                                   animation=response['url'],
                                   reply_to_message_id=update.message.message_id)
            else:
                BOT.send_photo(chat_id=update.message.chat_id,
                               photo=response['url'],
                               reply_to_message_id=update.message.message_id)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as error:
            LOGGER.error(error)
            _send_reply(update, 'Думер умер на пути к серверу.')


def cat(update, context):
    """Get a random cat image"""
    # Go to a website with a json, that contains a link, pass the link to the BOT,
    # let the server download the image
    if _command_antispam_passed(update):
        try:
            response = requests.get(
                'http://aws.random.cat/meow', timeout=REQUEST_TIMEOUT).json()
            BOT.send_photo(chat_id=update.message.chat_id,
                           photo=response['file'],
                           reply_to_message_id=update.message.message_id)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as error:
            LOGGER.error(error)
            _send_reply(update, 'Думер умер на пути к серверу.')


def dadjoke(update, context):
    """Get a random dad joke"""
    if _command_antispam_passed(update):
        # Retrieve the website source, find the joke in the code.
        headers = {'Accept': 'application/json'}
        try:
            response = requests.get(
                'https://icanhazdadjoke.com/', headers=headers, timeout=REQUEST_TIMEOUT).json()
            _send_reply(update, response['joke'])
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as error:
            LOGGER.error(error)
            _send_reply(update, 'Думер умер на пути к серверу.')


def slap(update, context):
    """Slap with random item"""
    if _command_antispam_passed(update):
        # List the items that the target will be slapped with
        # Check if the user has indicated the target by making his message a reply
        if update.message.reply_to_message is None:
            reply_text = ('Кого унижать то будем?\n'
                          'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
        else:
            # Shorten code and strip of [] to remove interference with Markdown
            initiator = update.message.from_user.first_name.strip('[]')
            target = update.message.reply_to_message.from_user.first_name.strip('[]')
            # Generate the answer + create the reply using markdown. Use weighted actions.
            weighted_keys = []
            for action, items in SLAPS.items():
                weighted_keys += [action] * len(items)
            action = random.choice(weighted_keys)
            # Slap using markdown, as some people don't have usernames to use them for notification
            reply_text = f"[{initiator}](tg://user?id={update.message.from_user.id}) {action} " \
                         f"[{target}](tg://user?id={update.message.reply_to_message.from_user.id}) " \
                         f"{random.choice(SLAPS[action])}"
        _send_reply(update, reply_text, parse_mode='Markdown')


def duel(update, context):
    """Duel to solve any kind of argument"""

    def _send_message(update, text_message, sleep_time: float = 0.25):
        """Shortener for normal messages with sleep"""
        BOT.send_message(chat_id=update.message.chat_id,
                         text=text_message,
                         parse_mode='Markdown')
        sleep(sleep_time)

    if _command_antispam_passed(update):
        # If not replied, ask for the target
        if update.message.reply_to_message is None:
            _send_reply(update, 'С кем дуэль проводить будем?')
        else:
            # Shorten the code, format the names
            initiator_name = update.message.from_user.first_name.strip('[]').capitalize()
            initiator_id = update.message.from_user.id
            target_name = update.message.reply_to_message.from_user.first_name.strip('[]').capitalize()
            target_id = update.message.reply_to_message.from_user.id
            participant_list = [(initiator_name, initiator_id), (target_name, target_id)]
            # Get the winner and the loser
            winner = participant_list.pop(random.choice([0, 1]))
            loser = participant_list[0]
            # Start the dueling text
            _send_message(update, 'Дуэлисты расходятся...')
            _send_message(update, 'Готовятся к выстрелу...')
            _send_message(update, '***BAM BAM***')
            duel_message = f'[{winner[0]}](tg://user?id={winner[1]}) подстрелил ' \
                           f'[{loser[0]}](tg://user?id={loser[1]}) как свинью!\n' \
                           f'Решительная победа за [{winner[0]}](tg://user?id={winner[1]}).'
            # Give result
            _send_message(update, duel_message, sleep_time=0)


def mute(update, context):
    """Autodelete messages of a user (only usable by the developer)"""
    try:
        # Shorten code
        to_mute_id = update.message.reply_to_message.from_user.id
        # Only works for the dev
        if update.message.from_user.id == DEVELOPER_ID:
            # If the chat does no exist, add instantly to muted
            if update.message.chat_id in MUTED:
                # Add to muted dictionary id and first name
                MUTED[update.message.chat_id][to_mute_id] = \
                    update.message.reply_to_message.from_user.first_name
                # If last name exists, add it too
                if update.message.reply_to_message.from_user.last_name:
                    MUTED[update.message.chat_id][
                        to_mute_id] += f' {update.message.reply_to_message.from_user.last_name}'
            # If the chat doesn't exist, create chat entry and add to muted
            else:
                MUTED[update.message.chat_id] = {}
                MUTED[update.message.chat_id][to_mute_id] = \
                    update.message.reply_to_message.from_user.first_name
                if update.message.reply_to_message.from_user.last_name:
                    MUTED[update.message.chat_id][
                        to_mute_id] += f' {update.message.reply_to_message.from_user.last_name}'
            # Send photo and explanation to the silenced person
            BOT.send_photo(chat_id=update.message.chat_id,
                           photo='https://www.dropbox.com/s/m1ek8cgis4echn9/silence.jpg?raw=1',
                           caption='Теперь ты под салом и не можешь писать в чат.',
                           reply_to_message_id=update.message.reply_to_message.message_id)
            # Record to database
            with open('muted.py', 'wb') as muted_storer:
                pickle.dump(MUTED, muted_storer)
    # In case when not a reply
    except AttributeError:
        _send_reply(update, 'Надо ответить пользователю.')


def unmute(update, context):
    """Stop autodeletion of messages of a user (only usable by the developer)"""
    # Only if the developer calls it
    if update.message.from_user.id == DEVELOPER_ID:
        # Create to enable unmute by reply and id
        to_unmute_id = None
        chat_id = update.message.chat_id
        # Check for arguments in form of the id
        if len(update.message.text.split()) > 1 and len(str(update.message.text.split()[1])) == 9:
            # Try to get id
            try:
                to_unmute_id = int(update.message.text.split()[1])
            # If didn't get id, check for reply
            except ValueError:
                # Check for reply
                try:
                    to_unmute_id = update.message.reply_to_message.from_user.id
                # If no reply, say that no argument was given
                except AttributeError:
                    _send_reply(update, 'Вы забыли указать айди.')
        # For replies, if no id is given
        else:
            to_unmute_id = update.message.reply_to_message.from_user.id
        # Only if the user is in the MUTED list
        if to_unmute_id is not None:
            # If the chat doesn't exist, then the user was never muted
            if chat_id in MUTED:
                # If was muted, unmute and notify of success
                if to_unmute_id in MUTED[chat_id]:
                    _send_reply(update, f'Успешно снял сало с '
                                        f'[{MUTED[chat_id][to_unmute_id]}](tg://user?id={to_unmute_id}).',
                                parse_mode='Markdown')
                    MUTED[chat_id].pop(to_unmute_id)
                    # If there are no more muted people in the chat, remove the chat instance
                    # This is garbage collection
                    if len(MUTED[chat_id]) == 0:
                        MUTED.pop(chat_id)
                    # Store in database
                    with open('muted.py', 'wb') as muted_storer:
                        pickle.dump(MUTED, muted_storer)
                else:
                    _send_reply(update, 'Этот пользователь уже не был в списке молчунов.')
            else:
                _send_reply(update, 'Этот пользователь уже не был в списке молчунов.')
        else:
            _send_reply(update, 'Кого пытаемся убрать из списка молчунов?')


def mutelist(update, context):
    """Get the list of muted ids"""
    # Only for developer
    if update.message.from_user.id == DEVELOPER_ID:
        # Somewhat of a table
        id_list = 'имя - айди пользователя:\n'
        # If chat existed, add users
        if update.message.chat_id in MUTED:
            for muted_id, muted_name in MUTED[update.message.chat_id].items():
                id_list += f'{muted_name} - {muted_id};\n'
        # If any entries, reply
        if id_list != 'имя - айди пользователя:\n':
            _send_reply(update, id_list)
        # If no entries, say nowhere there
        else:
            _send_reply(update, 'Cписок молчунов пуст.')


def _command_antispam_passed(update):
    """
    Check if the user is spamming
    Delay of CHAT_DELAY minute(s) for all commands toward the BOT
    Delay of INDIVIDUAL_USER_DELAY minute(s) for individual user commands, changeable.
    """
    # Shorten code
    chatid = update.message.chat_id
    userid = update.message.from_user.id
    # Turn off antispam for private conversations
    if update.message.chat.type == 'private':
        return True
    # Add exception for the BOT developer to be able to run tests
    if userid in ANTISPAM_EXCEPTIONS:
        return True
    # Remove messages from muted users
    if chatid in MUTED:
        if userid in MUTED[chatid]:
            _try_to_delete_message(update)
    # Get the time now to compare to previous messages
    message_time = datetime.datetime.now()
    # Create a holder for errors
    error_message = ''
    # If the chat has been encountered before, go into its info,
    # otherwise create chat info in SPAM_COUNTER
    if chatid in SPAM_COUNTER:
        # First check if there is a chat cooldown (1 minute)
        if 'last_chat_command' in SPAM_COUNTER[chatid]:
            if message_time > (SPAM_COUNTER[chatid]['last_chat_command'] +
                               datetime.timedelta(seconds=CHAT_DELAY)):
                SPAM_COUNTER[chatid]['last_chat_command'] = message_time
                chat_cooldown = False
            else:
                error_message += \
                    f"Бот отвечает на команды пользователей минимум через " \
                    f"каждую {CHAT_DELAY // 60} минуту.\n"
                chat_cooldown = True
        else:
            SPAM_COUNTER[chatid]['last_chat_command'] = message_time
            SPAM_COUNTER[chatid][userid] = {}
            SPAM_COUNTER[chatid][userid]['command_replied'] = message_time
            return True

        # Next check if there is a user cooldown (INDIVIDUAL_USER_DELAY minute)
        if userid in SPAM_COUNTER[chatid]:
            if 'command_replied' in SPAM_COUNTER[chatid][userid]:
                if message_time > (SPAM_COUNTER[chatid][userid]['command_replied'] +
                                   datetime.timedelta(seconds=INDIVIDUAL_USER_DELAY)):
                    SPAM_COUNTER[chatid][userid]['command_replied'] = message_time
                    user_cooldown = False
                else:
                    error_message += \
                        f"Ответ индивидуальным пользователям на команды минимум через " \
                        f"каждые {INDIVIDUAL_USER_DELAY // 60} минут.\n"
                    user_cooldown = True
            else:
                if not chat_cooldown:
                    SPAM_COUNTER[chatid][userid]['command_replied'] = message_time
                user_cooldown = False
        else:
            if not chat_cooldown:
                SPAM_COUNTER[chatid][userid] = {}
                SPAM_COUNTER[chatid][userid]['command_replied'] = message_time
            user_cooldown = False
    else:
        SPAM_COUNTER[chatid] = {}
        SPAM_COUNTER[chatid]['last_chat_command'] = message_time
        SPAM_COUNTER[chatid][userid] = {}
        SPAM_COUNTER[chatid][userid]['command_replied'] = message_time
        return True

    # If there is no user cooldown or a chat cooldown, return True to allow the commands to run
    if not chat_cooldown and not user_cooldown:
        return True
    # Give error at minimum every 1 minute (ERROR_DELAY)
    if 'last_error' in SPAM_COUNTER[chatid]:
        if message_time > (SPAM_COUNTER[chatid]['last_error'] +
                           datetime.timedelta(seconds=ERROR_DELAY)):
            SPAM_COUNTER[chatid]['last_error'] = message_time
            error_message += (f"Эта ошибка тоже появляется минимум каждую {ERROR_DELAY // 60} "
                              f"минуту.\nЗапросы во время кулдауна ошибки будут удаляться.")
            _send_reply(update, error_message)
        else:
            _try_to_delete_message(update)
    else:
        error_message += (f"Эта ошибка тоже появляется минимум каждую {ERROR_DELAY // 60} минуту.\n"
                          f"Запросы во время кулдауна ошибки будут удаляться.")
        _send_reply(update, error_message)
        SPAM_COUNTER[chatid]['last_error'] = message_time
    return False


def _text_antispam_passed(update):
    """Checks if somebody is spamming reply_all words"""
    # Turn off antispam for private conversations
    if update.message.chat.type == 'private':
        return True
    # Add exception for the BOT developer to be able to run tests
    if update.message.from_user.id in ANTISPAM_EXCEPTIONS:
        return True
    message_time = datetime.datetime.now()
    # Shorten code
    chatid = update.message.chat_id
    userid = update.message.from_user.id
    if chatid in SPAM_COUNTER:
        if userid in SPAM_COUNTER[chatid]:
            if 'text_replied' in SPAM_COUNTER[chatid][userid]:
                if message_time > (SPAM_COUNTER[chatid][userid]['text_replied'] +
                                   datetime.timedelta(seconds=INDIVIDUAL_REPLY_DELAY)):
                    SPAM_COUNTER[chatid][userid]['text_replied'] = message_time
                    return True
                else:
                    return False
            else:
                SPAM_COUNTER[chatid][userid]['text_replied'] = message_time
                return True
        else:
            SPAM_COUNTER[chatid][userid] = {}
            SPAM_COUNTER[chatid][userid]['text_replied'] = message_time
            return True
    else:
        SPAM_COUNTER[chatid] = {}
        SPAM_COUNTER[chatid]['last_chat_reply'] = message_time
        SPAM_COUNTER[chatid][userid] = {}
        SPAM_COUNTER[chatid][userid]['text_replied'] = message_time
        return True


def _try_to_delete_message(update):
    """Try to delete user message using admin rights. If no rights, pass."""
    try:
        BOT.delete_message(chat_id=update.message.chat_id,
                           message_id=update.message.message_id)
    except TelegramError:
        pass


def _send_reply(update, text: str, parse_mode: str = None):
    """Shortener of replies"""
    BOT.send_message(chat_id=update.message.chat_id,
                     text=text,
                     reply_to_message_id=update.message.message_id,
                     parse_mode=parse_mode)


def error(update, context):
    """Log Errors caused by Updates."""
    LOGGER.warning('Error "%s" caused by update "%s"', context.error, update)


def main():
    """Start the BOT."""
    # Create the Updater and pass it your BOT's token.
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("flip", flip))
    dispatcher.add_handler(CommandHandler("myiq", myiq))
    dispatcher.add_handler(CommandHandler("muhdick", muhdick))
    dispatcher.add_handler(CommandHandler("dog", dog))
    dispatcher.add_handler(CommandHandler("cat", cat))
    dispatcher.add_handler(CommandHandler("dadjoke", dadjoke))
    dispatcher.add_handler(CommandHandler("slap", slap))
    dispatcher.add_handler(CommandHandler("rules", rules))
    dispatcher.add_handler(CommandHandler('mute', mute))
    dispatcher.add_handler(CommandHandler('unmute', unmute))
    dispatcher.add_handler(CommandHandler('mutelist', mutelist))
    dispatcher.add_handler(CommandHandler('duel', duel))

    # add message handlers
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, welcomer))
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.left_chat_member, farewell))
    dispatcher.add_handler(MessageHandler(
        Filters.all, message_filter))

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    # Set clean to True to clean any pending updates on Telegram servers before
    # actually starting to poll. Otherwise the BOT may spam the chat on coming
    # back online
    updater.start_polling(clean=True)

    # Run the BOT until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the BOT gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
