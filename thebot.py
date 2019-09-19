"""
Telegram bot with various commands. Listed below.
"""
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)

from maindoomer import (admincommands, devcommands, maincommands,
                        occasionalcommands, textfiltering)
from maindoomer.__init__ import BOT, LOGGER
from maindoomer.helpers import callbackhandler, error_callback, ping


# Bot commands
USERCOMMANDS = [
    'Команды для рядовых пользователей',
    ("slap", maincommands.slap,
     'Кого-то унизить (надо ответить жертве, чтобы бот понял кого бить)'),
    ('duel', maincommands.duel, 'Устроить дуэль (надо ответить тому, с кем будет дуэль)'),
    ('myscore', maincommands.myscore, 'Мой счёт в дуэлях'),
    ('duelranking', maincommands.duelranking,
     'Ранкинг дуэлей чата (показывает только тех, у кого есть убийства и смерти)'),
    ('pidor', maincommands.pidor,
     'Пидор дня (новый пидор каждый день по немецкому времени)'),
    ('pidorme', maincommands.pidorme, 'Сколько раз вы были пидором дня'),
    ('pidorstats', maincommands.pidorstats, 'Статы чата по пидорам дня'),
    ("loli", maincommands.loli, 'Лоли фото (SFW/NSFW)'),
    ('lolimode', maincommands.lolimode, 'Настройка лоли на SFW или NSFW'),
    ("flip", maincommands.flip, 'Бросить монетку (Орёл/Решка)'),
    ("dadjoke", maincommands.dadjoke, 'Случайная шутка бати'),
    ("dog", maincommands.animal, 'Случайное фото собачки'),
    ("cat", maincommands.animal, 'Случайное фото котика'),
    ("help", occasionalcommands.bothelp, 'Меню помощи'),
    ('whatsnew', occasionalcommands.whatsnew, 'Новое в боте'),
    ('adminmenu', admincommands.adminmenu, 'Админское меню'),
    ]
ONLYADMINCOMMANDS = [
    'Команды для администраторов групп',
    ('leave', admincommands.leave, 'Сказать боту уйти'),
    ('duellimit', admincommands.duelstatus,
     'Изменить глобальный лимит на дуэли за день (число или убрать через None)'),
    ('duelstatus', admincommands.duelstatus, 'Включить/Выключить дуэли (on/off)'),
    ('immune', admincommands.immune,
     'Добавить пользователю иммунитет на задержку команд (ответить ему)'),
    ('unimmune', admincommands.unimmune, 'Снять иммунитет (ответить или имя)'),
    ('immunelist', admincommands.immunelist, 'Лист людей с иммунитетом')
    ]
UNUSUALCOMMANDS = [
    'Нечастые команды',
    ('allcommands', devcommands.allcommands, 'Все команды бота'),
    ('start', occasionalcommands.start, 'Начальное сообщение бота'),
    ('getlogs', devcommands.getlogs,
     'Получить логи бота (только для разработчика)'),
    ('getdatabase', devcommands.getdatabase, 'Получить датабазу'),
    ('sql', devcommands.sql, 'Использовать sqlite команду на дб')
    ]


def main():
    """The main function"""
    LOGGER.info('Creating the dispatcher...')
    # Create the updater
    updater = Updater(bot=BOT, use_context=True, workers=16)
    # Create dispatcher
    dispatcher = updater.dispatcher
    LOGGER.info('Adding handlers...')
    # Add command handles
    for commandlists in (USERCOMMANDS, ONLYADMINCOMMANDS, UNUSUALCOMMANDS):
        for command in commandlists[1:]:
            dispatcher.add_handler(CommandHandler(command[0], command[1]))
    # Add message handlers
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.new_chat_members, textfiltering.welcomer))
    dispatcher.add_handler(MessageHandler(
        Filters.status_update.left_chat_member, textfiltering.farewell))
    dispatcher.add_handler(MessageHandler(
        Filters.all, textfiltering.message_filter))
    # Add callback handler
    dispatcher.add_handler(CallbackQueryHandler(callbackhandler))
    # Log errors
    dispatcher.add_error_handler(error_callback)
    # Add job queue
    job_queue = updater.job_queue
    job_queue.run_repeating(callback=ping, interval=10 * 60, first=0, name='ping')
    # Start polling
    updater.start_polling(clean=True)
    LOGGER.info('Polling started.')
    LOGGER.info('-----------------------------------------------')
    updater.idle()


if __name__ == '__main__':
    main()
