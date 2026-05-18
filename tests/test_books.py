"""
Unit tests for the BookPulse Books module.
Tests book CRUD operations, search, import/export, and statistics.
"""

import os
import sys
import json
import csv
import tempfile
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bookpulse.storage import Storage
from bookpulse.books import BookManager


class TestBookManager(unittest.TestCase):
    """Test cases for BookManager."""

    def setUp(self):
        """Set up a temporary database for each test."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.storage = Storage(db_path=self.db_path)
        self.bm = BookManager(self.storage)

    def tearDown(self):
        """Clean up the temporary database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_add_book(self):
        """Test adding a book."""
        book_id = self.bm.add(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            isbn="9780743273565",
            category="Fiction",
            page_count=180,
        )
        self.assertIsNotNone(book_id)
        self.assertGreater(book_id, 0)

        # Verify the book was stored
        book = self.bm.get(book_id)
        self.assertEqual(book["title"], "The Great Gatsby")
        self.assertEqual(book["author"], "F. Scott Fitzgerald")
        self.assertEqual(book["isbn"], "9780743273565")
        self.assertEqual(book["category"], "Fiction")
        self.assertEqual(book["page_count"], 180)
        self.assertEqual(book["status"], "unread")

    def test_add_book_with_tags(self):
        """Test adding a book with tags."""
        book_id = self.bm.add(
            title="Dune",
            author="Frank Herbert",
            tags=["sci-fi", "classic", "space"],
        )
        book = self.bm.get(book_id)
        tags = json.loads(book["tags"])
        self.assertEqual(tags, ["sci-fi", "classic", "space"])

    def test_add_book_duplicate_isbn(self):
        """Test that duplicate ISBN raises ValueError."""
        self.bm.add(title="Book A", isbn="1111111111")
        with self.assertRaises(ValueError) as ctx:
            self.bm.add(title="Book B", isbn="1111111111")
        self.assertIn("already exists", str(ctx.exception))

    def test_add_book_empty_title(self):
        """Test that empty title raises ValueError."""
        with self.assertRaises(ValueError):
            self.bm.add(title="")

    def test_list_books(self):
        """Test listing books."""
        self.bm.add(title="Book A", author="Author A")
        self.bm.add(title="Book B", author="Author B")
        self.bm.add(title="Book C", author="Author A")

        books, total = self.bm.list()
        self.assertEqual(total, 3)
        self.assertEqual(len(books), 3)

    def test_list_books_filter_by_status(self):
        """Test listing books filtered by status."""
        id1 = self.bm.add(title="Book A")
        id2 = self.bm.add(title="Book B")
        self.bm.update(id1, status="reading")

        books, total = self.bm.list(status="reading")
        self.assertEqual(total, 1)
        self.assertEqual(books[0]["id"], id1)

    def test_list_books_filter_by_category(self):
        """Test listing books filtered by category."""
        self.bm.add(title="Book A", category="Mystery")
        self.bm.add(title="Book B", category="Romance")
        self.bm.add(title="Book C", category="Mystery")

        books, total = self.bm.list(category="Mystery")
        self.assertEqual(total, 2)

    def test_list_books_pagination(self):
        """Test book listing pagination."""
        for i in range(25):
            self.bm.add(title=f"Book {i:02d}")

        books, total = self.bm.list(page=1, page_size=10)
        self.assertEqual(total, 25)
        self.assertEqual(len(books), 10)

        books2, _ = self.bm.list(page=2, page_size=10)
        self.assertEqual(len(books2), 10)

        books3, _ = self.bm.list(page=3, page_size=10)
        self.assertEqual(len(books3), 5)

    def test_list_books_sorting(self):
        """Test book listing with sorting."""
        self.bm.add(title="C Book", author="Z Author")
        self.bm.add(title="A Book", author="X Author")
        self.bm.add(title="B Book", author="Y Author")

        books, _ = self.bm.list(sort_by="title", sort_order="asc")
        self.assertEqual(books[0]["title"], "A Book")
        self.assertEqual(books[2]["title"], "C Book")

    def test_search_books(self):
        """Test searching books."""
        self.bm.add(title="The Python Cookbook", author="David Beazley")
        self.bm.add(title="Learning Python", author="Mark Lutz")
        self.bm.add(title="JavaScript: The Good Parts", author="Douglas Crockford")

        results = self.bm.search("Python")
        self.assertEqual(len(results), 2)

        results = self.bm.search("Python", field="title")
        self.assertEqual(len(results), 2)

        results = self.bm.search("Beazley", field="author")
        self.assertEqual(len(results), 1)

    def test_search_books_no_results(self):
        """Test searching with no matching results."""
        self.bm.add(title="Book A")
        results = self.bm.search("nonexistent")
        self.assertEqual(len(results), 0)

    def test_get_book(self):
        """Test getting a single book by ID."""
        book_id = self.bm.add(title="Test Book", author="Test Author")
        book = self.bm.get(book_id)
        self.assertIsNotNone(book)
        self.assertEqual(book["title"], "Test Book")

    def test_get_book_not_found(self):
        """Test getting a non-existent book."""
        book = self.bm.get(9999)
        self.assertIsNone(book)

    def test_get_by_isbn(self):
        """Test getting a book by ISBN."""
        self.bm.add(title="Test Book", isbn="1234567890")
        book = self.bm.get_by_isbn("1234567890")
        self.assertIsNotNone(book)
        self.assertEqual(book["title"], "Test Book")

    def test_update_book(self):
        """Test updating a book."""
        book_id = self.bm.add(title="Old Title", author="Old Author")
        result = self.bm.update(book_id, title="New Title", author="New Author")
        self.assertTrue(result)

        book = self.bm.get(book_id)
        self.assertEqual(book["title"], "New Title")
        self.assertEqual(book["author"], "New Author")

    def test_update_book_status(self):
        """Test updating book status."""
        book_id = self.bm.add(title="Test Book")
        self.bm.update(book_id, status="reading")
        book = self.bm.get(book_id)
        self.assertEqual(book["status"], "reading")

    def test_update_book_invalid_status(self):
        """Test that invalid status raises ValueError."""
        book_id = self.bm.add(title="Test Book")
        with self.assertRaises(ValueError):
            self.bm.update(book_id, status="invalid_status")

    def test_update_book_not_found(self):
        """Test updating a non-existent book."""
        result = self.bm.update(9999, title="New Title")
        self.assertFalse(result)

    def test_update_book_tags(self):
        """Test updating book tags."""
        book_id = self.bm.add(title="Test Book", tags=["old"])
        self.bm.update(book_id, tags=["new1", "new2"])
        book = self.bm.get(book_id)
        tags = json.loads(book["tags"])
        self.assertEqual(tags, ["new1", "new2"])

    def test_remove_book(self):
        """Test removing a book."""
        book_id = self.bm.add(title="To Be Removed")
        result = self.bm.remove(book_id)
        self.assertTrue(result)
        self.assertIsNone(self.bm.get(book_id))

    def test_remove_book_not_found(self):
        """Test removing a non-existent book."""
        result = self.bm.remove(9999)
        self.assertFalse(result)

    def test_stats(self):
        """Test library statistics."""
        self.bm.add(title="Book A", category="Fiction", tags=["fiction"])
        self.bm.add(title="Book B", category="Non-Fiction", tags=["non-fiction"])
        self.bm.add(title="Book C", category="Fiction", tags=["fiction", "classic"])

        stats = self.bm.stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_status"]["unread"], 3)
        self.assertEqual(stats["by_category"]["Fiction"], 2)
        self.assertEqual(stats["by_category"]["Non-Fiction"], 1)
        self.assertEqual(stats["tags"]["fiction"], 2)
        self.assertEqual(stats["tags"]["classic"], 1)

    def test_import_from_json(self):
        """Test importing books from a JSON file."""
        data = {
            "books": [
                {
                    "title": "Imported Book 1",
                    "author": "Author 1",
                    "isbn": "1111111111",
                    "category": "Fiction",
                    "tags": ["test"],
                },
                {
                    "title": "Imported Book 2",
                    "author": "Author 2",
                    "isbn": "2222222222",
                    "category": "Non-Fiction",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            filepath = f.name

        try:
            count = self.bm.import_books(filepath, fmt="json")
            self.assertEqual(count, 2)

            books, total = self.bm.list()
            self.assertEqual(total, 2)
        finally:
            os.unlink(filepath)

    def test_import_from_csv(self):
        """Test importing books from a CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "title", "author", "isbn", "category", "page_count", "rating"
            ])
            writer.writeheader()
            writer.writerow({
                "title": "CSV Book 1",
                "author": "Author 1",
                "isbn": "3333333333",
                "category": "Fiction",
                "page_count": 200,
                "rating": 4.5,
            })
            filepath = f.name

        try:
            count = self.bm.import_books(filepath, fmt="csv")
            self.assertEqual(count, 1)

            books, total = self.bm.list()
            self.assertEqual(total, 1)
            self.assertEqual(books[0]["title"], "CSV Book 1")
        finally:
            os.unlink(filepath)

    def test_export_to_json(self):
        """Test exporting books to a JSON file."""
        self.bm.add(title="Export Test", author="Author")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            self.bm.export_books(filepath, fmt="json")
            with open(filepath, "r") as f:
                data = json.load(f)
            self.assertIn("books", data)
            self.assertEqual(len(data["books"]), 1)
            self.assertEqual(data["books"][0]["title"], "Export Test")
        finally:
            os.unlink(filepath)

    def test_export_to_csv(self):
        """Test exporting books to a CSV file."""
        self.bm.add(title="Export Test", author="Author", isbn="4444444444")

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            filepath = f.name

        try:
            self.bm.export_books(filepath, fmt="csv")
            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["title"], "Export Test")
        finally:
            os.unlink(filepath)

    def test_add_book_with_rating(self):
        """Test adding a book with a rating."""
        book_id = self.bm.add(title="Rated Book", rating=4.5)
        book = self.bm.get(book_id)
        self.assertEqual(book["rating"], 4.5)

    def test_add_book_minimal(self):
        """Test adding a book with only required fields."""
        book_id = self.bm.add(title="Minimal Book")
        book = self.bm.get(book_id)
        self.assertEqual(book["title"], "Minimal Book")
        self.assertEqual(book["author"], "")
        self.assertEqual(book["status"], "unread")


if __name__ == "__main__":
    unittest.main()
