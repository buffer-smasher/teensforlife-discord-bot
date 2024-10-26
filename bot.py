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
    CREATE TABLE IF NOT EXISTS ageRequirements (
        userid INTEGER PRIMARY KEY
    )
    ''')

    conn.commit()
    conn.close()


async def query_age_requirements(id):
    conn = await aiosqlite.connect('users.db')
    cursor = await conn.cursor()
    await cursor.execute('SELECT userid FROM ageRequirements WHERE userid = ?', (id,))
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
    minimum_age = configuration['min_age']
    account_created = member.created_at
    now = datetime.now(timezone.utc)
    delta = now - account_created

    is_allowed = await query_age_requirements(member.id)
    if is_allowed is not None:
        return

    if delta <= timedelta(days=minimum_age):
        await member.send(f'Your account does not meet the minimum creation date requirements. Please check back in {minimum_age - delta.days} days! :smile:')
        await member.kick(reason="Account doesn't meet minimum creation date requirements")
        channel = bot.get_channel(configuration['reports_channel'])
        await channel.send(f'Kicked new user for account age: {member.mention}')


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


@bot.command(help='Add exclusion to account age restriction based on user ID (arg1: integer<ID>')
@commands.has_permissions(kick_members=True)
async def allow_user_age(ctx, arg):
    conn = await aiosqlite.connect('users.db')
    cursor = await conn.cursor()

    try:
        user_id = int(arg)
        username = await bot.fetch_user(user_id)
        await cursor.execute('SELECT userid FROM ageRequirements WHERE userid = ?', (user_id,))
        valid = await cursor.fetchone()
        if valid:
            await ctx.reply(f"User '{username}' already excluded")
            return
    except (ValueError, discord.NotFound, discord.HTTPException):
        await ctx.reply('Please pass valid user ID')
        return

    await cursor.execute('INSERT INTO ageRequirements (userid) VALUES (?)', (user_id,))
    await conn.commit()
    await conn.close()
    await ctx.reply(f"Successfully added user '{username}' to exception list")


@bot.command(help='Remove existing exclusion to account age restriction based on user ID (arg1: integer<ID>')
@commands.has_permissions(kick_members=True)
async def deny_user_age(ctx, arg):
    conn = await aiosqlite.connect('users.db')
    cursor = await conn.cursor()

    try:
        user_id = int(arg)
        username = await bot.fetch_user(user_id)
        await cursor.execute('SELECT userid FROM ageRequirements WHERE userid = ?', (user_id,))
        valid = await cursor.fetchone()
        if not valid:
            await ctx.reply('User ID not in table, ignoring')
            return
    except (ValueError, discord.NotFound, discord.HTTPException):
        await ctx.reply('Please pass valid user ID')
        return

    await cursor.execute('DELETE FROM ageRequirements WHERE userid = ?', (user_id,))
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


