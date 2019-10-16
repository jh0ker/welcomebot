"""/pidorme command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import BOT
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@command_antispam_passed
@check_if_group_chat
def pidorme(update: Update, context: CallbackContext) -> None:
    """Give the user the number of times he has been pidor of the day."""
    timespidor = run_query(
        'SELECT timespidor FROM userdata WHERE chat_id=(?) AND user_id=(?)''',
        (update.effective_chat.id, update.effective_user.id)
    )
    if timespidor:
        reply = f'Вы были пидором дня *{timespidor[0][0]} раз(а)*!'
    else:
        reply = 'Вы ещё не разу не были пидором дня!'
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=reply,
        parse_mode='Markdown'
    )
