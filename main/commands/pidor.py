"""/pidor command."""

from datetime import date

from telegram import Update, Message
from telegram.error import BadRequest
from telegram.ext import CallbackContext, run_async

from main import randomizer
from main.helpers import check_if_group_chat, antispam_passed
from main.database import *
import time


@run_async
@antispam_passed
@check_if_group_chat
@db_session
def pidor(update: Update, context: CallbackContext) -> Message:
    """Get the pidor of the day from all users stored for the chat."""
    start = time.time()
    chat_users = select(q.user_id for q in User_Stats
                        if q.chat_id == Chats[update.message.chat.id])[:]
    # If no chat data
    if not chat_users:
        update.message.reply_text('Нужно больше данных')
        return
    # Find a pidor that's still in the chat and delete those that are gone.
    while chat_users:
        pidor = randomizer.choice(chat_users)
        pidor_status = update.message.chat.get_member(pidor.id).status
        if pidor_status in ['restricted, left, kicked']:
            delete(u for u in User_Stats if u.user_id == Users[pidor.id])
        else:
            break
    # Assign a tag if he's new
    name = f'[{pidor.full_name}](tg://user?id={pidor.id})'
    if not Pidors.exists(chat_id=Chats[update.message.chat.id]):
        Pidors(chat_id=Chats[update.message.chat.id],
               user_id=pidor,
               day=date.today())
        User_Stats[Users[pidor.id],
                   Chats[update.message.chat.id]].times_pidor += 1
    else:
        if Pidors[Chats[update.message.chat.id]].day == date.today():
            pidor = Pidors[Chats[update.message.chat.id]].user_id
            name = pidor.full_name
        elif Pidors[Chats[update.message.chat.id]].day < date.today():
            Pidors[Chats[update.message.chat.id]].user_id = pidor
            Pidors[Chats[update.message.chat.id]].day = date.today()
            User_Stats[Users[pidor.id],
                       Chats[update.message.chat.id]].times_pidor += 1
    reply = f'Пидором дня является {name}!'
    update.message.reply_text(text=reply, parse_mode='Markdown')
    print(time.time() - start)
