import unittest

from store import DAY, Store


class FakeClock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.store = Store(":memory:", clock=self.clock)

    def test_new_card_is_due_immediately(self):
        card_id = self.store.add_card(1, "Capital of India?", "New Delhi")
        self.assertEqual(self.store.next_due_card(1)["id"], card_id)

    def test_correct_answer_moves_up_and_delays_card(self):
        card_id = self.store.add_card(1, "q", "a")
        self.assertEqual(self.store.review(card_id, 1, True), 2)
        self.assertIsNone(self.store.next_due_card(1))
        self.clock.now += 2 * DAY
        self.assertIsNotNone(self.store.next_due_card(1))

    def test_wrong_answer_resets_to_box_one(self):
        card_id = self.store.add_card(1, "q", "a")
        for _ in range(3):
            self.store.review(card_id, 1, True)
        self.assertEqual(self.store.review(card_id, 1, False), 1)

    def test_box_is_capped(self):
        card_id = self.store.add_card(1, "q", "a")
        box = 0
        for _ in range(10):
            box = self.store.review(card_id, 1, True)
        self.assertEqual(box, 5)

    def test_users_cannot_touch_each_others_cards(self):
        card_id = self.store.add_card(1, "q", "a")
        with self.assertRaises(KeyError):
            self.store.review(card_id, 2, True)
        self.assertIsNone(self.store.next_due_card(2))

    def test_empty_card_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add_card(1, "   ", "a")

    def test_stats(self):
        a = self.store.add_card(1, "q1", "a1")
        self.store.add_card(1, "q2", "a2")
        self.store.review(a, 1, True)
        stats = self.store.card_stats(1)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["due"], 1)
        self.assertEqual(stats["per_box"][2], 1)

    def test_todo_flow(self):
        t = self.store.add_todo(1, "Finish lab record")
        self.assertEqual(len(self.store.list_todos(1)), 1)
        self.assertFalse(self.store.complete_todo(2, t))
        self.assertTrue(self.store.complete_todo(1, t))
        self.assertFalse(self.store.complete_todo(1, t))
        self.assertEqual(self.store.list_todos(1), [])
        self.assertEqual(len(self.store.list_todos(1, include_done=True)), 1)


if __name__ == "__main__":
    unittest.main()
