from discord.ext import commands
from discord import app_commands
import discord
import aiosqlite

class channel(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot


    async def execute_query(self, query, params=()):
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return await cursor.fetchall()


    @app_commands.command(name='reports', description='Channel to send moderation reports')
    async def reports_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET reportsChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Reports channel set to {channel.mention}')


    @app_commands.command(name='welcome', description='Channel where greetings are sent (to be deleted on ban)')
    async def welcome_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET welcomeChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Welcome channel set to {channel.mention}')


    @app_commands.command(name='anonymous', description='Channel where anonymous chatting occurs')
    async def anonymous_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET anonymousChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Anonymous channel set to {channel.mention}')


    @app_commands.command(name='quotes', description='Channel to send quotes')
    async def quotes_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET quotesChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Quotes channel set to {channel.mention}')


    @app_commands.command(name='music', description='Channel for playlist collaboration')
    async def music_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET musicChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Music channel set to {channel.mention}')


async def setup(bot):
    await bot.add_cog(channel(bot))
