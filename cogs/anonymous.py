from datetime import datetime, timezone
from discord.ext import commands
from discord import app_commands
import discord
import aiosqlite

class Anonymous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def execute_query(self, query, params=()):
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return await cursor.fetchall()


    @app_commands.command(name='anon', description='Send an anonymous message')
    @app_commands.checks.has_permissions(send_messages=True)
    async def anon_message(self, inter: discord.Interaction, message: str):
        specified_channel_id = await self.execute_query('SELECT anonymousChannel FROM guildConfigs WHERE guildid = ?', (inter.guild.id,))
        specified_channel_id = specified_channel_id[0][0]
        if specified_channel_id is not None:
            if specified_channel_id != inter.channel.id:
                channel = self.bot.get_channel(specified_channel_id)
                await inter.response.send_message(f'Please use this command in {channel.mention}', ephemeral=True)
                return

        button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.primary)

        async def button_callback(inter: discord.Interaction):
            await inter.response.defer()
            bot_msg = await inter.channel.send(message)

            timestamp = datetime.now(timezone.utc)
            await self.execute_query('''
            INSERT INTO anonymousChat(messageid, serverid, channelid, userid, username, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bot_msg.id, inter.guild.id, inter.channel.id, inter.user.id, inter.user.name, message, timestamp))

        button.callback = button_callback

        view = discord.ui.View()
        view.add_item(item=button)

        confirm_dialogue = f'## Is this the message you want to send?\n\n`{message}`\n\nPlease note that your information will be **logged** for review if this message is found to contain inappropriate content.'
        await inter.response.send_message(confirm_dialogue, ephemeral=True, view=view)


    @app_commands.command(name='anon_channel', description='Sets channel where /anon command can be used')
    async def set_anon_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET anonymousChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Set anonymous channel to {channel.mention}')


async def setup(bot):
    await bot.add_cog(Anonymous(bot))
