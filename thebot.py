"""
Authors (telegrams) - @doitforgachi, @dovaogedot
"""

import datetime
import logging
import random
from os import environ
from time import sleep
import sqlite3

import requests
from telegram import Bot
from telegram import TelegramError
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

# Import huts, slaps, duels
from modules.huts import HUTS
from modules.slaps import SLAPS
from modules.duels import DUELS


# Enable logging into file
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename='logs.log')
LOGGER = logging.getLogger(__name__)

# Import the database with muted, exceptions and duel data
db = sqlite3.connect('doomerbot.db', check_same_thread=False)
dbc = db.cursor()

# Import the changelog
try:
    with open('changelog.md', 'r', encoding='utf-8') as changelog:
        CHANGES = changelog.read()
except (EOFError, FileNotFoundError) as changelog_err:
    LOGGER.error(changelog_err)
    CHANGES = 'Не смог добраться до изменений. Что-то не так.'

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
    185500059: "mel_a_real_programmer",
    }

# Delays in seconds for the BOT
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
            "/whatsnew - Новое в боте;\n"
            "/rules - Правила думерского чата;\n"
            "/slap - Кого-то унизить "
            "(надо ответить жертве, чтобы бот понял кого бить);\n"
            "/duel - Устроить дуэль "
            "(надо ответить тому, с кем будет дуэль);\n"
            "/myscore - Мой счёт в дуэлях;\n"
            "/cat - Случайное фото котика;\n"
            "/dog - Случайное фото собачки;\n"
            "/dadjoke - Случайная шутка бати;\n"
            "\n"
            "<b>Генераторы чисел:</b>\n"
            "/myiq - Мой IQ (1 - 200);\n"
            "/muhdick - Длина моего шланга (1 - 25);\n"
            "/flip - Бросить монетку (Орёл/Решка);\n"
            "\n"
            "<b>Дополнительная информация:</b>\n"
            "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
            f"2. Кулдаун на каждую команду {INDIVIDUAL_USER_DELAY // 60} минуту для "
            f"индивидуального пользователя.\n"
            f"3. Ошибка о кулдауне даётся минимум через каждую {ERROR_DELAY // 60} минуту. "
            "Спам команд во время кд удаляется.\n"
        )
        _send_reply(update, help_text, parse_mode='HTML')


def whatsnew(update, context):
    """Reply with all new goodies"""
    if _command_antispam_passed(update):
        # Get the last 3 day changes
        latest_changes = ''
        for change in CHANGES.split('\n\n')[:3]:
            latest_changes += change + '\n\n'
        _send_reply(update, latest_changes, parse_mode='Markdown')


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
    # Create a loop over a list in cast many users have been invited at once
    for new_member in update.message.new_chat_members:
        tagged_user = \
            f"[{new_member.first_name.strip('[]')}](tg://user?id={new_member.id})"
        # A BOT entered the chat, and not this BOT
        if new_member.is_bot and new_member.id != BOT.id:
            reply_text = f"Уходи, {tagged_user}, нам больше ботов не надо."
        # This BOT joined the chat
        elif new_member.id == BOT.id:
            reply_text = "Думер бот в чате. Для списка функций используйте /help."
        # Another user joined the chat
        else:
            reply_text = (f"Приветствуем вас в Думерском Чате, {tagged_user}!\n"
                          f"По традициям группы, с вас фото своих ног.\n")
        _send_reply(update, reply_text, parse_mode='Markdown')


def farewell(update, context):
    """Goodbye message"""
    # A a BOT was removed
    if update.message.left_chat_member.is_bot:
        _send_reply(
            update, f"{update.message.left_chat_member.first_name}'a убили, красиво, уважаю.")


def message_filter(update, context):
    """Replies to all messages
    Думер > Земляночка > """
    try:
        # If user is in the muted list, delete his message unless he is in exceptions
        # to avoid possible self-mutes
        doomer_word = _doomer_word_handler(update)
        if _muted(update):
            _try_to_delete_message(update)
        # Handle the word doomer
        elif doomer_word:
            if _text_antispam_passed(update):
                _send_reply(update, doomer_word)
        # Handle землянoчкy
        elif _anprim_word_handler(update):
            if _text_antispam_passed(update):
                BOT.send_photo(chat_id=update.message.chat_id,
                               photo=random.choice(HUTS),
                               caption='Эх, жить бы подальше от общества как анприм и там думить..',
                               reply_to_message_id=update.message.message_id)
    # Skip the edits, don't log this error
    except AttributeError:
        pass


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
    reply_word = ''
    # If any of the variations have been found, give a reply
    if doomer_word_start is not None:
        # Find the word in the message, get the word and all adjacent symbol
        # noinspection PyUnboundLocalVariable
        word_with_symbols = \
            update.message.text.lower()[doomer_word_start:].replace(
                found_word, 'хуюмер').split()[0]
        # Get only the word, until any number or non alpha symbol is encountered
        for i in word_with_symbols:
            if i.isalpha():
                reply_word += i
            else:
                break
    # If the word is not found, return False
    return reply_word


def _anprim_word_handler(update):
    """Image of earth hut"""
    variations = ['земляночку бы', 'земляночкy бы',
                  'землянoчку бы', 'зeмляночку бы',
                  'землянoчкy бы', 'зeмляночкy бы',
                  'зeмлянoчку бы', 'зeмлянoчкy бы']
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
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
            LOGGER.error(err)
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
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
            LOGGER.error(err)
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
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
            LOGGER.error(err)
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
            # Generate the answer + create the reply using markdown. Use weighted actions.
            # Determine if the initiator failed or succeeded
            success_and_fail = []
            # Add successes
            for action, items in SLAPS['success'].items():
                success_and_fail += ['success'] * len(items)
            # Add failures
            success_and_fail += ['failure'] * len(SLAPS['failure'])
            # Different replies if the user failed or succeeded to slap
            if random.choice(success_and_fail) == 'success':
                weighted_keys = []
                for action, items in SLAPS['success'].items():
                    weighted_keys += [action] * len(items)
                action = random.choice(weighted_keys)
                # Slap using markdown, as some people don't have usernames to use them for notification
                reply_text = f"[{_get(update, 'init_name')}](tg://user?id={_get(update, 'init_id')}) {action} " \
                             f"[{_get(update, 'target_name')}](tg://user?id={_get(update, 'target_id')}) " \
                             f"{random.choice(SLAPS['success'][action])}"
            else:
                action = random.choice(SLAPS['failure'])
                reply_text = f"[{_get(update, 'init_name')}](tg://user?id={_get(update, 'init_id')}) {action}"
        # Send the reply with result
        _send_reply(update, reply_text, parse_mode='Markdown')


def duel(update, context):
    """Duel to solve any kind of argument"""

    def _send_message(text_message, sleep_time: float = 0.25):
        """Shorten normal messages with sleep"""
        nonlocal update
        BOT.send_message(chat_id=update.message.chat_id,
                         text=text_message,
                         parse_mode='Markdown')
        sleep(sleep_time)

    def _score_the_results(p1_kd, p2_kd):
        """Score the results in the database"""
        nonlocal winner, loser
        # Set winner (p1) data
        dbc.execute(f'INSERT OR IGNORE INTO duels (id, firstname) VALUES ("{winner[1]}", "{winner[0]}")')
        dbc.execute(f'UPDATE duels SET kills = kills + {p1_kd[0]} WHERE id={winner[1]}')
        dbc.execute(f'UPDATE duels SET deaths = deaths + {p1_kd[1]} WHERE id={winner[1]}')
        # Set loser (p2) data
        dbc.execute(f'INSERT OR IGNORE INTO duels (id, firstname) VALUES ("{loser[1]}", "{loser[0]}")')
        dbc.execute(f'UPDATE duels SET kills = kills + {p2_kd[0]} WHERE id={loser[1]}')
        dbc.execute(f'UPDATE duels SET deaths = deaths + {p2_kd[1]} WHERE id={loser[1]}')
        db.commit()

    if _command_antispam_passed(update):
        # If not replied, ask for the target
        if update.message.reply_to_message is None:
            _send_reply(update, 'С кем дуэль проводить будем?\n'
                                'Чтобы подуэлиться, надо чтобы вы ответили вашему оппоненту.')
        else:
            # Shorten the code, format the names
            initiator_name, initiator_id = _get(update, 'init_name'), _get(update, 'init_id')
            target_name, target_id = _get(update, 'target_name'), _get(update, 'target_id')
            answered = False
            # Tree for when the target is not self
            if initiator_id != target_id:
                # Tree for when the bot is not the target
                if target_id != BOT.id:
                    participant_list = [(initiator_name, initiator_id),
                                        (target_name, target_id)]
                    # Start the dueling text
                    _send_message('Дуэлисты расходятся...')
                    _send_message('Готовятся к выстрелу...')
                    shooting_sound = random.random() * 100
                    if shooting_sound <= 96:
                        _send_message('***BANG BANG***')
                    elif 96 < shooting_sound <= 98:
                        _send_message('***ПИФ-ПАФ***')
                    else:
                        _send_message('***RAPE GANG***')
                    # Get the winner and the loser
                    winner = participant_list.pop(random.choice([0, 1]))
                    loser = participant_list[0]
                    winner_tag = f'[{winner[0].capitalize()}](tg://user?id={winner[1]})'
                    loser_tag = f'[{loser[0].capitalize()}](tg://user?id={loser[1]})'
                    # Make possible scenarios - 15% miss, 85% hit
                    scenarios = []
                    scenarios += ['miss'] * 3 + ['hit'] * 17
                    random.shuffle(scenarios)
                    scenario = scenarios.pop()
                    # Make the scenario tree
                    if scenario == 'hit':
                        # Get weighted scenarios for 1v1 (onewinner or alldead)
                        weighted_direction = []
                        for direction, scenario in DUELS['1v1'].items():
                            weighted_direction += [direction] * len(scenario)
                        duel_type = random.choice(weighted_direction)
                        event = random.choice(DUELS['1v1'][duel_type])
                        duel_result = event.replace('winner', winner_tag).replace('loser', loser_tag)
                        if duel_type == 'onewinner':
                            duel_result += f'!\nРешительная победа за {winner_tag}.'
                            _score_the_results((1, 0), (0, 1))
                        else:  # 'alldead', no result scoring
                            duel_result += '\nВ этот раз ничья! (0, 0)'
                    else:  # 'miss'
                        duel_result = random.choice(DUELS['1v1']['miss'])
                        duel_result = \
                            duel_result.replace('winner', winner_tag).replace('loser', loser_tag)
                else:
                    # If the bot is the target, send an angry message
                    duel_result = random.choice(DUELS['bot'])
                    _send_reply(update, duel_result)
                    answered = True
            else:
                # Suicide message
                initiator_name_formatted = f'[{initiator_name}](tg://user?id={initiator_id})'
                duel_result = f"{random.choice(DUELS['self']).replace('loser', initiator_name_formatted)}!\n" \
                              f"За суицид экспа/статы не даются!"
            # Give result if not answered and unless the connection died.
            # If it did, try another message.
            if not answered:
                try:
                    _send_message(duel_result, sleep_time=0)
                except TelegramError:
                    _send_message('Пошёл ливень и дуэль была отменена.\n'
                                  'Приносим прощения! Заходите ещё!', sleep_time=0)


def myscore(update, context):
    """Give the user his K/D for duels"""
    if _command_antispam_passed(update):
        user_data = dbc.execute(f'''SELECT * FROM duels WHERE id={update.message.from_user.id}''').fetchone()
        if user_data is not None:
            _send_reply(update, f'Для K/D равен {user_data[2]}/{user_data[3]}.')
        else:
            _send_reply(update, f'Сначала подуэлься, потом спрашивай.')


def mute(update, context):
    """Autodelete messages of a user (only usable by the developer)"""
    # Only works for the dev
    if _get(update, 'init_id') == DEVELOPER_ID:
        try:
            # Shorten code
            to_mute_id, chat_id = _get(update, 'target_id'), _get(update, 'chat_id')
            # Mute and record into database
            dbc.execute(f'''
            INSERT OR IGNORE INTO "muted" (id, chatid, firstname) 
            VALUES 
            ("{to_mute_id}", 
            "{update.message.chat_id}", 
            "{update.message.reply_to_message.from_user.first_name}")''')
            # Get mute reason if there is any
            if len(update.message.text.split()) > 1:
                mutereason = ' '.join((update.message.text).split()[1:])
                dbc.execute(f'''
                    UPDATE "muted" SET reason="{mutereason}" WHERE id={to_mute_id} AND chatid={update.message.chat_id}''')
            db.commit()
            # Send photo and explanation to the silenced person
            BOT.send_photo(chat_id=chat_id,
                           photo='https://www.dropbox.com/s/m1ek8cgis4echn9/silence.jpg?raw=1',
                           caption='Теперь ты под салом и не можешь писать в чат.',
                           reply_to_message_id=update.message.reply_to_message.message_id)
        except KeyError:
            _send_reply(update, 'Пожалуйста, выберите цель.')
    # If an ordinary used tries to use the command
    else:
        if _command_antispam_passed(update):
            _send_reply(update, 'Пошёл нахуй, ты не админ.')


def unmute(update, context):
    """Stop autodeletion of messages of a user (only usable by the developer)"""
    # Only if the developer calls it
    if _get(update, 'init_id') == DEVELOPER_ID:
        # Get chat id, create the replied flag to not make large trees
        replied = False

        # If there is a reply, get the id of the reply target
        if update.message.reply_to_message is not None:
            to_unmute_id = _get(update, 'target_id')
        # If no reply target, take the argument if it exists
        else:
            try:
                to_unmute_id = update.message.text.split()[1]
            except IndexError:
                _send_reply(update, 'Вы не указали цель.')
                to_unmute_id, replied = 'NULL', True
        # Check if the entry exists
        target = dbc.execute(f'''SELECT * FROM "muted" 
        WHERE id={to_unmute_id} AND chatid={update.message.chat_id}''').fetchone()
        if target is not None:
            # Get the target name
            target_name = target[1].strip('[]')
            # Create a markdown tagged name
            target_tagged = f'[{target_name}](tg://user?id={to_unmute_id})'
            # Send the reply of successful unmute
            _send_reply(update, f'Успешно снял мут с {target_tagged}.', parse_mode='Markdown')
            # Delete the user from the muted database and commit
            dbc.execute(f'''DELETE FROM "muted" 
            WHERE id={to_unmute_id} AND chatid={update.message.chat_id}''')
            db.commit()
        elif target is None and not replied:
            _send_reply(update, 'Такого в списке нет.')
    # If an ordinary used tries to use the command
    else:
        if _command_antispam_passed(update):
            _send_reply(update, 'Пошёл нахуй, ты не админ.')


def mutelist(update, context):
    """Get the list of muted ids"""
    # Only for developer
    if _get(update, 'init_id') == DEVELOPER_ID:
        # Somewhat of a table
        id_list = 'имя - айди пользователя:\n'
        # If there are muted targets, send reply, else say that there is nobody
        listnumber = 1
        for entry in dbc.execute(f'SELECT * FROM "muted" WHERE chatid={update.message.chat_id}').fetchall():
            id_list += f'{listnumber}. {entry[1]} - {entry[0]}\n'
            if entry[2]:
                id_list += f'Причина: {entry[2].capitalize()}\n'
            else:
                id_list += 'Причина не указана.\n'
            listnumber += 1
        if id_list != 'имя - айди пользователя:\n':
            _send_reply(update, id_list)
        else:
            _send_reply(update, 'В муте никого нет.')
    # If an ordinary used tries to use the command
    else:
        if _command_antispam_passed(update):
            _send_reply(update, 'Пошёл нахуй, ты не админ.')


def leave(update, context):
    """Make the bot leave the group, usable only by the developer."""
    if _get(update, 'init_id') == DEVELOPER_ID:
        BOT.leave_chat(chat_id=update.message.chat_id)
    else:
        if _command_antispam_passed(update):
            _send_reply(update, 'Пошёл нахуй, ты не админ.')


def _command_antispam_passed(update):
    """
    Check if the user is spamming
    Delay of INDIVIDUAL_USER_DELAY minute(s) for individual user commands, changeable.
    """
    return check_cooldown(update, 'lastcommandreply', INDIVIDUAL_USER_DELAY)


def _text_antispam_passed(update):
    """Checks if somebody is spamming reply_all words"""
    return check_cooldown(update, 'lasttextreply', INDIVIDUAL_REPLY_DELAY)


def check_cooldown(update, whattocheck, cooldown):
    """Check cooldown of command, reply, error
    Whattocheck should be the sql column name"""

    def _give_command_error():
        """Give command cooldown error"""
        nonlocal update
        if check_cooldown(update, 'lastusercommanderror', ERROR_DELAY):
            time_remaining = str((threshold - message_time)).split('.')[0][3:]
            _send_reply(update, f'До команды осталось {time_remaining} (ММ:СС). Пока можешь идти нахуй.')

    if update.message.chat.type == 'private':
        return True
    # Add exceptions for some users
    if dbc.execute(f'''
    SELECT * FROM exceptions 
    WHERE id={update.message.from_user.id}
    ''').fetchone():
        return True
    if whattocheck == 'lastcommandreply':
        if _muted(update):
            _try_to_delete_message(update)
            return False
    # Create table if doesn't exist
    # Shorten code
    user_id = update.message.from_user.id
    message_time = datetime.datetime.now()
    lastinstance = dbc.execute(f'''
    SELECT {whattocheck} from "chat"
    WHERE id={user_id} AND chatid={update.message.chat_id}''').fetchone()
    if isinstance(lastinstance, tuple):
        lastinstance = lastinstance[0]
    # If there was a last one
    if lastinstance is not None:
        # Check if the cooldown has passed
        threshold = datetime.datetime.fromisoformat(lastinstance) + \
                    datetime.timedelta(seconds=cooldown)
        if message_time > threshold:
            # If it did, update table, return True
            dbc.execute(f'''
            UPDATE "chat" SET {whattocheck}="{message_time}" WHERE id={user_id} AND chatid={update.message.chat_id}''')
            db.commit()
            return True
        else:
            if whattocheck == 'lastcommandreply':
                _give_command_error()
            # If it didn't return False
            return False
    # If there was none, create entry and return True
    else:
        dbc.execute(f'''INSERT OR IGNORE INTO "chat" (id, chatid, firstname, {whattocheck}) 
        VALUES ({user_id}, "{update.message.chat_id}" ,"{update.message.from_user.first_name}", "{message_time}")''')
        dbc.execute(f'''
        UPDATE "chat" SET {whattocheck}="{message_time}" WHERE id={user_id} AND chatid={update.message.chat_id}''')
        db.commit()
        return True


def _create_chat_table():
    """Create a database with chat data"""
    dbc.execute(f'''
        CREATE TABLE IF NOT EXISTS "chat" 
        (id NUMERIC PRIMARY KEY, 
        chatid NUMERIC, 
        firstname TEXT DEFAULT NULL, 
        lastcommandreply TEXT DEFAULT NULL, 
        lastusercommanderror TEXT DEFAULT NULL, 
        lasttextreply TEXT DEFAULT NULL
        )''')
    db.commit()


def _create_mute_table():
    """Create a muted database"""
    dbc.execute(f'''
        CREATE TABLE IF NOT EXISTS "muted" 
        (id NUMERIC PRIMARY KEY, 
        chatid NUMERIC, 
        firstname TEXT DEFAULT NULL, 
        reason TEXT DEFAULT NULL
        )''')
    db.commit()


def _try_to_delete_message(update):
    """Try to delete user message using admin rights. If no rights, pass."""
    try:
        BOT.delete_message(chat_id=update.message.chat_id,
                           message_id=update.message.message_id)
    except TelegramError:
        pass


def _send_reply(update, text: str, parse_mode: str = None):
    """Shorten replies"""
    BOT.send_message(chat_id=update.message.chat_id,
                     text=text,
                     reply_to_message_id=update.message.message_id,
                     parse_mode=parse_mode)


def _get(update, what_is_needed: str):
    """Get something from update"""
    update_data = {
        'chat_id': update.message.chat_id,
        'init_name': update.message.from_user.first_name.strip('[]'),
        'init_id': update.message.from_user.id,
        }
    if update.message.reply_to_message is not None:
        update_data['target_name'] = \
            update.message.reply_to_message.from_user.first_name.strip('[]')
        update_data['target_id'] = \
            update.message.reply_to_message.from_user.id
    return update_data[what_is_needed]


def _muted(update):
    """Check if the user is muted"""
    _create_mute_table()
    found = dbc.execute(f'''SELECT id FROM "muted" 
    WHERE id={update.message.from_user.id} AND chatid={update.message.chat_id}''').fetchone()
    # Except non existent table, then not muted
    if found is None:
        return False
    else:
        return True


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
    dispatcher.add_handler(CommandHandler('whatsnew', whatsnew))
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
    dispatcher.add_handler(CommandHandler('myscore', myscore))
    dispatcher.add_handler(CommandHandler('leave', leave))

    # add message handlers
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, welcomer))
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.left_chat_member, farewell))
    dispatcher.add_handler(MessageHandler(
        Filters.all, message_filter))

    # log all errors
    dispatcher.add_error_handler(error)

    # Create databases
    _create_chat_table()
    _create_mute_table()

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
