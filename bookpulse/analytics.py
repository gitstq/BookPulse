"""
BookPulse - Analytics Module
Reading statistics, charts, goals, reports, and rankings.
"""

import datetime
import json
import math
from collections import defaultdict
from .storage import Storage
from . import ui


class Analytics:
    """Provides reading analytics, charts, goals, and reports."""

    def __init__(self, storage=None):
        """Initialize with a Storage instance.

        Args:
            storage: A Storage instance. If None, creates a default one.
        """
        self.storage = storage or Storage()

    # ── Summary ────────────────────────────────────────────────────────────

    def summary(self):
        """Get a reading overview summary.

        Returns:
            A dictionary with reading statistics:
            - total_books: Total number of books.
            - finished: Number of finished books.
            - reading: Number of books currently being read.
            - unread: Number of unread books.
            - dropped: Number of dropped books.
            - total_pages_read: Estimated total pages read.
            - avg_rating: Average rating of finished books.
            - this_month: Books finished this month.
            - this_year: Books finished this year.
        """
        with self.storage.get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]

            status_rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM books GROUP BY status"
            ).fetchall()
            by_status = {row["status"]: row["cnt"] for row in status_rows}

            # Total pages read (sum of current_page for finished books)
            pages_row = conn.execute(
                "SELECT SUM(current_page) as total FROM books WHERE status = 'finished'"
            ).fetchone()
            total_pages_read = pages_row["total"] or 0

            # Average rating
            avg_row = conn.execute(
                "SELECT AVG(rating) as avg FROM books WHERE rating IS NOT NULL"
            ).fetchone()
            avg_rating = round(avg_row["avg"], 2) if avg_row["avg"] else None

            # This month finished
            this_month = datetime.date.today().strftime("%Y-%m")
            month_row = conn.execute("""
                SELECT COUNT(*) as cnt FROM books
                WHERE status = 'finished'
                AND updated_at LIKE ?
            """, (f"{this_month}%",)).fetchone()

            # This year finished
            this_year = datetime.date.today().strftime("%Y")
            year_row = conn.execute("""
                SELECT COUNT(*) as cnt FROM books
                WHERE status = 'finished'
                AND updated_at LIKE ?
            """, (f"{this_year}%",)).fetchone()

            return {
                "total_books": total,
                "finished": by_status.get("finished", 0),
                "reading": by_status.get("reading", 0),
                "unread": by_status.get("unread", 0),
                "dropped": by_status.get("dropped", 0),
                "total_pages_read": total_pages_read,
                "avg_rating": avg_rating,
                "this_month": month_row["cnt"],
                "this_year": year_row["cnt"],
            }

    # ── Monthly Trend ──────────────────────────────────────────────────────

    def monthly_trend(self, months=12):
        """Get monthly reading trend data.

        Args:
            months: Number of months to look back.

        Returns:
            A list of dictionaries with 'month' and 'count' keys,
            ordered chronologically.
        """
        with self.storage.get_connection() as conn:
            rows = conn.execute("""
                SELECT strftime('%Y-%m', updated_at) as month, COUNT(*) as count
                FROM books
                WHERE status = 'finished' AND updated_at IS NOT NULL
                GROUP BY month
                ORDER BY month DESC
                LIMIT ?
            """, (months,)).fetchall()

            result = [{"month": row["month"], "count": row["count"]} for row in rows]
            result.reverse()
            return result

    # ── Terminal Charts ────────────────────────────────────────────────────

    def chart_monthly(self, months=12):
        """Render a terminal bar chart of monthly reading activity.

        Args:
            months: Number of months to display.
        """
        trend = self.monthly_trend(months)

        if not trend:
            ui.print_info("No reading data to chart.")
            return

        max_count = max(item["count"] for item in trend)
        if max_count == 0:
            max_count = 1

        chart_width = 40

        ui.print_header("Monthly Reading Chart")

        for item in trend:
            bar_len = int(item["count"] / max_count * chart_width)
            bar = "\u2588" * bar_len
            label = item["month"] or "N/A"
            count = item["count"]

            if ui.ENABLE_COLOR:
                if count == max_count:
                    bar = f"{ui.Color.GREEN}{bar}{ui.Color.RESET}"
                elif count >= max_count * 0.5:
                    bar = f"{ui.Color.YELLOW}{bar}{ui.Color.RESET}"
                else:
                    bar = f"{ui.Color.CYAN}{bar}{ui.Color.RESET}"

            print(f"  {ui.dim(label)}  {bar} {ui.bold(str(count))}")

        print()

    def chart_category_distribution(self):
        """Render a text-based category distribution chart."""
        with self.storage.get_connection() as conn:
            rows = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM books
                WHERE category != '' AND category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """).fetchall()

        if not rows:
            ui.print_info("No category data to chart.")
            return

        total = sum(row["count"] for row in rows)

        ui.print_header("Category Distribution")

        for row in rows:
            pct = row["count"] / total * 100 if total > 0 else 0
            bar_len = int(pct / 100 * 30)
            bar = "\u2588" * bar_len
            label = row["category"]
            count = row["count"]

            print(f"  {label:<20} {bar} {count} ({pct:.1f}%)")

        print()

    def chart_status_distribution(self):
        """Render a text-based status distribution chart."""
        with self.storage.get_connection() as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM books
                GROUP BY status
                ORDER BY count DESC
            """).fetchall()

        if not rows:
            ui.print_info("No status data to chart.")
            return

        total = sum(row["count"] for row in rows)

        ui.print_header("Status Distribution")

        for row in rows:
            pct = row["count"] / total * 100 if total > 0 else 0
            bar_len = int(pct / 100 * 30)
            bar = "\u2588" * bar_len
            label = ui.status_color(row["status"])
            count = row["count"]

            print(f"  {label:<20} {bar} {count} ({pct:.1f}%)")

        print()

    # ── Reading Goals ──────────────────────────────────────────────────────

    def set_goal(self, goal_type, target_count, period=None):
        """Set a reading goal.

        Args:
            goal_type: 'yearly' or 'monthly'.
            target_count: Number of books to read.
            period: The goal period (e.g., '2025' for yearly, '2025-06' for monthly).
                    If None, auto-determined from goal_type.

        Returns:
            The ID of the created goal.
        """
        if period is None:
            now = datetime.date.today()
            if goal_type == "yearly":
                period = str(now.year)
            else:
                period = now.strftime("%Y-%m")

        with self.storage.get_connection() as conn:
            # Remove existing goal for the same type and period
            conn.execute(
                "DELETE FROM reading_goals WHERE goal_type = ? AND period = ?",
                (goal_type, period)
            )
            cursor = conn.execute("""
                INSERT INTO reading_goals (goal_type, target_count, period)
                VALUES (?, ?, ?)
            """, (goal_type, target_count, period))
            return cursor.lastrowid

    def get_goal_progress(self, goal_type=None, period=None):
        """Get reading goal progress.

        Args:
            goal_type: 'yearly' or 'monthly'. If None, returns all goals.
            period: The goal period. If None, auto-determined.

        Returns:
            A list of dictionaries with goal info and progress.
        """
        with self.storage.get_connection() as conn:
            if period is None:
                now = datetime.date.today()
                if goal_type == "yearly":
                    period = str(now.year)
                elif goal_type == "monthly":
                    period = now.strftime("%Y-%m")

            conditions = []
            params = []
            if goal_type:
                conditions.append("goal_type = ?")
                params.append(goal_type)
            if period:
                conditions.append("period = ?")
                params.append(period)

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            goals = conn.execute(f"""
                SELECT * FROM reading_goals {where_clause}
                ORDER BY created_at DESC
            """, params).fetchall()

            result = []
            for goal in goals:
                # Count books finished in the goal period
                period_pattern = goal["period"] + "%"
                finished = conn.execute("""
                    SELECT COUNT(*) as cnt FROM books
                    WHERE status = 'finished' AND updated_at LIKE ?
                """, (period_pattern,)).fetchone()["cnt"]

                target = goal["target_count"]
                pct = round(finished / target * 100, 1) if target > 0 else 0

                result.append({
                    "id": goal["id"],
                    "goal_type": goal["goal_type"],
                    "target": target,
                    "finished": finished,
                    "percentage": pct,
                    "period": goal["period"],
                    "remaining": max(0, target - finished),
                })

            return result

    def display_goals(self):
        """Display reading goals with progress bars."""
        goals = self.get_goal_progress()

        if not goals:
            ui.print_info("No reading goals set. Use 'goal set' to create one.")
            return

        ui.print_header("Reading Goals")

        for goal in goals:
            goal_label = f"{goal['goal_type'].capitalize()} Goal ({goal['period']})"
            print(f"\n  {ui.bold(goal_label)}")
            print(f"  {ui.progress_bar(goal['percentage'])}")
            print(f"  {goal['finished']} / {goal['target']} books "
                  f"({goal['remaining']} remaining)")

    # ── Reading Report ─────────────────────────────────────────────────────

    def report(self):
        """Generate a comprehensive reading report.

        Returns:
            A dictionary with detailed reading statistics.
        """
        with self.storage.get_connection() as conn:
            report_data = {}

            # Most active month
            active_months = conn.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
                FROM reading_logs
                GROUP BY month
                ORDER BY count DESC
                LIMIT 5
            """).fetchall()
            report_data["most_active_months"] = [
                {"month": r["month"], "count": r["count"]} for r in active_months
            ]

            # Favorite authors (by number of finished books)
            fav_authors = conn.execute("""
                SELECT author, COUNT(*) as count
                FROM books
                WHERE status = 'finished' AND author != ''
                GROUP BY author
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            report_data["favorite_authors"] = [
                {"author": r["author"], "count": r["count"]} for r in fav_authors
            ]

            # Favorite categories
            fav_categories = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM books
                WHERE status = 'finished' AND category != ''
                GROUP BY category
                ORDER BY count DESC
                LIMIT 10
            """).fetchall()
            report_data["favorite_categories"] = [
                {"category": r["category"], "count": r["count"]} for r in fav_categories
            ]

            # Average reading speed (pages per day for finished books)
            # Estimate: total pages / date range
            speed_row = conn.execute("""
                SELECT
                    SUM(b.page_count) as total_pages,
                    MIN(b.updated_at) as first_finish,
                    MAX(b.updated_at) as last_finish,
                    COUNT(*) as book_count
                FROM books b
                WHERE b.status = 'finished' AND b.page_count IS NOT NULL
            """).fetchone()

            if (speed_row["total_pages"] and speed_row["first_finish"]
                    and speed_row["last_finish"] and speed_row["book_count"] > 1):
                first = datetime.datetime.strptime(
                    speed_row["first_finish"], "%Y-%m-%d %H:%M:%S"
                )
                last = datetime.datetime.strptime(
                    speed_row["last_finish"], "%Y-%m-%d %H:%M:%S"
                )
                days = max(1, (last - first).days)
                report_data["avg_pages_per_day"] = round(
                    speed_row["total_pages"] / days, 1
                )
                report_data["avg_books_per_month"] = round(
                    speed_row["book_count"] / max(1, days / 30), 1
                )
            else:
                report_data["avg_pages_per_day"] = None
                report_data["avg_books_per_month"] = None

            # Longest book
            longest = conn.execute("""
                SELECT title, author, page_count FROM books
                WHERE page_count IS NOT NULL AND status = 'finished'
                ORDER BY page_count DESC LIMIT 1
            """).fetchone()
            report_data["longest_book"] = dict(longest) if longest else None

            # Highest rated
            highest = conn.execute("""
                SELECT title, author, rating FROM books
                WHERE rating IS NOT NULL
                ORDER BY rating DESC LIMIT 5
            """).fetchall()
            report_data["highest_rated"] = [dict(r) for r in highest]

            # Total notes
            notes_count = conn.execute(
                "SELECT COUNT(*) FROM reading_logs WHERE action = 'note'"
            ).fetchone()[0]
            report_data["total_notes"] = notes_count

            return report_data

    def display_report(self):
        """Display the reading report in the terminal."""
        rpt = self.report()
        summ = self.summary()

        lines = [
            f"Total Books:          {ui.bold(str(summ['total_books']))}",
            f"Books Finished:       {ui.bold(str(summ['finished']))}",
            f"Currently Reading:    {ui.bold(str(summ['reading']))}",
            f"Unread:               {ui.bold(str(summ['unread']))}",
            f"Dropped:              {ui.bold(str(summ['dropped']))}",
            f"Total Pages Read:     {ui.bold(str(summ['total_pages_read']))}",
            f"Average Rating:       {ui.rating_stars(summ['avg_rating'])}"
            if summ['avg_rating'] else "Average Rating:       N/A",
            f"Finished This Month:  {ui.bold(str(summ['this_month']))}",
            f"Finished This Year:   {ui.bold(str(summ['this_year']))}",
            f"Total Notes:          {ui.bold(str(rpt['total_notes']))}",
        ]

        if rpt["avg_pages_per_day"]:
            lines.append(f"Avg Pages/Day:        {ui.bold(str(rpt['avg_pages_per_day']))}")
        if rpt["avg_books_per_month"]:
            lines.append(f"Avg Books/Month:      {ui.bold(str(rpt['avg_books_per_month']))}")

        if rpt["longest_book"]:
            lb = rpt["longest_book"]
            lines.append(f"Longest Book:         {lb['title']} ({lb['page_count']} pages)")

        print(ui.render_panel("Reading Report", lines))

        # Favorite authors
        if rpt["favorite_authors"]:
            ui.print_header("Favorite Authors")
            headers = ["Author", "Books"]
            rows = [[a["author"], str(a["count"])] for a in rpt["favorite_authors"]]
            print(ui.render_table(headers, rows))

        # Favorite categories
        if rpt["favorite_categories"]:
            ui.print_header("Favorite Categories")
            headers = ["Category", "Books"]
            rows = [[c["category"], str(c["count"])] for c in rpt["favorite_categories"]]
            print(ui.render_table(headers, rows))

        # Most active months
        if rpt["most_active_months"]:
            ui.print_header("Most Active Months")
            headers = ["Month", "Activities"]
            rows = [[m["month"], str(m["count"])] for m in rpt["most_active_months"]]
            print(ui.render_table(headers, rows))

        # Highest rated
        if rpt["highest_rated"]:
            ui.print_header("Highest Rated Books")
            headers = ["Title", "Author", "Rating"]
            rows = [
                [b["title"], b["author"], ui.rating_stars(b["rating"])]
                for b in rpt["highest_rated"]
            ]
            print(ui.render_table(headers, rows))

    # ── Rankings ───────────────────────────────────────────────────────────

    def ranking(self, sort_by="rating", limit=20):
        """Get book rankings.

        Args:
            sort_by: Sort criterion - 'rating', 'pages', 'recent'.
            limit: Maximum number of books to return.

        Returns:
            A list of book dictionaries sorted by the criterion.
        """
        with self.storage.get_connection() as conn:
            if sort_by == "rating":
                rows = conn.execute("""
                    SELECT * FROM books
                    WHERE rating IS NOT NULL
                    ORDER BY rating DESC, title ASC
                    LIMIT ?
                """, (limit,)).fetchall()
            elif sort_by == "pages":
                rows = conn.execute("""
                    SELECT * FROM books
                    WHERE page_count IS NOT NULL
                    ORDER BY page_count DESC, title ASC
                    LIMIT ?
                """, (limit,)).fetchall()
            elif sort_by == "recent":
                rows = conn.execute("""
                    SELECT * FROM books
                    WHERE status = 'finished'
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM books
                    ORDER BY rating DESC NULLS LAST, title ASC
                    LIMIT ?
                """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    def display_ranking(self, sort_by="rating", limit=20):
        """Display book rankings in the terminal.

        Args:
            sort_by: Sort criterion.
            limit: Maximum number of books.
        """
        books = self.ranking(sort_by, limit)

        if not books:
            ui.print_info("No books to rank.")
            return

        sort_labels = {
            "rating": "By Rating",
            "pages": "By Page Count",
            "recent": "Recently Finished",
        }
        title = f"Book Rankings - {sort_labels.get(sort_by, sort_by)}"

        headers = ["#", "Title", "Author", "Rating", "Pages", "Status"]
        rows = []
        for i, book in enumerate(books, 1):
            medal = ""
            if i == 1:
                medal = "\U0001F947"
            elif i == 2:
                medal = "\U0001F948"
            elif i == 3:
                medal = "\U0001F949"

            rows.append([
                f"{medal} {i}" if medal else str(i),
                book.get("title", ""),
                book.get("author", ""),
                ui.rating_stars(book.get("rating")),
                str(book.get("page_count") or "-"),
                ui.status_color(book.get("status", "unread")),
            ])

        print(ui.render_table(headers, rows, title=title))

    # ── Display Summary ────────────────────────────────────────────────────

    def display_summary(self):
        """Display the reading summary in the terminal."""
        summ = self.summary()

        lines = [
            f"Total Books:          {ui.bold(str(summ['total_books']))}",
            f"Finished:             {ui.green(str(summ['finished']))}",
            f"Reading:              {ui.yellow(str(summ['reading']))}",
            f"Unread:               {ui.cyan(str(summ['unread']))}",
            f"Dropped:              {ui.red(str(summ['dropped']))}",
            f"Pages Read:           {ui.bold(str(summ['total_pages_read']))}",
            f"Avg Rating:           {ui.rating_stars(summ['avg_rating'])}"
            if summ['avg_rating'] else "Avg Rating:           N/A",
            "",
            f"This Month:           {ui.bold(str(summ['this_month']))} finished",
            f"This Year:            {ui.bold(str(summ['this_year']))} finished",
        ]

        print(ui.render_panel("Reading Summary", lines))
