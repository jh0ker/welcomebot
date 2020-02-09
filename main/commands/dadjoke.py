"""/dadjoke command."""

import requests
import telegram.error
from telegram import Update
from telegram.ext import CallbackContext, run_async

from main.constants import REQUEST_TIMEOUT
from main.helpers import antispam_passed


@run_async
@antispam_passed
def dadjoke(update: Update, context: CallbackContext):
    """Get a random dad joke.

    Raise errors to reset the command cooldown.
    telegram.error.BadRequest is handled by @antispam_passed to reset.
    """
    # Retrieve the json with the joke
    try:
        response = requests.get(
            url='https://icanhazdadjoke.com/',
            headers={'Accept': 'application/json'},
            timeout=REQUEST_TIMEOUT
        ).json()
    except:
        update.message.reply_text('Бот умер на пути к серверу. '
                                  'Попробуйте ещё раз.')
        # Reset cooldown
        raise telegram.error.BadRequest
    # Send the joke
    update.message.reply_text(response['joke'])
