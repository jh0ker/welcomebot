#!/usr/bin/env python3

import telegram
from flask import Flask, request
import pickledb

# Configuration
BOTNAME = 'examplebot'  # The name of the bot, without @
TOKEN = ''  # Security Token given from the @BotFather
BASE_URL = 'sub.example.com'  # Domain name of your server, without protocol. You may include a port, if you dont want to use 443.
HOST = '0.0.0.0'  # IP Address on which Flask should listen on
PORT = 5000  # Port on which Flask should listen on

# If Flask won't handle your SSL stuff, ignore this
CERT     = '/etc/pki/tls/certs/examplebot.pem'
CERT_KEY = '/etc/pki/tls/certs/examplebot.key'

# Internal
ABOTNAME = '@' + BOTNAME
CONTEXT = (CERT, CERT_KEY)

app = Flask(__name__)

global bot
bot = telegram.Bot(token=TOKEN)

global helptext
helptext  = 'Welcomes everyone that enters a group chat that this bot is a part of. You can set a custom welcome message with /message (use $username and $title as placeholders)'

# Create database object
global db
db = pickledb.load('bot.db', False)

# Welcome a user to the chat
def welcome(update):
    chat_id = update.message.chat.id
    
    # Pull the custom message for this chat from the database
    message = db.get(chat_id)
    
    # Use default message if there's no custom one set
    if message is None:
        message = 'Hello $username! Welcome to $title 😊'
    
    # Replace placeholders and send message
    text = message.replace('$username', update.message.new_chat_participant.first_name).replace('$title', update.message.chat.title)
    bot.sendMessage(chat_id=chat_id, text=text)
    
    return 'ok'
    
# Introduce the bot to a chat its been added to
def introduce(update):
    chat_id = update.message.chat.id
    
    text = 'Hello %s! I will now greet anyone who joins this chat with a nice message %s \nYou can set a custom welcome message with /message (use $username and $title as placeholders)' % (update.message.chat.title, telegram.emoji.Emoji.GRINNING_FACE_WITH_SMILING_EYES.decode('utf-8'))
    bot.sendMessage(chat_id=chat_id, text=text)
    
    return 'ok'
    
# Print help text
def help(update):
    chat_id = update.message.chat.id
    
    bot.sendMessage(chat_id=chat_id, text=helptext, parse_mode=telegram.ParseMode.MARKDOWN)
    
    return 'ok'
    
# Set custom message
def message(update):
    chat_id = update.message.chat.id
    
    # Split message into words and remove mentions of the bot
    text = list([word.replace(ABOTNAME, '') for word in filter(lambda word2: word2 != ABOTNAME, update.message.text.split())])
            
    # Only continue if there's a message
    if len(text) < 2:
        bot.sendMessage(chat_id=chat_id, text='You need to send a message, too! For example:\n/message Hello $username, welcome to $title!')
        return 'ok'
    
    # Join message back together
    message = ' '.join(text[1:])
    
    # Put message into database
    db.set(chat_id, message)
    
    bot.sendMessage(chat_id=chat_id, text='Got it!')
    
    return 'ok'

# The webhook for Telegram messages
@app.route('/webhook_tg', methods=['POST'])
def tg_webhook_handler():
    if request.method == "POST":
        
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))
        # Message is empty
        
        text = update.message.text
        
        # split command into list of words and remove mentions of botname
        text = list([word.replace(ABOTNAME, '') for word in filter(lambda word2: word2 != ABOTNAME, text.split())])
        
        if update.message.new_chat_participant is not None:
            # Bot was added to a group chat
            if update.message.new_chat_participant.username == BOTNAME:
                return introduce(update)
            # Another user joined the chat
            else:
                return welcome(update)
                
        # Text is empty
        elif len(text) is 0:
            return 'ok'
            
        # Run commands
        elif text[0] == '/help' or text[0] == '/start':
            return help(update)
        elif text[0] == '/message':
            return message(update)
            
    return 'ok'

# Go to https://BASE_URL/set_webhook with your browser to register the telegram webhook of your bot
# You may want to comment out this route after triggering it once
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://%s/webhook_tg' % BASE_URL)
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

# Confirm that the bot is running and accessible by going to https://BASE_URL/ with your browser
@app.route('/')
def index():
    return 'Welcomebot is running!'
    

# Start Flask with SSL handling
#app.run(host=HOST,port=PORT, ssl_context=CONTEXT, threaded=True, debug=False)

# Start Flask without SSL handling
app.run(host=HOST,port=PORT, threaded=True, debug=False)

