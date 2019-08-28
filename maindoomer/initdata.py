"""
Module dedicated to bot initiation variables that are usable in other modules
"""
import logging

from telegram import Bot
from telegram.utils.request import Request

from maindoomer.sqlcommands import create_tables


# Setup logging
logging.basicConfig(filename='logs.log',
                    format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Bot initialization
LOGGER.info('-----------------------------------------------')
LOGGER.info('Initializing the bot...')
TOKEN = "824227677:AAG_KhaNi5KEPcBt6LCLW-cpgXSTUo1eiXE"
BOT = Bot(token=TOKEN, request=Request(con_pool_size=20))

# Create tables in the database if they don't exist
LOGGER.info('Creating database tables if needed...')
create_tables()
LOGGER.info('Creating memory instances of known users and chats to make less queries to the database...')
