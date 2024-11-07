import discord
from discord.ext import commands
from discord import ButtonStyle, Embed, Color, app_commands
from discord.ui import Button, View
import asyncio
from typing import List, Dict
from datetime import datetime
import aiosqlite

##################################################################################################
#                                                                                                #
#                               CODE COURTESY OF @jazxyss                                        #
# (READ: this is 100% AI generated with the exception of my edits to integrate it into this bot) #
#                            Not my fault if shit gets messed up :)                              #
#                                                                                                #
##################################################################################################


QUESTIONS = [
    {
        "question": "What's your personality type?",
        "options": ["Analytical", "Creative", "Social", "Practical"],
        "weight": 1.5
    },
    {
        "question": "What are your main hobbies?",
        "options": ["Gaming", "Reading", "Sports", "Arts"],
        "weight": 1.2
    },
    {
        "question": "What's your preferred social setting?",
        "options": ["Small groups", "Large parties", "One-on-one", "Online"],
        "weight": 1.3
    },
    {
        "question": "Are you more of an:",
        "options": ["Introvert", "Extrovert", "Ambivert", "Depends on mood"],
        "weight": 1.4
    },
    {
        "question": "What's your ideal weekend activity?",
        "options": ["Outdoor adventure", "Stay home relaxing", "Social events", "Learning something new"],
        "weight": 1.1
    },
    {
        "question": "What's your communication style?",
        "options": ["Direct", "Diplomatic", "Casual", "Professional"],
        "weight": 1.2
    },
    {
        "question": "What do you value most in friendships?",
        "options": ["Loyalty", "Humor", "Common interests", "Deep conversations"],
        "weight": 1.4
    }
]


class friendfinder(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='quiz', description='Take the friend finder quiz')
    async def quiz(self, inter: discord.Interaction):
        embed = create_question_embed(1, QUESTIONS[0])
        view = QuizView(QUESTIONS)
        await inter.response.send_message(embed=embed, view=view)

    @app_commands.command(name='results', description='View friend finder quiz results')
    async def results(self, inter: discord.Interaction):
        results = await execute_query('SELECT * FROM friendQuiz WHERE user_id = ?', (inter.user.id,))

        if not results:
            await inter.response.send_message("❗ You haven't taken the quiz yet! Use `/friendfinder quiz` to start.")
            return

        embed = Embed(
            title="📊 Your Profile",
            description="Here are your current quiz responses:",
            color=Color.blue()
        )

        for i, answer in enumerate(results[0][1:8], 1):
            embed.add_field(
                name=QUESTIONS[i-1]["question"],
                value=f"➡️ {answer}",
                inline=False
            )

        await inter.response.send_message(embed=embed)

    @app_commands.command(name='matches', description='View your matches based on the friend finder quiz')
    async def matches(self, inter: discord.Interaction):
        user_results = await execute_query('SELECT * FROM friendQuiz WHERE user_id = ?', (inter.user.id,))

        if not user_results:
            await inter.response.send_message("❗ You haven't taken the quiz yet! Use `/friendfinder quiz` to start.")
            return

        other_results = await execute_query('SELECT * FROM friendQuiz WHERE user_id != ?', (inter.user.id,))

        if not other_results:
            await inter.response.send_message('👥 No matches found yet! Encourage others to take the quiz using `/friendfinder quiz`')
            return

        matches = []
        for other_user in other_results:
            match_score = calculate_match_score(user_results[0], other_user)
            matches.append({
                'user_id': other_user[0],
                'percentage': match_score
            })

        matches.sort(key=lambda x: x['percentage'], reverse=True)

        matches_embed = Embed(
            title="🤝 Your Top Matches",
            description="Here are people you might want to connect with!",
            color=Color.green()
        )

        for i, match in enumerate(matches[:5], 1):
            user = await self.bot.fetch_user(match['user_id'])
            match_description = get_match_description(match['percentage'])
            matches_embed.add_field(
                name=f"{i}. {user.name} - {match['percentage']:.1f}%",
                value=f"{match_description}",
                inline=False
            )

        if not matches:
            matches_embed.description = "👥 No matches found yet! Encourage others to take the quiz using `!quiz`"

        await inter.response.send_message(embed=matches_embed)

class QuizButton(Button):
    def __init__(self, label: str, style: ButtonStyle):
        super().__init__(label=label, style=style)
        self.answer = label

    async def callback(self, inter: discord.Interaction):
        view: QuizView = self.view
        view.responses.append(self.answer)

        if view.current_question + 1 < len(view.questions):
            view.current_question += 1
            view.setup_buttons()
            embed = create_question_embed(view.current_question + 1, view.questions[view.current_question])
            await inter.response.edit_message(embed=embed, view=view)
        else:
            await execute_query('''
                INSERT OR REPLACE INTO friendQuiz
                    (user_id, q1, q2, q3, q4, q5, q6, q7)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (inter.user.id, *view.responses))

            completion_embed = Embed(
                title="🎉 Quiz Completed!",
                description="Thanks for updating your profile! Here's what you can do next:",
                color=Color.green()
            )
            completion_embed.add_field(
                name="📊 View Your Results",
                value="Use `/friendfinder results` to see your responses",
                inline=False
            )
            completion_embed.add_field(
                name="🤝 Find Matches",
                value="Use `/friendfinder matches` to discover compatible friends",
                inline=False
            )
            await inter.response.edit_message(embed=completion_embed, view=None)

class QuizView(View):
    def __init__(self, questions: List[Dict]):
        super().__init__(timeout=None)
        self.questions = questions
        self.current_question = 0
        self.responses = []
        self.setup_buttons()

    def setup_buttons(self):
        self.clear_items()
        styles = [ButtonStyle.primary, ButtonStyle.success, ButtonStyle.danger, ButtonStyle.secondary]
        for i, option in enumerate(self.questions[self.current_question]["options"]):
            self.add_item(QuizButton(option, style=styles[i % len(styles)]))

def create_question_embed(question_num: int, question_data: Dict) -> Embed:
    embed = Embed(
        title=f"Question {question_num}/{len(QUESTIONS)}",
        description=question_data["question"],
        color=Color.blue()
    )
    embed.add_field(
        name="Choose your answer:",
        value="\n".join(f"• {option}" for option in question_data["options"]),
        inline=False
    )
    embed.set_footer(text="Click a button below to answer!")
    return embed

def calculate_match_score(user1_responses: tuple, user2_responses: tuple) -> float:
    total_weight = sum(q["weight"] for q in QUESTIONS)
    weighted_score = 0

    for i, (ans1, ans2) in enumerate(zip(user1_responses[1:8], user2_responses[1:8])):
        if ans1 == ans2:
            weighted_score += QUESTIONS[i]["weight"]
        elif (ans1 in ["Gaming", "Reading"] and ans2 in ["Gaming", "Reading"]) or \
             (ans1 in ["Sports", "Arts"] and ans2 in ["Sports", "Arts"]):
            weighted_score += QUESTIONS[i]["weight"] * 0.5

    return (weighted_score / total_weight) * 100

def get_match_description(percentage: float) -> str:
    if percentage >= 90:
        return "🌟 Perfect Match! You two would get along great!"
    elif percentage >= 75:
        return "✨ Strong Match! You have lots in common!"
    elif percentage >= 60:
        return "👍 Good Match! You might enjoy chatting!"
    else:
        return "🤔 You might learn something new from each other!"


async def execute_query(query, params=()):
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(query, params) as cursor:
            await conn.commit()
            return await cursor.fetchall()


async def setup(bot):
    await bot.add_cog(friendfinder(bot))
