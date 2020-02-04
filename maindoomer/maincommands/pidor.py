"""/pidor command."""

from datetime import date

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, run_async

from maindoomer import randomizer
from maindoomer.helpers import check_if_group_chat, command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@command_antispam_passed
@check_if_group_chat
def pidor(update: Update, context: CallbackContext) -> None:
    """Get the pidor of the day from all users stored for the chat."""
    # Check last pidor day
    # Use index to select first, no exception as chat data is created by antispam handler
    lastpidor = run_query(
        'SELECT lastpidorid, lastpidorday, lastpidorname FROM chattable '
        'WHERE chat_id=(?)', (update.effective_chat.id,)
    )
    if not lastpidor:
        todaypidor = _get_new_pidor(update, context, lastpidor).result()
    elif lastpidor[0][0] is None or \
        date.fromisoformat(lastpidor[0][1]) < date.today() or \
            context.bot.get_chat_member(
                chat_id=update.effective_chat.id,
                user_id=lastpidor[0][0]
    ).status in ['left', 'restricted', 'kicked']:
        todaypidor = _get_new_pidor(update, context, lastpidor).result()
    else:
        todaypidor = lastpidor[0][2]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Пидором дня является {todaypidor}!',
        reply_to_message_id=update.effective_message.message_id,
        parse_mode='Markdown'
    )


@run_async
def _get_new_pidor(update: Update, context: CallbackContext, lastpidor: list) -> str:
    while True:
        allchatusers = run_query(
            'SELECT user_id FROM userdata WHERE chat_id=(?)',
            (update.effective_chat.id,)
        )
        if not allchatusers:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Попробуйте ещё раз! (недостаточно данных по чату)',
                reply_to_message_id=update.effective_message.message_id
            )
            return
        todaypidorid = randomizer.choice(allchatusers)[0]
        # Remove repetition
        if lastpidor:
            if len(allchatusers) > 1 and todaypidorid == lastpidor[0][0]:
                continue
        try:
            newpidor = context.bot.get_chat_member(
                chat_id=update.effective_chat.id,
                user_id=todaypidorid
            )
            if newpidor.status in ['left', 'restricted', 'kicked']:
                run_query(
                    'DELETE FROM userdata WHERE chat_id=(?) AND user_id=(?)',
                    (update.effective_chat.id, todaypidorid)
                )
                continue
            newpidorname = newpidor.user.first_name
            break
        except BadRequest:
            run_query(
                'DELETE FROM userdata WHERE chat_id=(?) AND user_id=(?)',
                (update.effective_chat.id, todaypidorid)
            )
    run_query(
        'UPDATE chattable SET lastpidorday=(?), lastpidorid=(?), lastpidorname=(?) '
        'WHERE chat_id=(?)',
        (date.today().isoformat(), todaypidorid,
         newpidorname, update.effective_chat.id)
    )
    run_query(
        'UPDATE userdata SET timespidor=timespidor+1, firstname=(?) '
        'WHERE chat_id=(?) AND user_id=(?)',
        (newpidorname, update.effective_chat.id, todaypidorid)
    )
    return f"[{newpidorname.strip('[]')}](tg://user?id={todaypidorid})"
