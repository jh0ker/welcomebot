"""/duelscore command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from main.constants import DUELDICT as DD
from main.database import *
from main.helpers import ResetError, antispam_passed, check_if_group_chat


@run_async
@check_if_group_chat
@antispam_passed
@db_session
def duelscore(update: Update, context: CallbackContext):
    """Give the user his K/D for duels."""
    # Get userdata
    u_data = select((q.kills, q.deaths, q.misses) for q in User_Stats
                    if q.user_id == Users[update.message.from_user.id] and
                    q.chat_id == Chats[update.message.chat.id])[:]
    # Check if the data for the user exists
    if u_data:
        # If there is user data, get the score
        _handle_score(update, context, u_data)
    else:
        context.bot.send_message('Сначала подуэлься, потом спрашивай.')
        raise ResetError


@run_async
def _handle_score(update: Update, context: CallbackContext, userdata: tuple):
    userkda = userdata[0]
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
             f"промах.")
    update.message.reply_text(reply)
