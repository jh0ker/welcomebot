"""/slap command."""

from telegram import Update, Message
from telegram.ext import CallbackContext, run_async

from commandPretexts.slaps import SLAPS
from main import randomizer
from main.helpers import check_if_group_chat, antispam_passed


@run_async
@antispam_passed
@check_if_group_chat
def slap(update: Update, context: CallbackContext) -> Message:
    """Slap with random item."""
    # Check if there was a target
    if update.message.reply_to_message is None:
        reply = ('Кого унижать то будем?\n'
                 'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
    else:
        # Get user tags as it is used in both cases
        init = update.message.from_user
        targ = update.message.reply_to_message.from_user
        # Replace premade text with user tags.
        reply = randomizer.choice(SLAPS).replace(
            'init', f"[{init.full_name}](tg://user?id={init.id})").replace(
                'target', f"[{targ.first_name}](tg://user?id={targ.id})")
    update.message.reply_text(text=reply, parse_mode='Markdown')
