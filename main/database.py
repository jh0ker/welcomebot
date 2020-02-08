from datetime import date
from datetime import datetime
from pony.orm import *
from main.constants import DATABASE_NAME


db = Database()


class Users(db.Entity):
    id = PrimaryKey(int)
    # The user’s first_name, followed by (if available) last_name
    full_name = Required(str)
    username = Optional(str)
    # If username is available, returns a t.me link of the user.
    link = Optional(str)
    pidors = Set('Pidors')
    duels = Set('User_Stats')
    cooldowns = Set('Cooldowns')


class Chats(db.Entity):
    id = PrimaryKey(int, size=64)
    title = Optional(str)
    # If the chat has a username, returns a t.me link of the chat.
    link = Optional(str)
    options = Optional('Options')
    cooldowns = Set('Cooldowns')
    pidors = Optional('Pidors')
    duels = Set('User_Stats')


class User_Stats(db.Entity):
    user_id = Required(Users)
    chat_id = Required(Chats)
    kills = Required(int, default=0)
    deaths = Required(int, default=0)
    misses = Required(int, default=0)
    times_pidor = Required(int, default=0)
    exception = Required(int, default=0)
    PrimaryKey(user_id, chat_id)


class Pidors(db.Entity):
    chat_id = PrimaryKey(Chats)
    user_id = Required(Users)
    day = Required(date)


class Options(db.Entity):
    chat_id = PrimaryKey(Chats)
    cooldown = Required(int, default=10)
    duel_active = Optional(int, default=1)


class Cooldowns(db.Entity):
    user_id = Required(Users)
    chat_id = Required(Chats)
    last_command = Required(datetime, default=lambda: datetime.now())
    error_sent = Required(int, default=0)
    PrimaryKey(user_id, chat_id)
