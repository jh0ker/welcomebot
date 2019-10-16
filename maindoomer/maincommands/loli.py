"""/loli command."""

import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, run_async

from constants import INDIVIDUAL_USER_DELAY, LOLI_BASE_URL
from maindoomer import BOT
from maindoomer.helpers import command_antispam_passed
from maindoomer.sqlcommands import run_query


@run_async
@command_antispam_passed
def loli(update: Update, context: CallbackContext) -> None:
    """Send photo of loli."""
    # Get the photo type Safe/Explicit
    lolitype = run_query(
        '''SELECT loliNSFW from "chattable" WHERE chat_id=(?)''',
        (update.effective_chat.id,)
        )[0][0]
    tags = 'child+highres+1girl+Rating%3ASafe' if lolitype == 0 else 'loli+highres+sex'
    BOT.send_chat_action(
        chat_id=update.effective_chat.id,
        action='upload_photo'
        )
    post_count = ET.fromstring(requests.get(
        LOLI_BASE_URL + tags).content).get('count')
    # Get the random offset
    offset = random.randint(0, int(post_count))
    # Get the random image in json
    url = LOLI_BASE_URL + tags + f'&json=1&pid={offset}'
    response = requests.get(url).json()[0]
    # Get the image link
    image_link = response['file_url']
    source = response.get('source')
    # Create a source button
    if source:
        keyboard = [[InlineKeyboardButton(text='Первоисточник', url=source)]]
        source_button = InlineKeyboardMarkup(keyboard)
        caption = None
    else:
        caption = 'Первоисточник не найден'
        source_button = None
    # Send the result
    try:
        BOT.send_photo(
            chat_id=update.effective_chat.id,
            photo=image_link,
            reply_markup=source_button,
            caption=caption,
            reply_to_message_id=update.effective_message.message_id
            )
    except BadRequest:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Думер умер на пути к серверу. Попробуйте ещё раз.'
            )
        # Reset cooldown if sending failed
        run_query(
            'UPDATE cooldowns SET lastcommandreply=(?) WHERE '
            'chat_id=(?) AND user_id=(?)',
            (datetime.now() - timedelta(minutes=INDIVIDUAL_USER_DELAY),
             update.effective_chat.id, update.effective_user.id)
            )
