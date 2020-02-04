"""Module dedicated to commands that are not the main purpose of the bot but usable by users."""
from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import LOGGER
from maindoomer.helpers import command_antispam_passed


@run_async
@command_antispam_passed
def start(update: Update, context: CallbackContext):
    """Send out a start message."""
    text = 'Думер бот в чате. Для списка функций используйте /help.\n'
    # Add explanation for groups for best experience
    text += 'Для наилучшего экспириенса, дайте боту права на удаление сообщений.' \
        if update.effective_chat.type != 'private' else ''
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=text
    )


@run_async
@command_antispam_passed
def whatsnew(update: Update, context: CallbackContext):
    """Reply with all new goodies."""
    # Choose for how many days to get the changelog
    lastdayschanges = 2
    # Import the changelog
    try:
        with open('changelog.md', 'r', encoding='utf-8') as changelog:
            changes = changelog.read()
    except (EOFError, FileNotFoundError) as changelog_err:
        LOGGER.error(changelog_err)
        changes = 'Не смог добраться до изменений. Что-то не так.'
    # Get the last 2 day changes
    latest_changes = ''
    for change in changes.split('\n\n')[:lastdayschanges]:
        latest_changes += change + '\n\n'
    latest_changes += 'Вся история изменений: https://bit.ly/DoomerChangelog'
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=latest_changes,
        parse_mode='Markdown'
    )


@run_async
@command_antispam_passed
def bothelp(update: Update, context: CallbackContext):
    """Help message."""
    from thebot import USERCOMMANDS
    from constants import INDIVIDUAL_USER_DELAY
    help_text = f"<b>Пример команды для бота:</b> /help@{context.bot.username}\n"
    for commandinfo in USERCOMMANDS[1:]:
        help_text += f'/{commandinfo[0]} - {commandinfo[2]};\n'
    help_text += \
        ("<b>Дополнительная информация:</b>\n"
         "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
         f"2. Кулдаун на команды <b>{INDIVIDUAL_USER_DELAY // 60}</b> минут.\n"
         "Спам команд во время кд удаляется, если у бота есть на это права.\n")
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=help_text,
        parse_mode='HTML'
    )
