"""/cat and /dog command."""

import requests
from telegram import Update
from telegram.ext import CallbackContext, run_async

from constants import REQUEST_TIMEOUT
from maindoomer import BOT, LOGGER
from maindoomer.helpers import command_antispam_passed


@run_async
@command_antispam_passed
def animal(update: Update, context: CallbackContext) -> None:
    """Get photo/video/gif of dog or cat."""
    # Cat link
    if '/cat' in update.effective_message.text.lower():
        link = 'http://aws.random.cat/meow'
    # Dog link
    else:
        link = 'https://random.dog/woof.json'
    try:
        BOT.send_chat_action(
            chat_id=update.effective_chat.id,
            action='upload_photo'
        )
        response = requests.get(
            url=link,
            timeout=REQUEST_TIMEOUT
        ).json()
        _handle_format_and_reply(update, response)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        LOGGER.error(err)
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text='Думер умер на пути к серверу. Попробуйте ещё раз.',
            reply_to_message_id=update.effective_message.message_id
        )


@run_async
def _handle_format_and_reply(update: Update, response: dict) -> None:
    """Handle the format of the file and reply accordingly."""
    # Send uploading state
    file_link = list(response.values())[0]
    file_extension = file_link.split('.')[-1]
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
