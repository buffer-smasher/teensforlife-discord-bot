from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
import discord
import aiosqlite
import random

class rock(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot


    async def execute_query(self, query, params=()):
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(query, params) as cursor:
                await conn.commit()
                return await cursor.fetchall()


    @app_commands.command(name='help', description='Get help with your pet rock')
    async def rock_help(self, inter: discord.Interaction):
        await inter.response.send_message("# The rock: the ultimate pet - silent, loyal, and never judges your life choices!\n\nTo adopt your first rock pet use the `/rock adopt <name>` command and give it whatever name you want! You can change the name later with `/rock rename <name>`\n\nNow that you have a pet rock you can:\nTake it on walks: `/rock walk`\nShow it off to your friends: `/rock showoff`\nSee its stats: `/rock stats`\nKill it... `/rock kill`\n\nThat's the beauty of a rock pet. You can do whatever you want with it and PETA can't do a thing about it!", ephemeral=True)


    @app_commands.command(name='adopt', description='Adopt a cute little pet rock')
    async def rock_adopt(self, inter: discord.Interaction, name: str):
        rock_types = [
            "Basalt", "Granite", "Obsidian", "Pumice", "Andesite",
            "Diorite", "Rhyolite", "Gabbro", "Tuff", "Peridotite",
            "Pegmatite", "Volcanic Ash", "Scoria", "Felsite", "Basanite",
            "Sandstone", "Limestone", "Shale", "Conglomerate", "Siltstone",
            "Claystone", "Breccia", "Chalk", "Coal", "Lignite",
            "Dolostone", "Turbidite", "Variegated Claystone", "Phosphorite", "Mudstone",
            "Marble", "Schist", "Gneiss", "Slate", "Quartzite",
            "Phyllite", "Serpentinite", "Amphibolite", "Hornfels", "Metaconglomerate",
            "Mylonite", "Eclogite", "Tachylite", "Soapstone"
        ]

        rock = await self.execute_query('SELECT rockName FROM petRocks WHERE userid = ?', (inter.user.id,))
        if not rock:
            random_type = random.choice(rock_types)
            timenow = datetime.now(timezone.utc)
            await self.execute_query('INSERT INTO petRocks(userid, rockName, creationTime, rockType) VALUES (?, ?, ?, ?)', (inter.user.id, name, timenow, random_type))
            await inter.response.send_message(f'You just adopted a pet `{random_type}` rock named `{name}`! :rock:\n\nIf you want to know more about your little friend use the command `/rock help`', ephemeral=True)
        else:
            await inter.response.send_message(f"Hold on! You already have a rock named `{rock[0][0]}`.\nDon't you love your pet? :cry:", ephemeral=True)


    @app_commands.command(name='stats', description='View the stats of your pet rock')
    async def rock_stats(self, inter: discord.Interaction):
        rock = await self.execute_query('SELECT rockName, creationTime, rockType FROM petRocks WHERE userid = ?', (inter.user.id,))
        if rock:
            DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f%z"
            creation_time = datetime.strptime(rock[0][1], DATE_FORMAT)
            date_difference = datetime.now(timezone.utc) - creation_time
            await inter.response.send_message(f'**Name:** `{rock[0][0]}`\n**Age:** `{date_difference.days} days`\n**Type:** `{rock[0][2]}`\n\nWhat an awesome rock you have there!', ephemeral=True)
        else:
            await inter.response.send_message('You need to have a rock to view its stats', ephemeral=True)


    @app_commands.command(name='rename', description='Rename your rock')
    async def rock_name(self, inter: discord.Interaction, name: str):
        if inter.user.id:
            await self.execute_query('UPDATE petRocks SET rockName = ? WHERE userid = ?', (name, inter.user.id))
            await inter.response.send_message(f"Your rock has been renamed to {name}. That's a nice choice", ephemeral=True)


    @app_commands.command(name='showoff', description='Show your rock off to everyone')
    async def rock_showoff(self, inter: discord.Interaction):
        rock = await self.execute_query('SELECT rockName, creationTime, rockType FROM petRocks WHERE userid = ?', (inter.user.id,))
        if rock:
            DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f%z"
            creation_time = datetime.strptime(rock[0][1], DATE_FORMAT)
            date_difference = datetime.now(timezone.utc) - creation_time
            await inter.response.send_message('Showing your rock to the admirers', ephemeral=True)
            await inter.channel.send(f"{inter.user.mention} wants to show off their `{rock[0][2]}` rock, `{rock[0][0]}`!\n\nThey managed to keep their rock alive for `{date_difference.days} days`! That's pretty impressive.")
        else:
            await inter.response.send_message("No can do, boss. You don't have a rock to show off!", ephemeral=True)


    @app_commands.command(name='walk', description='Walk your rock')
    async def rock_walk(self, inter: discord.Interaction):
        await inter.response.send_message("I don't know how you expect to take a rock on a walk...\n\nDid you really think that was a good idea? :rofl:", ephemeral=True)


    @app_commands.command(name='kill', description='Are you evil?')
    async def rock_kill(self, inter: discord.Interaction):
        rock = await self.execute_query('SELECT rockName FROM petRocks WHERE userid = ?', (inter.user.id,))
        if rock:
            handled = False
            async def confirm_callback(inter: discord.Interaction):
                nonlocal handled
                if inter.user.id:
                    await self.execute_query('DELETE FROM petRocks WHERE userid = ?', (inter.user.id,))
                    await inter.response.send_message('Your rock is dead now. I hope you feel happy about what you just did! :sob:', ephemeral=True)
                    handled = True

            async def deny_callback(inter: discord.Interaction):
                nonlocal handled
                await inter.response.send_message('You are truly a merciful and reasonable rock owner :pray:', ephemeral=True)
                handled = True

            view = discord.ui.View(timeout=60)

            confirm_button = discord.ui.Button(label='Yes, I do', style=discord.ButtonStyle.green)
            deny_button = discord.ui.Button(label='No No No', style=discord.ButtonStyle.red)
            confirm_button.callback=confirm_callback
            deny_button.callback=deny_callback
            view.add_item(confirm_button)
            view.add_item(deny_button)

            await inter.response.send_message(f'Are you sure you want to kill your innocent little rock, `{rock[0][0]}`? :cry:', view=view, ephemeral=True)

            await view.wait()
            if not handled:
                await inter.followup.send('Your request timed out and your rock continutes to live', ephemeral=True)

        else:
            await inter.response.send_message("Don't get ahead of yourself! You don't have a rock to kill", ephemeral=True)


async def setup(bot):
    await bot.add_cog(rock(bot))
