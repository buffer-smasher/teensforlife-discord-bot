# Teens For Life Discord Bot
---
The following are instruction on how to run this using your own bot

### Features
- Ban new users based on flagged words in name
- Timeout new users based on account creation date
- Anonymous chatting
- Daily quotes
- Greetings
- Rock pets
- Collaborative Spotify playlist

### Installation
Prerequisites:
- Docker or Python
- Git

First, clone this repository 
`git clone https://github.com/TeensForLife/discord-bot`

Then you will need to create a file named `.env` containing the following, replacing 'token' with your actual token:
`BOT_TOKEN=token`

### Usage
There are two ways to use this bot:
1. Run using python in terminal
2. Run as a Docker container

Python:
This method requires that the terminal window remain open for the bot to continue working.
You simply need to `cd` into the `discord-bot` directory and run `python bot.py`

Docker:
This method allows the program to run in the background, containerised from the rest of your system.

`cd discord-bot`
`docker build -t tfl-discord-bot`
`docker compose up -d`

The container should now be running disconnected from your terminal window

---
### Contact Me
If for whatever reason I am unable to maintain the existing bot and you wish to use the token you can contact me at:

Discord: illiterate.elephant

Email: githubalt.cake077@silomails.com 
