"""Module dedicated to bot initiation variables that are usable in other modules."""
import logging
from os import environ

from telegram import Bot
from telegram.utils.request import Request

from maindoomer.sqlcommands import create_tables


__author__ = "Vlad Chitic"
__copyright__ = "Copyright 2019, Vlad Chitic"
__credits__ = ["Vlad Chitic"]
__license__ = "MIT License"
__version__ = "1.0 stable"
__maintainer__ = "Vlad Chitic"
__email__ = "feorache@protonmail.com"
__status__ = "Production"

# Setup logging
logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
LOGGER = logging.getLogger(__name__)

# Bot initialization
LOGGER.info('-----------------------------------------------')
LOGGER.info('Initializing the bot...')
BOT = Bot(
    token="824227677:AAG_KhaNi5KEPcBt6LCLW-cpgXSTUo1eiXE",
    request=Request(con_pool_size=20)
)

# Create tables in the database if they don't exist
LOGGER.info('Creating database tables if needed...')
create_tables()
LOGGER.info(
    'Creating memory instances of known users and '
    'chats to make less queries to the database...'
)
