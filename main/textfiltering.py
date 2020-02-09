"""Module dedicated to message handlers."""
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from main.helpers import record_data


@run_async
def welcomer(update: Update, context: CallbackContext):
    """Send the welcoming message to the newcoming member."""
    # Create a loop over a list in cast many users have been invited at once
    for new_member in update.message.new_chat_members:
        # This bot joined the chat
        if new_member.id == context.bot.id:
            reply = "Думер бот в чате. Для списка функций используйте /help."
        # Another user joined the chat
        else:
            if update.message.chat.title is not None:
                loc = update.message.chat.title
            else:
                loc = 'нашем чате'
            reply = f'Приветствуем вас в {loc}, {new_member.full_name}!\n'
            if update.message.chat.id in [-1001226124289, -1001445688548]:
                reply += 'По традициям группы, с вас фото своих ног.'
        update.message.reply_text(text=reply, parse_mode='Markdown')


@run_async
def farewell(update: Update, context: CallbackContext):
    """Send the goodbye message to the leaving member."""
    leftuser = update.message.left_chat_member
    # Not this bot was removed
    if leftuser.id != context.bot.id:
        # Other bot was removed
        if leftuser.is_bot:
            reply = f"{leftuser.first_name}'а убили, красиво, уважаю."
        # A user was removed
        else:
            reply = f'Сегодня нас покинул {leftuser.full_name}.'
        update.message.reply_text(text=reply, parse_mode='Markdown')


@run_async
def message_filter(update: Update, context: CallbackContext) -> None:
    """Store chat and user data."""
    record_data(update)
