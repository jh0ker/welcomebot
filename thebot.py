"""
Authors (telegrams) - @doitforgachi, @dovaogedot......
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
logging = logging.getLogger(__name__)
logging.info('-----------------------------------------------')
logging.info('Initializing the bot...')

# Import the database with muted, exceptions and duel data
logging.info("Connecting to the database 'doomerbot.db'...")
db = sqlite3.connect('doomerbot.db', check_same_thread=False)
dbc = db.cursor()

# Get the last logdate
logging.info("Getting the last logfile date...")
with open('logs.log', 'r') as logfile:
    LOGDATE = datetime.date.fromisoformat(logfile.readline()[0:10])

# Bot initialization
TOKEN = environ.get("TG_BOT_TOKEN")
BOT = Bot(TOKEN)


def create_duel_table(func):
    """Create dueling table for each chat"""

    def executor(update, *args, **kwargs):
        tablename = f"\"duels{update.message.chat_id}\""
        exists = dbc.execute(f'''SELECT name FROM "sqlite_master" 
                WHERE type="table" AND name={tablename}''').fetchone()
        if exists is None:
            chat_title = BOT.get_chat(chat_id=update.message.chat_id).title
            logging.info(f'First duel happened in chat \"{chat_title}\" '
                         f'with id {update.message.chat_id}, '
                         f'creating the duels table for this chat.')
            # Duel table with stats
            dbc.execute(f'''CREATE TABLE {tablename}
            (user_id NUMERIC UNIQUE,
            firstname TEXT DEFAULT NULL,
            kills NUMERIC DEFAULT 0,
            deaths NUMERIC DEFAULT 0,
            winpercent NUMERIC DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES userdata(id),
            FOREIGN KEY(firstname) REFERENCES userdata(firstname))
            ''')
            db.commit()
        func(update, *args, **kwargs)

    return executor


def command_antispam_passed(func):
    """
    Check if the user is spamming
    Delay of INDIVIDUAL_USER_DELAY minute(s) for individual user commands, changeable.
    """

    def executor(update: Update, *args, **kwargs):
        if _check_cooldown(update, 'lastcommandreply', INDIVIDUAL_USER_DELAY):
            func(update, *args, **kwargs)

    return executor


@run_async
def start(update: Update, context: CallbackContext):
    """Send out a start message"""
    _send_reply(update, 'Думер бот в чате. Для списка функций используйте /help.')


@run_async
def welcomer(update: Update, context: CallbackContext):
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


@run_async
def farewell(update: Update, context: CallbackContext):
    """Goodbye message"""
    leftuser = update.message.left_chat_member
    # A a BOT was removed
    if update.message.left_chat_member.is_bot:
        try:
            _send_reply(
                update, f"{leftuser.first_name}'а убили, красиво, уважаю.")
        # When the bot itself was kicked
        except telegram.error.Unauthorized:
            pass
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
def adminmenu(update: Update, context: CallbackContext):
    """Send the admin menu commands"""
    if _creatoradmindev(update):
        text = ONLYADMINCOMMANDS[0] + '\n'
        for command in ONLYADMINCOMMANDS[1:]:
            text += f'/{command[0]} - {command[2]};\n'
        _send_reply(update, text)
    else:
        informthepleb(update)


@run_async
@command_antispam_passed
def whatsnew(update: Update, context: CallbackContext):
    """Reply with all new goodies"""
    # Import the changelog
    try:
        with open('changelog.md', 'r', encoding='utf-8') as changelog:
            CHANGES = changelog.read()
    except (EOFError, FileNotFoundError) as changelog_err:
        logging.error(changelog_err)
        CHANGES = 'Не смог добраться до изменений. Что-то не так.'
    # Get the last 3 day changes
    latest_changes = ''
    for change in CHANGES.split('\n\n')[:3]:
        latest_changes += change + '\n\n'
    # Add Link to full changelog
    latest_changes += 'Вся история изменений: https://bit.ly/DoomerChangelog'
    _send_reply(update, latest_changes, parse_mode='Markdown')


@run_async
def getlogs(update: Update, context: CallbackContext):
    """Get the bot logs manually or automatically to chat with id LOGCHATID"""
    # My call
    if update.message.from_user.id == DEVELOPER_ID and \
        update.message.text.lower() == '/logs':
        try:
            sendlogs(noworyesterday='now')
        except (EOFError, FileNotFoundError) as changelog_err:
            logging.ERROR(changelog_err)
            _send_reply(update, 'Не смог добраться до логов. Что-то не так.')
    # Random message for autologs
    else:
        global LOGDATE
        if datetime.date.today() > LOGDATE:
            LOGDATE = datetime.date.today()
            sendlogs(noworyesterday='yesterday')

@run_async
def sendlogs(noworyesterday: str = 'now'):
    """Send the logs"""
    # Calculate the file name
    if noworyesterday == 'yesterday':
        filename = (LOGDATE - datetime.timedelta(days=1)).isoformat()
    else:
        filename = datetime.date.today().isoformat()
    # Send the file
    BOT.send_document(chat_id=LOGCHATID,
                      document=open('logs.log', 'rb'),
                      filename=f'{filename}.log')
    # Clean the file
    with open('logs.log', 'w') as logfile:
        logfile.write(f'{datetime.date.today().isoformat()} - Start of the log file.\n')
        logfile.close()


@run_async
@command_antispam_passed
def allcommands(update: Update, context: CallbackContext):
    """Get all commands"""
    if update.message.from_user.id == DEVELOPER_ID:
        text = ''
        for commandlists in (USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS):
            text += f'<b>{commandlists[0]}:</b>\n'
            for commands in commandlists[1:]:
                text += f'/{commands[0]} - {commands[2]};\n'
        _send_reply(update, text, parse_mode='HTML')


@run_async
@command_antispam_passed
def rules(update: Update, context: CallbackContext):
    """Reply to the user with the rules of the chat"""
    reply_text = ("1. Не быть зумером, не сообщать зумерам о думском клубе;\n"
                  "2. Всяк сюда входящий, с того фото своих ножек;\n"
                  "3. Никаких гей-гифок;\n"
                  "4. За спам - фото своих ног;\n"
                  "5. Думерскую историю рассказать;\n")
    _send_reply(update, reply_text)


@run_async
def message_filter(update: Update, context: CallbackContext):
    """Replies to all messages
    Думер > Земляночка > """
    # Get logs trigged by messages
    getlogs(update, context)
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


def _doomer_word_handler(update) -> str:
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
    return reply_word if not None else False


def _anprim_word_handler(update) -> bool:
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
            BOT.send_video(chat_id=update.message.chat_id,
                           video=file_link,
                           reply_to_message_id=update.message.message_id)
        elif 'gif' in file_extension:
            BOT.send_animation(chat_id=update.message.chat_id,
                               animation=file_link,
                               reply_to_message_id=update.message.message_id)
        else:
            BOT.send_photo(chat_id=update.message.chat_id,
                           photo=file_link,
                           reply_to_message_id=update.message.message_id)

    # Cat link
    if '/cat' in update.message.text.lower():
        link = 'http://aws.random.cat/meow'
    # Dog link
    else:
        link = 'https://random.dog/woof.json'
    try:
        response = requests.get(link, timeout=REQUEST_TIMEOUT).json()
        _handle_format_and_reply(update)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        logging.error(err)
        _send_reply(update, 'Думер умер на пути к серверу.')


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
        logging.error(err)
        _send_reply(update, 'Думер умер на пути к серверу.')


@run_async
@command_antispam_passed
def slap(update: Update, context: CallbackContext):
    """Slap with random item"""
    # List the items that the target will be slapped with
    # Check if the user has indicated the target by making his message a reply
    if update.message.reply_to_message is None:
        reply = ('Кого унижать то будем?\n'
                 'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
    else:
        """Do the slap"""
        # Generate the answer + create the reply using markdown. Use weighted actions.
        # Determine if the initiator failed or succeeded
        success_and_fail = []
        # Add failures and successes if its empty and shuffle (optimize CPU usage)
        if success_and_fail == []:
            success_and_fail += ['failure'] * len(SLAPS['failure']) + \
                                ['success'] * len(SLAPS['success'])
            random.shuffle(success_and_fail)
        # Get init as it is used in both cases
        init_tag = f"[{_get(update, 'init_name')}](tg://user?id={_get(update, 'init_id')})"
        # Different replies if the user failed or succeeded to slap
        if success_and_fail.pop() == 'success':
            # Get the phrase
            action = random.choice(SLAPS['success'])
            # Slap using markdown, as some people don't have usernames to use them for notification
            target_tag = f"[{_get(update, 'target_name')}](tg://user?id={_get(update, 'target_id')})"
            reply = action.replace('init', init_tag).replace('target', target_tag)
        else:
            # Get phrase
            action = random.choice(SLAPS['failure'])
            # Prepare text
            reply = action.replace('init', init_tag)
    _send_reply(update, reply, parse_mode='Markdown')


def duel(update: Update, context: CallbackContext):
    """Duel to solve any kind of argument"""

    def _getuserstr(userid: int) -> float:
        """Get strength if the user to assist in duels"""
        userfound = dbc.execute(f'''SELECT kills, deaths from {tablename}
        WHERE user_id={userid}''').fetchone()
        if userfound:
            HARDCAP = THRESHOLDCAP * 0.95
            STRENGTH = random.uniform(LOW_BASE_ACCURACY, HIGH_BASE_ACCURACY) \
                       + userfound[0] * KILLMULT \
                       + userfound[1] * DEATHMULT
            return min(STRENGTH, HARDCAP)
        else:
            return random.uniform(LOW_BASE_ACCURACY, HIGH_BASE_ACCURACY)

    def _send_message(text_message, sleep_time: float = 0.25):
        """Shorten normal messages with sleep"""
        nonlocal update
        BOT.send_message(chat_id=update.message.chat_id,
                         text=text_message,
                         parse_mode='Markdown')
        sleep(sleep_time)

    @run_async
    def _score_the_results(winners: list, losers: list, p1_kd: tuple, p2_kd: tuple):
        """Score the results in the database"""
        # Update data
        winner, loser = winners[0], losers[0]
        counter = 0
        for player in (winner, loser):
            if counter == 0:
                kd = p1_kd
            else:  # counter == 1
                kd = p2_kd
            userid, firstname = player[1], player[0]
            dbc.execute(f'INSERT OR IGNORE INTO {tablename} (user_id, firstname) '
                        f'VALUES ("{userid}", "{firstname}")')
            dbc.execute(f'UPDATE {tablename} SET kills = kills + {kd[0]} '
                        f'WHERE user_id={userid}')
            dbc.execute(f'UPDATE {tablename} SET deaths = deaths + {kd[1]} '
                        f'WHERE user_id={userid}')
            data = dbc.execute(f'SELECT kills, deaths from {tablename} '
                               f'WHERE user_id={userid}').fetchone()
            try:
                wr = data[0] / (data[0] + data[1]) * 100
            except ZeroDivisionError:
                wr = 100
            dbc.execute(f'UPDATE {tablename} SET winpercent = {wr} '
                        f'WHERE user_id={userid}')
            counter += 1
        db.commit()

    def _usenames(scenario: str, winners: list = None, losers: list = None) -> str:
        """Insert names into the strings"""
        nonlocal update
        init_tag = f"[{_get(update, 'init_name')}](tg://user?id={_get(update, 'init_id')})"
        phrase = random.choice(DUELS['1v1'][scenario])
        if scenario == 'nonedead':
            return phrase.replace('loser1', losers[0][3]).replace('loser2', losers[1][3])
        elif scenario == 'onedead':
            phrase = phrase.replace('winner', winners[0][3]).replace('loser', losers[0][3])
            phrase += f'\nПобеда за {winners[0][3]}!'
            return phrase
        elif scenario == 'alldead':
            return phrase.replace('winner1', winners[0][3]).replace('winner2', winners[1][3])
        elif scenario == 'suicide':
            return phrase.replace('loser', init_tag)

    def _check_duel_status(update: Update):
        """Check if the duels are allowed/more possible"""
        chatid = f"\"{update.message.chat_id}\""
        chatdata = dbc.execute(f'''SELECT duelstatusonoff, duelmaximum,
        duelcount, accountingday FROM "duellimits" WHERE chat_id={chatid}''').fetchone()
        now = f"\"{datetime.datetime.now().date()}\""
        if chatdata is not None:
            if chatdata[0] == 0:
                return False
            else:
                if chatdata[1] is None:
                    return True
                else:
                    if chatdata[3] is None:
                        dbc.execute(f'''UPDATE "duellimits" SET 
                        accountingday ={now}
                        WHERE chat_id={chatid}''')
                        dbc.execute(f'''UPDATE "duellimits" SET 
                        duelcount = duelcount + 1
                        WHERE chat_id={chatid}''')
                        db.commit()
                        return True
                    if chatdata[2] >= chatdata[1]:
                        # Reset every day
                        if datetime.datetime.now().date() > datetime.date.fromisoformat(chatdata[3]):
                            dbc.execute(f'''UPDATE "duellimits" SET 
                            duelcount = 1, accountingday = {now} 
                            WHERE chat_id={chatid}''')
                            db.commit()
                            return True
                        else:
                            return False
                    else:
                        dbc.execute(f'''UPDATE "duellimits" SET 
                        duelcount = duelcount + 1
                        WHERE chat_id={chatid}''')
                        db.commit()
                        return True
        else:
            dbc.execute(f'''INSERT OR IGNORE INTO "duellimits" 
            (chat_id, duelcount, accountingday) VALUES 
            ({update.message.chat_id}, 1, {now})''')
            db.commit()
            return True

    @command_antispam_passed
    @create_duel_table
    def trytoduel(update):
        if update.message.reply_to_message is None:
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
                        (initiator_name, initiator_id,
                         _getuserstr(initiator_id), initiator_tag),
                        (target_name, target_id,
                         _getuserstr(target_id), target_tag)]
                    # Start the dueling text
                    _duel_sounds()
                    # Get the winner and the loser. Check 1
                    winthreshold = random.uniform(0, THRESHOLDCAP)
                    winners, losers = [], []
                    for player in participant_list:
                        if player[2] > winthreshold:
                            winners.append(player)
                        else:
                            losers.append(player)
                    # Get the winner and the loser. Check 2
                    if len(winners) == 2:
                        random.shuffle(winners)
                        losers.append(winners.pop())
                    # Make the scenario tree
                    if len(winners) == 0:
                        scenario = 'nonedead'
                    elif len(winners) == 1:
                        scenario = 'onedead'
                        _score_the_results(winners, losers, (1, 0), (0, 1))
                    else:
                        scenario = 'alldead'
                    # Get the result
                    duel_result = _usenames(scenario, winners, losers)
                else:
                    # If the bot is the target, send an angry message
                    scenario = 'bot'
                    duel_result = random.choice(DUELS[scenario])
            else:
                # Suicide message
                scenario = 'suicide'
                duel_result = f"{_usenames(scenario)}!\n" \
                              f"За суицид экспа/статы не даются!"
            # Give result if not answered and unless the connection died.
            # If it did, try another message.
            _send_message(duel_result, sleep_time=0)

    def _duel_sounds():
        _send_message('Дуэлисты расходятся...')
        _send_message('Готовятся к выстрелу...')
        shooting_sound = random.random() * 100
        if shooting_sound <= 96:
            _send_message('***BANG BANG***')
        elif 96 < shooting_sound <= 98:
            _send_message('***ПИФ-ПАФ***')
        else:
            _send_message('***RAPE GANG***')

    tablename = f"\"duels{update.message.chat_id}\""
    # If not replied, ask for the target
    if update.message.chat.type == 'private':
        _send_reply(update, 'Это только для групп.')
    elif _check_duel_status(update):
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
        # Get the kill, death multiplier and their percentage to total
        KILLMULTPERC = round(KILLMULT / THRESHOLDCAP * 100, 2)
        DEATHMULTPERC = round(DEATHMULT / THRESHOLDCAP * 100, 2)
        # Get the current additional strength
        ADDITIONALSTR = u_data[0] * KILLMULT + u_data[1] * DEATHMULT
        # 36 is maximum additional strength
        ADDITIONALSTR = min(ADDITIONALHARDCAP, ADDITIONALSTR)
        # Calculate the winrate increase
        WRINCREASE = round(ADDITIONALSTR / THRESHOLDCAP * 100, 2)
        reply = (f'Твой K/D равен {u_data[0]}/{u_data[1]}.\n'
                 f'Шанс победы из-за опыта повышен на {WRINCREASE}%. (максимум 45%)\n'
                 f'P.S. +{KILLMULTPERC}% за убийство, +{DEATHMULTPERC}% за смерть.')
        _send_reply(update, reply)

    # Check if not private
    if update.message.chat.type != 'private':
        # If private, assume that there was no userdata
        tablename = f"duels{update.message.chat_id}"
        # Check if the chat table exists
        if dbc.execute(f'''SELECT name FROM "sqlite_master" 
        WHERE type="table" AND name="{tablename}"''').fetchone() is not None:
            # If exists, get user data
            u_data = dbc.execute(f'''SELECT kills, deaths FROM "{tablename}" WHERE 
                user_id={update.message.from_user.id}''').fetchone()
            # If there is user data, get it
            if u_data is not None:
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
        ranking, headers = '', ''
        for query in (('Лучшие:\n', 'DESC'), ('Худшие:\n', 'ASC')):
            # Create headers to see if there was data
            headers += query[0]
            # Start the table
            ranking += query[0]
            counter = 1
            # Add to the table the five best and five worst
            for q in dbc.execute(f'''SELECT firstname, kills, deaths, winpercent 
                                        FROM "duels{update.message.chat_id}" 
                                        WHERE kills>2 AND deaths>2 
                                        ORDER BY winpercent {query[1]} LIMIT 5'''):
                ranking += f'№{counter} {q[0]}\t -\t {q[1]}/{q[2]}'
                ranking += f' ({round(q[3], 2)}%)\n'
                counter += 1
        # If got no data, inform the user
        if ranking == headers:
            ranking = 'Пока что недостаточно данных. Продолжайте дуэлиться.'
        _send_reply(update, ranking, parse_mode='Markdown')

    # Duels table create
    if update.message.chat.type != 'private':
        # Get tablename
        tablename = f"duels{update.message.chat_id}"
        # Check if the chat table exists
        if dbc.execute(f'''SELECT name FROM "sqlite_master" 
                WHERE type="table" AND name="{tablename}"''').fetchone() is not None:
            _handle_ranking(update)
        else:
            _send_reply(update, 'Для этого чата нет данных.')
    else:
        _send_reply(update, 'Это только для групп.')


@run_async
def duelstatus(update: Update, context: CallbackContext):
    """Make a global maximum duels per chat and be able to turn them on and off"""

    @run_async
    def _handle_limits():
        """Handle the global limits to duels of the chat"""
        nonlocal arg, update
        # Remove limits
        if arg == 'none':
            dbc.execute(f'''UPDATE "duellimits" 
            set duelmaximum=NULL WHERE chat_id={update.message.chat_id}''')
            _send_reply(update, 'Был убран лимит дуэлей.')
        # Set maximum
        else:
            try:
                arg = int(arg)
                dbc.execute(f'''UPDATE "duellimits" 
                set duelmaximum={arg} WHERE chat_id={update.message.chat_id}''')
                _send_reply(update, f'Максимальное количество дуэлей за день стало {arg}.')
            except ValueError:
                _send_reply(update, f'{arg} не подходит. Дайте число. /adminmenu для справки.')
        db.commit()

    @run_async
    def _handle_status():
        """Handle the on/off state of duels in the chat
        1 for turned on, 0 for turned off"""
        nonlocal arg, update
        status = None
        # Get the integer from stats
        if arg == 'on':
            status = 1
            _send_reply(update, 'Дуэли были включены для этого чата.')
        elif arg == 'off':
            status = 0
            _send_reply(update, 'Дуэли были выключены для этого чата.')
        # Update table or say that the argument was wrong
        if status == 1 or status == 0:
            dbc.execute(f'''UPDATE "duellimits" 
            set duelstatusonoff={status} WHERE chat_id={update.message.chat_id}''')
            db.commit()
        else:
            _send_reply(update, 'Всмысле? Или on или off. /adminmenu для справки.')

    commands = ['/duellimit', '/duelstatus']
    # Check if used by admin, a valid command, and there an argument to handle
    if _creatoradmindev(update) and \
            update.message.chat.type != 'private' and \
            len(update.message.text.split()) == 2:
        # Get the argument
        arg = update.message.text.lower().split()[1]
        # Pass to handlers
        if commands[0] in update.message.text.lower():
            _handle_limits()
        if commands[1] in update.message.text.lower():
            _handle_status()


@run_async
def mute(update: Update, context: CallbackContext):
    """Autodelete messages of a user (only usable by the developer)"""
    # Only works for the dev/admin/creator
    if _creatoradmindev(update):
        try:
            # Shorten code
            to_mute_id, chat_id = _get(update, 'target_id'), _get(update, 'chat_id')
            # Mute and record into database
            dbc.execute(f'''
            INSERT OR IGNORE INTO "muted" (user_id, chat_id, firstname) 
            VALUES 
            ("{to_mute_id}", 
            "{update.message.chat_id}", 
            "{update.message.reply_to_message.from_user.first_name}")''')
            # Get mute reason if there is any
            if len(update.message.text.split()) > 1:
                mutereason = ' '.join((update.message.text).split()[1:])
                dbc.execute(f'''
                    UPDATE "muted" SET reason="{mutereason}" WHERE user_id={to_mute_id} 
                    AND chat_id={update.message.chat_id}''')
            db.commit()
            # Send photo and explanation to the silenced person
            BOT.send_message(chat_id=chat_id,
                             text='Теперь ты под салом и не можешь писать в чат.',
                             reply_to_message_id=update.message.reply_to_message.message_id)
        except KeyError:
            _send_reply(update, 'Пожалуйста, выберите цель.')
    # If an ordinary used tries to use the command
    else:
        informthepleb(update)


@run_async
@command_antispam_passed
def informthepleb(update):
    _send_reply(update, 'Пошёл нахуй, ты не админ.')


@run_async
def unmute(update: Update, context: CallbackContext):
    """Stop autodeletion of messages of a user (only usable by the admin/dev/creator)"""
    # Only if the developer calls it
    if _creatoradmindev(update):
        # Get chat id, create the replied flag to not make large trees
        replied = False
        to_unmute_name = 'NULL'
        to_unmute_id = 'NULL'
        # If there is a reply, get the id of the reply target
        if update.message.reply_to_message is not None:
            to_unmute_id = _get(update, 'target_id')
        # If no reply target, take the argument if it exists
        else:
            try:
                to_unmute_name = ' '.join(update.message.text.split()[1:])
            except IndexError:
                _send_reply(update, 'Вы не указали цель.')
                replied = True
        # Check if the entry exists
        target = dbc.execute(f'''SELECT user_id, firstname FROM "muted" 
        WHERE chat_id={update.message.chat_id} AND 
        (user_id={to_unmute_id} OR firstname="{to_unmute_name}")''').fetchone()
        if target is not None:
            # Get the target name
            target_name = target[1].strip('[]')
            # Create a markdown tagged name
            target_tagged = f'[{target_name}](tg://user?id={to_unmute_id})'
            # Send the reply of successful unmute
            _send_reply(update, f'Успешно снял мут с {target_tagged}.', parse_mode='Markdown')
            # Delete the user from the muted database and commit
            dbc.execute(f'''DELETE FROM "muted" 
            WHERE chat_id={update.message.chat_id} AND 
            (user_id={to_unmute_id} OR firstname="{to_unmute_name}")''')
            db.commit()
        elif target is None and not replied:
            _send_reply(update, 'Такого в списке нет.')
    # If an ordinary used tries to use the command
    else:
        informthepleb(update)


@run_async
def immune(update: Update, context: CallbackContext):
    """Add user to exceptions"""
    if _creatoradmindev(update):
        if update.message.reply_to_message is not None:
            dbc.execute(f'''INSERT OR IGNORE INTO "exceptions" 
            (user_id, firstname) VALUES 
            ({update.message.reply_to_message.from_user.id}, 
            "{update.message.reply_to_message.from_user.first_name}")''')
            db.commit()
        else:
            _send_reply(update, 'Дай цель.')
    else:
        informthepleb(update)


@run_async
def unimmune(update: Update, context: CallbackContext):
    """Remove user from exceptions"""
    if _creatoradmindev(update):
        if update.message.reply_to_message:
            dbc.execute(f'''DELETE FROM "exceptions" 
            WHERE user_id={update.message.reply_to_message.from_user.id}''')
            db.commit()
        else:
            if len(update.message.text.split()) > 1:
                unimmune_target = ' '.join(update.message.text.split()[1:])
                dbc.execute(f'''DELETE FROM "exceptions" 
                WHERE firstname="{unimmune_target}"''')
                db.commit()
            else:
                _send_reply(update, 'Дай цель.')
    else:
        informthepleb(update)


@run_async
def immunelist(update: Update, context: CallbackContext):
    """Get the exceptions list"""
    return _getsqllist(update, 'immunelist')


@run_async
def mutelist(update: Update, context: CallbackContext):
    """Get the mute list"""
    return _getsqllist(update, 'mutelist')


@run_async
def leave(update: Update, context: CallbackContext):
    """Make the bot leave the group, usable only by the admin/dev/creator."""
    if _creatoradmindev(update):
        try:
            BOT.leave_chat(chat_id=update.message.chat_id)
        except telegram.error.BadRequest as leaveerror:
            logging.info(leaveerror)
            _send_reply(update, 'Я не могу уйти отсюда. Сам уйди.')
    else:
        informthepleb(update)


def _creatoradmindev(update):
    """Check if the user is creator or admin or dev"""
    userrank = BOT.get_chat_member(chat_id=update.message.chat_id,
                                   user_id=update.message.from_user.id)
    permitted = ['creator', 'administrator']
    if userrank in permitted or update.message.from_user.id == DEVELOPER_ID:
        return True
    else:
        return False


def _check_cooldown(update, whattocheck, cooldown):
    """Check cooldown of command, reply, error
    Whattocheck should be the sql column name"""

    def _give_command_error():
        """Give command cooldown error, if the user still spams, delete his message"""
        nonlocal update
        # Check if the error was given
        if dbc.execute(f'''SELECT errorgiven from "cooldowns" WHERE
        chat_id={update.message.chat_id} AND 
        user_id={update.message.from_user.id}''').fetchone()[0] == 0:
            # If it wasn't, give the time remaining and update the flag.
            time_remaining = str((timediff - message_time)).split('.')[0][3:]
            _send_reply(update, f'До команды осталось {time_remaining} (ММ:СС). '
                                f'Пока можешь идти нахуй, я буду пытаться удалять твои команды.')
            dbc.execute(f'''UPDATE "cooldowns" SET errorgiven = 1
            WHERE chat_id={update.message.chat_id} AND user_id={update.message.from_user.id}''')
            db.commit()
        # If it was, try to delete the message
        else:
            _try_to_delete_message(update)

    if update.message.chat.type == 'private':
        return True
    # Add exceptions for some users
    if dbc.execute(f'''SELECT * FROM exceptions 
    WHERE user_id={update.message.from_user.id}''').fetchone():
        return True
    if whattocheck == 'lastcommandreply':
        if _muted(update):
            _try_to_delete_message(update)
            return False
    # Create table if doesn't exist
    # Shorten code
    user_id = update.message.from_user.id
    message_time = datetime.datetime.now()
    # Find last instance
    lastinstance = dbc.execute(f'''SELECT {whattocheck} from "cooldowns"
    WHERE user_id={user_id} AND chat_id={update.message.chat_id}''').fetchone()
    if isinstance(lastinstance, tuple):
        lastinstance = lastinstance[0]
    # If there was a last one
    if lastinstance is not None:
        # Check if the cooldown has passed
        timediff = datetime.datetime.fromisoformat(lastinstance) + \
                   datetime.timedelta(seconds=cooldown)
        if message_time > timediff:
            # If it did, update table, return True
            dbc.execute(f'''UPDATE "cooldowns" SET 
            {whattocheck}="{message_time}", errorgiven=0 
            WHERE user_id={user_id} AND chat_id={update.message.chat_id}''')
            db.commit()
            return True
        else:
            if whattocheck == 'lastcommandreply':
                _give_command_error()
            # If it didn't return False
            return False
    # If there was none, create entry and return True
    else:
        dbc.execute(f'''INSERT OR IGNORE INTO "cooldowns" 
        (user_id, chat_id, firstname, {whattocheck}) 
        VALUES ({user_id}, "{update.message.chat_id}", 
        "{update.message.from_user.first_name}", "{message_time}")''')
        dbc.execute(f'''UPDATE "cooldowns" SET {whattocheck}="{message_time}" 
        WHERE user_id={user_id} AND chat_id={update.message.chat_id}''')
        db.commit()
        return True


@run_async
def _getsqllist(update, query: str):
    """Get the list of muted ids"""
    # Only for developer/admin/creator
    if _creatoradmindev(update):
        insert = {}
        if query == 'mutelist':
            insert['variables'] = "\"firstname\", \"reason\""
            insert['table'] = "\"muted\""
            insert['constraint'] = f"WHERE chat_id={update.message.chat_id}"
        else:  # 'immunelist'
            insert['variables'] = "\"firstname\""
            insert['table'] = "\"exceptions\""
            insert['constraint'] = ""
        # Somewhat of a table
        table = ''
        # If there are muted targets, send reply, else say that there is nobody
        listnumber = 1
        for entry in dbc.execute(f"""SELECT {insert['variables']} FROM {insert['table']} 
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
    # If an ordinary used tries to use the command
    else:
        informthepleb(update)


def _text_antispam_passed(update):
    """Checks if somebody is spamming reply_all words"""
    return _check_cooldown(update, 'lasttextreply', INDIVIDUAL_REPLY_DELAY)


def _create_tables():
    """Create a muted databases"""
    # Userdata
    dbc.execute(f'''CREATE TABLE IF NOT EXISTS "userdata"
    (id NUMERIC PRIMARY KEY UNIQUE,
    firstname TEXT NOT NULL,
    lastname TEXT DEFAULT NULL,
    username TEXT DEFAULT NULL
    )''')
    # Cooldowns
    dbc.execute(f'''CREATE TABLE IF NOT EXISTS "cooldowns" 
    (user_id NUMERIC UNIQUE, 
    chat_id NUMERIC, 
    firstname TEXT DEFAULT NULL, 
    lastcommandreply TEXT DEFAULT NULL, 
    errorgiven NUMERIC DEFAULT 0, 
    lasttextreply TEXT DEFAULT NULL,
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname)
    )''')
    # Muted
    dbc.execute(f'''CREATE TABLE IF NOT EXISTS "muted" 
    (user_id NUMERIC UNIQUE, 
    chat_id NUMERIC, 
    firstname TEXT DEFAULT NULL, 
    reason TEXT DEFAULT NULL,
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname)
    )''')
    # Exceptions
    dbc.execute(f'''CREATE TABLE IF NOT EXISTS "exceptions"
    (user_id NUMERIC UNIQUE,
    firstname TEXT DEFAULT NULL,
    FOREIGN KEY(user_id) REFERENCES userdata(id),
    FOREIGN KEY(firstname) REFERENCES userdata(firstname))
    ''')
    dbc.execute(f''' 
    INSERT OR REPLACE INTO "exceptions" (user_id, firstname) 
    VALUES 
    (255295801, "doitforricardo"), 
    (413327053, "comradesanya"),
    (205762941, "dovaogedot"),
    (185500059, "mel_a_real_programmer")''')
    # Table that tracks limitations of number of duels per day
    dbc.execute(f'''CREATE TABLE IF NOT EXISTS "duellimits"
     (chat_id NUMERIC PRIMARY KEY,
     duelstatusonoff NUMERIC DEFAULT 1,
     duelmaximum NUMERIC DEFAULT NULL,
     duelcount NUMERIC DEFAULT 0,
     accountingday TEXT DEFAULT NULL
     )''')
    # Commit the database
    db.commit()


@run_async
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


def _get(update: Update, what_is_needed: str):
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
    found = dbc.execute(f'''SELECT "user_id" FROM "muted" 
    WHERE user_id={update.message.from_user.id} AND 
    chat_id={update.message.chat_id}''').fetchone()
    if found is None:
        return False
    else:
        # Check for exceptions
        exception = dbc.execute(f'''SELECT "user_id" from "exceptions"
        WHERE user_id={update.message.from_user.id}''').fetchone()
        if exception is None:
            return True
        else:
            return False


def error_callback(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logging.warning('Error "%s" caused by update "%s"', context.error, update)


# Bot commands
USERCOMMANDS = [
    'Команды для рядовых пользователей',
    ("help", help, 'Меню помощи'),
    ('whatsnew', whatsnew, 'Новое в боте'),
    ("rules", rules, 'Правила думерского чата'),
    ('adminmenu', adminmenu, 'Админское меню'),
    ("slap", slap, 'Кого-то унизить (надо ответить жертве, чтобы бот понял кого бить)'),
    ('duel', duel, 'Устроить дуэль (надо ответить тому, с кем будет дуэль)'),
    ('myscore', myscore, 'Мой счёт в дуэлях'),
    ('duelranking', duelranking, 'Ранкинг дуэлей чата (показывает только тех, у кого больше 2-х убийств и смертей)'),
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
    ('mute', mute, 'Замутить человека в этом чате (надо ему ответить командой)'),
    ('unmute', unmute, 'Cнять мут в этом чате (ответить или имя)'),
    ('mutelist', mutelist, 'Показать всех в муте в этом чате'),
    ]
UNUSUALCOMMANDS = [
    'Нечастые команды',
    ('allcommands', allcommands, 'Все команды бота'),
    ('start', start, 'Начальное сообщение бота'),
    ('logs', getlogs, 'Получить логи бота (только для разработчика)')
    ]


def main():
    """Start the BOT."""
    # Create the Updater and pass it your BOT's token.
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    logging.info('Adding handlers...')
    # Add command handles
    for commandlists in (USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS):
        for command in commandlists[1:]:
            dp.add_handler(CommandHandler(command[0], command[1]))

    # add message handlers
    dp.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, welcomer))
    dp.add_handler(MessageHandler(
        Filters.status_update.left_chat_member, farewell))
    dp.add_handler(MessageHandler(
        Filters.all, message_filter))

    # log all errors
    dp.add_error_handler(error_callback)

    # Create databases
    logging.info('Creating database tables if needed...')
    _create_tables()

    # Start the Bot
    # Set clean to True to clean any pending updates on Telegram servers before
    # actually starting to poll. Otherwise the BOT may spam the chat on coming
    # back online
    updater.start_polling(clean=True)
    logging.info('Polling started.')
    logging.info('-----------------------------------------------')

    # Run the BOT until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the BOT gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
