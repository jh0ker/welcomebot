"""/flip command."""

import random

from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer.__init__ import BOT
from maindoomer.helpers import command_antispam_passed


@run_async
@command_antispam_passed
def flip(update: Update, context: CallbackContext) -> None:
    """Flip a coin."""
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=random.choice(['Орёл!', 'Решка!'])
    )
