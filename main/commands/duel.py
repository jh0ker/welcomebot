"""/duel command."""

from datetime import date, datetime, timedelta

from telegram import Update, Message
from telegram.ext import CallbackContext, run_async
from main import randomizer
from commandPretexts.duels import DUELS
from main.helpers import check_if_group_chat, antispam_passed, set_cooldown
from main.database import *


def duel(update: Update, context: CallbackContext) -> Message:
    """Duel to solve any kind of argument."""
    # noinspection PyUnresolvedReferences
    if duels_active(update):
        _try_to_duel(update, context)
    else:
        update.message.reply_text('Дуэли отключены.')


@db_session
def duels_active(update: Update) -> bool:
    """Check if the duels are allowed."""
    if Options[Chats[update.message.chat.id]].duel_active:
        return True
    return False


@run_async
@antispam_passed
def _try_to_duel(update: Update, context: CallbackContext) -> None:
    """Try to duel. Main duel function."""
    if update.message.reply_to_message is None:
        reply = ('С кем дуэль проводить будем?\n'
                 'Чтобы подуэлиться, надо чтобы вы ответили вашему оппоненту.')
        update.message.reply_text(reply)
        set_cooldown(update, False)
        return
    from main.constants import THRESHOLDCAP
    # Shorten the code, format the names
    init_data = update.message.from_user
    targ_data = update.message.reply_to_message.from_user
    init_name, init_id = init_data.full_name, init_data.id
    targ_name, targ_id = targ_data.full_name, targ_data.id
    init_tag = f'[{init_name}](tg://user?id={init_id})'
    targ_tag = f'[{targ_name}](tg://user?id={targ_id})'
    # Tree for when the target is not self
    if init_id != targ_id:
        # Tree for when the bot is not the target
        if targ_id != context.bot.id:
            # Get the player list
            participant_list = [
                (init_name, init_id,
                 _get_user_str(update, init_id), init_tag),
                (targ_name, targ_id,
                 _get_user_str(update, targ_id), targ_tag)
            ]
            # Get the winner and the loser. Check 1
            winners, losers = [], []
            for player in participant_list:
                individualwinreq = randomizer.uniform(0, THRESHOLDCAP)
                winners.append(player) if player[2] > individualwinreq \
                    else losers.append(player)
            # Get the winner and the loser. Check 2
            if len(winners) == 2:
                randomizer.shuffle(winners)
                losers.append(winners.pop())
            # Make the scenario tree
            scenario = 'onedead' if winners else 'nonedead'
            if scenario == 'onedead':
                _score_the_results(update, winners, losers,
                                   (1, 0, 0), (0, 1, 0))
            else:
                _score_the_results(update, winners, losers,
                                   (0, 0, 1), (0, 0, 1))
            # Get the result
            duel_result = _use_names(update, scenario, winners, losers)
            return _conclude_the_duel(update, context, duel_result, participant_list)
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
    update.message.reply_text(text=duel_result, parse_mode='Markdown')


@db_session
def _get_user_str(update: Update, userid: int) -> float:
    """Get strength if the user to assist in duels."""
    from main.constants import DUELDICT as DD
    user_score = User_Stats[Users[userid], Chats[update.message.chat.id]]
    strength = randomizer.uniform(DD['LOW_BASE_ACCURACY'], DD['HIGH_BASE_ACCURACY']) \
        + user_score.kills * DD['KILLMULT'] \
        + user_score.deaths * DD['DEATHMULT'] \
        + user_score.misses * DD['MISSMULT']
    return min(strength, DD['STRENGTHCAP'])


def _use_names(update: Update, scenario: str, winners: list = None,
               losers: list = None) -> str:
    """Insert names into the strings."""
    init_tag = f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"
    phrase = randomizer.choice(DUELS[scenario])
    if scenario == 'nonedead':
        return phrase.replace('loser1', losers[0][3]).replace('loser2', losers[1][3])
    if scenario == 'onedead':
        phrase = phrase.replace('winner', winners[0][3]).replace(
            'loser', losers[0][3])
        phrase += f'\nПобеда за {winners[0][3]}!'
        if winners[0][1] == update.effective_user.id:
            from main.constants import SHORTCD
            phrase += f'\nТвой кулдаун был ресетнут до {SHORTCD // 60}-х минут!'
        return phrase
    if scenario == 'suicide':
        return phrase.replace('loser', init_tag)
    if scenario == 'bot':
        return randomizer.choice(DUELS[scenario])


@run_async
@db_session
def _score_the_results(update: Update, winners: list, losers: list,
                       p1_kdm: tuple, p2_kdm: tuple) -> None:
    """Score the results in the database."""
    # One dead
    if winners:
        player_1, player_2 = winners[0], losers[0]
        # Remove cooldown from the winner if it was the initiator
        if update.effective_user.id == player_1[1]:
            # Reduce winner cooldown
            from main.constants import CDREDUCTION
            shortercd = datetime.now() - timedelta(seconds=CDREDUCTION)
            Cooldowns[Users[player_1[1]],
                      Chats[update.message.chat.id]].last_command = shortercd
    # None dead
    else:
        player_1, player_2 = losers[0], losers[1]
    counter = 0
    for player in (player_1, player_2):
        duelscore = p1_kdm if counter == 0 else p2_kdm
        userid, firstname = player[1], player[0]
        db_con = User_Stats[Users[userid], Chats[update.message.chat.id]]
        db_con.kills += duelscore[0]
        db_con.deaths += duelscore[1]
        db_con.misses += duelscore[2]
        counter += 1


@run_async
def _conclude_the_duel(update: Update, context: CallbackContext, result: str, participants) -> None:
    """Send all the messages for the duel."""
    from time import sleep
    # Send the initial message
    botmsg = update.message.reply_text('Дуэлисты расходятся...')
    # Get the sound of the duel
    sound = '***BANG BANG***' if randomizer.random() < 0.90 else '***ПИФ-ПАФ***'
    # Make the message loop
    for phrase in ('Готовятся к выстрелу...', sound, result):
        sleep(0.85)
        botmsg = context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            text=phrase,
            message_id=botmsg.message_id,
            parse_mode='Markdown'
        )
