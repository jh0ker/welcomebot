"""/pidorme command."""

from telegram import Update, Message
from telegram.ext import CallbackContext, run_async

from main.helpers import check_if_group_chat, antispam_passed
from main.database import *


@run_async
@antispam_passed
@check_if_group_chat
@db_session
def pidorme(update: Update, context: CallbackContext) -> Message:
    """Give the user the number of times he has been pidor of the day."""
    times_pidor = User_Stats[Users[update.message.from_user.id],
                             Chats[update.message.chat.id]].times_pidor
    reply = f'Вы были пидором дня *{times_pidor}* раз.'
    update.message.reply_text(text=reply, parse_mode='Markdown')
