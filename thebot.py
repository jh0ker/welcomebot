"""
Authors (telegrams) - @doitforgachi, @dovaogedot
Version: 1.0 beta
"""

import datetime
import logging
import random
import sqlite3
from os import environ
from time import sleep

import requests
import telegram
from telegram import Bot
from telegram import TelegramError
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async
from telegram.utils.request import Request

# Import constants
from modules.constants import *
# Import phrases for slaps, duels and links to images of huts
from modules.duels import DUELS
from modules.huts import HUTS
from modules.slaps import SLAPS


# Enable logging into file
logging.basicConfig(filename='logs.log',
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
LOGGER = logging.getLogger(__name__)
LOGGER.info('-----------------------------------------------')
LOGGER.info('Initializing the bot...')

# Import the database with muted, exceptions and duel data
LOGGER.info(f"Connecting to the database '{DATABASENAME}'...")
DB = sqlite3.connect(DATABASENAME, check_same_thread=False)
DBC = DB.cursor()

# Bot initialization
TOKEN = environ.get("TG_BOT_TOKEN")
BOT = Bot(token=TOKEN, request=Request(con_pool_size=20))

@run_async
def store_user_data(update: Update):
    """Add user data to the userdata table of the database"""
    global KNOWNUSERSIDS
    if update.effective_message.from_user.id not in KNOWNUSERSIDS:
        userdata = BOT.get_chat_member(chat_id=update.effective_message.chat_id,
                                       user_id=update.effective_message.from_user.id).user
        id = userdata.id
        firstname = userdata.first_name
        lastname = update.effective_message.from_user.last_name if update.effective_message.from_user.last_name else ''
        username = update.effective_message.from_user.username if update.effective_message.from_user.username else ''
        userlink = userdata.link if userdata.link else ''
        # Try to get the chat name
        try:
            chatname = BOT.get_chat(chat_id=update.effective_message.chat_id).title
        except:
            chatname = ''
        # Try to get the chat link
        try:
            chatlink = "t.me/" + update.effective_message.chat.username
        except:
            chatlink = 'private'
        usable_data = []
        usable_variable = []
        for data in (
                (id, 'id'),
                (firstname, 'firstname'),
                (lastname, 'lastname'),
                (username, 'username'),
                (chatname, 'chatname'),
                (userlink, 'userlink'),
                (chatlink, 'chatlink')):
            if data[0]:
                usable_data += [data[0]]
                usable_variable += [data[1]]
        DBC.execute(f'''INSERT OR IGNORE INTO "userdata"
        {tuple(usable_variable)} VALUES {tuple(usable_data)}''')
        DB.commit()
        KNOWNUSERSIDS += [id]


def command_antispam_passed(func):
    """
    Check if the user is spamming
    Delay of INDIVIDUAL_USER_DELAY minute(s) for individual user commands, changeable.
    """

    def executor(update: Update, *args, **kwargs):
        store_user_data(update)
        if _check_cooldown(update, 'lastcommandreply', INDIVIDUAL_USER_DELAY):
            func(update, *args, **kwargs)

    return executor


def text_antispam_passed(func):
    """Checks if somebody is spamming reply_all words"""

    def executor(update: Update, *args, **kwargs):
        store_user_data(update)
        if _check_cooldown(update, 'lasttextreply', INDIVIDUAL_REPLY_DELAY):
            func(update, *args, **kwargs)

    return executor


def rightscheck(func):
    """Checks if the user has enough right
    Enough rights are defined as creator or administrator or developer"""

    def executor(update: Update, *args, **kwargs):
        store_user_data(update)
        rank = BOT.get_chat_member(chat_id=update.effective_message.chat_id,
                                   user_id=update.effective_message.from_user.id).status
        permitted = ['creator', 'administrator']
        if rank in permitted or update.effective_message.from_user.id == DEV:
            func(update, *args, **kwargs)
        else:
            informthepleb(update)

    return executor


@run_async
@command_antispam_passed
def start(update: Update, context: CallbackContext):
    """Send out a start message"""
    _send_reply(update, 'Думер бот в чате. Для списка функций используйте /help.\n'
                        'Для наилучшего экспириенса, дайте боту права на удаление сообщений.')


@run_async
def welcomer(update: Update, context: CallbackContext):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    # Create a loop over a list in cast many users have been invited at once
    for new_member in update.effective_message.new_chat_members:
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
        botmsg = _send_reply(update, reply_text, parse_mode='Markdown')
        # Sleep and check if user is still there or voicy kicked it
        sleep(70)
        if BOT.get_chat_member(chat_id=update.effective_message.chat_id,
                               user_id=new_member.id).status in ['restricted', 'left', 'kicked']:
            # Delete the bot welcome message
            BOT.delete_message(chat_id=botmsg.chat_id,
                               message_id=botmsg.message_id)
            # Delete the join notification unless no rights or it was deleted
            try:
                BOT.delete_message(chat_id=update.effective_message.chat_id,
                                   message_id=update.effective_message.message_id)
            except telegram.error.BadRequest:
                pass


@run_async
def farewell(update: Update, context: CallbackContext):
    """Goodbye message"""
    leftuser = update.effective_message.left_chat_member
    # Not this bot was removed
    if leftuser.id != BOT.id:
        # Other bot was removed
        if leftuser.is_bot and leftuser.id != BOT.id:
            _send_reply(update, f"{leftuser.first_name}'а убили, красиво, уважаю.")
        # A user was removed
        else:
            leftusertag = f"[{leftuser.first_name.strip('[]')}](tg://user?id={leftuser.id})"
            _send_reply(update, f'Сегодня нас покинул {leftusertag}.', parse_mode='Markdown')


@run_async
@command_antispam_passed
def help(update: Update, context: CallbackContext):
    """Help message"""
    help_text = f"<b>Пример команды для бота:</b> /help@{BOT.username}\n"
    for commandinfo in USERCOMMANDS[1:]:
        help_text += f'/{commandinfo[0]} - {commandinfo[2]};\n'
    help_text += \
        ("<b>Дополнительная информация:</b>\n"
         "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
         f"2. Кулдаун на команды <b>{INDIVIDUAL_USER_DELAY // 60}</b> минут.\n"
         f"3. Ошибка о кулдауне даётся минимум через каждые <b>{ERROR_DELAY // 60}</b> минут. "
         "Спам команд во время кд удаляется.\n")
    _send_reply(update, help_text, parse_mode='HTML')


@run_async
@rightscheck
def adminmenu(update: Update, context: CallbackContext):
    """Send the admin menu commands"""
    text = ONLYADMINCOMMANDS[0] + '\n'
    for command in ONLYADMINCOMMANDS[1:]:
        text += f'/{command[0]} - {command[2]};\n'
    _send_reply(update, text)


@run_async
@command_antispam_passed
def whatsnew(update: Update, context: CallbackContext):
    """Reply with all new goodies"""
    # Import the changelog
    try:
        with open('changelog.md', 'r', encoding='utf-8') as changelog:
            changes = changelog.read()
    except (EOFError, FileNotFoundError) as changelog_err:
        LOGGER.error(changelog_err)
        changes = 'Не смог добраться до изменений. Что-то не так.'
    # Get the last 3 day changes
    latest_changes = ''
    for change in changes.split('\n\n')[:3]:
        latest_changes += change + '\n\n'
    # Add Link to full changelog
    latest_changes += 'Вся история изменений: https://bit.ly/DoomerChangelog'
    _send_reply(update, latest_changes, parse_mode='Markdown')


@run_async
def getlogs(update: Update, context: CallbackContext):
    """Get the bot logs"""
    # My call
    if update.effective_message.from_user.id == DEV:
        try:
            # Get the filename
            filename = datetime.date.today().isoformat()
            # Send the file
            BOT.send_document(chat_id=update.effective_message.chat_id,
                              document=open('logs.log', 'rb'),
                              filename=f'{filename}.log')
        except (EOFError, FileNotFoundError) as changelog_err:
            LOGGER.error(changelog_err)
            _send_reply(update, 'Не смог добраться до логов. Что-то не так.')
        finally:
            # Clean the file after sending/create a new one if failed to get it
            with open('logs.log', 'w') as logfile:
                logfile.write(f'{datetime.datetime.now().isoformat()} - Start of the log file.\n')
                logfile.close()


@run_async
def getdatabase(update: Update, context: CallbackContext):
    """Get the database as a document"""
    # My call
    if update.effective_message.from_user.id == DEV:
        try:
            # Send the file
            BOT.send_document(chat_id=update.effective_message.chat_id,
                              document=open(DATABASENAME, 'rb'))
        except (EOFError, FileNotFoundError) as database_err:
            LOGGER.error(database_err)
            _send_reply(update, 'Не смог добраться до датабазы. Что-то не так.')


def sql(update: Update, context: CallbackContext):
    """Use sql commands for the database"""
    if update.effective_message.from_user.id == DEV:
        statement = ' '.join(update.effective_message.text.split()[1:])
        DBC.execute(f'''{statement}''')
        DB.commit()


@run_async
def allcommands(update: Update, context: CallbackContext):
    """Get all commands"""
    if update.effective_message.from_user.id == DEV:
        text = ''
        for commandlists in (USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS):
            text += f'<b>{commandlists[0]}:</b>\n'
            for commands in commandlists[1:]:
                text += f'/{commands[0]} - {commands[2]};\n'
        _send_reply(update, text, parse_mode='HTML')


@run_async
def message_filter(update: Update, context: CallbackContext):
    """Replies to all messages
    Думер > Земляночка"""

    @text_antispam_passed
    def _giveanswer(update: Update, case: str):
        """Give the answer"""
        nonlocal doomer_word
        if case == 'думер':
            _send_reply(update, doomer_word)
        else:
            BOT.send_photo(chat_id=update.effective_message.chat_id,
                           photo=random.choice(HUTS),
                           caption='Эх, жить бы подальше от общества как анприм и там думить..',
                           reply_to_message_id=update.effective_message.message_id)

    # Add storing the userdata
    store_user_data(update)
    try:
        LOGGER.info(
            f'{update.effective_message.from_user.first_name}[{update.effective_message.from_user.id}] - '
            f'{BOT.get_chat(chat_id=update.effective_message.chat_id).title} - {update.effective_message.text}')
    except UnicodeEncodeError:
        LOGGER.info('Failed to print message due to russian symbols')
    # If user is in the muted list, delete his message unless he is in exceptions
    # to avoid possible self-mutes
    doomer_word = _doomer_word_handler(update)
    if _muted(update):
        _try_to_delete_message(update)
    # Handle the word doomer
    elif doomer_word:
        _giveanswer(update, 'думер')
    # Handle землянoчкy
    elif _anprim_word_handler(update):
        _giveanswer(update, 'землянка')


def _doomer_word_handler(update) -> str:
    # Make the preparations with variations of the word with latin letters
    variations_with_latin_letters = [
        'думер', 'дyмер', 'дyмeр', 'дyмep', 'думeр', 'думep', 'думеp'
        ]
    doomer_word_start = None
    # Check if any of the variations are in the text, if there are break
    if update.effective_message.text is not None:
        for variation in variations_with_latin_letters:
            position = update.effective_message.text.lower().find(variation)
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
            update.effective_message.text.lower()[doomer_word_start:].replace(
                found_word, 'хуюмер').split()[0]
        # Get only the word, until any number or non alpha symbol is encountered
        for i in word_with_symbols:
            if i.isalpha():
                reply_word += i
            else:
                break
    # If the word is not found, return False
    return reply_word


def _anprim_word_handler(update) -> bool:
    """Image of earth hut"""
    variations = ['земляночку бы', 'земляночкy бы',
                  'землянoчку бы', 'зeмляночку бы',
                  'землянoчкy бы', 'зeмляночкy бы',
                  'зeмлянoчку бы', 'зeмлянoчкy бы']
    # If the word is found, return true
    if update.effective_message.text is not None:
        for variation in variations:
            if variation in update.effective_message.text.lower():
                return True
    # If the word is not found, return false
    return False


@run_async
@command_antispam_passed
def flip(update: Update, context: CallbackContext):
    """Flip a Coin"""
    _send_reply(update, random.choice(['Орёл!', 'Решка!']))


@run_async
@command_antispam_passed
def myiq(update: Update, context: CallbackContext):
    """Return IQ level (1 - 200)"""
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


@run_async
@command_antispam_passed
def muhdick(update: Update, context: CallbackContext):
    """Return dick size in cm (1 - 25)"""
    muh_dick = random.randint(1, 25)
    reply_text = f"Длина твоей палочки {muh_dick} см! "
    if 1 <= muh_dick <= 11:
        reply_text += "\U0001F92D "
    elif 21 <= muh_dick <= 25:
        reply_text += "\U0001F631 "
    reply_text += "(1 - 25)"
    _send_reply(update, reply_text)


@run_async
def animal(update: Update, context: CallbackContext):
    """Get photo/video/gif of dog or cat"""

    @run_async
    @command_antispam_passed
    def _handle_format_and_reply(update):
        """Handle the format of the file and reply accordingly"""
        nonlocal response
        file_link = list(response.values())[0]
        file_extension = file_link.split('.')[-1]
        if 'mp4' in file_extension:
            BOT.send_video(chat_id=update.effective_message.chat_id,
                           video=file_link,
                           reply_to_message_id=update.effective_message.message_id)
        elif 'gif' in file_extension:
            BOT.send_animation(chat_id=update.effective_message.chat_id,
                               animation=file_link,
                               reply_to_message_id=update.effective_message.message_id)
        else:
            BOT.send_photo(chat_id=update.effective_message.chat_id,
                           photo=file_link,
                           reply_to_message_id=update.effective_message.message_id)

    # Cat link
    if '/cat' in update.effective_message.text.lower():
        link = 'http://aws.random.cat/meow'
    # Dog link
    else:
        link = 'https://random.dog/woof.json'
    try:
        response = requests.get(link, timeout=REQUEST_TIMEOUT).json()
        _handle_format_and_reply(update)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        LOGGER.error(err)
        _send_reply(update, 'Думер умер на пути к серверу. Попробуйте ещё раз.')


@run_async
def dadjoke(update: Update, context: CallbackContext):
    """Get a random dad joke"""

    @run_async
    @command_antispam_passed
    def _handle_joke(update):
        """Reply using this to account for the antispam decorator."""
        _send_reply(update, response['joke'])

    # Retrieve the json with, the joke
    try:
        response = requests.get(
            'https://icanhazdadjoke.com/', headers={'Accept': 'application/json'},
            timeout=REQUEST_TIMEOUT).json()
        _handle_joke(update)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        LOGGER.error(err)
        _send_reply(update, 'Думер умер на пути к серверу. Попробуйте ещё раз.')


@run_async
@command_antispam_passed
def slap(update: Update, context: CallbackContext):
    """Slap with random item"""
    # Check if there was a target
    if update.effective_message.reply_to_message is None:
        reply = ('Кого унижать то будем?\n'
                 'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
    else:
        # Get success and fail chances
        success_and_fail = []
        # Add failures and successes if its empty and shuffle (optimize CPU usage)
        if not success_and_fail:
            success_and_fail += ['failure'] * len(SLAPS['failure']) + \
                                ['success'] * len(SLAPS['success'])
            random.shuffle(success_and_fail)
        # Get user tags as it is used in both cases
        init_tag = f"[{_get(update, 'init_name')}](tg://user?id={_get(update, 'init_id')})"
        target_tag = f"[{_get(update, 'target_name')}](tg://user?id={_get(update, 'target_id')})"
        # Different depending on the scenario
        scenario = success_and_fail.pop()
        action = random.choice(SLAPS[scenario])
        # Replace premade text with user tags.
        reply = action.replace('init', init_tag).replace('target', target_tag)
    _send_reply(update, reply, parse_mode='Markdown')


def duel(update: Update, context: CallbackContext):
    """Duel to solve any kind of argument"""

    def _getuserstr(userid: int) -> float:
        """Get strength if the user to assist in duels"""
        # Check if table exists
        userfound = DBC.execute(f'''SELECT kills, deaths, misses from "duels"
        WHERE user_id={userid} and chat_id={update.effective_message.chat_id}''').fetchone()
        if userfound:
            strength = random.uniform(LOW_BASE_ACCURACY, HIGH_BASE_ACCURACY) \
                       + userfound[0] * KILLMULT \
                       + userfound[1] * DEATHMULT \
                       + userfound[2] * MISSMULT
            return min(strength, STRENGTHCAP)
        # Return base if table not found or user not found
        return random.uniform(LOW_BASE_ACCURACY, HIGH_BASE_ACCURACY)

    @run_async
    def _score_the_results(winners: list, losers: list, p1_kdm: tuple, p2_kdm: tuple):
        """Score the results in the database"""
        # Update data
        # One dead
        if winners:
            p1, p2 = winners[0], losers[0]
            # Remove cooldown from the winner if it was the initiator
            if update.effective_message.from_user.id == p1[1]:
                # Reduce winner cooldown
                shortercd = datetime.datetime.now() - datetime.timedelta(seconds=CDREDUCTION)
                DBC.execute(f'''UPDATE "cooldowns" SET lastcommandreply="{shortercd}",
                lasttextreply="{shortercd}" WHERE user_id={p1[1]} AND chat_id={update.effective_message.chat_id}''')
        # None dead
        else:
            p1, p2 = losers[0], losers[1]
        counter = 0
        for player in (p1, p2):
            kd = p1_kdm if counter == 0 else p2_kdm
            userid, firstname = player[1], player[0]
            DBC.execute(f'INSERT OR IGNORE INTO "duels" (user_id, chat_id, firstname) '
                        f'VALUES ("{userid}", "{update.effective_message.chat_id}", "{firstname}")')
            DBC.execute(f'UPDATE "duels" SET kills = kills + {kd[0]}, '
                        f'deaths = deaths + {kd[1]}, misses = misses + {kd[2]} '
                        f'WHERE user_id="{userid}" AND chat_id="{update.effective_message.chat_id}"')
            counter += 1
        DB.commit()

    def _usenames(scenario: str, winners: list = None, losers: list = None) -> str:
        """Insert names into the strings"""
        nonlocal update
        init_tag = f"[{_get(update, 'init_name')}](tg://user?id={_get(update, 'init_id')})"
        phrase = random.choice(DUELS['1v1'][scenario])
        if scenario == 'nonedead':
            return phrase.replace('loser1', losers[0][3]).replace('loser2', losers[1][3])
        if scenario == 'onedead':
            phrase = phrase.replace('winner', winners[0][3]).replace('loser', losers[0][3])
            phrase += f'\nПобеда за {winners[0][3]}!'
            if winners[0][1] == update.effective_message.from_user.id:
                phrase += f'\nВсе твои кулдауны были ресетнуты до {SHORTCD // 60}-х минут!'
            return phrase
        if scenario == 'suicide':
            return phrase.replace('loser', init_tag)

    def _check_duel_status() -> bool:
        """Check if the duels are allowed/more possible"""
        nonlocal update
        chatid = f"{update.effective_message.chat_id}"
        chatdata = DBC.execute(f'''SELECT duelstatusonoff, duelmaximum,
        duelcount, accountingday FROM "duellimits" WHERE chat_id="{chatid}"''').fetchone()
        now = f"{datetime.datetime.now().date()}"
        if chatdata is not None:
            # If duels are turned off, disallow duels
            if chatdata[0] == 0:
                return False
            # If there is no maximum, allow for duels
            if chatdata[1] is None:
                return True
            # If no duels have been counted, or old day, increment by 1
            if chatdata[3] is None or \
                    datetime.date.fromisoformat(now) > datetime.date.fromisoformat(chatdata[3]):
                DBC.execute(f'''UPDATE "duellimits" SET
                accountingday="{now}", duelcount=1
                WHERE chat_id="{chatid}"''')
                DB.commit()
                return True
            # If number of duels done is higher than the maximum
            if chatdata[2] >= chatdata[1]:
                # Reset every day
                if datetime.datetime.now().date() > \
                        datetime.date.fromisoformat(chatdata[3]):
                    DBC.execute(f'''UPDATE "duellimits" SET
                    duelcount = 1, accountingday="{now}" 
                    WHERE chat_id="{chatid}"''')
                    DB.commit()
                    return True
                return False
            # Increment if none of the conditions were met
            DBC.execute(f'''UPDATE "duellimits" SET
            duelcount = duelcount + 1
            WHERE chat_id="{chatid}"''')
            DB.commit()
            return True
        # If there is no chat data, create it
        DBC.execute(f'''INSERT OR IGNORE INTO "duellimits"
        (chat_id, duelcount, accountingday) VALUES 
        ("{chatid}", 1, "{now}")''')
        DB.commit()
        return True

    @run_async
    @command_antispam_passed
    def trytoduel(update):
        if update.effective_message.reply_to_message is None:
            _send_reply(update, 'С кем дуэль проводить будем?\n'
                                'Чтобы подуэлиться, надо чтобы вы ответили вашему оппоненту.')
        else:
            # Shorten the code, format the names
            initiator_name, initiator_id = _get(update, 'init_name'), _get(update, 'init_id')
            target_name, target_id = _get(update, 'target_name'), _get(update, 'target_id')
            initiator_tag = f'[{initiator_name}](tg://user?id={initiator_id})'
            target_tag = f'[{target_name}](tg://user?id={target_id})'
            # Tree for when the target is not self
            if initiator_id != target_id:
                # Tree for when the bot is not the target
                if target_id != BOT.id:
                    # Get the player list
                    participant_list = [
                        (initiator_name, initiator_id, _getuserstr(initiator_id), initiator_tag),
                        (target_name, target_id, _getuserstr(target_id), target_tag)
                        ]
                    # Get the winner and the loser. Check 1
                    winners, losers = [], []
                    for player in participant_list:
                        individualwinreq = random.uniform(0, THRESHOLDCAP)
                        winners.append(player) if player[2] > individualwinreq \
                            else losers.append(player)
                    # Get the winner and the loser. Check 2
                    if len(winners) == 2:
                        random.shuffle(winners)
                        losers.append(winners.pop())
                    # Make the scenario tree
                    scenario = 'onedead' if winners else 'nonedead'
                    if scenario == 'onedead':
                        _score_the_results(winners, losers, (1, 0, 0), (0, 1, 0))
                    else:
                        _score_the_results(winners, losers, (0, 0, 1), (0, 0, 1))
                    # Get the result
                    duel_result = _usenames(scenario, winners, losers)
                    _conclude_the_duel(duel_result, participant_list)
                else:
                    # If the bot is the target, send an angry message
                    scenario = 'bot'
                    duel_result = random.choice(DUELS[scenario])
                    _send_reply(update, duel_result, parse_mode='Markdown')
            else:
                # Suicide message
                scenario = 'suicide'
                duel_result = f"{_usenames(scenario)}!\n" \
                              f"За суицид экспа/статы не даются!"
                _send_reply(update, duel_result, parse_mode='Markdown')

    @run_async
    def _conclude_the_duel(result: str, participants):
        """Send all the messages for the duel."""
        nonlocal update
        # Send the initial message
        botmsg = BOT.send_message(chat_id=update.effective_message.chat_id,
                                  text='Дуэлисты расходятся...')
        # Get the sound of the duel
        sound = '***BANG BANG***' if random.random() * 100 < 90 else '***ПИФ-ПАФ***'
        # Make the message loop
        for phrase in ('Готовятся к выстрелу...', sound, result):
            sleep(0.8)
            botmsg = BOT.edit_message_text(chat_id=update.effective_message.chat_id,
                                           text=phrase,
                                           message_id=botmsg.message_id,
                                           parse_mode='Markdown')
        for player in participants:
            _try_to_hard_reset(player)

    def _try_to_hard_reset(participant):
        """Try to hard reset stats"""
        nonlocal update
        if random.uniform(0, 1) < HARDRESETCHANCE:
            DBC.execute(f'''DELETE FROM "duels" WHERE
            user_id={participant[1]} AND chat_id={update.effective_message.chat_id}''')
            DB.commit()
            BOT.send_message(chat_id=update.effective_message.chat_id,
                             text=f'Упс, я случайно ресетнул все статы {participant[3]}.\n'
                                  f'Кому-то сегодня не везёт.',
                             parse_mode='Markdown')

    # If not replied, ask for the target
    if update.effective_message.chat.type == 'private':
        _send_reply(update, 'Это только для групп.')
    elif _check_duel_status():
        trytoduel(update)
    else:
        _send_reply(update, 'На сегодня дуэли всё/дуэли отключены.')


@run_async
def myscore(update: Update, context: CallbackContext):
    """Give the user his K/D for duels"""

    @run_async
    @command_antispam_passed
    def _handle_score(update):
        nonlocal u_data
        # Get the current additional strength
        wrincrease = u_data[0] * KILLMULTPERC + u_data[1] * DEATHMULTPERC + u_data[2] * MISSMULTPERC
        wrincrease = min(round(wrincrease, 2), 45)
        try:
            wr = u_data[0] / (u_data[0] + u_data[1]) * 100
        except ZeroDivisionError:
            wr = 100
        reply = (f'Твой K/D/M равен {u_data[0]}/{u_data[1]}/{u_data[2]} ({round(wr, 2)}%)\n'
                 f'Шанс победы из-за опыта изменен на {wrincrease}%. (максимум {ADDITIONALPERCENTCAP}%)\n'
                 f'P.S. {KILLMULTPERC}% за убийство, {DEATHMULTPERC}% за смерть, {MISSMULTPERC}% за мисс.')
        _send_reply(update, reply)

    # Check if not private
    if update.effective_message.chat.type != 'private':
        # Get userdata
        u_data = DBC.execute(f'''SELECT kills, deaths, misses FROM "duels"
        WHERE user_id={update.effective_message.from_user.id} AND chat_id={update.effective_message.chat_id}''').fetchone()
        # Check if the data for the user exists
        if u_data is not None:
            # If there is user data, get the score
            _handle_score(update)
        else:
            _send_reply(update, 'Сначала подуэлься, потом спрашивай.')
    else:
        # Send error
        _send_reply(update, 'Это только для групп.')


@run_async
def duelranking(update: Update, context: CallbackContext):
    """Get the top best duelists"""

    @run_async
    @command_antispam_passed
    def _handle_ranking(update):
        ranking = headers = '***Убийства/Смерти/Непопадания\n***'
        for query in (('Лучшие:\n', 'DESC'), ('Худшие:\n', 'ASC')):
            # Create headers to see if there was data
            headers += query[0]
            # Start the table
            ranking += query[0]
            counter = 1
            # Add to the table the five best and five worst
            for Q in DBC.execute(f'''SELECT winrate.firstname, doom.kills, doom.deaths, doom.misses, winrate.wr
            FROM "duels" AS doom JOIN
            (SELECT firstname, kills * 100.0/(kills+deaths) AS wr
                FROM "duels"
                    WHERE deaths!=0 AND kills!=0 AND chat_id="{update.effective_message.chat_id}") AS winrate
            ON doom.firstname=winrate.firstname WHERE chat_id="{update.effective_message.chat_id}"
            ORDER BY wr {query[1]} LIMIT 5'''):
                ranking += f'№{counter} {Q[0]}\t -\t {Q[1]}/{Q[2]}/{Q[3]}'
                ranking += f' ({round(Q[4], 2)}%)\n'
                counter += 1
        # If got no data, inform the user
        if ranking == headers:
            ranking = 'Пока что недостаточно данных. Продолжайте дуэлиться.'
        # Add a footer to the table
        else:
            ranking += 'Показываются только дуэлянты у которых есть убийства и смерти.'
        _send_reply(update, ranking, parse_mode='Markdown')

    if update.effective_message.chat.type != 'private':
        # Check if the chat table exists
        if DBC.execute(f'''SELECT user_id FROM "duels"
        WHERE chat_id={update.effective_message.chat_id}''').fetchone() is not None:
            _handle_ranking(update)
        else:
            _send_reply(update, 'Для этого чата нет данных.')
    else:
        _send_reply(update, 'Это только для групп.')


@run_async
@rightscheck
def duelstatus(update: Update, context: CallbackContext):
    """Make a global maximum duels per chat and be able to turn them on and off"""

    @run_async
    def _handle_limits():
        """Handle the global limits to duels of the chat"""
        nonlocal arg, update
        # Remove limits
        if arg == 'none':
            DBC.execute(f'''UPDATE "duellimits"
            set duelmaximum=NULL WHERE chat_id="{update.effective_message.chat_id}"''')
            reply = 'Был убран лимит дуэлей.'
        # Get current status if no argument was given
        elif arg is None:
            status = DBC.execute(f'''SELECT duelmaximum from "duellimits"
            WHERE chat_id="{update.effective_message.chat_id}"''').fetchone()[0]
            # If nothing, means no limit
            if status is None:
                reply = 'Лимита на дуэли нет.'
            else:
                duelsused = DBC.execute(f'''SELECT duelcount from "duellimits"
                WHERE chat_id="{update.effective_message.chat_id}"''').fetchone()[0]
                reply = f'Лимит дуэлей составляет {status}. Уже использовано {duelsused}.'
        # Set maximum
        else:
            try:
                arg = int(arg)
                DBC.execute(f'''UPDATE "duellimits"
                set duelmaximum={arg} WHERE chat_id="{update.effective_message.chat_id}"''')
                reply = f'Максимальное количество дуэлей за день стало {arg}.'
            except ValueError:
                reply = f'\"{arg}\" не подходит. Дайте число. /adminmenu для справки.'
        _send_reply(update, reply)
        DB.commit()

    @run_async
    def _handle_status():
        """Handle the on/off state of duels in the chat
        1 for turned on, 0 for turned off
        If no argument, get the current status"""
        nonlocal arg, update
        status = None
        reply = 'Чё?'
        if arg in ['on', 'off']:
            status = 1 if arg == 'on' else 0
            DBC.execute(f'''UPDATE "duellimits"
            set duelstatusonoff={status} WHERE chat_id={update.effective_message.chat_id}''')
            DB.commit()
        elif arg is None:
            status = DBC.execute(f'''SELECT duelstatusonoff from "duellimits"
            WHERE chat_id={update.effective_message.chat_id}''').fetchone()[0]
        else:
            reply = 'Всмысле? Ты обосрался. /adminmenu для справки.'
        if status == 1:
            reply = 'Дуэли включены для этого чата.'
        elif status == 0:
            reply = 'Дуэли выключены для этого чата.'
        _send_reply(update, reply)

    commands = ['/duellimit', '/duelstatus']
    # Check if used by admin, a valid command, and there an argument to handle
    if update.effective_message.chat.type != 'private':
        if len(update.effective_message.text.split()) < 3:
            # Get the accounting day
            now = f"\"{datetime.datetime.now().date()}\""
            # Create table entry if it didn't exist
            DBC.execute(f'''INSERT OR IGNORE INTO "duellimits"
                        (chat_id, duelcount, accountingday) VALUES 
                        ({update.effective_message.chat_id}, 1, {now})''')
            DB.commit()
            # Get the argument
            try:
                arg = update.effective_message.text.lower().split()[1]
            except IndexError:
                arg = None
            # Pass to handlers
            if commands[0] in update.effective_message.text.lower():
                _handle_limits()
            if commands[1] in update.effective_message.text.lower():
                _handle_status()
        else:
            _send_reply(update, 'Всмысле? Ты обосрался. /adminmenu для справки.')
    else:
        _send_reply(update, 'В приват нет смысла это менять, тут дуэль не провести.')


@run_async
@command_antispam_passed
def informthepleb(update):
    """If was not called by admin/creator/dev, inform the user that he is a pleb"""
    _send_reply(update, 'Пошёл нахуй, ты не админ.')


@run_async
@rightscheck
def mute(update: Update, context: CallbackContext):
    """Autodelete messages of a user (only usable by the developer)"""
    # Only works for the dev/admin/creator
    try:
        # Shorten code
        targetdata = update.effective_message.reply_to_message.from_user
        # Mute and record into database
        DBC.execute(f'''INSERT OR IGNORE INTO "muted" (user_id, chat_id, firstname)
        VALUES ("{targetdata.id}", "{update.effective_message.chat_id}", "{targetdata.first_name}")''')
        # Get mute reason if there is any
        if len(update.effective_message.text.split()) > 1:
            mutereason = ' '.join(update.effective_message.text.split()[1:])
            DBC.execute(f'''UPDATE "muted" SET reason="{mutereason}"
            WHERE user_id="{targetdata.id}" AND chat_id="{update.effective_message.chat_id}"''')
        # Get username if exists
        if targetdata.username:
            DBC.execute(f'''UPDATE "muted" SET username="{targetdata.username}"
            WHERE user_id="{targetdata.id}" and chat_id="{update.effective_message.chat_id}"''')
        DB.commit()
        # Send photo and explanation to the silenced person
        BOT.send_message(chat_id=update.effective_message.chat_id,
                         text='Теперь ты под салом и не можешь писать в чат.',
                         reply_to_message_id=update.effective_message.reply_to_message.message_id)
    except KeyError:
        _send_reply(update, 'Пожалуйста, выберите цель.')


@run_async
@rightscheck
def unmute(update: Update, context: CallbackContext):
    """Stop autodeletion of messages of a user (only usable by the admin/dev/creator)"""
    # Get chat id, create the replied flag to not make large trees
    to_unmute_name = 'NULL'
    to_unmute_id = 'NULL'
    # If there is a reply, get the id of the reply target
    if update.effective_message.reply_to_message is not None:
        to_unmute_id = _get(update, 'target_id')
    # If no reply target, take the argument if it exists
    else:
        try:
            to_unmute_name = ' '.join(update.effective_message.text.split()[1:])
        except IndexError:
            # Finish if no target given at all
            _send_reply(update, 'Вы не указали цель.')
            return
    # Check if the entry exists
    target = DBC.execute(f'''SELECT user_id, firstname FROM "muted"
    WHERE chat_id="{update.effective_message.chat_id}" AND 
    (user_id="{to_unmute_id}" OR firstname="{to_unmute_name}")''').fetchone()
    if target is not None:
        # Get the target name
        target_name = target[1].strip('[]')
        # Create a markdown tagged name
        target_tagged = f'[{target_name}](tg://user?id={to_unmute_id})'
        # Delete the user from the muted database and commit
        DBC.execute(f'''DELETE FROM "muted" WHERE chat_id="{update.effective_message.chat_id}" AND
        (user_id="{to_unmute_id}" OR firstname="{to_unmute_name}")''')
        # Send the reply of successful unmute
        _send_reply(update, f'Успешно снял мут с \"{target_tagged}\".', parse_mode='Markdown')
        DB.commit()
    elif target is None:
        _send_reply(update, 'Такого в списке нет.')


@run_async
@rightscheck
def immune(update: Update, context: CallbackContext):
    """Add user to exceptions"""
    if update.effective_message.reply_to_message is not None:
        targetdata = update.effective_message.reply_to_message.from_user
        # Insert the target entry
        DBC.execute(f'''INSERT OR IGNORE INTO "exceptions"
        (user_id, chat_id, firstname) VALUES 
        ("{targetdata.id}", "{update.effective_message.chat_id}", "{targetdata.first_name}")''')
        # If the user has a username
        if targetdata.username:
            DBC.execute(f'''UPDATE "exceptions"
            SET username="{targetdata.username}" WHERE 
            chat_id="{update.effective_message.chat_id}" AND user_id="{targetdata.id}"''')
        DB.commit()
        _send_reply(update, f'Готово. \"{targetdata.first_name}\" теперь под иммунитетом!')
    else:
        _send_reply(update, 'Дай цель.')


@run_async
@rightscheck
def unimmune(update: Update, context: CallbackContext):
    """Remove user from exceptions"""
    if update.effective_message.reply_to_message:
        targetdata = update.effective_message.reply_to_message.from_user
        DBC.execute(f'''DELETE FROM "exceptions"
        WHERE user_id="{targetdata.id}"
        AND chat_id="{update.effective_message.chat_id}"''')
        _send_reply(update, f'Сделано. \"{targetdata.first_name}\" больше не под имуном')
        DB.commit()
    else:
        if len(update.effective_message.text.split()) > 1:
            unimmune_target = ' '.join(update.effective_message.text.split()[1:])
            DBC.execute(f'''DELETE FROM "exceptions"
            WHERE chat_id="{update.effective_message.chat_id}" AND 
            (username="{unimmune_target}" OR firstname="{unimmune_target}")''')
            DB.commit()
        else:
            _send_reply(update, 'Дай цель.')


@run_async
@rightscheck
def immunelist(update: Update, context: CallbackContext):
    """Get the exceptions list"""
    return _getsqllist(update, 'immunelist')


@run_async
@rightscheck
def mutelist(update: Update, context: CallbackContext):
    """Get the mute list"""
    return _getsqllist(update, 'mutelist')


@run_async
@rightscheck
def leave(update: Update, context: CallbackContext):
    """Make the bot leave the group, usable only by the admin/dev/creator."""
    try:
        BOT.leave_chat(chat_id=update.effective_message.chat_id)
    except telegram.error.BadRequest as leaveerror:
        LOGGER.info(leaveerror)
        _send_reply(update, 'Я не могу уйти отсюда. Сам уйди.')


def _check_cooldown(update, whattocheck, cooldown):
    """Check cooldown of command, reply, error
    Whattocheck should be the sql column name"""

    def _give_command_error():
        """Give command cooldown error, if the user still spams, delete his message"""
        nonlocal update
        # Check if the error was given
        if DBC.execute(f'''SELECT errorgiven from "cooldowns" WHERE
        chat_id="{update.effective_message.chat_id}" AND 
        user_id="{update.effective_message.from_user.id}"''').fetchone()[0] == 0:
            # If it wasn't, give the time remaining and update the flag.
            time_remaining = str((timediff - message_time)).split('.')[0][3:]
            _send_reply(update, f'До команды осталось {time_remaining} (ММ:СС). '
                                f'Пока можешь идти нахуй, я буду пытаться удалять твои команды.')
            DBC.execute(f'''UPDATE "cooldowns" SET errorgiven = 1
            WHERE chat_id="{update.effective_message.chat_id}" AND user_id="{update.effective_message.from_user.id}"''')
            DB.commit()
        # If it was, try to delete the message
        else:
            _try_to_delete_message(update)

    if update.effective_message.chat.type == 'private':
        return True
    # Add exceptions for some users
    user_id = update.effective_message.from_user.id
    if DBC.execute(f'''SELECT * FROM exceptions WHERE user_id="{user_id}"''').fetchall() is not None:
        for chatexcused in \
                DBC.execute(f'''SELECT chat_id FROM exceptions WHERE user_id="{user_id}"''').fetchall():
            # 1 is global
            if chatexcused[0] == update.effective_message.chat_id or chatexcused[0] == 1:
                return True
    if whattocheck == 'lastcommandreply':
        if _muted(update):
            _try_to_delete_message(update)
            return False
    # Create table if doesn't exist
    # Shorten code
    message_time = datetime.datetime.now()
    # Find last instance
    lastinstance = DBC.execute(f'''SELECT {whattocheck} from "cooldowns"
    WHERE user_id="{user_id}" AND chat_id="{update.effective_message.chat_id}"''').fetchone()
    if isinstance(lastinstance, tuple):
        lastinstance = lastinstance[0]
    # If there was a last one
    if lastinstance is not None:
        # Check if the cooldown has passed
        timediff = datetime.datetime.fromisoformat(lastinstance) + \
                   datetime.timedelta(seconds=cooldown)
        if message_time > timediff:
            # If it did, update table, return True
            DBC.execute(f'''UPDATE "cooldowns" SET
            {whattocheck}="{message_time}", errorgiven=0 
            WHERE user_id="{user_id}" AND chat_id="{update.effective_message.chat_id}"''')
            DB.commit()
            return True
        if whattocheck == 'lastcommandreply':
            _give_command_error()
        # If it didn't return False
        return False
    # If there was none, create entry and return True
    DBC.execute(f'''INSERT OR IGNORE INTO "cooldowns"
    (user_id, chat_id, firstname, {whattocheck}) 
    VALUES ("{user_id}", "{update.effective_message.chat_id}", 
    "{update.effective_message.from_user.first_name}", "{message_time}")''')
    DBC.execute(f'''UPDATE "cooldowns" SET {whattocheck}="{message_time}"
    WHERE user_id="{user_id}" AND chat_id={update.effective_message.chat_id}''')
    DB.commit()
    return True


@run_async
def _getsqllist(update, query: str):
    """Get the list of muted and immuned ids"""
    insert = {}
    if query == 'mutelist':
        insert['variables'] = "\"firstname\", \"reason\""
        insert['table'] = "\"muted\""
        insert['constraint'] = f"WHERE chat_id={update.effective_message.chat_id}"
    else:  # 'immunelist'
        insert['variables'] = "\"firstname\""
        insert['table'] = "\"exceptions\""
        if update.effective_message.from_user.id != DEV:
            insert['constraint'] = f"WHERE chat_id={update.effective_message.chat_id}"
        else:
            insert['constraint'] = ''
    # Somewhat of a table
    table = ''
    # If there are muted targets, send reply, else say that there is nobody
    listnumber = 1
    for entry in DBC.execute(f"""SELECT {insert['variables']} FROM {insert['table']}
                            {insert['constraint']}""").fetchall():
        table += f'{listnumber}. {entry[0]}\n'
        if query == 'mutelist':
            if entry[1]:
                table += f'Причина: {entry[1].capitalize()}\n'
            else:
                table += 'Причина не указана.\n'
        listnumber += 1
    if table:
        _send_reply(update, table)
    else:
        _send_reply(update, 'Список пуст.')


def _create_tables():
    """Create a muted databases"""
    # Userdata
    DBC.execute(f'''CREATE TABLE IF NOT EXISTS "userdata"
    (id NUMERIC PRIMARY KEY UNIQUE,
    firstname TEXT NOT NULL,
    lastname TEXT DEFAULT NULL,
    username TEXT DEFAULT NULL,
    chatname TEXT DEFAULT NULL,
    userlink TEXT DEFAULT NULL,
    chatlink TEXT DEFAULT NULL
    )''')
    # Cooldowns
    DBC.execute(f'''CREATE TABLE IF NOT EXISTS "cooldowns"
    (user_id NUMERIC,
    chat_id NUMERIC,
    firstname TEXT DEFAULT NULL,
    lastcommandreply TEXT DEFAULT NULL,
    errorgiven NUMERIC DEFAULT 0,
    lasttextreply TEXT DEFAULT NULL,
    PRIMARY KEY (user_id, chat_id),
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname)
    )''')
    # Muted
    DBC.execute(f'''CREATE TABLE IF NOT EXISTS "muted"
    (user_id NUMERIC,
    chat_id NUMERIC,
    firstname TEXT,
    username TEXT DEFAULT NULL,
    reason TEXT DEFAULT NULL,
    PRIMARY KEY (user_id, chat_id),
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname)
    )''')
    # Exceptions
    DBC.execute(f'''CREATE TABLE IF NOT EXISTS "exceptions"
    (user_id NUMERIC,
    chat_id NUMERIC,
    firstname TEXT,
    username TEXT DEFAULT NULL,
    PRIMARY KEY (user_id, chat_id),
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname),
    FOREIGN KEY(username) REFERENCES userdata(username))
    ''')
    # use 1 for global
    DBC.execute(f'''
    INSERT OR IGNORE INTO "exceptions" (user_id, chat_id, firstname) 
    VALUES 
    (255295801, 1, "doitforricardo"),
    (205762941, 1, "dovaogedot"),
    (185500059, 1, "mel_a_real_programmer")''')
    # Create a duel table
    DBC.execute(f'''CREATE TABLE IF NOT EXISTS "duels"
    (user_id NUMERIC,
    chat_id NUMERIC,
    firstname TEXT DEFAULT NULL,
    kills NUMERIC DEFAULT 0,
    deaths NUMERIC DEFAULT 0,
    misses NUMERIC DEFAULT 0,
    duelsdone NUMERIC DEFAULT 0,
    accountingday TEXT DEFAULT NULL,
    PRIMARY KEY (user_id, chat_id),
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname))''')
    # Table that tracks limitations of number of duels per day
    DBC.execute(f'''CREATE TABLE IF NOT EXISTS "duellimits"
     (chat_id NUMERIC PRIMARY KEY,
     duelstatusonoff NUMERIC DEFAULT 1,
     duelmaximum NUMERIC DEFAULT NULL,
     duelcount NUMERIC DEFAULT 0,
     accountingday TEXT DEFAULT NULL
     )''')
    # Commit the database
    DB.commit()


@run_async
def _try_to_delete_message(update):
    """Try to delete user message using admin rights. If no rights, pass."""
    try:
        BOT.delete_message(chat_id=update.effective_message.chat_id,
                           message_id=update.effective_message.message_id)
    except TelegramError:
        pass


def _send_reply(update, text: str, parse_mode: str = None):
    """Shorten replies"""
    return BOT.send_message(chat_id=update.effective_message.chat_id,
                            text=text,
                            reply_to_message_id=update.effective_message.message_id,
                            parse_mode=parse_mode)


def _get(update: Update, what_is_needed: str):
    """Get something from update"""
    update_data = {
        'chat_id': update.effective_message.chat_id,
        'init_name': update.effective_message.from_user.first_name.strip('[]'),
        'init_id': update.effective_message.from_user.id,
        }
    target = update.effective_message.reply_to_message
    update_data['target_id'] = target.from_user.id if target is not None else ''
    update_data['target_name'] = target.from_user.first_name.strip('[]') if target is not None else ''
    return update_data[what_is_needed]


def _muted(update):
    """Check if the user is muted"""
    # Check for exceptions
    if DBC.execute(f'''SELECT user_id, chat_id from "exceptions"
    WHERE user_id={update.effective_message.from_user.id}
    AND chat_id={update.effective_message.chat_id}''').fetchone() is not None:
        return False
    # Check the muted table
    if DBC.execute(f'''SELECT user_id FROM muted
    WHERE user_id="{update.effective_message.from_user.id}" AND 
    chat_id="{update.effective_message.chat_id}"''').fetchone() is not None:
        return True
    # If nothing found, return false
    return False


def error_callback(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    LOGGER.warning('Error "%s" caused by update "%s"', context.error, update)


# Bot commands
USERCOMMANDS = [
    'Команды для рядовых пользователей',
    ("help", help, 'Меню помощи'),
    ('whatsnew', whatsnew, 'Новое в боте'),
    ('adminmenu', adminmenu, 'Админское меню'),
    ("slap", slap, 'Кого-то унизить (надо ответить жертве, чтобы бот понял кого бить)'),
    ('duel', duel, 'Устроить дуэль (надо ответить тому, с кем будет дуэль)'),
    ('myscore', myscore, 'Мой счёт в дуэлях'),
    ('duelranking', duelranking, 'Ранкинг дуэлей чата (показывает только тех, у кого больше есть убийства и смерти)'),
    ("flip", flip, 'Бросить монетку (Орёл/Решка)'),
    ("dadjoke", dadjoke, 'Случайная шутка бати'),
    ("myiq", myiq, 'Мой IQ (1 - 200)'),
    ("muhdick", muhdick, 'Длина моего шланга (1 - 25)'),
    ("dog", animal, 'Случайное фото собачки'),
    ("cat", animal, 'Случайное фото котика'),
    ]
ONLYADMINCOMMANDS = [
    'Команды для администраторов групп',
    ('leave', leave, 'Сказать боту уйти'),
    ('duellimit', duelstatus, 'Изменить глобальный лимит на дуэли за день (число или убрать через None)'),
    ('duelstatus', duelstatus, 'Включить/Выключить дуэли (on/off)'),
    ('immune', immune, 'Добавить пользователю иммунитет на задержку команд (ответить ему)'),
    ('unimmune', unimmune, 'Снять иммунитет (ответить или имя)'),
    ('immunelist', immunelist, 'Лист людей с иммунитетом'),
    ('mute', mute, 'Замутить человека в этом чате (надо ему ответить командой, у бота должны быть права на удаление сообщений)'),
    ('unmute', unmute, 'Cнять мут в этом чате (ответить или имя)'),
    ('mutelist', mutelist, 'Показать всех в муте в этом чате'),
    ]
UNUSUALCOMMANDS = [
    'Нечастые команды',
    ('allcommands', allcommands, 'Все команды бота'),
    ('start', start, 'Начальное сообщение бота'),
    ('getlogs', getlogs, 'Получить логи бота (только для разработчика'),
    ('getdatabase', getdatabase, 'Получить датабазу'),
    ('sql', sql, 'Использовать sqlite команду на дб')
    ]

_create_tables()
KNOWNUSERSIDS = DBC.execute(f'''SELECT id FROM "userdata"''').fetchall()
KNOWNUSERSIDS = [item for t in KNOWNUSERSIDS for item in t]


def main():
    """Start the BOT."""
    # Create the Updater and pass it your BOT's token.
    updater = Updater(bot=BOT, use_context=True, workers=16)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    LOGGER.info('Adding handlers...')
    # Add command handles
    for commandlists in (USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS):
        for command in commandlists[1:]:
            dispatcher.add_handler(CommandHandler(command[0], command[1]))

    # add message handlers
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, welcomer))
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.left_chat_member, farewell))
    dispatcher.add_handler(MessageHandler(
        Filters.all, message_filter))

    # log all errors
    dispatcher.add_error_handler(error_callback)

    # Create databases
    LOGGER.info('Creating database tables if needed...')

    # Start the Bot
    # Set clean to True to clean any pending updates on Telegram servers before
    # actually starting to poll. Otherwise the BOT may spam the chat on coming
    # back online
    updater.start_polling(clean=True)
    LOGGER.info('Polling started.')
    LOGGER.info('-----------------------------------------------')

    # Run the BOT until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the BOT gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
