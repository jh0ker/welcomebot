"""/pidorstats command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import BOT
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@command_antispam_passed
@check_if_group_chat
def pidorstats(update: Update, context: CallbackContext) -> None:
    """Get the chat stats of how many times people have been pidors of the day."""
    chatstats = run_query(
        'SELECT firstname, timespidor FROM userdata '
        'WHERE chat_id=(?) ORDER BY timespidor DESC, firstname',
        (update.effective_chat.id,)
    )
    table = ''
    counter = 1
    # Get top 10
    for entry in chatstats:
        table += f'{counter}. {entry[0]} - *{entry[1]} раз(а)*\n'
        if counter == 10:
            break
        counter += 1
    # Get the number of players
    number_of_players = len(chatstats)
    if number_of_players != 0:
        table += f'\nВсего участников - *{number_of_players}*'
    if table == '':
        reply = 'Пидоров дня ещё не было!'
    else:
        reply = table
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=reply,
        parse_mode='Markdown'
    )
