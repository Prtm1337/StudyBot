# StudyBot

A Discord bot for students: spaced-repetition flashcards (Leitner system) and a personal to-do list, built with Python, discord.py and SQLite.

## Features
- `/addcard front back` - add a flashcard
- `/quiz` - get your next due card, reveal the answer with a button, then mark it "Got it" or "Missed it"
- `/stats` - see how many cards you have, how many are due, and how they are spread across boxes
- `/todo add`, `/todo list`, `/todo done` - a simple personal task list

All replies are private (only you see them), and every user's data is kept separate.

## How the flashcards work
Cards live in 5 boxes. A correct answer moves a card up a box, so it is shown less often (after 1, 2, 4, 8, then 16 days). A wrong answer sends it back to box 1. This is the Leitner system, a simple form of spaced repetition.

## Project structure
- `store.py` - all the logic and database code (no Discord code, so it is easy to test)
- `bot.py` - the Discord commands and button interface
- `test_store.py` - unit tests for the logic

## Setup
1. Create an application and bot at the [Discord Developer Portal](https://discord.com/developers/applications) and copy the bot token.
2. Invite the bot to your server with the `bot` and `applications.commands` scopes.
3. Install and configure:
   ```bash
   pip install -r requirements.txt
   cp .env.example .env     # then paste your token into .env
   python bot.py
   ```
4. Optional: set `TEST_GUILD_ID` in `.env` to your server's ID so new commands appear instantly.

## Run the tests
```bash
python -m unittest
```

## Ideas for next steps
- Pomodoro timer command that pings you when a focus session ends
- Import and export cards as CSV
- Decks (separate card sets per subject)
- Daily reminder of due cards

## Author
Pritam Panda - B.Tech Electrical Engineering, VSSUT Burla
