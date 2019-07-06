import asyncio
import logging
import os
from collections import defaultdict
from time import time
from random import choice, sample
from itertools import compress
from inspect import iscoroutinefunction
from hashlib import md5, sha256

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import ContentType
from requests_async import get

from slaps import slaps

API_TOKEN = os.environ['TG_BOT_TOKEN']

logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        , level=logging.INFO
        )
logger = logging.getLogger(__name__)


bot = Bot(token=API_TOKEN, timeout=1000)
dp = Dispatcher(bot)

ANTISPAMMER_EXCEPTIONS = {
        255295801: "doitforricardo",
        413327053: "comradesanya",
        205762941: "dovaogedot",
        185500059: "melancholiak"
}

CHAT_DELAY = 1 * 60
ERROR_DELAY = 1 * 60
INDIVIDUAL_USER_DELAY = 10 * 60


async def is_spam(msg, spam_counter=defaultdict(int)):
    if msg.from_user.id in ANTISPAMMER_EXCEPTIONS:
        return False
    
    msg_time = time()
    error = None
    if msg_time - spam_counter[(msg.chat.id, 'msg')] >= CHAT_DELAY:
        spam_counter[(msg.chat.id, 'msg')] = msg_time
        return False
    elif (msg_time - spam_counter[(msg.chat.id, msg.from_user.id)]
            < INDIVIDUAL_USER_DELAY):
        error = ('Ответ индивидуальным пользователям на '
                 'команды минимум через каждые 10 минут.\n')
    else:
        error = ('Бот отвечает на команды пользователей '
                 'минимум через каждую 1 минуту.\n')

    if msg_time - spam_counter[(msg.chat.id, 'err')] >= ERROR_DELAY:
        spam_counter[(msg.chat.id, 'err')] = msg_time
        spam_counter[(msg.chat.id, 'cooldown')] = 0
        await msg.reply(error)
    else:
        if spam_counter[(msg.chat.id, 'cooldown')] != 0:
            await msg.delete()
        else:
            await msg.reply(f"{error}Эта ошибка тоже появляется минимум"
                             " каждую 1 минуту.\nЗапросы во время кулдауна"
                             "ошибки будут удаляться")
            spam_counter[(msg.chat.id, 'cooldown')] = 1
    return True


def antispam(f):
    async def _(msg):
        if not (await is_spam(msg)):
            await f(msg)
    return _


def handle(*args, **kwargs):
    if len(args) == 1 and iscoroutinefunction(args[0]):
        return dp.message_handler()(args[0])
    return dp.message_handler(*args, **kwargs)


@handle(commands=['help'])
@antispam
async def _(msg):
    help_text = ("Пример команды для бота: /help@random_welcome_bot\n"
                 "[ ] в самой команде не использовать.\n"
                 "/help - Это меню;\n"
                 "/cat - Случайное фото котика;\n"
                 "/dog - Случайное фото собачки;\n"
                 "/image [тематика] - Случайное фото. Можно задать"
                 " тематику на английском;\n"
                 "/dadjoke - Случайная шутка бати;\n"
                 "/slap [@имя пользователя] - Кого-то унизить;\n"
                 "\n"
                 "Генераторы чисел:\n"
                 "/myiq - Мой IQ (0 - 200);\n"
                 "/muhdick - Длина моего шланга (0 - 25);\n"
                 "/flip - Бросить монетку (Орёл или Решка);\n"
                 "\n"
                 "Дополнительная информация:\n"
                 "1. Бот здоровается с людьми, прибывшими в чат и"
                  " просит у них имя, фамилию, фото ног.\n"
                  f"2. Кулдаун бота на любые команды {CHAT_DELAY//60} "
                  "минут(а|ы).\n"
                  f"3. Кулдаун на каждую команду {INDIVIDUAL_USER_DELAY//60}"
                  " минут(ы|) для"
                  " индивидуального пользователя.\n"
                  "4. Ошибка о кулдауне даётся минимум через каждую"
                  f" {ERROR_DELAY//60} минут(у|ы).")
    await msg.reply(help_text)


@handle(content_types=ContentType.NEW_CHAT_MEMBERS)
async def _(msg):
    if msg.from_user.is_bot and msg.from_user.id != 705781870:
        await msg.reply('Уходи, нам больше ботов не надо.')
    elif msg.from_user.id == 705781870:
        await msg.reply('Думер бот в чате. Для помощи используйте /help.')
    else:
        await msg.reply(f"Приветствуем вас в Думерском Чате, "
                        "{msg.new_chat_members[0].first_name}!\n"
                        f"По традициям группы, с вас фото своих ног.\n")


@handle(content_types=ContentType.LEFT_CHAT_MEMBER)
async def _(msg):
    if msg.from_user.is_bot:
        await msg.reply(f"{msg.left_chat_member.first_name}'a убили, "
                        "красиво. Уважаю.")


@handle(commands=['roll'])
@antispam
async def _(msg):
    if msg.reply_to_message is None:
        await msg.reply(choice(['Да', 'Нет']))
    else:
        await msg.reply_to_message.reply(choice(['Да', 'Нет']))


for c, a, l in [('iq', md5, 200), ('dick', sha256, 25)]:
    calc_hash = lambda alg, id_: int(a(str(id_).encode()).hexdigest(), 16)
    @handle(commands=[c])
    @antispam
    async def _(msg):
        if msg.reply_to_message is None:
            await msg.reply(calc_hash(a, msg.from_user.id) % l)
        else:
            await msg.reply_to_message.reply(calc_hash(a, msg.from_user.id) % l)


@handle(commands=['dog'])
@antispam
async def _(msg):
    url = (await get('https://random.dog/woof.json')).json()['url']
    if url.find('mp4') > 0:
        await bot.send_video(msg.chat.id, url)
    elif url.find('gif') > 0:
        await bot.send_animation(msg.chat.id, url)
    else:
        await bot.send_photo(msg.chat.id, url)


@handle(commands=['cat'])
@antispam
async def _(msg):
    response = (await get('http://aws.random.cat/meow')).json()
    await msg.reply(response['file'])


@handle(lambda m: not m.is_command())
async def _(msg):
    text = msg.text
    variations_with_latin_letters = [
        'думер'
    ]
    mask = [text.find(w) >= 0 for w in variations_with_latin_letters] 
    if any(mask):
        for w in compress(variations_with_latin_letters, mask):
            text = text.replace(w, 'хуюмер')
        await msg.reply(text)


async def image_unsplash(msg):
    user_theme = ','.join(msg.get_args())
    response = await get(f'https://source.unsplash.com/500x700/?{user_theme}')
    await bot.send_photo(msg.chat.id
                         , response.url
                         , reply_to_message_id=msg.message_id)


async def image_pixbay(msg):
    user_theme = '+'.join(msg.get_args())
    response = (await get('https://pixabay.com/api/',
                          params={
                                'key': '12793256-08bafec09c832951d5d3366f1',
                                'q': user_theme,
                                "safesearch": "false",
                                "lang": "en"
                          })).json()
    if response['totalHits'] != 0:
        photo = choice(response['hits'])['largeImageURL']
        await bot.send_photo(msg.chat.id
                             , photo
                             , reply_to_message_id=msg.message_id)
    else:
        await msg.reply('Фото по запросу не найдено.')


@handle(commands=['pic'])
@antispam
async def _(msg):
    await choice([image_pixbay, image_unsplash])(msg)


@handle(commands=['dadjoke'])
@antispam
async def _(msg):
    headers = {'Accept': 'application/json'}
    response = (await get('https://icanhazdadjoke.com/'
                          , headers=headers)).json()
    await msg.reply(response['joke'])


@handle(commands=['slap'])
@antispam
async def _(msg, things=sample(slaps, len(slaps))):
    right = msg.from_user.mention
    if not things:
        things.extend(sample(slaps, len(slaps)))
    thing = things.pop(0)
    if msg.reply_to_message is None:
        left = 'Doomer'
        await msg.reply(f'{left} slaps {right} with {thing}')
    else:
        left = msg.reply_to_message.from_user.mention
        await msg.reply_to_message.reply(f'{right} slaps {left} with {thing}')


executor.start_polling(dp, skip_updates=True)
