"""/duel command."""

import random
from datetime import date, datetime, timedelta

from telegram import Update
from telegram.ext import CallbackContext, run_async
from maindoomer import BOT
from commandPretexts.duels import DUELS
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@check_if_group_chat
def duel(update: Update, context: CallbackContext):
    """Duel to solve any kind of argument."""
    # noinspection PyUnresolvedReferences
    if _check_duel_status(update):
        _try_to_duel(update)
    else:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='На сегодня дуэли всё/дуэли отключены.'
        )


def _check_duel_status(update: Update) -> bool:
    """Check if the duels are allowed/more possible."""
    chat_id = f"{update.effective_chat.id}"
    chatdata = run_query(
        'SELECT duelstatusonoff, duelmaximum, duelcount, accountingday '
        'FROM chattable WHERE chat_id=(?)', (chat_id,)
    )[0]
    now = f"{datetime.now().date()}"
    if chatdata:
            # If duels are turned off, disallow duels
        if chatdata[0] == 0:
            return False
        # If there is no maximum, allow for duels
        if chatdata[1] is None:
            return True
        # If no duels have been counted, or old day, increment by 1
        if chatdata[3] is None or \
                date.fromisoformat(now) > date.fromisoformat(chatdata[3]):
            run_query(
                'UPDATE chattable SET accountingday=(?), duelcount=1 '
                'WHERE chat_id=(?)', (now, chat_id)
            )
            return True
        # If number of duels done is higher than the maximum
        if chatdata[2] >= chatdata[1]:
            # Reset every day
            if datetime.now().date() > \
                    date.fromisoformat(chatdata[3]):
                run_query(
                    'UPDATE chattable SET duelcount=1, accountingday=(?)'
                    'WHERE chat_id=(?)', (now, chat_id)
                )
                return True
            return False
        # Increment if none of the conditions were met
        run_query(
            'UPDATE chattable SET duelcount=duelcount+1 WHERE chat_id=(?)',
            (chat_id,)
        )
        return True
    # If there is no chat data, create it
    run_query(
        'INSERT OR IGNORE INTO chattable (chat_id, duelcount, accountingday)'
        'VALUES (?, ?, ?)', (chat_id, 1, now)
    )
    return True


@run_async
@command_antispam_passed
def _try_to_duel(update: Update):
    """Try to duel. Main duel function."""
    if update.effective_message.reply_to_message is None:
        reply = ('С кем дуэль проводить будем?\n'
                 'Чтобы подуэлиться, надо чтобы вы ответили вашему оппоненту.')
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text=reply
        )
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
                (initiator_name, initiator_id,
                 _get_user_str(update, initiator_id), initiator_tag),
                (target_name, target_id,
                 _get_user_str(update, target_id), target_tag)
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
            duel_result = _use_names(update, scenario, winners, losers)
            return _conclude_the_duel(update, duel_result, participant_list)
        else:
            # If the bot is the target, send an angry message
            scenario = 'bot'
            duel_result = _use_names(update, scenario)
    else:
        # Suicide message
        scenario = 'suicide'
        duel_result = f"{_use_names(update, scenario)}!\n" \
                      f"За суицид экспа/статы не даются!"
    # Send the reply for all cases
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=duel_result,
        parse_mode='Markdown'
    )


def _get_user_str(update: Update, userid: int) -> float:
    """Get strength if the user to assist in duels."""
    # Check if table exists
    userfound = run_query(
        'SELECT kills, deaths, misses FROM duels WHERE '
        'user_id=(?) AND chat_id=(?)',
        (userid, update.effective_chat.id)
    )
    if userfound:
        from constants import DUELDICT as DD
        userdata = userfound[0]
        strength = random.uniform(DD['LOW_BASE_ACCURACY'], DD['HIGH_BASE_ACCURACY']) \
            + userdata[0] * DD['KILLMULT'] \
            + userdata[1] * DD['DEATHMULT'] \
            + userdata[2] * DD['MISSMULT']
        return min(strength, DD['STRENGTHCAP'])
    # Return base if table not found or user not found
    return random.uniform(DD['LOW_BASE_ACCURACY'], DD['HIGH_BASE_ACCURACY'])


def _use_names(update: Update, scenario: str, winners: list = None, losers: list = None) -> str:
    """Insert names into the strings."""
    init_tag = f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"
    phrase = random.choice(DUELS[scenario])
    if scenario == 'nonedead':
        return phrase.replace('loser1', losers[0][3]).replace('loser2', losers[1][3])
    if scenario == 'onedead':
        phrase = phrase.replace('winner', winners[0][3]).replace(
            'loser', losers[0][3])
        phrase += f'\nПобеда за {winners[0][3]}!'
        if winners[0][1] == update.effective_user.id:
            from constants import SHORTCD
            phrase += f'\nТвой кулдаун был ресетнут до {SHORTCD // 60}-х минут!'
        return phrase
    if scenario == 'suicide':
        return phrase.replace('loser', init_tag)
    if scenario == 'bot':
        return random.choice(DUELS[scenario])


@run_async
def _score_the_results(winners: list, losers: list, p1_kdm: tuple, p2_kdm: tuple):
    """Score the results in the database."""
    # One dead
    if winners:
        player_1, player_2 = winners[0], losers[0]
        # Remove cooldown from the winner if it was the initiator
        if update.effective_user.id == player_1[1]:
            # Reduce winner cooldown
            from constants import CDREDUCTION
            shortercd = datetime.now() - timedelta(seconds=CDREDUCTION)
            run_query(
                'UPDATE cooldowns SET lastcommandreply=(?) WHERE user_id=(?) '
                'AND chat_id=(?)',
                (shortercd, player_1[1], update.effective_chat.id)
            )
    # None dead
    else:
        player_1, player_2 = losers[0], losers[1]
    counter = 0
    for player in (player_1, player_2):
        duelscore = p1_kdm if counter == 0 else p2_kdm
        userid, firstname = player[1], player[0]
        run_query(
            'INSERT OR IGNORE INTO duels (user_id, chat_id, firstname) '
            'VALUES (?, ?, ?)', (userid, update.effective_chat.id, firstname)
        )
        run_query(
            'UPDATE duels SET kills=kills+(?), deaths=deaths+(?), misses=misses+(?)'
            'WHERE user_id=(?) AND chat_id=(?)',
            (duelscore[0], duelscore[1], duelscore[2],
             userid, update.effective_chat.id)
        )
        counter += 1


@run_async
def _conclude_the_duel(update: Update, result: str, participants):
    """Send all the messages for the duel."""
    from time import sleep
    # Send the initial message
    botmsg = BOT.send_message(
        chat_id=update.effective_chat.id,
        text='Дуэлисты расходятся...'
    )
    # Get the sound of the duel
    sound = '***BANG BANG***' if random.random() < 0.90 else '***ПИФ-ПАФ***'
    # Make the message loop
    for phrase in ('Готовятся к выстрелу...', sound, result):
        sleep(0.85)
        botmsg = BOT.edit_message_text(
            chat_id=update.effective_chat.id,
            text=phrase,
            message_id=botmsg.message_id,
            parse_mode='Markdown'
        )
    for player in participants:
        _try_to_hard_reset(update, player)


def _try_to_hard_reset(update: Update, participant: list) -> None:
    """Try to hard reset stats."""
    from constants import HARDRESETCHANCE
    if random.uniform(0, 1) < HARDRESETCHANCE:
        run_query('DELETE FROM duels WHERE user_id=(?) AND chat_id=(?)',
                  (participant[1], update.effective_chat.id))
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text=f'Упс, я случайно ресетнул все статы {participant[3]}.\n'
            f'Кому-то сегодня не везёт.',
            parse_mode='Markdown'
        )
