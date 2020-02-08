"""Module dedicated to commands that are not the main purpose of the bot but usable by users."""
from telegram import Update, Message
from telegram.ext import CallbackContext, run_async

from main import LOGGER
from main.helpers import antispam_passed


@run_async
@antispam_passed
def start(update: Update, context: CallbackContext) -> Message:
    """Send out a start message."""
    reply = 'Думер бот в чате. Для списка функций используйте /help.\n'
    # Add explanation for groups for best experience
    reply += 'Для наилучшего экспириенса, дайте боту права на удаление сообщений.' \
        if update.effective_chat.type != 'private' else ''
    update.message.reply_text(reply)


@run_async
@antispam_passed
def whatsnew(update: Update, context: CallbackContext) -> Message:
    """Reply with all new goodies."""
    # Choose for how many days to get the changelog
    lastdayschanges = 3
    # Import the changelog
    try:
        with open('changelog.md', 'r', encoding='utf-8') as changelog:
            changes = changelog.read()
    except (EOFError, FileNotFoundError) as changelog_err:
        LOGGER.error(changelog_err)
        changes = 'Не смог добраться до изменений. Что-то не так.'
    # Get the last 2 day changes
    reply = ''
    for change in changes.split('\n\n')[:lastdayschanges]:
        reply += change + '\n\n'
    reply += 'Вся история изменений: https://bit.ly/DoomerChangelog'
    update.message.reply_text(text=reply, parse_mode='Markdown')


@run_async
@antispam_passed
def bothelp(update: Update, context: CallbackContext) -> Message:
    """Help message."""
    from thebot import USERCOMMANDS
    from main.constants import INDIVIDUAL_USER_DELAY
    help_text = f"<b>Пример команды для бота:</b> /help@{context.bot.username}\n"
    for commandinfo in USERCOMMANDS[1:]:
        help_text += f'/{commandinfo[0]} - {commandinfo[2]};\n'
    help_text += \
        ("<b>Дополнительная информация:</b>\n"
         "1. Бот здоровается с людьми, прибывшими в чат и просит у них имя, фамилию, фото ног.\n"
         f"2. Кулдаун на команды <b>{INDIVIDUAL_USER_DELAY // 60}</b> минут.\n"
         "Спам команд во время кд удаляется, если у бота есть на это права.\n")
    update.message.reply_text(text=help_text, parse_mode='HTML')
