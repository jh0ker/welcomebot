"""/slap command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from commandPretexts.slaps import SLAPS
from maindoomer import BOT, randomizer
from maindoomer.helpers import check_if_group_chat, command_antispam_passed


@run_async
@command_antispam_passed
@check_if_group_chat
def slap(update: Update, context: CallbackContext) -> None:
    """Slap with random item."""
    # Check if there was a target
    if update.effective_message.reply_to_message is None:
        reply = ('Кого унижать то будем?\n'
                 'Чтобы унизить, надо чтобы вы ответили вашей жертве.')
    else:
        # Get success and fail chances
        success_and_fail = ['failure'] * len(SLAPS['failure']) + \
                           ['success'] * len(SLAPS['success'])
        # Get user tags as it is used in both cases
        init_tag = f"[{update.effective_user.first_name}](tg://user?id={update.effective_user.id})"
        tdata = update.effective_message.reply_to_message.from_user
        target_tag = f"[{tdata.first_name}](tg://user?id={tdata.id})"
        # Different depending on the scenario
        scenario = success_and_fail.pop()
        action = randomizer.choice(SLAPS[scenario])
        # Replace premade text with user tags.
        reply = action.replace('init', init_tag).replace('target', target_tag)
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=reply,
        parse_mode='Markdown'
    )
