"""
BookPulse - Storage Module
SQLite database management with auto-backup, data import/export, and migration.
"""

import os
import json
import sqlite3
import shutil
import datetime
from contextlib import contextmanager


# Default database file path
DEFAULT_DB_PATH = os.path.expanduser("~/.bookpulse/bookpulse.db")
DEFAULT_BACKUP_DIR = os.path.expanduser("~/.bookpulse/backups")


class Storage:
    """Manages the SQLite database for BookPulse."""

    def __init__(self, db_path=None):
        """Initialize storage with the given database path.

        Args:
            db_path: Path to the SQLite database file. Defaults to ~/.bookpulse/bookpulse.db.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.backup_dir = DEFAULT_BACKUP_DIR
        self._ensure_dirs()
        self._init_schema()

    def _ensure_dirs(self):
        """Ensure database and backup directories exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Provide a database connection as a context manager.

        Yields a sqlite3.Connection with row factory enabled.
        Automatically commits on success, rolls back on error.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Create all database tables if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isbn TEXT UNIQUE,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL DEFAULT '',
                    publisher TEXT DEFAULT '',
                    publish_year INTEGER,
                    category TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    cover_path TEXT DEFAULT '',
                    rating REAL,
                    page_count INTEGER,
                    current_page INTEGER DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'unread'
                        CHECK(status IN ('unread', 'reading', 'finished', 'dropped')),
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS reading_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    action TEXT NOT NULL
                        CHECK(action IN ('start', 'progress', 'finish', 'note')),
                    page INTEGER,
                    percentage REAL,
                    note TEXT DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS booklists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS booklist_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    booklist_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    added_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (booklist_id) REFERENCES booklists(id) ON DELETE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                    UNIQUE(booklist_id, book_id)
                );

                CREATE TABLE IF NOT EXISTS reading_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_type TEXT NOT NULL CHECK(goal_type IN ('yearly', 'monthly')),
                    target_count INTEGER NOT NULL DEFAULT 12,
                    period TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
                CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
                CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
                CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
                CREATE INDEX IF NOT EXISTS idx_reading_logs_book_id ON reading_logs(book_id);
                CREATE INDEX IF NOT EXISTS idx_reading_logs_action ON reading_logs(action);
                CREATE INDEX IF NOT EXISTS idx_reading_logs_created_at ON reading_logs(created_at);
                CREATE INDEX IF NOT EXISTS idx_booklist_items_booklist_id ON booklist_items(booklist_id);
                CREATE INDEX IF NOT EXISTS idx_booklist_items_book_id ON booklist_items(book_id);
            """)

            # Initialize default booklists if they don't exist
            default_lists = ["Want to Read", "Currently Reading", "Finished"]
            for name in default_lists:
                conn.execute(
                    "INSERT OR IGNORE INTO booklists (name, description) VALUES (?, ?)",
                    (name, f"Default booklist: {name}")
                )

            # Initialize default config
            defaults = {
                "version": "1.0.0",
                "default_view": "table",
                "page_size": "20",
            }
            for key, value in defaults.items():
                conn.execute(
                    "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
                    (key, value)
                )

    # ── Config Management ─────────────────────────────────────────────────

    def get_config(self, key, default=None):
        """Get a configuration value by key.

        Args:
            key: The config key.
            default: Default value if key is not found.

        Returns:
            The config value as a string, or the default.
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM config WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_config(self, key, value):
        """Set a configuration value.

        Args:
            key: The config key.
            value: The config value.
        """
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, str(value))
            )

    # ── Backup ────────────────────────────────────────────────────────────

    def backup(self, backup_name=None):
        """Create a backup of the database.

        Args:
            backup_name: Optional custom name for the backup file.

        Returns:
            The path to the created backup file.
        """
        if backup_name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"bookpulse_backup_{timestamp}.db"

        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def list_backups(self):
        """List all available backup files.

        Returns:
            A list of backup file paths sorted by modification time (newest first).
        """
        if not os.path.isdir(self.backup_dir):
            return []
        backups = [
            os.path.join(self.backup_dir, f)
            for f in os.listdir(self.backup_dir)
            if f.endswith(".db")
        ]
        backups.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return backups

    def restore_backup(self, backup_path):
        """Restore the database from a backup file.

        Args:
            backup_path: Path to the backup file.

        Raises:
            FileNotFoundError: If the backup file does not exist.
        """
        if not os.path.isfile(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        shutil.copy2(backup_path, self.db_path)

    # ── Data Export ────────────────────────────────────────────────────────

    def export_all_data(self):
        """Export all data from the database as a dictionary.

        Returns:
            A dictionary containing all tables' data.
        """
        data = {}
        tables = ["books", "reading_logs", "booklists", "booklist_items", "reading_goals", "config"]
        with self.get_connection() as conn:
            for table in tables:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                data[table] = [dict(row) for row in rows]
        return data

    def export_to_json(self, filepath):
        """Export all data to a JSON file.

        Args:
            filepath: Path to the output JSON file.
        """
        data = self.export_all_data()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_to_csv(self, filepath):
        """Export books table to a CSV file.

        Args:
            filepath: Path to the output CSV file.
        """
        import csv
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM books").fetchall()
            if not rows:
                return
            columns = rows[0].keys()
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

    # ── Data Import ────────────────────────────────────────────────────────

    def import_from_json(self, filepath):
        """Import data from a JSON file.

        Args:
            filepath: Path to the input JSON file.

        Returns:
            The number of books imported.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported = 0
        with self.get_connection() as conn:
            if "books" in data:
                for book in data["books"]:
                    try:
                        tags = book.get("tags", "[]")
                        if isinstance(tags, list):
                            tags = json.dumps(tags)
                        conn.execute("""
                            INSERT OR IGNORE INTO books
                            (isbn, title, author, publisher, publish_year, category,
                             tags, cover_path, rating, page_count, current_page, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            book.get("isbn"),
                            book.get("title", "Unknown"),
                            book.get("author", "Unknown"),
                            book.get("publisher", ""),
                            book.get("publish_year"),
                            book.get("category", ""),
                            tags,
                            book.get("cover_path", ""),
                            book.get("rating"),
                            book.get("page_count"),
                            book.get("current_page", 0),
                            book.get("status", "unread"),
                        ))
                        imported += 1
                    except sqlite3.IntegrityError:
                        continue
        return imported

    def import_from_csv(self, filepath):
        """Import books from a CSV file.

        Args:
            filepath: Path to the input CSV file.

        Returns:
            The number of books imported.
        """
        import csv
        imported = 0
        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            with self.get_connection() as conn:
                for row in reader:
                    try:
                        tags = row.get("tags", "[]")
                        if isinstance(tags, str):
                            try:
                                json.loads(tags)
                            except (json.JSONDecodeError, TypeError):
                                tags = json.dumps([t.strip() for t in tags.split(",") if t.strip()])
                        conn.execute("""
                            INSERT OR IGNORE INTO books
                            (isbn, title, author, publisher, publish_year, category,
                             tags, cover_path, rating, page_count, current_page, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get("isbn", ""),
                            row.get("title", "Unknown"),
                            row.get("author", "Unknown"),
                            row.get("publisher", ""),
                            _safe_int(row.get("publish_year")),
                            row.get("category", ""),
                            tags,
                            row.get("cover_path", ""),
                            _safe_float(row.get("rating")),
                            _safe_int(row.get("page_count")),
                            _safe_int(row.get("current_page", 0)),
                            row.get("status", "unread"),
                        ))
                        imported += 1
                    except sqlite3.IntegrityError:
                        continue
        return imported

    # ── Database Info ──────────────────────────────────────────────────────

    def db_stats(self):
        """Get database statistics.

        Returns:
            A dictionary with table row counts and database file size.
        """
        stats = {}
        tables = ["books", "reading_logs", "booklists", "booklist_items", "reading_goals"]
        with self.get_connection() as conn:
            for table in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count

        if os.path.isfile(self.db_path):
            stats["db_size_bytes"] = os.path.getsize(self.db_path)
            stats["db_size_human"] = _human_readable_size(stats["db_size_bytes"])
        else:
            stats["db_size_bytes"] = 0
            stats["db_size_human"] = "0 B"

        return stats

    def vacuum(self):
        """Vacuum the database to reclaim unused space."""
        with self.get_connection() as conn:
            conn.execute("VACUUM")


# ── Utility Functions ─────────────────────────────────────────────────────────

def _safe_int(value):
    """Safely convert a value to integer."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _safe_float(value):
    """Safely convert a value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _human_readable_size(size_bytes):
    """Convert bytes to a human-readable size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
