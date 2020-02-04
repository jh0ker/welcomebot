"""/dadjoke command."""

import requests
import telegram.error
from telegram import Update
from telegram.ext import CallbackContext, run_async

from constants import REQUEST_TIMEOUT
from maindoomer import LOGGER
from maindoomer.helpers import command_antispam_passed, reset_command_cooldown


@run_async
@command_antispam_passed
def dadjoke(update: Update, context: CallbackContext) -> None:
    """Get a random dad joke.

    Raise errors to reset the command cooldown.
    telegram.error.BadRequest is handled by @command_antispam_passed to reset.
    """
    # Retrieve the json with the joke
    try:
        response = requests.get(
            url='https://icanhazdadjoke.com/',
            headers={'Accept': 'application/json'},
            timeout=REQUEST_TIMEOUT
        ).json()
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Думер умер на пути к серверу. Попробуйте ещё раз.'
        )
        # Reset cooldown
        raise
    # Try to send the joke
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=response['joke']
    )
