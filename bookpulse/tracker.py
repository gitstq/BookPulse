"""
BookPulse - Reading Tracker Module
Track reading progress: start, progress, finish, notes, history, streaks.
"""

import datetime
from collections import defaultdict
from .storage import Storage
from . import ui


class ReadingTracker:
    """Tracks reading activity and progress for books."""

    def __init__(self, storage=None):
        """Initialize with a Storage instance.

        Args:
            storage: A Storage instance. If None, creates a default one.
        """
        self.storage = storage or Storage()

    # ── Start Reading ──────────────────────────────────────────────────────

    def start(self, book_id):
        """Mark a book as currently being read.

        Args:
            book_id: The book's primary key ID.

        Returns:
            True if successful.

        Raises:
            ValueError: If the book is not found.
        """
        with self.storage.get_connection() as conn:
            book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                raise ValueError(f"Book with ID {book_id} not found.")

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update book status
            conn.execute(
                "UPDATE books SET status = 'reading', current_page = 0, updated_at = ? WHERE id = ?",
                (now, book_id)
            )

            # Log the action
            note_text = f"Started reading '{book['title']}'"
            conn.execute("""
                INSERT INTO reading_logs (book_id, action, page, percentage, note, created_at)
                VALUES (?, 'start', 0, 0, ?, ?)
            """, (book_id, note_text, now))

        return True

    # ── Update Progress ────────────────────────────────────────────────────

    def progress(self, book_id, page=None, percentage=None):
        """Update reading progress for a book.

        Args:
            book_id: The book's primary key ID.
            page: Current page number.
            percentage: Progress percentage (0-100). Used if page is not provided.

        Returns:
            A dictionary with updated progress info.

        Raises:
            ValueError: If the book is not found or not in 'reading' status.
        """
        with self.storage.get_connection() as conn:
            book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                raise ValueError(f"Book with ID {book_id} not found.")
            if book["status"] != "reading":
                raise ValueError(
                    f"Book '{book['title']}' is not currently being read. "
                    f"Status: {book['status']}"
                )

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            page_count = book["page_count"] or 0

            # Calculate percentage from page if not provided
            if percentage is None and page is not None and page_count > 0:
                percentage = round(page / page_count * 100, 1)

            # Calculate page from percentage if not provided
            if page is None and percentage is not None and page_count > 0:
                page = int(page_count * percentage / 100)

            # Clamp values
            if percentage is not None:
                percentage = max(0.0, min(100.0, percentage))
            if page is not None and page_count > 0:
                page = max(0, min(page_count, page))

            # Update book
            conn.execute("""
                UPDATE books SET current_page = ?, updated_at = ? WHERE id = ?
            """, (page, now, book_id))

            # Log the action
            conn.execute("""
                INSERT INTO reading_logs (book_id, action, page, percentage, note, created_at)
                VALUES (?, 'progress', ?, ?, ?, ?)
            """, (book_id, page, percentage, f"Progress: {percentage}%" if percentage else "", now))

            return {
                "book_id": book_id,
                "title": book["title"],
                "page": page,
                "page_count": page_count,
                "percentage": percentage,
            }

    # ── Finish Reading ─────────────────────────────────────────────────────

    def finish(self, book_id):
        """Mark a book as finished reading.

        Args:
            book_id: The book's primary key ID.

        Returns:
            True if successful.

        Raises:
            ValueError: If the book is not found.
        """
        with self.storage.get_connection() as conn:
            book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                raise ValueError(f"Book with ID {book_id} not found.")

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            page_count = book["page_count"] or 0

            # Update book status
            conn.execute("""
                UPDATE books SET status = 'finished', current_page = ?, updated_at = ?
                WHERE id = ?
            """, (page_count, now, book_id))

            # Log the action
            conn.execute("""
                INSERT INTO reading_logs (book_id, action, page, percentage, note, created_at)
                VALUES (?, 'finish', ?, 100, ?, ?)
            """, (book_id, page_count, f"Finished reading '{book['title']}'", now))

        return True

    # ── Add Note ───────────────────────────────────────────────────────────

    def log_note(self, book_id, note):
        """Add a reading note or excerpt for a book.

        Args:
            book_id: The book's primary key ID.
            note: The note text.

        Returns:
            The ID of the created log entry.

        Raises:
            ValueError: If the book is not found.
        """
        if not note or not note.strip():
            raise ValueError("Note text cannot be empty.")

        with self.storage.get_connection() as conn:
            book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if not book:
                raise ValueError(f"Book with ID {book_id} not found.")

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor = conn.execute("""
                INSERT INTO reading_logs (book_id, action, page, percentage, note, created_at)
                VALUES (?, 'note', ?, ?, ?, ?)
            """, (book_id, book["current_page"], None, note.strip(), now))

            return cursor.lastrowid

    # ── Reading History ────────────────────────────────────────────────────

    def history(self, book_id=None, action=None, limit=50, offset=0):
        """Get reading history logs.

        Args:
            book_id: Filter by book ID. If None, show all books.
            action: Filter by action type (start/progress/finish/note).
            limit: Maximum number of entries.
            offset: Number of entries to skip.

        Returns:
            A list of log entry dictionaries.
        """
        conditions = []
        params = []

        if book_id is not None:
            conditions.append("rl.book_id = ?")
            params.append(book_id)
        if action:
            conditions.append("rl.action = ?")
            params.append(action)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with self.storage.get_connection() as conn:
            rows = conn.execute(f"""
                SELECT rl.*, b.title, b.author
                FROM reading_logs rl
                JOIN books b ON rl.book_id = b.id
                {where_clause}
                ORDER BY rl.id DESC
                LIMIT ? OFFSET ?
            """, params + [limit, offset]).fetchall()

            return [dict(row) for row in rows]

    # ── Currently Reading ──────────────────────────────────────────────────

    def current(self):
        """Get all books currently being read.

        Returns:
            A list of book dictionaries with status 'reading'.
        """
        with self.storage.get_connection() as conn:
            rows = conn.execute("""
                SELECT b.*,
                    (SELECT MAX(percentage) FROM reading_logs
                     WHERE book_id = b.id AND percentage IS NOT NULL) as last_percentage,
                    (SELECT MAX(created_at) FROM reading_logs
                     WHERE book_id = b.id) as last_activity
                FROM books b
                WHERE b.status = 'reading'
                ORDER BY b.updated_at DESC
            """).fetchall()

            return [dict(row) for row in rows]

    # ── Reading Streak ─────────────────────────────────────────────────────

    def streak(self):
        """Calculate reading streak statistics.

        Returns:
            A dictionary with:
            - current_streak: Number of consecutive days with reading activity.
            - longest_streak: Longest consecutive reading streak.
            - total_reading_days: Total number of days with reading activity.
            - streak_history: List of date strings for the current streak.
        """
        with self.storage.get_connection() as conn:
            # Get all unique dates with reading activity
            rows = conn.execute("""
                SELECT DISTINCT DATE(created_at) as reading_date
                FROM reading_logs
                ORDER BY reading_date DESC
            """).fetchall()

            if not rows:
                return {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "total_reading_days": 0,
                    "streak_history": [],
                }

            dates = [row["reading_date"] for row in rows]
            total_reading_days = len(dates)

            # Calculate current streak
            current_streak = 0
            streak_history = []
            today = datetime.date.today().strftime("%Y-%m-%d")

            # Check if today or yesterday has activity
            if dates and (dates[0] == today or dates[0] == _yesterday_str()):
                current_streak = 1
                streak_history.append(dates[0])

                for i in range(1, len(dates)):
                    prev = datetime.datetime.strptime(dates[i - 1], "%Y-%m-%d").date()
                    curr = datetime.datetime.strptime(dates[i], "%Y-%m-%d").date()
                    diff = (prev - curr).days
                    if diff == 1:
                        current_streak += 1
                        streak_history.append(dates[i])
                    else:
                        break

            # Calculate longest streak
            longest_streak = 1
            temp_streak = 1
            for i in range(1, len(dates)):
                prev = datetime.datetime.strptime(dates[i - 1], "%Y-%m-%d").date()
                curr = datetime.datetime.strptime(dates[i], "%Y-%m-%d").date()
                diff = (prev - curr).days
                if diff == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1

            if not dates:
                longest_streak = 0

            return {
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "total_reading_days": total_reading_days,
                "streak_history": streak_history,
            }

    # ── Display Helpers ────────────────────────────────────────────────────

    def display_current(self):
        """Display currently reading books with progress bars."""
        books = self.current()

        if not books:
            ui.print_info("You are not currently reading any books.")
            return

        ui.print_header("Currently Reading")

        for book in books:
            page_count = book.get("page_count") or 0
            current_page = book.get("current_page") or 0
            pct = book.get("last_percentage")
            if pct is None and page_count > 0:
                pct = round(current_page / page_count * 100, 1)
            elif pct is None:
                pct = 0.0

            title_str = book['title']
            author_str = book['author']
            print(f"\n  {ui.bold(ui.cyan(title_str))}  {ui.dim('by ' + author_str)}")
            print(f"  {ui.progress_bar(pct)}")
            print(f"  Page {current_page} / {page_count or '?'}")
            if book.get("last_activity"):
                print(f"  Last activity: {ui.dim(book['last_activity'])}")

    def display_history(self, logs):
        """Display reading history logs in a table.

        Args:
            logs: List of log entry dictionaries.
        """
        if not logs:
            ui.print_info("No reading history found.")
            return

        headers = ["Date", "Book", "Action", "Page", "%", "Note"]
        rows = []
        for log in logs:
            action_display = {
                "start": ui.green("Start"),
                "progress": ui.yellow("Progress"),
                "finish": ui.blue("Finish"),
                "note": ui.magenta("Note"),
            }.get(log["action"], log["action"])

            note = log.get("note", "") or ""
            if len(note) > 40:
                note = note[:37] + "..."

            rows.append([
                log.get("created_at", "")[:16],
                log.get("title", ""),
                action_display,
                str(log.get("page", "")),
                f"{log['percentage']}%" if log.get("percentage") is not None else "",
                note,
            ])

        print(ui.render_table(headers, rows, title="Reading History"))

    def display_streak(self):
        """Display reading streak information."""
        streak = self.streak()

        lines = [
            f"Current Streak:     {ui.bold(str(streak['current_streak']))} days",
            f"Longest Streak:     {ui.bold(str(streak['longest_streak']))} days",
            f"Total Reading Days: {ui.bold(str(streak['total_reading_days']))}",
        ]

        if streak["streak_history"]:
            lines.append("")
            lines.append("Recent streak:")
            for date in streak["streak_history"][:7]:
                lines.append(f"  {ui.green(date)}")

        print(ui.render_panel("Reading Streak", lines))


# ── Utility ────────────────────────────────────────────────────────────────────

def _yesterday_str():
    """Return yesterday's date as a YYYY-MM-DD string."""
    return (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
