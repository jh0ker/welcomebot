"""Module dedicated to bot initiation variables that are usable in other modules."""
import logging
from os import environ
import random

from telegram.ext import Updater
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

LOGGER.info('-----------------------------------------------')
LOGGER.info('Initializing the bot and creating database tables if needed...')

# Bot initialization
updater = Updater(token=environ.get("TG_BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

# Create tables in the database if they don't exist
create_tables()

# Create a randomizer
randomizer = random.SystemRandom()
