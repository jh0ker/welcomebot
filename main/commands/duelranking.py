"""/duelranking command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from main.database import *
from main.helpers import ResetError, antispam_passed, check_if_group_chat


@run_async
@check_if_group_chat
@antispam_passed
@db_session
def duelranking(update: Update, context: CallbackContext):
    """Get the top best duelists."""

    # TODO - Improve the desc to User_Stats.kills*3 + User_Stats.deaths*2 + User_Stats.misses*1
    query = select(q for q in User_Stats
                   if q.chat_id == Chats[update.message.chat.id]
                   ).order_by(
        desc(User_Stats.kills))[:10]
    # Check if the chat table exists
    if not query:
        update.message.reply_text('Для этого чата нет данных.')
        raise ResetError

    reply = '\n'.join(
        [f'{c.user_id.full_name} - {c.kills}/{c.deaths}/{c.misses}' for c in query])
    update.message.reply_text(reply)
