"""/roll command."""

from telegram import Update
from telegram.ext import CallbackContext, run_async

from maindoomer import randomizer
from maindoomer.helpers import command_antispam_passed


@run_async
@command_antispam_passed
def roll(update: Update, context: CallbackContext) -> None:
    """Roll a number between 0 and the given or 100 if not given."""
    end_number = 100
    addition = f'***Диапазон 0-{end_number}, если не задано другое число.***'
    try:
        arg = update.effective_message.text.lower().split()[1]
        end_number = int(arg)
        addition = f'***Диапазон 0-{end_number}, если не задано другое число.***'
    except IndexError:
        pass
    except ValueError:
        addition = ('***Использую диапазон 0-100, потому что аргумент неправильный. '
                    'Используйте /help.***')
    finally:
        text = f'Ваше число - {randomizer.randint(0, end_number)}\n{addition}'
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.effective_message.message_id,
            text=text,
            parse_mode='Markdown'
        )
