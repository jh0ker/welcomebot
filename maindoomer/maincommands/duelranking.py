"""/duelranking command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import BOT
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@check_if_group_chat
def duelranking(update: Update, context: CallbackContext) -> None:
    """Get the top best duelists."""
    if update.effective_message.chat.type == 'private':
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Это только для групп.'
        )
        return
    # Check if the chat table exists
    if run_query('SELECT user_id FROM duels WHERE chat_id=(?)',
                 (update.effective_chat.id,)):
        _handle_ranking(update)
    else:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Для этого чата нет данных.'
        )


@run_async
@command_antispam_passed
def _handle_ranking(update: Update) -> None:
    ranking = headers = '***Убийства/Смерти/Непопадания\n***'
    for query in (('Лучшие:\n', 'DESC'), ('Худшие:\n', 'ASC')):
        # Create headers to see if there was data
        headers += query[0]
        # Start the table
        ranking += query[0]
        counter = 1
        # Add to the table the five best and five worst
        for Q in run_query(f'''SELECT winrate.firstname, doom.kills, doom.deaths, doom.misses, winrate.wr
            FROM "duels" AS doom JOIN
            (SELECT firstname, kills * 100.0/(kills+deaths) AS wr
                FROM "duels"
                    WHERE deaths!=0 AND kills!=0 AND chat_id=(?)) AS winrate
            ON doom.firstname=winrate.firstname WHERE chat_id=(?)
                ORDER BY wr {query[1]} LIMIT 5''', (update.effective_chat.id, update.effective_chat.id)):
            ranking += f'№{counter} {Q[0]}\t -\t {Q[1]}/{Q[2]}/{Q[3]}'
            ranking += f' ({round(Q[4], 2)}%)\n'
            counter += 1
    # If got no data, inform the user
    if ranking == headers:
        ranking = 'Пока что недостаточно данных. Продолжайте дуэлиться.'
    # Add a footer to the table
    else:
        ranking += 'Показываются только дуэлянты у которых есть убийства и смерти.'
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=ranking,
        parse_mode='Markdown'
    )
