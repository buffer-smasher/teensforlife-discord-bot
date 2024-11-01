import discord
from discord.ext import commands
from discord import app_commands


class Greeter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def greet_member(self, member: discord.Member):
        # hard codes links because I'm not a masochist and I don't actually have unlimited free time
        CHAN_URL_TEMPLATE = 'https://discord.com/channels/1257601875625377842/{cid}'
        RULES_CHAN = CHAN_URL_TEMPLATE.format(cid=1257603437240127569)
        FSHIP_CHAN = CHAN_URL_TEMPLATE.format(cid=1258784306541891594)
        REL_CHAN = CHAN_URL_TEMPLATE.format(cid=1258338116599677029)
        MENTAL_CHAN = CHAN_URL_TEMPLATE.format(cid=1258784230767333396)
        EVENT_CHAN = CHAN_URL_TEMPLATE.format(cid=1277625638601097318)
        INTRO_CHAN = CHAN_URL_TEMPLATE.format(cid=1257605867088384091)
        FEEDBACK_CHAN = CHAN_URL_TEMPLATE.format(cid=1272097107469144146)
        RESOURCES_CHAN = CHAN_URL_TEMPLATE.format(cid=1258786113116569670)

        async def button1_callback(inter: discord.Interaction):
            community_text = (
                "# Community Rules & Values\n"
                "1. **What are the community guidelines?**\n"
                "   We value respect, support, and positivity! Our guidelines are here to make sure everyone has a safe, enjoyable experience.\n"
                f"   A full list of our rules can be found at {RULES_CHAN}.\n\n"
                "2. **How can I report an issue?**\n"
                "   If you come across any concerns, feel free to reach out to any of our moderators or type `/report` to start a private conversation.\n\n"
                "3. **Are there any privacy policies I should know about?**\n"
                "   Yes! We value your privacy, and all personal data is treated confidentially."
            )
            await inter.response.send_message(community_text)

        async def button2_callback(inter: discord.Interaction):
            features_text = (
                "# Features and Channels\n"
                "1. **What can I do here?**\n"
                "   In Teensforlife, you can join group discussions, participate in events, and connect with people facing similar challenges.\n"
                "   We provide various channels dedicated to providing you with the resources that you need to become the best version of yourself.\n"
                "   We even host live events where you can join and participate.\n\n"
                "2. **Where can I talk to others about friendships, relationships, or mental health?**\n"
                "   We have dedicated channels for each topic!\n"
                f"   Head over to {FSHIP_CHAN} for friendships, {REL_CHAN} for relationship advice, and {MENTAL_CHAN} for wellness discussions.\n\n"
                "3. **How can I find upcoming events?**\n"
                f"   Events are listed in {EVENT_CHAN}.\n"
                "   Keep an eye out for our announcements for upcoming workshops and fun activities!"
            )
            await inter.response.send_message(features_text)

        async def button3_callback(inter: discord.Interaction):
            earn_text = (
                "# Earning and Participating\n"
                "1. **How can I earn points or rewards?**\n"
                "   You can earn points by participating in challenges, completing daily check-ins, and helping others.\n"
                "   Accumulate points to unlock cool rewards!\n\n"
                "2. **What's the easiest way to get involved?**\n"
                f"   Great question! You can introduce yourself in {INTRO_CHAN}, join a topic channel, or join a challenge to get started.\n"
                "   We encourage all members to participate and connect.\n\n"
                "3. **Are there leadership roles for members?**\n"
                "   Absolutely! Members who actively participate can apply for roles like ‘*Support Leader*’ or ‘*Event Helper.*’\n"
                "   Roles have perks and responsibilities!"
            )
            await inter.response.send_message(earn_text)

        async def button4_callback(inter: discord.Interaction):
            misc_text = (
                "# Miscellaneous\n"
                "1. **Who should I reach out to if I need help?**\n"
                "   You can reach out to any of our moderators. They're here to help you\n\n"
                "2. **How can I give feedback or suggest new features?**\n"
                f"   We love hearing your ideas! Drop any feedback or suggestions in the {FEEDBACK_CHAN}, or DM a moderator directory\n\n"
                "3. **How can I access resources like books or guides?**\n"
                f"   We have a resource library available in {RESOURCES_CHAN}, with guides, articles, and books created just for you"

            )
            await inter.response.send_message(misc_text)

        async def button5_callback(inter: discord.Interaction):
            bye_text = (
                "Thanks for checking in! We hope you enjoy your time in Teensforlife.\n"
                "Don't hesitate to reach out if you ever have questions or just want to talk.\n\n"
                "**We're glad to have you here!**"
            )
            await inter.response.send_message(bye_text)

        view = discord.ui.View(timeout=86400)


        button1 = discord.ui.Button(label='Community Rules & Values', style=discord.ButtonStyle.primary, row=0)
        button2 = discord.ui.Button(label='Features and Channels', style=discord.ButtonStyle.primary, row=0)
        button3 = discord.ui.Button(label='Earning and Participating', style=discord.ButtonStyle.primary, row=0)
        button4 = discord.ui.Button(label='Miscellaneous', style=discord.ButtonStyle.primary, row=0)
        button5 = discord.ui.Button(label="Ready to explore?", style=discord.ButtonStyle.green, row=1)

        button1.callback = button1_callback
        button2.callback = button2_callback
        button3.callback = button3_callback
        button4.callback = button4_callback
        button5.callback = button5_callback

        view.add_item(item=button1)
        view.add_item(item=button2)
        view.add_item(item=button3)
        view.add_item(item=button4)
        view.add_item(item=button5)

        greeting_dialogue = f"Hey there, {member.mention}! :tada:\nWelcome to Teensforlife — your space to connect, grow, and find support.\n\nI’m here to help you get started and answer any questions you might have.\nJust click any of the options below, and I’ll guide you along!\n\n"

        greeting_message = await member.send(greeting_dialogue, view=view)

        await view.wait()
        await greeting_message.edit(content='This message has expired, please use `/greetme` to see this message again', view=None)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.greet_member(member)


    @app_commands.command(name='greet', description='Greet a user')
    @app_commands.checks.has_permissions(kick_members=True)
    async def greet_command(self, inter: discord.Interaction, member: discord.Member):
        await inter.response.send_message('Greeting sent!', ephemeral=True)
        await self.greet_member(member)


    @app_commands.command(name='greetme', description='Greet yourself')
    async def greetme_command(self, inter: discord.Interaction):
        await inter.response.send_message('Greeting sent!', ephemeral=True)
        await self.greet_member(inter.user)


async def setup(bot):
    await bot.add_cog(Greeter(bot))
