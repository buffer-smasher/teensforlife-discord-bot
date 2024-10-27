#!/usr/bin/python

import os
import json
import sqlite3
import discord
import aiosqlite
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# TODO: Reminder to set reports channel
# TODO: Help command

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


intents = discord.Intents.all()
bot = commands.Bot(command_prefix=None, intents=intents)


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
        reportsChannel INTEGER,
        welcomeChannel INTEGER,
        minimumAge INTEGER DEFAULT 3
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
    cogs_list = ['authentication']
    for cog in cogs_list:
        await bot.load_extension(f'cogs.{cog}')

async def sync_commands():
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)


@bot.event
async def on_ready():
    await load_cogs()

    for guild in bot.guilds:
        await execute_query('INSERT OR IGNORE INTO guildConfigs(guildid) VALUES (?)', (guild.id,))

    await sync_commands()

    await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = 'you'))


    print('Logged in as {0.user}'.format(bot))

@bot.event
async def on_command_error(inter: discord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await inter.response.send_message("You don't have permission to use this command.")
    else:
        print(error)

################################################
### CURRENTLY NOT WORKING DUE TO SYNC ISSUES ###
################################################
# @bot.tree.command(name='help', description='Displays help text')
# async def custom_help(inter: discord.Interaction):
#     help_text = '## The following are all the available commands:\n'
#     await inter.response.send_message(help_text)

load_db()
bot.run(TOKEN)

