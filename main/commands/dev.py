"""Module dedicated to commands available only to the dev."""

from datetime import date, datetime

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from main import LOGGER
from main.constants import DEVS, DATABASE_NAME


@run_async
def getlogs(update: Update, context: CallbackContext):
    """Get the bot logs."""
    if update.message.from_user.id not in DEVS:
        return
    try:
        # Get the filename
        filename = date.today().isoformat()
        # Send the file
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open('logs.log', 'rb'),
            filename=f'{filename}.log'
            )
    except (EOFError, FileNotFoundError) as changelog_err:
        LOGGER.error(changelog_err)
        update.message.reply_text('Не смог добраться до логов. Что-то не так.')
    finally:
        # Clean the file after sending/create a new one if failed to get it
        with open('logs.log', 'w') as logfile:
            logfile.write(
                f"{datetime.now().isoformat(sep=' ')} - Start of the log file.\n")


@run_async
def getdatabase(update: Update, context: CallbackContext):
    """Get the database as a document."""
    if update.message.from_user.id not in DEVS:
        return
    try:
        # Send the file
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(DATABASE_NAME, 'rb')
            )
    except (EOFError, FileNotFoundError) as database_err:
        LOGGER.error(database_err)
        update.message.reply_text('Не смог добраться до базы. Что-то не так.')


@run_async
def allcommands(update: Update, context: CallbackContext):
    """Send the list of all commands."""
    if update.message.from_user.id not in DEVS:
        return
    from thebot import USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS
    reply = ''
    for commandlists in (USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS):
        reply += f'<b>{commandlists[0]}:</b>\n'
        for commands in commandlists[1:]:
            reply += f'/{commands[0]} - {commands[2]};\n'
    update.message.reply_text(text=reply, parse_mode='HTML')
