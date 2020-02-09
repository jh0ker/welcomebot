"""Module dedicated to commands available only to admins and the developer."""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from main.database import *
from main.helpers import ResetError, admin_priv, antispam_passed, check_if_group_chat


@run_async
@check_if_group_chat
def leave(update: Update, context: CallbackContext):
    """Make the bot leave the group, usable only by the admin/dev/creator."""
    if admin_priv(update, context):
        update.message.reply_text("Ну ладно, ухожу \U0001F61E")
        context.bot.leave_chat(update.message.chat.id)


@run_async
@antispam_passed
def adminmenu(update: Update, context: CallbackContext):
    """Send the admin menu commands."""
    if admin_priv(update, context):
        from thebot import ONLYADMINCOMMANDS
        reply = ONLYADMINCOMMANDS[0] + '\n'
        for command in ONLYADMINCOMMANDS[1:]:
            reply += f'/{command[0]} - {command[2]};\n'
        update.message.reply_text(reply)
    else:
        raise ResetError


@run_async
@check_if_group_chat
@antispam_passed
@db_session
def duelstatus(update: Update, context: CallbackContext):
    """Handle the on/off state of duels in the chat.

    1 for turned on, 0 for turned off.
    If no argument, get the current status.
    """
    # Check command validity
    if not admin_priv(update, context):
        raise ResetError
    reply = 'Ошибка. /adminmenu для справки.'
    if len(update.message.text.split()) < 3:
        try:
            arg = update.message.text.lower().split()[1]
        except IndexError:
            arg = None
    else:
        update.message.reply_text(reply)
        return

    # Work with database
    status = None
    if arg in ['on', 'off']:
        status = 1 if arg == 'on' else 0
        Options[Chats[update.message.chat.id]].duel_active = status
    elif arg is None:
        status = Options[Chats[update.message.chat.id]].duel_active
    # Generate reply
    if status == 1:
        reply = 'Дуэли включены для этого чата.'
    elif status == 0:
        reply = 'Дуэли выключены для этого чата.'
    update.message.reply_text(reply)


@run_async
@check_if_group_chat
@antispam_passed
@db_session
def immune(update: Update, context: CallbackContext,
           reverse: bool = False):
    """Add user to exceptions."""
    # Check command validity
    if not admin_priv(update, context):
        raise ResetError

    if update.message.reply_to_message is not None:
        tar = update.message.reply_to_message.from_user
        add = 0 if reverse else 1
        User_Stats[Users[tar.id],
                   Chats[update.message.chat.id]].exception = add
        if add:
            reply = f'Готово. {tar.full_name} теперь под иммунитетом от задержек!'
        else:
            reply = f'Готово. {tar.full_name} теперь не под иммунитетом от задержек!'
    else:
        reply = 'Не выбрана цель.'
    update.message.reply_text(reply)


@run_async
def unimmune(update: Update, context: CallbackContext):
    """Remove user from exceptions."""
    immune(update, context, reverse=True)


@run_async
@check_if_group_chat
@antispam_passed
@db_session
def immunelist(update: Update, context: CallbackContext):
    """Get the exceptions list."""
    # Check command validity
    if not admin_priv(update, context):
        raise ResetError

    query = select(q.user_id.full_name for q in User_Stats
                   if q.chat_id == Chats[update.message.chat.id]
                   and q.exception == 1)[:]
    if query:
        reply = '\n'.join([f'{u[0]}. {u[1]}' for u in enumerate(query, 1)])
    else:
        reply = 'Список пуст.'
    update.message.reply_text(reply)
