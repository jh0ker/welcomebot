"""/flip command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import randomizer
from maindoomer.helpers import command_antispam_passed


@run_async
@command_antispam_passed
def flip(update: Update, context: CallbackContext) -> None:
    """Flip a coin."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=randomizer.choice(['Орёл!', 'Решка!'])
    )
