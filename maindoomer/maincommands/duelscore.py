"""/duelscore command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from constants import DUELDICT as DD
from maindoomer import BOT
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@check_if_group_chat
def duelscore(update: Update, context: CallbackContext) -> None:
    """Give the user his K/D for duels."""
    # Get userdata
    u_data = run_query(
        'SELECT kills, deaths, misses from duels WHERE user_id=(?) AND chat_id=(?)',
        (update.effective_user.id, update.effective_chat.id)
    )
    # Check if the data for the user exists
    if u_data:
        # If there is user data, get the score
        _handle_score(update, u_data)
    else:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Сначала подуэлься, потом спрашивай.'
        )


@run_async
@command_antispam_passed
def _handle_score(update: Update, userdata: tuple) -> None:
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
             f"мисс.")
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=reply
    )
