#!/usr/bin/python

import os
import json
import sqlite3
import discord
import aiosqlite
import asyncio
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# TODO: One command to set channels
# TODO: Think of more ideas

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='commandprefixessuck', intents=intents)


def load_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kickExceptions (
        userid INTEGER PRIMARY KEY
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guildConfigs (
        guildID INTEGER PRIMARY KEY,
        minimumAge INTEGER DEFAULT 3,
        reportsChannel INTEGER,
        welcomeChannel INTEGER,
        anonymousChannel INTEGER,
        quotesChannel INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anonymousChat (
        messageid INTEGER PRIMARY KEY,
        serverid INTEGER NOT NULL,
        channelid INTEGER NOT NULL,
        userid INTEGER NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()


async def execute_query(query, params=()):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(query, params) as cursor:
            await conn.commit()
            return await cursor.fetchall()

async def load_cogs():
    cogs_list = ['authentication', 'anonymous', 'quotes', 'setchannels', 'greeter']
    for cog in cogs_list:
        await bot.load_extension(f'cogs.{cog}')

async def sync_commands():
    await bot.tree.sync()


@bot.event
async def on_ready():
    for guild in bot.guilds:
        await execute_query('INSERT OR IGNORE INTO guildConfigs(guildid) VALUES (?)', (guild.id,))

    await sync_commands()

    await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = 'you'))


    print('Logged in as {0.user}'.format(bot))
    print('Version: 1.06')


@bot.event
async def on_command_error(inter: discord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await inter.response.send_message("You don't have permission to use this command.", ephemeral=True)
    else:
        print(error)


@bot.tree.command(name='help', description='Displays help text')
async def custom_help(inter: discord.Interaction):
    help_text = '## The following commands are available:'
    for command in bot.tree.get_commands():
        help_text += f'\n- **{command.name}**: {command.description}'
    await inter.response.send_message(help_text)

load_db()
asyncio.run(load_cogs())
bot.run(TOKEN)

