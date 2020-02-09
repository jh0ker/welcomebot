"""/pidorme command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from main.database import *
from main.helpers import antispam_passed, check_if_group_chat


@run_async
@antispam_passed
@check_if_group_chat
@db_session
def pidorme(update: Update, context: CallbackContext):
    """Give the user the number of times he has been pidor of the day."""
    times_pidor = User_Stats[Users[update.message.from_user.id],
                             Chats[update.message.chat.id]].times_pidor
    reply = f'Вы были пидором дня *{times_pidor}* раз.'
    update.message.reply_text(text=reply, parse_mode='Markdown')
