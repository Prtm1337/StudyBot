"""Storage and study logic for StudyBot (no Discord code in here, so it is easy to test).

Flashcards use the Leitner system: a correct answer moves a card to a higher box
(reviewed less often), a wrong answer sends it back to box 1.
"""

import sqlite3
import time

DAY = 86400
BOX_INTERVAL_DAYS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
MAX_BOX = max(BOX_INTERVAL_DAYS)

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    box INTEGER NOT NULL DEFAULT 1,
    due_ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0
);
"""


class Store:
    def __init__(self, path="studybot.db", clock=time.time):
        self.clock = clock
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    # ---------- flashcards ----------
    def add_card(self, user_id, front, back):
        front, back = front.strip(), back.strip()
        if not front or not back:
            raise ValueError("Both sides of a card need some text.")
        cur = self.db.execute(
            "INSERT INTO cards (user_id, front, back, box, due_ts) VALUES (?, ?, ?, 1, ?)",
            (user_id, front, back, self.clock()),
        )
        self.db.commit()
        return cur.lastrowid

    def next_due_card(self, user_id):
        return self.db.execute(
            "SELECT * FROM cards WHERE user_id = ? AND due_ts <= ? ORDER BY due_ts LIMIT 1",
            (user_id, self.clock()),
        ).fetchone()

    def review(self, card_id, user_id, correct):
        """Record an answer and return the card's new box number."""
        card = self.db.execute(
            "SELECT * FROM cards WHERE id = ? AND user_id = ?", (card_id, user_id)
        ).fetchone()
        if card is None:
            raise KeyError("Card not found.")
        box = min(card["box"] + 1, MAX_BOX) if correct else 1
        due = self.clock() + BOX_INTERVAL_DAYS[box] * DAY
        self.db.execute("UPDATE cards SET box = ?, due_ts = ? WHERE id = ?", (box, due, card_id))
        self.db.commit()
        return box

    def card_stats(self, user_id):
        rows = self.db.execute(
            "SELECT box, COUNT(*) AS n FROM cards WHERE user_id = ? GROUP BY box", (user_id,)
        ).fetchall()
        due = self.db.execute(
            "SELECT COUNT(*) FROM cards WHERE user_id = ? AND due_ts <= ?",
            (user_id, self.clock()),
        ).fetchone()[0]
        per_box = {b: 0 for b in BOX_INTERVAL_DAYS}
        for r in rows:
            per_box[r["box"]] = r["n"]
        return {"total": sum(per_box.values()), "due": due, "per_box": per_box}

    # ---------- to-do list ----------
    def add_todo(self, user_id, text):
        text = text.strip()
        if not text:
            raise ValueError("Task text can't be empty.")
        cur = self.db.execute(
            "INSERT INTO todos (user_id, text) VALUES (?, ?)", (user_id, text)
        )
        self.db.commit()
        return cur.lastrowid

    def list_todos(self, user_id, include_done=False):
        query = "SELECT * FROM todos WHERE user_id = ?"
        if not include_done:
            query += " AND done = 0"
        return self.db.execute(query + " ORDER BY id", (user_id,)).fetchall()

    def complete_todo(self, user_id, todo_id):
        cur = self.db.execute(
            "UPDATE todos SET done = 1 WHERE id = ? AND user_id = ? AND done = 0",
            (todo_id, user_id),
        )
        self.db.commit()
        return cur.rowcount == 1
