"""/dadjoke command."""

import requests
from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import BOT, LOGGER
from maindoomer.helpers import command_antispam_passed


@run_async
def dadjoke(update: Update, context: CallbackContext) -> None:
    """Get a random dad joke."""
    # Retrieve the json with, the joke
    try:
        from constants import REQUEST_TIMEOUT
        response = requests.get(
            url='https://icanhazdadjoke.com/',
            headers={'Accept': 'application/json'},
            timeout=REQUEST_TIMEOUT
        ).json()
        _handle_joke(update, response)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as err:
        LOGGER.error(err)
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Думер умер на пути к серверу. Попробуйте ещё раз.'
        )


@run_async
@command_antispam_passed
def _handle_joke(update: Update, response: dict) -> None:
    """Reply using this to account for the antispam decorator."""
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=response['joke']
    )
