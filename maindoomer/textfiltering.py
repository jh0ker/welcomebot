"""
Module dedicated to message handlers.
"""
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from maindoomer.__init__ import BOT, LOGGER
from maindoomer.helpers import store_data


@run_async
def welcomer(update: Update, context: CallbackContext):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member.
    """
    from time import sleep
    from telegram.error import BadRequest
    # Create a loop over a list in cast many users have been invited at once
    for new_member in update.effective_message.new_chat_members:
        tagged_user = \
            f"[{new_member.first_name.strip('[]')}](tg://user?id={new_member.id})"
        # A BOT entered the chat, and not this BOT
        if new_member.is_bot and new_member.id != BOT.id:
            reply_text = f"Уходи, {tagged_user}, нам больше ботов не надо."
        # This BOT joined the chat
        elif new_member.id == BOT.id:
            reply_text = "Думер бот в чате. Для списка функций используйте /help."
        # Another user joined the chat
        else:
            if update.effective_chat.id in [-1001226124289, -1001445688548]:
                reply_text = (f"Приветствуем вас в Думерском Чате, {tagged_user}!\n"
                              f"По традициям группы, с вас фото своих ног.\n")
            else:
                try:
                    chattitle = BOT.get_chat(chat_id=update.effective_message.chat_id).title
                    reply_text = f'Приветствуем вас в {chattitle}, {tagged_user}!\n'
                except:
                    reply_text = 'Приветствуем вас в нашем чате, tagged_user}!\n'
        botmsg = BOT.send_message(chat_id=update.effective_chat.id,
                                  reply_to_message_id=update.effective_message.message_id,
                                  text=reply_text,
                                  parse_mode='Markdown')
        # Sleep and check if user is still there or voicy kicked it
        sleep(70)
        if BOT.get_chat_member(chat_id=update.effective_message.chat_id,
                               user_id=new_member.id).status in ['restricted', 'left', 'kicked']:
            # Delete the bot welcome message
            BOT.delete_message(chat_id=botmsg.chat_id,
                               message_id=botmsg.message_id)
            # Delete the join notification unless no rights or it was deleted
            try:
                BOT.delete_message(chat_id=update.effective_message.chat_id,
                                   message_id=update.effective_message.message_id)
            except BadRequest:
                pass


@run_async
def farewell(update: Update, context: CallbackContext):
    """Goodbye message"""
    leftuser = update.effective_message.left_chat_member
    # Not this bot was removed
    if leftuser.id != BOT.id:
        # Other bot was removed
        if leftuser.is_bot and leftuser.id != BOT.id:
            reply = f"{leftuser.first_name}'а убили, красиво, уважаю."
        # A user was removed
        else:
            leftusertag = f"[{leftuser.first_name.strip('[]')}](tg://user?id={leftuser.id})"
            reply = f'Сегодня нас покинул {leftusertag}.'
        BOT.send_message(chat_id=update.effective_chat.id,
                         reply_to_message_id=update.effective_message.message_id,
                         text=reply,
                         parse_mode='Markdown')


@run_async
def message_filter(update: Update, context: CallbackContext):
    """Adds messages to logs, stores chat and user data"""
    # Log messages
    LOGGER.info(f'{update.effective_user.first_name}[{update.effective_user.id}] - '
                f'{update.effective_chat.title} - {update.effective_message.text}')
    # Store chat and user data
    store_data(update)
