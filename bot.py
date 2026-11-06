"""StudyBot - a Discord bot with Leitner flashcards and a to-do list.

Setup: copy .env.example to .env, put your bot token in it, then run:  python bot.py
"""

import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from store import BOX_INTERVAL_DAYS, Store

load_dotenv()
store = Store(os.getenv("DB_PATH", "studybot.db"))


class StudyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # With TEST_GUILD_ID set, commands show up instantly in that server (good for testing).
        guild_id = os.getenv("TEST_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (id {self.user.id})")


bot = StudyBot()


# ---------------- flashcards ----------------
def quiz_embed(front, back=None):
    embed = discord.Embed(title="Flashcard", colour=discord.Colour.blurple())
    embed.add_field(name="Question", value=front, inline=False)
    if back is not None:
        embed.add_field(name="Answer", value=back, inline=False)
    return embed


class QuizView(discord.ui.View):
    """Buttons: Show answer, then Got it / Missed it. Only the quiz owner can click."""

    def __init__(self, card_id, front, back, owner_id):
        super().__init__(timeout=300)
        self.card_id, self.front, self.back, self.owner_id = card_id, front, back, owner_id
        self.got_it.disabled = True
        self.missed.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This quiz belongs to someone else.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Show answer", style=discord.ButtonStyle.primary)
    async def reveal(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        self.got_it.disabled = False
        self.missed.disabled = False
        await interaction.response.edit_message(embed=quiz_embed(self.front, self.back), view=self)

    @discord.ui.button(label="Got it", style=discord.ButtonStyle.success)
    async def got_it(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, correct=True)

    @discord.ui.button(label="Missed it", style=discord.ButtonStyle.danger)
    async def missed(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finish(interaction, correct=False)

    async def _finish(self, interaction, correct):
        box = store.review(self.card_id, self.owner_id, correct)
        for child in self.children:
            child.disabled = True
        self.stop()
        days = BOX_INTERVAL_DAYS[box]
        verdict = "Nice!" if correct else "No worries, you'll see it again soon."
        await interaction.response.edit_message(
            content=f"{verdict} Card is now in box {box} (next review in {days} day{'s' if days != 1 else ''}).",
            view=self,
        )


@bot.tree.command(name="addcard", description="Add a flashcard")
@app_commands.describe(front="The question", back="The answer")
async def addcard(interaction: discord.Interaction, front: app_commands.Range[str, 1, 500], back: app_commands.Range[str, 1, 500]):
    card_id = store.add_card(interaction.user.id, front, back)
    await interaction.response.send_message(f"Card #{card_id} added.", ephemeral=True)


@bot.tree.command(name="quiz", description="Get your next due flashcard")
async def quiz(interaction: discord.Interaction):
    card = store.next_due_card(interaction.user.id)
    if card is None:
        await interaction.response.send_message("You're all caught up. No cards due!", ephemeral=True)
        return
    view = QuizView(card["id"], card["front"], card["back"], interaction.user.id)
    await interaction.response.send_message(embed=quiz_embed(card["front"]), view=view, ephemeral=True)


@bot.tree.command(name="stats", description="See how your flashcards are doing")
async def stats(interaction: discord.Interaction):
    s = store.card_stats(interaction.user.id)
    boxes = "\n".join(f"Box {b}: {n}" for b, n in s["per_box"].items())
    await interaction.response.send_message(
        f"**Cards:** {s['total']}  |  **Due now:** {s['due']}\n{boxes}", ephemeral=True
    )


# ---------------- to-do list ----------------
todo = app_commands.Group(name="todo", description="Your personal to-do list")


@todo.command(name="add", description="Add a task")
async def todo_add(interaction: discord.Interaction, task: app_commands.Range[str, 1, 200]):
    todo_id = store.add_todo(interaction.user.id, task)
    await interaction.response.send_message(f"Task #{todo_id} added.", ephemeral=True)


@todo.command(name="list", description="Show your open tasks")
async def todo_list(interaction: discord.Interaction):
    items = store.list_todos(interaction.user.id)
    text = "\n".join(f"`#{t['id']}` {t['text']}" for t in items) or "Nothing to do. Enjoy!"
    await interaction.response.send_message(text, ephemeral=True)


@todo.command(name="done", description="Mark a task as done")
@app_commands.describe(task_id="The number shown in /todo list")
async def todo_done(interaction: discord.Interaction, task_id: int):
    ok = store.complete_todo(interaction.user.id, task_id)
    msg = f"Task #{task_id} done." if ok else "No open task with that number."
    await interaction.response.send_message(msg, ephemeral=True)


bot.tree.add_command(todo)


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_TOKEN in your .env file first (see README).")
    bot.run(token)
