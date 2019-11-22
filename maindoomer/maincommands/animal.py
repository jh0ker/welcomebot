"""/cat and /dog command."""

import requests
import telegram.error
from telegram import Update
from telegram.ext import CallbackContext, run_async

from constants import REQUEST_TIMEOUT
from maindoomer import BOT, LOGGER
from maindoomer.helpers import command_antispam_passed, reset_command_cooldown


@run_async
@command_antispam_passed
def animal(update: Update, context: CallbackContext) -> None:
    """Get photo/video/gif of dog or cat.

    Raise errors to reset the command cooldown.
    telegram.error.BadRequest is handled by @command_antispam_passed to reset.
    """
    # Cat link
    if '/cat' in update.effective_message.text.lower():
        link = 'http://aws.random.cat/meow'
    # Dog link
    else:
        link = 'https://random.dog/woof.json'
    # Try to get the image/gif, check for connection to the server
    try:
        response = requests.get(
            url=link,
            timeout=REQUEST_TIMEOUT
        ).json()
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text='Думер умер на пути к серверу. Попробуйте ещё раз.',
            reply_to_message_id=update.effective_message.message_id
        )
        # Reset cooldown
        raise
    # Try to send chat action, check if the bot has the right to send messages
    BOT.send_chat_action(
        chat_id=update.effective_chat.id,
        action='upload_photo'
    )
    file_link = [item for item in response.values() if 'http' in str(item)][0]
    file_extension = file_link.split('.')[-1]
    # Try to send it to the chat
    try:
        if 'mp4' in file_extension:
            BOT.send_video(
                chat_id=update.effective_chat.id,
                video=file_link,
                reply_to_message_id=update.effective_message.message_id
            )
        elif 'gif' in file_extension:
            BOT.send_animation(
                chat_id=update.effective_chat.id,
                animation=file_link,
                reply_to_message_id=update.effective_message.message_id
            )
        else:
            BOT.send_photo(
                chat_id=update.effective_chat.id,
                photo=file_link,
                reply_to_message_id=update.effective_message.message_id
            )
    except telegram.error.BadRequest:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text=('Недостаточно прав для отправки медиа файлов, вопросы к админу.\n'
                  'Нужно право на отправку медиа файлов и GIF файлов.'),
            reply_to_message_id=update.effective_message.message_id
        )
        # Reset cooldown
        raise
