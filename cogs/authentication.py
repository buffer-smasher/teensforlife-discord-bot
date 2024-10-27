from discord.ext import commands
from discord import app_commands
import aiosqlite
from datetime import datetime, timezone, timedelta
import discord

class Authentication(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def execute_query(self, query, params=()):
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return await cursor.fetchall()


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        result = await self.execute_query('SELECT reportsChannel, minimumAge FROM guildConfigs WHERE guildid = ?', (member.guild.id,))
        report_channel_id, minimum_age = result[0]

        report_channel = self.bot.get_channel(report_channel_id)
        minimum_age_delta = timedelta(days=minimum_age)
        restricted_words = {
            'gay': 0.5,
            'cp': 1,
            'sell': 1,
            'rape': 1.5,
            'incest': 2,
            'mega': 0.5,
            'link': 0.5,
            'legit': 0.5
        }

        # check if user is an exception
        is_allowed = await self.execute_query('SELECT userid FROM kickExceptions WHERE userid = ?', (member.id,))
        if is_allowed:
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
            try:
                await report_channel.send(f'Banned new user for flagged username: {member.mention}')
            except AttributeError:
    # no report channel set
                pass
            welcome_channel_id = await self.execute_query('SELECT welcomeChannel FROM guildConfigs WHERE guildid = ?', (member.guild.id,))
            try:
                welcome_channel = self.bot.get_channel(welcome_channel_id[0][0])
            except AttributeError:
                # no welcome channel set
                pass
            else:
                async for msg in welcome_channel.history(limit=2):
                    for mention in msg.mentions:
                        if mention.id == member.id:
                            await msg.delete()
            return

        # check account creation date
        account_created = member.created_at
        now = datetime.now(timezone.utc)
        delta = now - account_created
        if delta <= minimum_age_delta:
            timeout_until = minimum_age_delta - delta
            await member.send(f'Your account does not meet the minimum creation date requirements; therefore, you have been timed out. Please check back later! :smile:')
            await member.timeout(timeout_until, reason="Account doesn't meet minimum creation date requirements")
            await report_channel.send(f'Timed out new user for account age: {member.mention}')
            return


    @app_commands.command(name='account-age', description='Set minimum account age for new members. Counts in days from present time')
    @app_commands.checks.has_permissions(kick_members=True)
    async def set_min_creation_date(self, inter: discord.Interaction, days: int):
        try:
            await self.execute_query('UPDATE guildConfigs SET minimumAge = ? WHERE guildid = ?', (days, inter.guild.id))
            await inter.response.send_message(f'Minimum creation date set to: {days} days')
        except ValueError:
            await inter.response.send_message('Please use integer as argument')
            return


    @app_commands.command(name='bypass-user', description='Add exclusion to account auto-filter based on user ID')
    @app_commands.checks.has_permissions(ban_members=True)
    async def allow_user_age(self, inter: discord.Interaction, userID: int):
        conn = await aiosqlite.connect('users.db')
        cursor = await conn.cursor()

        try:
            username = await self.bot.fetch_user(userID)
            valid = await self.execute_query('SELECT userid FROM kickExceptions WHERE userid = ?', (userID,))
            if valid:
                await inter.response.send_message(f"User '{username}' already excluded")
                return
        except (ValueError, discord.NotFound, discord.HTTPException):
            await inter.response.send_message('Please pass valid user ID')
            return

        await self.execute_query('INSERT INTO kickExceptions (userid) VALUES (?)', (userID,))
        await inter.response.send_message(f"Successfully added user '{username}' to exception list")


    @app_commands.command(name='bypass-user-remove', description='Remove existing exclusion to account auto-filter based on user ID')
    @app_commands.checks.has_permissions(ban_members=True)
    async def deny_user_age(self, inter: discord.Interaction, userID: int):
        try:
            username = await self.bot.fetch_user(userID)
            valid = await self.execute_query('SELECT userid FROM kickExceptions WHERE userid = ?', (userID,))
            if not valid:
                await inter.response.send_message('User ID not in table, ignoring')
                return
        except (ValueError, discord.NotFound, discord.HTTPException):
            await inter.response.send_message('Please pass valid user ID')
            return
        await self.execute_query('DELETE FROM kickExceptions WHERE userid = ?', (userID,))
        await inter.response.send_message(f"Successfully removed user '{username}' from exception list")


    @app_commands.command(name='reports-channel', description='Sets reports channel to #mentioned channel')
    async def set_reports_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET reportsChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Set reports channel to {channel.mention}')


    @app_commands.command(name='welcome-channel', description='Sets welcome channel to #mentioned channel')
    async def set_welcome_channel(self, inter: discord.Interaction, channel: discord.TextChannel):
        await self.execute_query('UPDATE guildConfigs SET welcomeChannel = ? WHERE guildid = ?', (channel.id, inter.guild.id))
        await inter.response.send_message(f'Set welcome channel to {channel.mention}')


async def setup(bot):
    await bot.add_cog(Authentication(bot))
