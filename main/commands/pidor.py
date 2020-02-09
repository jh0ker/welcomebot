"""/pidor command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from main import randomizer
from main.database import *
from main.helpers import antispam_passed, check_if_group_chat


@run_async
@antispam_passed
@check_if_group_chat
@db_session
def pidor(update: Update, context: CallbackContext):
    """Get the pidor of the day from all users stored for the chat."""
    chat_users = select(q.user_id for q in User_Stats
                        if q.chat_id == Chats[update.message.chat.id])[:]
    # If no chat data
    if not chat_users:
        update.message.reply_text('Нужно больше данных')
        return
    # Find a pidor that's still in the chat and delete those that are gone.
    while True:
        pidor = randomizer.choice(chat_users)
        pidor_data = update.message.chat.get_member(pidor.id)
        if pidor_data.status in ['restricted', 'left', 'kicked']:
            delete(u for u in User_Stats
                   if u.user_id == pidor
                   and u.chat_id == Chats[update.message.chat.id])
        else:
            break
    Users[pidor.id].full_name = pidor_data.user.full_name
    pidor = Users[pidor.id]
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
