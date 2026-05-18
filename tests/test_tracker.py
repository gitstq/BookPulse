"""
Unit tests for the BookPulse Reading Tracker module.
Tests reading start, progress, finish, notes, history, and streaks.
"""

import os
import sys
import tempfile
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bookpulse.storage import Storage
from bookpulse.books import BookManager
from bookpulse.tracker import ReadingTracker


class TestReadingTracker(unittest.TestCase):
    """Test cases for ReadingTracker."""

    def setUp(self):
        """Set up a temporary database with test books."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.storage = Storage(db_path=self.db_path)
        self.bm = BookManager(self.storage)
        self.tracker = ReadingTracker(self.storage)

        # Create test books
        self.book1_id = self.bm.add(
            title="Test Book 1",
            author="Author A",
            page_count=300,
        )
        self.book2_id = self.bm.add(
            title="Test Book 2",
            author="Author B",
            page_count=200,
        )
        self.book3_id = self.bm.add(
            title="Test Book 3",
            author="Author C",
            page_count=150,
        )

    def tearDown(self):
        """Clean up the temporary database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_start_reading(self):
        """Test starting to read a book."""
        result = self.tracker.start(self.book1_id)
        self.assertTrue(result)

        book = self.bm.get(self.book1_id)
        self.assertEqual(book["status"], "reading")
        self.assertEqual(book["current_page"], 0)

    def test_start_reading_nonexistent(self):
        """Test starting to read a non-existent book."""
        with self.assertRaises(ValueError):
            self.tracker.start(9999)

    def test_update_progress_by_page(self):
        """Test updating progress by page number."""
        self.tracker.start(self.book1_id)
        result = self.tracker.progress(self.book1_id, page=150)

        self.assertEqual(result["page"], 150)
        self.assertEqual(result["percentage"], 50.0)
        self.assertEqual(result["page_count"], 300)

        book = self.bm.get(self.book1_id)
        self.assertEqual(book["current_page"], 150)

    def test_update_progress_by_percentage(self):
        """Test updating progress by percentage."""
        self.tracker.start(self.book1_id)
        result = self.tracker.progress(self.book1_id, percentage=75.0)

        self.assertEqual(result["percentage"], 75.0)
        self.assertEqual(result["page"], 225)

    def test_update_progress_not_reading(self):
        """Test updating progress on a book not being read."""
        with self.assertRaises(ValueError) as ctx:
            self.tracker.progress(self.book1_id, page=50)
        self.assertIn("not currently being read", str(ctx.exception))

    def test_update_progress_nonexistent(self):
        """Test updating progress on a non-existent book."""
        with self.assertRaises(ValueError):
            self.tracker.progress(9999, page=50)

    def test_finish_reading(self):
        """Test finishing a book."""
        self.tracker.start(self.book1_id)
        self.tracker.progress(self.book1_id, page=200)
        result = self.tracker.finish(self.book1_id)
        self.assertTrue(result)

        book = self.bm.get(self.book1_id)
        self.assertEqual(book["status"], "finished")
        self.assertEqual(book["current_page"], 300)

    def test_finish_reading_nonexistent(self):
        """Test finishing a non-existent book."""
        with self.assertRaises(ValueError):
            self.tracker.finish(9999)

    def test_log_note(self):
        """Test adding a reading note."""
        note_id = self.tracker.log_note(self.book1_id, "Great chapter about dragons!")
        self.assertIsNotNone(note_id)
        self.assertGreater(note_id, 0)

    def test_log_note_empty(self):
        """Test that empty note raises ValueError."""
        with self.assertRaises(ValueError):
            self.tracker.log_note(self.book1_id, "")

    def test_log_note_nonexistent(self):
        """Test adding a note to a non-existent book."""
        with self.assertRaises(ValueError):
            self.tracker.log_note(9999, "Some note")

    def test_history(self):
        """Test reading history retrieval."""
        self.tracker.start(self.book1_id)
        self.tracker.progress(self.book1_id, page=100)
        self.tracker.log_note(self.book1_id, "Interesting point")

        logs = self.tracker.history(book_id=self.book1_id)
        self.assertEqual(len(logs), 3)

        # Most recent first
        self.assertEqual(logs[0]["action"], "note")
        self.assertEqual(logs[1]["action"], "progress")
        self.assertEqual(logs[2]["action"], "start")

    def test_history_filter_by_action(self):
        """Test filtering history by action type."""
        self.tracker.start(self.book1_id)
        self.tracker.progress(self.book1_id, page=50)
        self.tracker.log_note(self.book1_id, "Note 1")
        self.tracker.log_note(self.book1_id, "Note 2")

        logs = self.tracker.history(book_id=self.book1_id, action="note")
        self.assertEqual(len(logs), 2)
        for log in logs:
            self.assertEqual(log["action"], "note")

    def test_history_pagination(self):
        """Test history pagination."""
        self.tracker.start(self.book1_id)
        for i in range(10):
            self.tracker.progress(self.book1_id, page=(i + 1) * 10)
            self.tracker.log_note(self.book1_id, f"Note {i}")

        logs = self.tracker.history(limit=5)
        self.assertEqual(len(logs), 5)

    def test_current(self):
        """Test getting currently reading books."""
        self.tracker.start(self.book1_id)
        self.tracker.start(self.book2_id)

        current = self.tracker.current()
        self.assertEqual(len(current), 2)

        titles = [b["title"] for b in current]
        self.assertIn("Test Book 1", titles)
        self.assertIn("Test Book 2", titles)

    def test_current_empty(self):
        """Test getting currently reading books when none."""
        current = self.tracker.current()
        self.assertEqual(len(current), 0)

    def test_streak_no_activity(self):
        """Test streak with no reading activity."""
        streak = self.tracker.streak()
        self.assertEqual(streak["current_streak"], 0)
        self.assertEqual(streak["longest_streak"], 0)
        self.assertEqual(streak["total_reading_days"], 0)

    def test_streak_with_activity(self):
        """Test streak calculation with reading activity."""
        self.tracker.start(self.book1_id)
        self.tracker.progress(self.book1_id, page=50)
        self.tracker.log_note(self.book1_id, "Note")

        streak = self.tracker.streak()
        self.assertGreater(streak["current_streak"], 0)
        self.assertGreater(streak["total_reading_days"], 0)

    def test_full_reading_workflow(self):
        """Test a complete reading workflow."""
        # Start reading
        self.tracker.start(self.book1_id)
        book = self.bm.get(self.book1_id)
        self.assertEqual(book["status"], "reading")

        # Update progress multiple times
        self.tracker.progress(self.book1_id, page=100)
        self.tracker.progress(self.book1_id, page=200)
        self.tracker.progress(self.book1_id, page=299)

        # Add notes
        self.tracker.log_note(self.book1_id, "Great first half!")
        self.tracker.log_note(self.book1_id, "Amazing ending!")

        # Finish
        self.tracker.finish(self.book1_id)
        book = self.bm.get(self.book1_id)
        self.assertEqual(book["status"], "finished")
        self.assertEqual(book["current_page"], 300)

        # Check history
        logs = self.tracker.history(book_id=self.book1_id)
        actions = [log["action"] for log in logs]
        self.assertIn("start", actions)
        self.assertIn("progress", actions)
        self.assertIn("note", actions)
        self.assertIn("finish", actions)

    def test_multiple_books_workflow(self):
        """Test reading multiple books simultaneously."""
        self.tracker.start(self.book1_id)
        self.tracker.start(self.book2_id)

        self.tracker.progress(self.book1_id, page=150)
        self.tracker.progress(self.book2_id, page=100)

        self.tracker.finish(self.book1_id)

        current = self.tracker.current()
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["id"], self.book2_id)

        book1 = self.bm.get(self.book1_id)
        self.assertEqual(book1["status"], "finished")

        book2 = self.bm.get(self.book2_id)
        self.assertEqual(book2["status"], "reading")


if __name__ == "__main__":
    unittest.main()
