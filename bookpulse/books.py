"""
BookPulse - Books Module
Book management: add, list, search, remove, update, import/export, stats.
"""

import json
import datetime
from .storage import Storage
from . import ui


class BookManager:
    """Manages book CRUD operations and queries."""

    def __init__(self, storage=None):
        """Initialize with a Storage instance.

        Args:
            storage: A Storage instance. If None, creates a default one.
        """
        self.storage = storage or Storage()

    # ── Add Book ───────────────────────────────────────────────────────────

    def add(self, title, author="", isbn="", publisher="", publish_year=None,
            category="", tags=None, cover_path="", rating=None, page_count=None):
        """Add a new book to the library.

        Args:
            title: Book title (required).
            author: Author name.
            isbn: ISBN string.
            publisher: Publisher name.
            publish_year: Publication year (integer).
            category: Book category/genre.
            tags: List of tag strings.
            cover_path: Path to cover image.
            rating: Rating from 0 to 5.
            page_count: Total number of pages.

        Returns:
            The ID of the newly added book.

        Raises:
            ValueError: If title is empty or ISBN already exists.
        """
        if not title or not title.strip():
            raise ValueError("Book title is required.")

        tags_json = json.dumps(tags if tags else [])

        with self.storage.get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO books
                    (isbn, title, author, publisher, publish_year, category,
                     tags, cover_path, rating, page_count, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'unread')
                """, (
                    isbn or None,
                    title.strip(),
                    author.strip(),
                    publisher.strip(),
                    publish_year,
                    category.strip(),
                    tags_json,
                    cover_path.strip(),
                    rating,
                    page_count,
                ))
                return cursor.lastrowid
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"A book with ISBN '{isbn}' already exists.") from e
                raise

    # ── List Books ─────────────────────────────────────────────────────────

    def list(self, status=None, category=None, author=None, sort_by="created_at",
             sort_order="desc", page=1, page_size=20):
        """List books with optional filtering, sorting, and pagination.

        Args:
            status: Filter by status (unread/reading/finished/dropped).
            category: Filter by category.
            author: Filter by author (partial match).
            sort_by: Column to sort by (title, author, rating, created_at, updated_at).
            sort_order: 'asc' or 'desc'.
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            A tuple of (books_list, total_count) where books_list is a list
            of dictionaries and total_count is the total number of matching books.
        """
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        if author:
            conditions.append("author LIKE ?")
            params.append(f"%{author}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Validate sort column
        valid_sorts = {"title", "author", "rating", "created_at", "updated_at",
                       "page_count", "status", "category"}
        if sort_by not in valid_sorts:
            sort_by = "created_at"
        if sort_order.lower() not in ("asc", "desc"):
            sort_order = "desc"

        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"

        with self.storage.get_connection() as conn:
            # Get total count
            count_row = conn.execute(
                f"SELECT COUNT(*) FROM books {where_clause}", params
            ).fetchone()
            total = count_row[0]

            # Get paginated results
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM books {where_clause} {order_clause} LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()

            books = [dict(row) for row in rows]
            return books, total

    # ── Search Books ───────────────────────────────────────────────────────

    def search(self, query, field="all"):
        """Search books by a query string.

        Args:
            query: The search query string.
            field: The field to search in. One of 'all', 'title', 'author',
                   'isbn', 'tags'. Defaults to 'all'.

        Returns:
            A list of matching book dictionaries.
        """
        query = query.strip()
        if not query:
            return []

        conditions = []
        params = []

        if field in ("all", "title"):
            conditions.append("title LIKE ?")
            params.append(f"%{query}%")
        if field in ("all", "author"):
            conditions.append("author LIKE ?")
            params.append(f"%{query}%")
        if field in ("all", "isbn"):
            conditions.append("isbn LIKE ?")
            params.append(f"%{query}%")
        if field in ("all", "tags"):
            conditions.append("tags LIKE ?")
            params.append(f"%{query}%")

        where_clause = "WHERE " + " OR ".join(conditions)

        with self.storage.get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM books {where_clause} ORDER BY title ASC", params
            ).fetchall()
            return [dict(row) for row in rows]

    # ── Get Book ───────────────────────────────────────────────────────────

    def get(self, book_id):
        """Get a single book by its ID.

        Args:
            book_id: The book's primary key ID.

        Returns:
            A dictionary representing the book, or None if not found.
        """
        with self.storage.get_connection() as conn:
            row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            return dict(row) if row else None

    def get_by_isbn(self, isbn):
        """Get a single book by ISBN.

        Args:
            isbn: The ISBN string.

        Returns:
            A dictionary representing the book, or None if not found.
        """
        with self.storage.get_connection() as conn:
            row = conn.execute("SELECT * FROM books WHERE isbn = ?", (isbn,)).fetchone()
            return dict(row) if row else None

    # ── Update Book ────────────────────────────────────────────────────────

    def update(self, book_id, **kwargs):
        """Update a book's information.

        Args:
            book_id: The book's primary key ID.
            **kwargs: Fields to update. Valid keys: title, author, isbn, publisher,
                      publish_year, category, tags, cover_path, rating, page_count,
                      current_page, status.

        Returns:
            True if the book was updated, False if not found.

        Raises:
            ValueError: If no valid fields are provided.
        """
        valid_fields = {
            "title", "author", "isbn", "publisher", "publish_year", "category",
            "tags", "cover_path", "rating", "page_count", "current_page", "status"
        }
        valid_statuses = {"unread", "reading", "finished", "dropped"}

        updates = {}
        for key, value in kwargs.items():
            if key not in valid_fields:
                continue
            if key == "tags" and isinstance(value, list):
                value = json.dumps(value)
            if key == "status" and value not in valid_statuses:
                raise ValueError(f"Invalid status '{value}'. Must be one of: {valid_statuses}")
            updates[key] = value

        if not updates:
            raise ValueError("No valid fields to update.")

        updates["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [book_id]

        with self.storage.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE books SET {set_clause} WHERE id = ?", values
            )
            return cursor.rowcount > 0

    # ── Remove Book ────────────────────────────────────────────────────────

    def remove(self, book_id):
        """Remove a book from the library.

        Args:
            book_id: The book's primary key ID.

        Returns:
            True if the book was removed, False if not found.
        """
        with self.storage.get_connection() as conn:
            cursor = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
            return cursor.rowcount > 0

    # ── Import Books ───────────────────────────────────────────────────────

    def import_books(self, filepath, fmt="auto"):
        """Import books from a CSV or JSON file.

        Args:
            filepath: Path to the import file.
            fmt: File format - 'csv', 'json', or 'auto' (detect from extension).

        Returns:
            The number of books successfully imported.
        """
        if fmt == "auto":
            if filepath.lower().endswith(".json"):
                fmt = "json"
            elif filepath.lower().endswith(".csv"):
                fmt = "csv"
            else:
                raise ValueError("Cannot detect file format. Please specify 'csv' or 'json'.")

        if fmt == "json":
            return self.storage.import_from_json(filepath)
        elif fmt == "csv":
            return self.storage.import_from_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    # ── Export Books ───────────────────────────────────────────────────────

    def export_books(self, filepath, fmt="auto"):
        """Export books to a CSV or JSON file.

        Args:
            filepath: Path to the output file.
            fmt: File format - 'csv', 'json', or 'auto'.
        """
        if fmt == "auto":
            if filepath.lower().endswith(".json"):
                fmt = "json"
            elif filepath.lower().endswith(".csv"):
                fmt = "csv"
            else:
                raise ValueError("Cannot detect file format. Please specify 'csv' or 'json'.")

        if fmt == "json":
            self.storage.export_to_json(filepath)
        elif fmt == "csv":
            self.storage.export_to_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    # ── Statistics ─────────────────────────────────────────────────────────

    def stats(self):
        """Get library statistics.

        Returns:
            A dictionary with various statistics:
            - total: Total number of books.
            - by_status: Count of books in each status.
            - by_category: Count of books in each category.
            - tags: Tag frequency dictionary.
            - avg_rating: Average rating across all rated books.
            - total_pages: Total page count of all books.
        """
        with self.storage.get_connection() as conn:
            # Total books
            total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]

            # By status
            status_rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM books GROUP BY status"
            ).fetchall()
            by_status = {row["status"]: row["cnt"] for row in status_rows}

            # By category
            cat_rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM books "
                "WHERE category != '' GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            by_category = {row["category"]: row["cnt"] for row in cat_rows}

            # Tags frequency
            all_books = conn.execute("SELECT tags FROM books").fetchall()
            tag_freq = {}
            for row in all_books:
                try:
                    tags = json.loads(row["tags"]) if row["tags"] else []
                    for tag in tags:
                        tag_freq[tag] = tag_freq.get(tag, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue

            # Average rating
            avg_row = conn.execute(
                "SELECT AVG(rating) as avg FROM books WHERE rating IS NOT NULL"
            ).fetchone()
            avg_rating = round(avg_row["avg"], 2) if avg_row["avg"] else None

            # Total pages
            pages_row = conn.execute(
                "SELECT SUM(page_count) as total FROM books WHERE page_count IS NOT NULL"
            ).fetchone()
            total_pages = pages_row["total"] or 0

            return {
                "total": total,
                "by_status": by_status,
                "by_category": by_category,
                "tags": tag_freq,
                "avg_rating": avg_rating,
                "total_pages": total_pages,
            }

    # ── Display Helpers ────────────────────────────────────────────────────

    def display_list(self, books, show_index=True):
        """Print a formatted table of books to the terminal.

        Args:
            books: List of book dictionaries.
            show_index: Whether to show row numbers.
        """
        if not books:
            ui.print_warning("No books found.")
            return

        headers = ["#", "Title", "Author", "Category", "Status", "Rating", "Progress"]
        rows = []
        for i, book in enumerate(books, 1):
            # Calculate progress percentage
            pct = 0.0
            if book.get("page_count") and book.get("page_count", 0) > 0:
                current = book.get("current_page", 0) or 0
                pct = round(current / book["page_count"] * 100, 1)

            idx = str(i) if show_index else ""
            rows.append([
                idx,
                book.get("title", ""),
                book.get("author", ""),
                book.get("category", "") or "-",
                ui.status_color(book.get("status", "unread")),
                ui.rating_stars(book.get("rating")),
                f"{pct}%",
            ])

        print(ui.render_table(headers, rows, title="Books"))

    def display_stats(self):
        """Print library statistics to the terminal."""
        stats = self.stats()

        lines = [
            f"Total Books:     {ui.bold(str(stats['total']))}",
            f"Total Pages:     {ui.bold(str(stats['total_pages']))}",
            f"Average Rating:  {ui.rating_stars(stats['avg_rating'])}"
            if stats['avg_rating'] else "Average Rating:  N/A",
            "",
            "By Status:",
        ]
        for status, count in stats["by_status"].items():
            lines.append(f"  {ui.status_color(status)}: {count}")

        if stats["by_category"]:
            lines.append("")
            lines.append("By Category:")
            for cat, count in stats["by_category"].items():
                lines.append(f"  {ui.bold(cat)}: {count}")

        if stats["tags"]:
            lines.append("")
            lines.append("Tag Cloud:")
            # Sort tags by frequency and display as weighted text
            sorted_tags = sorted(stats["tags"].items(), key=lambda x: x[1], reverse=True)
            tag_parts = []
            for tag, freq in sorted_tags[:20]:
                tag_parts.append(f"{tag}({freq})")
            lines.append("  " + "  ".join(tag_parts))

        print(ui.render_panel("Library Statistics", lines))
