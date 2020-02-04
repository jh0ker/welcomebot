"""/duelranking command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from constants import DUELDICT as DD
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@check_if_group_chat
def duelranking(update: Update, context: CallbackContext) -> None:
    """Get the top best duelists."""
    # Check if the chat table exists
    if run_query('SELECT user_id FROM duels WHERE chat_id=(?)',
                 (update.effective_chat.id,)):
        _handle_ranking(update)
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Для этого чата нет данных.'
        )


@run_async
@command_antispam_passed
def _handle_ranking(update: Update) -> None:
    header = '***Убийства/Смерти/Промахи/Модификатор силы***\n'
    ranking = ''
    # Get top 10 from the duel table
    chat_data = enumerate(run_query(f'''SELECT
        ptable.firstname, doom.kills, doom.deaths, doom.misses, ptable.points
            FROM "duels" AS doom JOIN
            (SELECT firstname, kills * 3 + deaths * 2 + misses * 1 AS points
                FROM "duels" WHERE chat_id=(?)) AS ptable
        ON doom.firstname=ptable.firstname WHERE chat_id=(?)
            ORDER BY points DESC LIMIT 10''', (update.effective_chat.id,
                                               update.effective_chat.id)
                                    )
                          )
    if chat_data == []:
        ranking = '\nПока что недостаточно данных. Продолжайте дуэлиться.'
    else:
        for Q in chat_data:
            wr_increase = Q[1][1] * DD['KILLMULTPERC'] + \
                Q[1][2] * DD['DEATHMULTPERC'] + \
                Q[1][3] * DD['MISSMULTPERC']
            wr_increase = min(round(wr_increase, 2), 45)
            ranking += (f'№{Q[0]+1} {Q[1][0]}\t -\t '
                        f'{Q[1][1]}/{Q[1][2]}/{Q[1][3]}/{wr_increase}%\n')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=header + ranking +
        'Показывается топ 10 по очкам.\n3/2/1 очко за убийство/смерть/промах.',
        parse_mode='Markdown'
    )
