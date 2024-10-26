#!/usr/bin/python

import os
import json
import aiosqlite
import sqlite3
import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

CONFIG_FILE = 'config.json'
configuration = {
    'min_age': 3,
    'reports_channel': 1272201018687361054
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='~', intents=intents)
bot.remove_command('help')


def load_config():
    global configuration
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as conf:
            configuration = json.load(conf)
    else:
        with open(CONFIG_FILE, 'w') as conf:
            json.dump(configuration, conf)


def load_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kickExceptions (
        userid INTEGER PRIMARY KEY
    )
    ''')

    conn.commit()
    conn.close()


async def query_kick_exception(id):
    conn = await aiosqlite.connect('users.db')
    cursor = await conn.cursor()
    await cursor.execute('SELECT userid FROM kickExceptions WHERE userid = ?', (id,))
    result = await cursor.fetchone()
    await conn.close()

    if result:
        return result[0]
    else:
        return None


@bot.event
async def on_ready():
    print('Logged in as {0.user}'.format(bot))
    await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = 'you'))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You don't have permission to use this command.")
    else:
        print(error)


@bot.event
async def on_member_join(member):
    report_channel = bot.get_channel(configuration['reports_channel'])
    minimum_age = timedelta(days=configuration['min_age'])
    restricted_words = {
        'gay': 0.5,
        'cp': 1,
        'sell': 1,
        'rape': 2,
        'incest': 2,
        'mega': 0.5,
        'link': 0.5,
        'legit': 0.5
    }

    # check if user is an exception
    is_allowed = await query_kick_exception(member.id)
    if is_allowed is not None:
        return

    # check username
    username = member.name
    username_score = 0
    for word in restricted_words.keys():
        if word in username:
            username_score += restricted_words[word]
    if username_score >= 2:
        await member.send('Your username contains words that are not allowed on our this server. You have been banned :frowning:')
        await member.ban(delete_message_days=1, reason='Username contains flagged words')
        await report_channel.send(f'Banned new user for flagged username: {member.mention}')
        return

    # check account creation date
    account_created = member.created_at
    now = datetime.now(timezone.utc)
    delta = now - account_created
    if delta <= minimum_age:
        timeout_until = minimum_age - delta
        await member.send(f'Your account does not meet the minimum creation date requirements; therefore, you have been timed out. Please check back later! :smile:')
        await member.timeout(timeout_until, reason="Account doesn't meet minimum creation date requirements")
        await report_channel.send(f'Timed out new user for account age: {member.mention}')
        return


@bot.command(help='Set minimum account age for new members. Counts in days from present time (arg1: integer<days>)')
@commands.has_permissions(kick_members=True)
async def set_min_creation_date(ctx, arg):
    global configuration
    try:
        configuration['min_age'] = int(arg)
        await ctx.reply(f'Minimum creation date set to: {int(arg)} days')
    except ValueError:
        await ctx.reply('Please use integer as argument')
        return

    with open(CONFIG_FILE, 'w') as conf:
        json.dump(configuration, conf)


@bot.command(help='Add exclusion to account auto-filter based on user ID (arg1: integer<ID>')
@commands.has_permissions(ban_members=True)
async def allow_user_age(ctx, arg):
    conn = await aiosqlite.connect('users.db')
    cursor = await conn.cursor()

    try:
        user_id = int(arg)
        username = await bot.fetch_user(user_id)
        await cursor.execute('SELECT userid FROM kickExceptions WHERE userid = ?', (user_id,))
        valid = await cursor.fetchone()
        if valid:
            await ctx.reply(f"User '{username}' already excluded")
            return
    except (ValueError, discord.NotFound, discord.HTTPException):
        await ctx.reply('Please pass valid user ID')
        return

    await cursor.execute('INSERT INTO kickExceptions (userid) VALUES (?)', (user_id,))
    await conn.commit()
    await conn.close()
    await ctx.reply(f"Successfully added user '{username}' to exception list")


@bot.command(help='Remove existing exclusion to account auto-filter based on user ID (arg1: integer<ID>')
@commands.has_permissions(ban_members=True)
async def deny_user_age(ctx, arg):
    conn = await aiosqlite.connect('users.db')
    cursor = await conn.cursor()

    try:
        user_id = int(arg)
        username = await bot.fetch_user(user_id)
        await cursor.execute('SELECT userid FROM kickExceptions WHERE userid = ?', (user_id,))
        valid = await cursor.fetchone()
        if not valid:
            await ctx.reply('User ID not in table, ignoring')
            return
    except (ValueError, discord.NotFound, discord.HTTPException):
        await ctx.reply('Please pass valid user ID')
        return

    await cursor.execute('DELETE FROM kickExceptions WHERE userid = ?', (user_id,))
    await conn.commit()
    await conn.close()

    await ctx.reply(f"Successfully removed user '{username}' from exception list")


@bot.command(name='help', help='Displays this text')
async def custom_help(ctx):
    help_text = '## The following are all the available commands: \n'
    command_list = [f"**{command.name}**: {command.help}" for command in bot.commands]
    help_text += '\n'.join(command_list)
    await ctx.reply(help_text)


@bot.command(help='Sets reports channel to #mentioned channel (arg1: string<#channel>')
async def set_reports_channel(ctx, channel: discord.TextChannel):
    global configuration
    channel_id = channel.id

    configuration['reports_channel'] = channel_id
    with open(CONFIG_FILE, 'w') as conf:
        json.dump(configuration, conf)

    await ctx.reply(f'Set reports channel to {channel.mention}')


load_config()
load_db()
bot.run(TOKEN)


