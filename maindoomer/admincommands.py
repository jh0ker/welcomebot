"""Module dedicated to commands available only to admins and the developer."""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

from maindoomer import BOT, LOGGER
from maindoomer.helpers import check_if_group_chat, rights_check
from maindoomer.sqlcommands import run_query


@run_async
@rights_check
@check_if_group_chat
def leave(update: Update, context: CallbackContext):
    """Make the bot leave the group, usable only by the admin/dev/creator."""
    from telegram.error import BadRequest
    try:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text="Ну ладно, ухожу \U0001F61E"
        )
        BOT.leave_chat(chat_id=update.effective_chat.id)
    except BadRequest as leaveerror:
        LOGGER.info(leaveerror)
        BOT.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text='Я не могу уйти отсюда. Сам уйди.'
        )


@run_async
@rights_check
def adminmenu(update: Update, context: CallbackContext):
    """Send the admin menu commands."""
    from thebot import ONLYADMINCOMMANDS
    text = ONLYADMINCOMMANDS[0] + '\n'
    for command in ONLYADMINCOMMANDS[1:]:
        text += f'/{command[0]} - {command[2]};\n'
    BOT.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text=text
    )


@run_async
@check_if_group_chat
@rights_check
def duelstatus(update: Update, context: CallbackContext):
    """Make a global maximum duels per chat and be able to turn them on and off."""
    @run_async
    def _handle_limits():
        """Handle the global limits to duels of the chat."""
        nonlocal arg, update
        # Remove limits
        if arg == 'none':
            run_query(
                'UPDATE chattable set duelmaximum=NULL WHERE chat_id=(?)',
                (update.effective_chat.id,)
            )
            reply = 'Был убран лимит дуэлей.'
        # Get current status if no argument was given
        elif arg is None:
            status = run_query(
                'SELECT duelmaximum from chattable WHERE chat_id=(?)',
                (update.effective_chat.id,)
            )
            # If nothing, means no limit
            if not status:
                reply = 'Лимита на дуэли нет.'
            else:
                duelsused = run_query(
                    'SELECT duelcount from "chattable" WHERE chat_id=(?)',
                    (update.effective_chat.id,)
                )
                reply = f'Лимит дуэлей составляет {status[0][0]}. ' \
                        f'Уже использовано {duelsused[0][0]}.'
        # Set maximum
        else:
            try:
                arg = int(arg)
                run_query(
                    'UPDATE chattable SET duelmaximum=(?) WHERE chat_id=(?)',
                    (arg, update.effective_chat.id)
                )
                reply = f'Максимальное количество дуэлей за день стало {arg}.'
            except ValueError:
                reply = f'\"{arg}\" не подходит. Дайте число. /adminmenu для справки.'
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text=reply,
            reply_to_message_id=update.effective_message.message_id
        )

    @run_async
    def _handle_status():
        """Handle the on/off state of duels in the chat.

        1 for turned on, 0 for turned off.
        If no argument, get the current status.
        """
        nonlocal arg, update
        status = None
        reply = 'Чё?'
        if arg in ['on', 'off']:
            status = 1 if arg == 'on' else 0
            run_query(
                'UPDATE chattable SET duelstatusonoff=(?) WHERE chat_id=(?)',
                (status, update.effective_chat.id)
            )
        elif arg is None:
            # Get the current status
            status = run_query(
                'SELECT duelstatusonoff from chattable WHERE chat_id=(?)',
                (update.effective_chat.id,)
            )[0][0]
        else:
            reply = 'Всмысле? Ты обосрался. /adminmenu для справки.'
        if status == 1:
            reply = 'Дуэли включены для этого чата.'
        elif status == 0:
            reply = 'Дуэли выключены для этого чата.'
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text=reply,
            reply_to_message_id=update.effective_message.message_id
        )

    commands = ['/duellimit', '/duelstatus']
    # Check if used by admin, a valid command, and there an argument to handle
    if len(update.effective_message.text.split()) < 3:
        # Get the argument
        try:
            arg = update.effective_message.text.lower().split()[1]
        except IndexError:
            arg = None
        # Pass to handlers
        if commands[0] in update.effective_message.text.lower():
            _handle_limits()
        if commands[1] in update.effective_message.text.lower():
            _handle_status()
    else:
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text='Всмысле? Ты обосрался. /adminmenu для справки.',
            reply_to_message_id=update.effective_message.reply_to_message.message_id
        )


@run_async
@rights_check
@check_if_group_chat
def immune(update: Update, context: CallbackContext):
    """Add user to exceptions."""
    if update.effective_message.reply_to_message is not None:
        targetdata = update.effective_message.reply_to_message.from_user
        # Insert the target entry
        run_query(
            'INSERT OR IGNORE INTO exceptions (user_id, chat_id, firstname) '
            'VALUES (?, ?, ?)',
            (targetdata.id, update.effective_chat.id, targetdata.first_name)
        )
        # If the user has a username
        if targetdata.username:
            run_query(
                'UPDATE exceptions SET username=(?) '
                'WHERE chat_id=(?) AND user_id=(?)',
                (targetdata.username, update.effective_chat.id, targetdata.id)
            )
        reply = f'Готово. \"{targetdata.first_name}\" теперь под иммунитетом!'
    else:
        reply = 'Дай цель.'
    BOT.send_message(
        chat_id=update.effective_chat.id,
        text=reply,
        reply_to_message_id=update.effective_message.message_id
    )


@run_async
@rights_check
@check_if_group_chat
def unimmune(update: Update, context: CallbackContext):
    """Remove user from exceptions."""
    if update.effective_message.reply_to_message:
        targetdata = update.effective_message.reply_to_message.from_user
        run_query(
            'DELETE FROM exceptions WHERE user_id=(?) AND chat_id=(?)',
            (targetdata.id, update.effective_chat.id)
        )
        BOT.send_message(
            chat_id=update.effective_chat.id,
            text=f'Сделано. \"{targetdata.first_name}\" больше не под имуном',
            reply_to_message_id=update.effective_message.reply_to_message.message_id
        )
    else:
        if len(update.effective_message.text.split()) > 1:
            unimmune_target = ' '.join(
                update.effective_message.text.split()[1:])
            run_query(
                'DELETE FROM exceptions WHERE chat_id=(?) AND '
                '(username=(?) OR firstname=(?))',
                (update.effective_chat.id, unimmune_target, unimmune_target)
            )
        else:
            BOT.send_message(
                chat_id=update.effective_chat.id,
                text='Дай цель.',
                reply_to_message_id=update.effective_message.message_id
            )


@run_async
@rights_check
@check_if_group_chat
def immunelist(update: Update, context: CallbackContext):
    """Get the exceptions list."""
    chatdata = run_query(
        "SELECT firstname FROM exceptions WHERE chat_id=(?)",
        (update.effective_chat.id,)
    )
    if not chatdata:
        reply = 'Список пуст.'
    else:
        # Somewhat of a table
        reply = ''
        listnumber = 1
        for entry in chatdata:
            reply += f'{listnumber}. {entry[0]}\n'
            listnumber += 1
    BOT.send_message(
        chat_id=update.effective_chat.id,
        text=reply,
        reply_to_message_id=update.effective_message.message_id
    )
