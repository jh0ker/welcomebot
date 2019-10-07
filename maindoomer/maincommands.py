"""
Module dedicated to the main commands of the bot.
This is all it has to offer in terms of functionality to regular users.
"""
import datetime
import random

import requests
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from maindoomer.__init__ import BOT, LOGGER
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@command_antispam_passed
def flip(update: Update, context: CallbackContext):
    """Flip a Coin"""
    BOT.send_message(chat_id=update.effective_chat.id,
                     reply_to_message_id=update.effective_message.message_id,
                     text=random.choice(['Орёл!', 'Решка!']))


@run_async
def dadjoke(update: Update, context: CallbackContext):
    """Get a random dad joke"""

    @run_async
    @command_antispam_passed
    def handle_joke(update: Update):
        """Reply using this to account for the antispam decorator."""
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text=response['joke'])

    # Retrieve the json with, the joke
    try:
        from constants import REQUEST_TIMEOUT
        response: dict = requests.get(
            'https://icanhazdadjoke.com/', headers={'Accept': 'application/json'},
            timeout=REQUEST_TIMEOUT).json()
        handle_joke(update)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        LOGGER.error(err)
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text='Думер умер на пути к серверу. Попробуйте ещё раз.')


@run_async
@command_antispam_passed
@check_if_group_chat
def slap(update: Update, context: CallbackContext):
    """Slap with random item"""
    from commandPretexts.slaps import SLAPS
    # Check if there was a target
    if update.effective_message.reply_to_message is None:
        reply = ('Кого унижать то будем?\n'
                 'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
    else:
        # Get success and fail chances
        success_and_fail: list = []
        # Add failures and successes if its empty and shuffle (optimize CPU usage)
        if not success_and_fail:
            success_and_fail += ['failure'] * len(SLAPS['failure']) + \
                                ['success'] * len(SLAPS['success'])
            random.shuffle(success_and_fail)
        # Get user tags as it is used in both cases
        init_tag = f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"
        tdata = update.effective_message.reply_to_message.from_user
        target_tag = f"[{tdata.first_name}](tg://user?id={tdata.id})"
        # Different depending on the scenario
        scenario = success_and_fail.pop()
        action = random.choice(SLAPS[scenario])
        # Replace premade text with user tags.
        reply = action.replace('init', init_tag).replace('target', target_tag)
    BOT.send_message(chat_id=update.effective_chat.id,
                     reply_to_message_id=update.effective_message.message_id,
                     text=reply,
                     parse_mode='Markdown')


@run_async
@command_antispam_passed
def loli(update: Update, context: CallbackContext):
    """Send photo of loli"""
    import xml.etree.ElementTree as ET
    from telegram import InlineKeyboardButton
    from telegram import InlineKeyboardMarkup
    # Get the photo type Safe/Explicit
    lolitype = run_query(
        '''SELECT loliNSFW from "chattable" WHERE chat_id=(?)''', (update.effective_chat.id,))[0][0]
    tags = 'child+highres+1girl+Rating%3ASafe' if lolitype == 0 else 'loli+highres+sex'
    # Send action of uploading the photo
    BOT.send_chat_action(chat_id=update.effective_chat.id,
                         action='upload_photo')
    # Get the photo ----------------------------------------------
    # Get the url start and get the count of the posts for the tag
    from constants import LOLI_BASE_URL
    post_count = ET.fromstring(requests.get(LOLI_BASE_URL + tags).content).get('count')
    # Get the random offset
    offset = random.randint(0, int(post_count))
    # Get the random image in json
    url = LOLI_BASE_URL + tags + f'&json=1&pid={offset}'
    response = requests.get(url).json()[0]
    # Get the image link
    image_link = response['file_url']
    # ------------------------------------------------------------
    # Get the source info
    source = response.get('source')
    # Create a source button
    if source:
        keyboard = [[InlineKeyboardButton(text='Первоисточник', url=source)]]
        source_button = InlineKeyboardMarkup(keyboard)
        caption = None
    else:
        caption = 'Первоисточник не найден'
        source_button = None
    # Send the result
    from telegram.error import BadRequest
    try:
        BOT.send_photo(chat_id=update.effective_chat.id,
                       photo=image_link,
                       reply_markup=source_button,
                       caption=caption,
                       reply_to_message_id=update.effective_message.message_id)
    except BadRequest:
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text='Думер умер на пути к серверу. Попробуйте ещё раз.')
        # Reset cooldown if sending failed
        from constants import INDIVIDUAL_USER_DELAY
        run_query('UPDATE cooldowns SET lastcommandreply=(?) WHERE '
                  'chat_id=(?) AND user_id=(?)',
                  (datetime.datetime.now() - datetime.timedelta(minutes=INDIVIDUAL_USER_DELAY),
                   update.effective_chat.id, update.effective_user.id))


@run_async
@command_antispam_passed
def lolimode(update: Update, context: CallbackContext):
    """Set SFW/NSFW for Loli content"""
    from telegram import InlineKeyboardButton
    from telegram import InlineKeyboardMarkup
    # Get current settings
    lolitype = run_query(
        '''SELECT loliNSFW from "chattable" WHERE chat_id=(?)''', (update.effective_chat.id,))[0][0]
    currentstate = 'На данный момент контент '
    currentstate += '***БЕЗ НЮДСОВ (SFW)***.' if lolitype == 0 else '***C НЮДСАМИ (NSFW)***.'
    info = '\nЭту настройку может менять только администратор или создатель чата.' \
           '\nЗапросы от других пользователей пропускаются.'
    # Create settings buttons
    keyboard = [[InlineKeyboardButton('Без нюдсов (SFW)', callback_data='legal'),
                 InlineKeyboardButton('С нюдсами (NSFW)', callback_data='illegal')]]
    loli_settings = InlineKeyboardMarkup(keyboard)
    # Send options
    BOT.send_message(chat_id=update.effective_chat.id,
                     text=currentstate + info,
                     reply_markup=loli_settings,
                     reply_to_message_id=update.effective_message.message_id,
                     parse_mode='Markdown')


@run_async
@command_antispam_passed
def animal(update: Update, context: CallbackContext):
    """Get photo/video/gif of dog or cat"""

    @run_async
    def _handle_format_and_reply(update: Update):
        """Handle the format of the file and reply accordingly"""
        nonlocal response
        # Send uploading state
        file_link = list(response.values())[0]
        file_extension = file_link.split('.')[-1]
        if 'mp4' in file_extension:
            BOT.send_video(chat_id=update.effective_chat.id,
                           video=file_link,
                           reply_to_message_id=update.effective_message.message_id)
        elif 'gif' in file_extension:
            BOT.send_animation(chat_id=update.effective_chat.id,
                               animation=file_link,
                               reply_to_message_id=update.effective_message.message_id)
        else:
            BOT.send_photo(chat_id=update.effective_chat.id,
                           photo=file_link,
                           reply_to_message_id=update.effective_message.message_id)

    from constants import REQUEST_TIMEOUT
    # Cat link
    if '/cat' in update.effective_message.text.lower():
        link = 'http://aws.random.cat/meow'
    # Dog link
    else:
        link = 'https://random.dog/woof.json'
    try:
        BOT.send_chat_action(chat_id=update.effective_chat.id,
                             action='upload_photo')
        response = requests.get(link, timeout=REQUEST_TIMEOUT).json()
        _handle_format_and_reply(update)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        LOGGER.error(err)
        BOT.send_message(chat_id=update.effective_chat.id,
                         text='Думер умер на пути к серверу. Попробуйте ещё раз.',
                         reply_to_message_id=update.effective_message.message_id)


@run_async
@command_antispam_passed
@check_if_group_chat
def pidor(update: Update, context: CallbackContext):
    """Get the pidor of the day from all users stored for the chat"""

    def getnewpidor():
        # Exclude users that are not in the chat, and delete their data if they are gone
        nonlocal lastpidor, update
        while True:
            allchatusers = run_query('SELECT user_id FROM userdata '
                                     'WHERE chat_id=(?)', (update.effective_chat.id,))
            if not allchatusers:
                return
            todaypidorid = random.choice(allchatusers)[0]
            # Remove repetition
            if lastpidor:
                if len(allchatusers) > 1 and todaypidorid == lastpidor[0][0]:
                    continue
            try:
                newpidor = BOT.get_chat_member(chat_id=update.effective_chat.id,
                                               user_id=todaypidorid)
                newpidorname = newpidor.user.first_name
                break
            except:
                run_query('DELETE FROM userdata WHERE chat_id=(?) AND user_id=(?)',
                          (update.effective_chat.id, todaypidorid))
                continue
        run_query('''UPDATE chattable SET lastpidorday=(?), lastpidorid=(?), lastpidorname=(?)
            WHERE chat_id=(?)''', (datetime.date.today().isoformat(), todaypidorid,
                                   newpidorname, update.effective_chat.id))
        run_query('''UPDATE userdata SET timespidor=timespidor+1, firstname=(?)
            WHERE chat_id=(?) AND user_id=(?)''', (newpidorname, update.effective_chat.id, todaypidorid))
        todaypidor = f"[{newpidorname.strip('[]')}](tg://user?id={todaypidorid})"
        return todaypidor

    # Check last pidor day
    # Use index to select first, no exception as chat data is created by antispam handler
    lastpidor = run_query('SELECT lastpidorid, lastpidorday, lastpidorname FROM chattable '
                          'WHERE chat_id=(?)', (update.effective_chat.id,))
    if not lastpidor:
        todaypidor = getnewpidor()
    elif lastpidor[0][0] is None or datetime.date.fromisoformat(lastpidor[0][1]) < datetime.date.today():
        todaypidor = getnewpidor()
    else:
        todaypidor = lastpidor[0][2]
    BOT.send_message(chat_id=update.effective_chat.id,
                     text=f'Пидором дня является {todaypidor}!',
                     reply_to_message_id=update.effective_message.message_id,
                     parse_mode='Markdown')


@run_async
@command_antispam_passed
@check_if_group_chat
def pidorme(update: Update, context: CallbackContext):
    """Give the user the number of times he has been pidor of the day"""
    timespidor = run_query('''SELECT timespidor FROM userdata WHERE
    chat_id=(?) AND user_id=(?)''', (update.effective_chat.id, update.effective_user.id))
    if timespidor:
        reply = f'Вы были пидором дня *{timespidor[0][0]} раз(а)*!'
    else:
        reply = 'Вы ещё не разу не были пидором дня!'
    BOT.send_message(chat_id=update.effective_chat.id,
                     reply_to_message_id=update.effective_message.message_id,
                     text=reply,
                     parse_mode='Markdown')


@run_async
@command_antispam_passed
@check_if_group_chat
def pidorstats(update: Update, context: CallbackContext):
    """Get the chat stats of how many times people have been pidors of the day"""
    chatstats = run_query('SELECT firstname, timespidor FROM userdata '
                          'WHERE chat_id=(?) ORDER BY timespidor DESC, firstname', (update.effective_chat.id,))
    table = ''
    counter = 1
    # Get top 10
    for entry in chatstats:
        table += f'{counter}. {entry[0]} - *{entry[1]} раз(а)*\n'
        if counter == 10:
            break
        counter += 1
    # Get the number of players
    numberofplayers = len(chatstats)
    if numberofplayers != 0:
        table += f'\nВсего участников - *{numberofplayers}*'
    if table == '':
        reply = 'Пидоров дня ещё не было!'
    else:
        reply = table
    BOT.send_message(chat_id=update.effective_chat.id,
                     reply_to_message_id=update.effective_message.message_id,
                     text=reply,
                     parse_mode='Markdown')


@check_if_group_chat
def duel(update: Update, context: CallbackContext):
    """Duel to solve any kind of argument"""

    def _getuserstr(userid: int) -> float:
        """Get strength if the user to assist in duels"""
        from constants import DUELDICT as DD
        # Check if table exists
        userfound = run_query('SELECT kills, deaths, misses FROM duels WHERE '
                              'user_id=(?) AND chat_id=(?)', (userid, update.effective_chat.id))
        if userfound:
            userdata = userfound[0]
            strength = random.uniform(DD['LOW_BASE_ACCURACY'], DD['HIGH_BASE_ACCURACY']) \
                       + userdata[0] * DD['KILLMULT'] \
                       + userdata[1] * DD['DEATHMULT'] \
                       + userdata[2] * DD['MISSMULT']
            return min(strength, DD['STRENGTHCAP'])
        # Return base if table not found or user not found
        return random.uniform(DD['LOW_BASE_ACCURACY'], DD['HIGH_BASE_ACCURACY'])

    @run_async
    def _score_the_results(winners: list, losers: list, p1_kdm: tuple, p2_kdm: tuple):
        """Score the results in the database"""
        # One dead
        if winners:
            player_1, player_2 = winners[0], losers[0]
            # Remove cooldown from the winner if it was the initiator
            if update.effective_user.id == player_1[1]:
                # Reduce winner cooldown
                from constants import CDREDUCTION
                shortercd = datetime.datetime.now() - datetime.timedelta(seconds=CDREDUCTION)
                run_query('UPDATE cooldowns SET lastcommandreply=(?) WHERE user_id=(?) '
                          'AND chat_id=(?)', (shortercd, player_1[1], update.effective_chat.id))
        # None dead
        else:
            player_1, player_2 = losers[0], losers[1]
        counter = 0
        for player in (player_1, player_2):
            duelscore = p1_kdm if counter == 0 else p2_kdm
            userid, firstname = player[1], player[0]
            run_query('INSERT OR IGNORE INTO duels (user_id, chat_id, firstname) '
                      'VALUES (?, ?, ?)', (userid, update.effective_chat.id, firstname))
            run_query('UPDATE duels SET kills=kills+(?), deaths=deaths+(?), misses=misses+(?)'
                      'WHERE user_id=(?) AND chat_id=(?)',
                      (duelscore[0], duelscore[1], duelscore[2], userid, update.effective_chat.id))
            counter += 1

    def _usenames(scenario: str, winners: list = None, losers: list = None) -> str:
        """Insert names into the strings"""
        nonlocal update, DUELS
        init_tag = f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"
        phrase = random.choice(DUELS[scenario])
        if scenario == 'nonedead':
            return phrase.replace('loser1', losers[0][3]).replace('loser2', losers[1][3])
        if scenario == 'onedead':
            phrase = phrase.replace('winner', winners[0][3]).replace('loser', losers[0][3])
            phrase += f'\nПобеда за {winners[0][3]}!'
            if winners[0][1] == update.effective_user.id:
                from constants import SHORTCD
                phrase += f'\nВсе твои кулдауны были ресетнуты до {SHORTCD // 60}-х минут!'
            return phrase
        if scenario == 'suicide':
            return phrase.replace('loser', init_tag)
        if scenario == 'bot':
            return random.choice(DUELS[scenario])

    def _check_duel_status() -> bool:
        """Check if the duels are allowed/more possible"""
        nonlocal update
        chatid = f"{update.effective_chat.id}"
        chatdata = run_query('SELECT duelstatusonoff, duelmaximum, duelcount, accountingday '
                             'FROM chattable WHERE chat_id=(?)', (chatid,))[0]
        now = f"{datetime.datetime.now().date()}"
        if chatdata:
            # If duels are turned off, disallow duels
            if chatdata[0] == 0:
                return False
            # If there is no maximum, allow for duels
            if chatdata[1] is None:
                return True
            # If no duels have been counted, or old day, increment by 1
            if chatdata[3] is None or \
                    datetime.date.fromisoformat(now) > datetime.date.fromisoformat(chatdata[3]):
                run_query('UPDATE chattable SET accountingday=(?), duelcount=1 '
                          'WHERE chat_id=(?)', (now, chatid))
                return True
            # If number of duels done is higher than the maximum
            if chatdata[2] >= chatdata[1]:
                # Reset every day
                if datetime.datetime.now().date() > \
                        datetime.date.fromisoformat(chatdata[3]):
                    run_query('UPDATE chattable SET duelcount=1, accountingday=(?)'
                              'WHERE chat_id=(?)', (now, chatid))
                    return True
                return False
            # Increment if none of the conditions were met
            run_query('UPDATE chattable SET duelcount=duelcount+1 WHERE chat_id=(?)',
                      (chatid,))
            return True
        # If there is no chat data, create it
        run_query('INSERT OR IGNORE INTO chattable (chat_id, duelcount, accountingday)'
                  'VALUES (?, ?, ?)', (chatid, 1, now))
        return True

    @run_async
    @command_antispam_passed
    def trytoduel(update: Update):
        """The main duel function"""
        if update.effective_message.reply_to_message is None:
            reply = ('С кем дуэль проводить будем?\n'
                     'Чтобы подуэлиться, надо чтобы вы ответили вашему оппоненту.')
            BOT.send_message(chat_id=update.effective_chat.id,
                             reply_to_message_id=update.effective_message.message_id,
                             text=reply)
            return
        from constants import THRESHOLDCAP
        # Shorten the code, format the names
        initiator_name, initiator_id = update.effective_user.first_name, update.effective_user.id
        tdata = update.effective_message.reply_to_message.from_user
        target_name, target_id = tdata.first_name, tdata.id
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
                return _conclude_the_duel(duel_result, participant_list)
            else:
                # If the bot is the target, send an angry message
                scenario = 'bot'
                duel_result = _usenames(scenario)
        else:
            # Suicide message
            scenario = 'suicide'
            duel_result = f"{_usenames(scenario)}!\n" \
                          f"За суицид экспа/статы не даются!"
        # Send the reply for all cases
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text=duel_result,
                         parse_mode='Markdown')

    @run_async
    def _conclude_the_duel(result: str, participants):
        """Send all the messages for the duel."""
        nonlocal update
        from time import sleep
        # Send the initial message
        botmsg = BOT.send_message(chat_id=update.effective_chat.id,
                                  text='Дуэлисты расходятся...')
        # Get the sound of the duel
        sound = '***BANG BANG***' if random.random() < 0.90 else '***ПИФ-ПАФ***'
        # Make the message loop
        for phrase in ('Готовятся к выстрелу...', sound, result):
            sleep(0.8)
            botmsg = BOT.edit_message_text(chat_id=update.effective_chat.id,
                                           text=phrase,
                                           message_id=botmsg.message_id,
                                           parse_mode='Markdown')
        for player in participants:
            _try_to_hard_reset(player)

    def _try_to_hard_reset(participant):
        """Try to hard reset stats"""
        nonlocal update
        from constants import HARDRESETCHANCE
        if random.uniform(0, 1) < HARDRESETCHANCE:
            run_query('DELETE FROM duels WHERE user_id=(?) AND chat_id=(?)',
                      (participant[1], update.effective_chat.id))
            BOT.send_message(chat_id=update.effective_chat.id,
                             text=f'Упс, я случайно ресетнул все статы {participant[3]}.\n'
                                  f'Кому-то сегодня не везёт.',
                             parse_mode='Markdown')

    # noinspection PyUnresolvedReferences
    from commandPretexts.duels import DUELS
    if _check_duel_status():
        trytoduel(update)
    else:
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text='На сегодня дуэли всё/дуэли отключены.')


@run_async
@check_if_group_chat
def myscore(update, context):
    """Give the user his K/D for duels"""

    @run_async
    @command_antispam_passed
    def _handle_score(update):
        nonlocal u_data
        userkda = u_data[0]
        from constants import DUELDICT as DD
        # Get the current additional strength
        wrincrease = userkda[0] * DD['KILLMULTPERC'] + \
                     userkda[1] * DD['DEATHMULTPERC'] + \
                     userkda[2] * DD['MISSMULTPERC']
        wrincrease = min(round(wrincrease, 2), 45)
        try:
            wr = userkda[0] / (userkda[0] + userkda[1]) * 100
        except ZeroDivisionError:
            wr = 100
        reply = (f'Твой K/D/M равен {userkda[0]}/{userkda[1]}/{userkda[2]} ({round(wr, 2)}%)\n'
                 f"Шанс победы из-за опыта изменен на {wrincrease}%. (максимум {DD['ADDITIONALPERCENTCAP']}%)\n"
                 f"P.S. {DD['KILLMULTPERC']}% за убийство, {DD['DEATHMULTPERC']}% за смерть, {DD['MISSMULTPERC']}% за "
                 f"мисс.")
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text=reply)

    # Get userdata

    u_data = run_query('SELECT kills, deaths, misses from duels WHERE user_id=(?) AND chat_id=(?)',
                       (update.effective_user.id, update.effective_chat.id))
    # Check if the data for the user exists
    if u_data:
        # If there is user data, get the score
        _handle_score(update)
    else:
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text='Сначала подуэлься, потом спрашивай.')


@run_async
@check_if_group_chat
def duelranking(update: Update, context: CallbackContext):
    """Get the top best duelists"""

    @run_async
    @command_antispam_passed
    def _handle_ranking(update: Update):
        ranking = headers = '***Убийства/Смерти/Непопадания\n***'
        for query in (('Лучшие:\n', 'DESC'), ('Худшие:\n', 'ASC')):
            # Create headers to see if there was data
            headers += query[0]
            # Start the table
            ranking += query[0]
            counter = 1
            # Add to the table the five best and five worst
            for Q in run_query(f'''SELECT winrate.firstname, doom.kills, doom.deaths, doom.misses, winrate.wr
            FROM "duels" AS doom JOIN
            (SELECT firstname, kills * 100.0/(kills+deaths) AS wr
                FROM "duels"
                    WHERE deaths!=0 AND kills!=0 AND chat_id=(?)) AS winrate
            ON doom.firstname=winrate.firstname WHERE chat_id=(?)
                ORDER BY wr {query[1]} LIMIT 5''', (update.effective_chat.id, update.effective_chat.id)):
                ranking += f'№{counter} {Q[0]}\t -\t {Q[1]}/{Q[2]}/{Q[3]}'
                ranking += f' ({round(Q[4], 2)}%)\n'
                counter += 1
        # If got no data, inform the user
        if ranking == headers:
            ranking = 'Пока что недостаточно данных. Продолжайте дуэлиться.'
        # Add a footer to the table
        else:
            ranking += 'Показываются только дуэлянты у которых есть убийства и смерти.'
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text=ranking,
                         parse_mode='Markdown')

    if update.effective_message.chat.type == 'private':
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text='Это только для групп.')
        return
    # Check if the chat table exists
    if run_query('SELECT user_id FROM duels WHERE chat_id=(?)', (update.effective_chat.id,)):
        _handle_ranking(update)
    else:
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text='Для этого чата нет данных.')

@run_async
@check_if_group_chat
def rolluser(update: Update, context: CallbackContext):
    """Get a random chat user"""
    users = run_query('SELECT user_id from userdata WHERE chat_id=(?)',
                      (update.effective_chat.id,))
    while True:
        user_id = random.choice(users)[0]
        try:
            userdata = BOT.get_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id
            ).user
            user_name = userdata.first_name
            break
        except:
            continue
    BOT.send_message(
        chat_id=update.effective_chat.id,
        text=f"[{user_name}](tg://user?id={user_id})",
        parse_mode='Markdown'
    )
    