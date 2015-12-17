# Welcome Bot
#### A Python Telegram Bot that greets everyone who joins a group chat

It uses the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library and [pickledb](https://bitbucket.org/patx/pickledb) for basic persistence.

Please also check out my other bots, [TexBot](https://github.com/jh0ker/texbot) and [GitBot](https://github.com/jh0ker/gitbot).

The file is prepared to be run by anyone by filling out the blanks in the configuration. The bot currently runs on [@jh0ker_welcomebot](https://telegram.me/jh0ker_welcomebot)

## Required
* Python 3.4 (may work with earlier versions, untested)
* [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot) module (tested with version 3.1.0)

## How to use
* Clone the repo
* Edit `BOTNAME` and `TOKEN` in `bot.py`
* If you want to use webhooks, fill out `BASE_URL`, `HOST` and `PORT` as well
* If you also want to handle SSL with python-telegram-bot, fill out the `CERT` and `CERT_KEY` fields and check the section about SSL.
* Follow Bot instructions

## SSL
You can start the server without an SSL context, if this is handled by another programm, like Apache or haproxy. You can leave out the SSL Information in the header and choose to run with polling in `main`. 

Please note that you need a valid ssl certificate or a self-signed one. Please refer to [this gist](https://gist.github.com/leandrotoledo/4e9362acdc5db33ae16c) for an example with self-signed certs.
