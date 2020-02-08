"""/pidorstats command."""

from telegram import Update, Message
from telegram.ext import CallbackContext, run_async

from main.helpers import check_if_group_chat, antispam_passed
from main.database import *


@run_async
@antispam_passed
@check_if_group_chat
@db_session
def pidorstats(update: Update, context: CallbackContext) -> Message:
    """Get the chat stats of how many times people have been pidors of the day."""
    query = select(q for q in User_Stats
                   if q.chat_id == Chats[update.message.chat.id]
                   ).order_by(desc(User_Stats.times_pidor))[:10]
    reply = '\n'.join(
        [f'{u.user_id.full_name} - {u.times_pidor} раз(а)' for u in query])
    update.message.reply_text(text=reply, parse_mode='Markdown')
