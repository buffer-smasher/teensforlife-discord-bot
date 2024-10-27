from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord import app_commands
import aiosqlite
import aiohttp
import discord
import asyncio
import json

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def execute_query(self, query, params=()):
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return await cursor.fetchall()


    async def daily_quote(self):
        while not self.bot.is_closed():
            try:
                now = datetime.now(timezone.utc)
                next_run = now.replace(hour=12, minute=0, second=0)
                if now >= next_run:
                    next_run += timedelta(days=1)
                wait_time = (next_run - now).total_seconds()
                await asyncio.sleep(wait_time)

                # get quote
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://zenquotes.io/api/random') as response:
                        quote_json = await response.json()
                        quote_message = f'"*{quote_json[0]['q']}*" -- **{quote_json[0]['a']}**'

                for guild in self.bot.guilds:
                    channel_id = await self.execute_query('SELECT quotesChannel FROM guildConfigs WHERE guildid = ?', (guild.id,))
                    if channel_id and channel_id[0][0] is not None:
                        channel = self.bot.get_channel(channel_id[0][0])
                        if channel:
                            await channel.send(quote_message)
            except Exception as error:
                print('Error sending daily quote')
                print(error)


    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.daily_quote())


async def setup(bot):
    await bot.add_cog(Quotes(bot))
