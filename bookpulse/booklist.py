"""
BookPulse - Booklist Module
Manage custom booklists: create, add/remove books, show lists.
"""

import datetime
from .storage import Storage
from . import ui


class BooklistManager:
    """Manages custom booklists for organizing books."""

    def __init__(self, storage=None):
        """Initialize with a Storage instance.

        Args:
            storage: A Storage instance. If None, creates a default one.
        """
        self.storage = storage or Storage()

    # ── Create Booklist ────────────────────────────────────────────────────

    def create(self, name, description=""):
        """Create a new booklist.

        Args:
            name: Name of the booklist (must be unique).
            description: Optional description.

        Returns:
            The ID of the created booklist.

        Raises:
            ValueError: If a booklist with the same name already exists.
        """
        if not name or not name.strip():
            raise ValueError("Booklist name is required.")

        with self.storage.get_connection() as conn:
            try:
                cursor = conn.execute("""
                    INSERT INTO booklists (name, description)
                    VALUES (?, ?)
                """, (name.strip(), description.strip()))
                return cursor.lastrowid
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"Booklist '{name}' already exists.") from e
                raise

    # ── List Booklists ─────────────────────────────────────────────────────

    def list(self):
        """Get all booklists.

        Returns:
            A list of booklist dictionaries with item counts.
        """
        with self.storage.get_connection() as conn:
            rows = conn.execute("""
                SELECT bl.*,
                    (SELECT COUNT(*) FROM booklist_items WHERE booklist_id = bl.id) as item_count
                FROM booklists bl
                ORDER BY bl.created_at ASC
            """).fetchall()
            return [dict(row) for row in rows]

    # ── Get Booklist ───────────────────────────────────────────────────────

    def get(self, booklist_id=None, name=None):
        """Get a booklist by ID or name.

        Args:
            booklist_id: The booklist's primary key ID.
            name: The booklist name.

        Returns:
            A dictionary representing the booklist, or None if not found.
        """
        with self.storage.get_connection() as conn:
            if booklist_id:
                row = conn.execute(
                    "SELECT * FROM booklists WHERE id = ?", (booklist_id,)
                ).fetchone()
            elif name:
                row = conn.execute(
                    "SELECT * FROM booklists WHERE name = ?", (name,)
                ).fetchone()
            else:
                return None
            return dict(row) if row else None

    # ── Add Book to Booklist ───────────────────────────────────────────────

    def add_book(self, booklist_id, book_id):
        """Add a book to a booklist.

        Args:
            booklist_id: The booklist's primary key ID.
            book_id: The book's primary key ID.

        Returns:
            True if the book was added successfully.

        Raises:
            ValueError: If the booklist or book is not found.
        """
        with self.storage.get_connection() as conn:
            # Verify booklist exists
            bl = conn.execute(
                "SELECT id FROM booklists WHERE id = ?", (booklist_id,)
            ).fetchone()
            if not bl:
                raise ValueError(f"Booklist with ID {booklist_id} not found.")

            # Verify book exists
            book = conn.execute(
                "SELECT id FROM books WHERE id = ?", (book_id,)
            ).fetchone()
            if not book:
                raise ValueError(f"Book with ID {book_id} not found.")

            try:
                conn.execute("""
                    INSERT INTO booklist_items (booklist_id, book_id)
                    VALUES (?, ?)
                """, (booklist_id, book_id))
                return True
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    # Book is already in the list, which is fine
                    return True
                raise

    # ── Remove Book from Booklist ──────────────────────────────────────────

    def remove_book(self, booklist_id, book_id):
        """Remove a book from a booklist.

        Args:
            booklist_id: The booklist's primary key ID.
            book_id: The book's primary key ID.

        Returns:
            True if the book was removed, False if it was not in the list.
        """
        with self.storage.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM booklist_items
                WHERE booklist_id = ? AND book_id = ?
            """, (booklist_id, book_id))
            return cursor.rowcount > 0

    # ── Show Booklist Contents ─────────────────────────────────────────────

    def show(self, booklist_id=None, name=None):
        """Get all books in a booklist.

        Args:
            booklist_id: The booklist's primary key ID.
            name: The booklist name (used if booklist_id is None).

        Returns:
            A tuple of (booklist_info, books_list) where booklist_info is a
            dictionary of the booklist metadata and books_list is a list of
            book dictionaries.
        """
        if name and not booklist_id:
            bl = self.get(name=name)
            if bl:
                booklist_id = bl["id"]
            else:
                return None, []

        if not booklist_id:
            return None, []

        with self.storage.get_connection() as conn:
            bl = conn.execute(
                "SELECT * FROM booklists WHERE id = ?", (booklist_id,)
            ).fetchone()

            if not bl:
                return None, []

            rows = conn.execute("""
                SELECT b.*, bi.added_at
                FROM books b
                JOIN booklist_items bi ON b.id = bi.book_id
                WHERE bi.booklist_id = ?
                ORDER BY bi.added_at DESC
            """, (booklist_id,)).fetchall()

            return dict(bl), [dict(row) for row in rows]

    # ── Delete Booklist ────────────────────────────────────────────────────

    def delete(self, booklist_id):
        """Delete a booklist.

        Args:
            booklist_id: The booklist's primary key ID.

        Returns:
            True if the booklist was deleted, False if not found.
        """
        with self.storage.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM booklists WHERE id = ?", (booklist_id,)
            )
            return cursor.rowcount > 0

    # ── Rename Booklist ────────────────────────────────────────────────────

    def rename(self, booklist_id, new_name):
        """Rename a booklist.

        Args:
            booklist_id: The booklist's primary key ID.
            new_name: The new name.

        Returns:
            True if renamed successfully.
        """
        with self.storage.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE booklists SET name = ? WHERE id = ?",
                (new_name.strip(), booklist_id)
            )
            return cursor.rowcount > 0

    # ── Display Helpers ────────────────────────────────────────────────────

    def display_list(self):
        """Display all booklists."""
        booklists = self.list()

        if not booklists:
            ui.print_info("No booklists found.")
            return

        headers = ["#", "Name", "Description", "Books", "Created"]
        rows = []
        for i, bl in enumerate(booklists, 1):
            desc = bl.get("description", "") or "-"
            if len(desc) > 30:
                desc = desc[:27] + "..."
            rows.append([
                str(i),
                ui.bold(bl["name"]),
                desc,
                str(bl["item_count"]),
                bl.get("created_at", "")[:10],
            ])

        print(ui.render_table(headers, rows, title="Booklists"))

    def display_booklist(self, booklist_id=None, name=None):
        """Display the contents of a booklist.

        Args:
            booklist_id: The booklist ID.
            name: The booklist name.
        """
        bl_info, books = self.show(booklist_id=booklist_id, name=name)

        if bl_info is None:
            ui.print_warning("Booklist not found.")
            return

        title = f"Booklist: {bl_info['name']}"
        if bl_info.get("description"):
            title += f" - {bl_info['description']}"

        if not books:
            ui.print_info(f"Booklist '{bl_info['name']}' is empty.")
            return

        headers = ["#", "Title", "Author", "Status", "Rating", "Added"]
        rows = []
        for i, book in enumerate(books, 1):
            rows.append([
                str(i),
                book.get("title", ""),
                book.get("author", ""),
                ui.status_color(book.get("status", "unread")),
                ui.rating_stars(book.get("rating")),
                book.get("added_at", "")[:10],
            ])

        print(ui.render_table(headers, rows, title=title))
