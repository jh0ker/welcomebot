"""/lolimode command."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, run_async

from maindoomer import BOT
from maindoomer.helpers import command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@command_antispam_passed
def lolimode(update: Update, context: CallbackContext) -> None:
    """Set SFW/NSFW for Loli content."""
    # Get current settings
    lolitype = run_query(
        '''SELECT loliNSFW from "chattable" WHERE chat_id=(?)''',
        (update.effective_chat.id,)
    )[0][0]
    currentstate = 'На данный момент контент '
    currentstate += '***SFW***.' if lolitype == 0 else '***NSFW***.'
    info = ('\nЭту настройку может менять только администратор или создатель чата.'
            '\nЗапросы от других пользователей пропускаются.')
    # Create settings buttons
    keyboard = [
        [
            InlineKeyboardButton('Без нюдсов (SFW)', callback_data='legal'),
            InlineKeyboardButton('С нюдсами (NSFW)', callback_data='illegal')
        ]
    ]
    loli_settings = InlineKeyboardMarkup(keyboard)
    # Send options
    BOT.send_message(
        chat_id=update.effective_chat.id,
        text=currentstate + info,
        reply_markup=loli_settings,
        reply_to_message_id=update.effective_message.message_id,
        parse_mode='Markdown'
    )
