"""
BookPulse - CLI Entry Point
Unified CLI with subcommand routing and configuration management.
"""

import argparse
import sys
import os


def create_parser():
    """Create and configure the argument parser with all subcommands.

    Returns:
        A configured argparse.ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="bookpulse",
        description="BookPulse - Lightweight personal book management and reading tracker CLI",
        epilog="Use 'bookpulse <command> --help' for detailed help on each command.",
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help="Path to the SQLite database file (default: ~/.bookpulse/bookpulse.db)"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version="BookPulse v1.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── Book Commands ──────────────────────────────────────────────────────
    book_parser = subparsers.add_parser("book", help="Book management commands")
    book_sub = book_parser.add_subparsers(dest="action", help="Book actions")

    # book add
    add_p = book_sub.add_parser("add", help="Add a new book")
    add_p.add_argument("--title", "-t", type=str, required=True, help="Book title")
    add_p.add_argument("--author", "-a", type=str, default="", help="Author name")
    add_p.add_argument("--isbn", type=str, default="", help="ISBN")
    add_p.add_argument("--publisher", type=str, default="", help="Publisher")
    add_p.add_argument("--year", type=int, default=None, help="Publication year")
    add_p.add_argument("--category", "-c", type=str, default="", help="Category/genre")
    add_p.add_argument("--tags", type=str, default="", help="Tags (comma-separated)")
    add_p.add_argument("--cover", type=str, default="", help="Path to cover image")
    add_p.add_argument("--rating", type=float, default=None, help="Rating (0-5)")
    add_p.add_argument("--pages", type=int, default=None, help="Total page count")

    # book list
    list_p = book_sub.add_parser("list", help="List all books")
    list_p.add_argument("--status", "-s", type=str, default=None,
                        choices=["unread", "reading", "finished", "dropped"],
                        help="Filter by status")
    list_p.add_argument("--category", type=str, default=None, help="Filter by category")
    list_p.add_argument("--author", type=str, default=None, help="Filter by author")
    list_p.add_argument("--sort", type=str, default="created_at",
                        help="Sort by field (title, author, rating, created_at)")
    list_p.add_argument("--order", type=str, default="desc", choices=["asc", "desc"],
                        help="Sort order")
    list_p.add_argument("--page", type=int, default=1, help="Page number")
    list_p.add_argument("--limit", type=int, default=20, help="Items per page")

    # book search
    search_p = book_sub.add_parser("search", help="Search books")
    search_p.add_argument("query", type=str, help="Search query")
    search_p.add_argument("--field", "-f", type=str, default="all",
                          choices=["all", "title", "author", "isbn", "tags"],
                          help="Field to search in")

    # book remove
    remove_p = book_sub.add_parser("remove", help="Remove a book")
    remove_p.add_argument("book_id", type=int, help="Book ID to remove")
    remove_p.add_argument("--force", "-f", action="store_true",
                          help="Skip confirmation")

    # book update
    update_p = book_sub.add_parser("update", help="Update book information")
    update_p.add_argument("book_id", type=int, help="Book ID to update")
    update_p.add_argument("--title", type=str, default=None, help="New title")
    update_p.add_argument("--author", type=str, default=None, help="New author")
    update_p.add_argument("--isbn", type=str, default=None, help="New ISBN")
    update_p.add_argument("--publisher", type=str, default=None, help="New publisher")
    update_p.add_argument("--year", type=int, default=None, help="New publication year")
    update_p.add_argument("--category", type=str, default=None, help="New category")
    update_p.add_argument("--tags", type=str, default=None, help="New tags (comma-separated)")
    update_p.add_argument("--rating", type=float, default=None, help="New rating (0-5)")
    update_p.add_argument("--pages", type=int, default=None, help="New page count")
    update_p.add_argument("--status", type=str, default=None,
                          choices=["unread", "reading", "finished", "dropped"],
                          help="New status")

    # book import
    import_p = book_sub.add_parser("import", help="Import books from file")
    import_p.add_argument("filepath", type=str, help="Path to import file (CSV or JSON)")
    import_p.add_argument("--format", "-f", type=str, default="auto",
                          choices=["auto", "csv", "json"], help="File format")

    # book export
    export_p = book_sub.add_parser("export", help="Export books to file")
    export_p.add_argument("filepath", type=str, help="Path to output file (CSV or JSON)")
    export_p.add_argument("--format", "-f", type=str, default="auto",
                          choices=["auto", "csv", "json"], help="File format")

    # book stats
    book_sub.add_parser("stats", help="Show library statistics")

    # ── Read Commands ──────────────────────────────────────────────────────
    read_parser = subparsers.add_parser("read", help="Reading tracker commands")
    read_sub = read_parser.add_subparsers(dest="action", help="Reading actions")

    # read start
    start_p = read_sub.add_parser("start", help="Start reading a book")
    start_p.add_argument("book_id", type=int, help="Book ID to start reading")

    # read progress
    progress_p = read_sub.add_parser("progress", help="Update reading progress")
    progress_p.add_argument("book_id", type=int, help="Book ID")
    progress_p.add_argument("--page", "-p", type=int, default=None, help="Current page")
    progress_p.add_argument("--percent", type=float, default=None, help="Progress percentage")

    # read finish
    finish_p = read_sub.add_parser("finish", help="Mark book as finished")
    finish_p.add_argument("book_id", type=int, help="Book ID to finish")

    # read note
    note_p = read_sub.add_parser("note", help="Add a reading note")
    note_p.add_argument("book_id", type=int, help="Book ID")
    note_p.add_argument("--text", "-t", type=str, default="", help="Note text")

    # read history
    history_p = read_sub.add_parser("history", help="View reading history")
    history_p.add_argument("--book", "-b", type=int, default=None, help="Filter by book ID")
    history_p.add_argument("--filter-action", type=str, default=None,
                           choices=["start", "progress", "finish", "note"],
                           help="Filter by action type")
    history_p.add_argument("--limit", type=int, default=20, help="Number of entries")

    # read current
    read_sub.add_parser("current", help="Show currently reading books")

    # read streak
    read_sub.add_parser("streak", help="Show reading streak statistics")

    # ── Analytics Commands ─────────────────────────────────────────────────
    analytics_parser = subparsers.add_parser("analytics", help="Analytics and statistics")
    analytics_sub = analytics_parser.add_subparsers(dest="action", help="Analytics actions")

    # analytics summary
    analytics_sub.add_parser("summary", help="Show reading summary")

    # analytics chart
    chart_p = analytics_sub.add_parser("chart", help="Show terminal charts")
    chart_p.add_argument("--type", "-t", type=str, default="monthly",
                         choices=["monthly", "category", "status"],
                         help="Chart type")
    chart_p.add_argument("--months", type=int, default=12, help="Months for monthly chart")

    # analytics goal
    goal_p = analytics_sub.add_parser("goal", help="Reading goals")
    goal_p.add_argument("goal_action", nargs="?", default="show",
                        choices=["set", "show"],
                        help="Goal action (set or show)")
    goal_p.add_argument("--type", "-t", type=str, default="yearly",
                        choices=["yearly", "monthly"], help="Goal type")
    goal_p.add_argument("--target", type=int, default=None, help="Target book count")
    goal_p.add_argument("--period", type=str, default=None, help="Goal period (e.g., 2025, 2025-06)")

    # analytics report
    analytics_sub.add_parser("report", help="Generate reading report")

    # analytics ranking
    rank_p = analytics_sub.add_parser("ranking", help="Book rankings")
    rank_p.add_argument("--sort", "-s", type=str, default="rating",
                        choices=["rating", "pages", "recent"],
                        help="Sort by criterion")
    rank_p.add_argument("--limit", type=int, default=20, help="Number of books")

    # ── Booklist Commands ──────────────────────────────────────────────────
    bl_parser = subparsers.add_parser("booklist", help="Booklist management")
    bl_sub = bl_parser.add_subparsers(dest="action", help="Booklist actions")

    # booklist create
    bl_create = bl_sub.add_parser("create", help="Create a booklist")
    bl_create.add_argument("name", type=str, help="Booklist name")
    bl_create.add_argument("--desc", "-d", type=str, default="", help="Description")

    # booklist list
    bl_sub.add_parser("list", help="List all booklists")

    # booklist show
    bl_show = bl_sub.add_parser("show", help="Show booklist contents")
    bl_show.add_argument("name", type=str, nargs="?", default=None, help="Booklist name")
    bl_show.add_argument("--id", type=int, default=None, help="Booklist ID")

    # booklist add
    bl_add = bl_sub.add_parser("add", help="Add a book to a booklist")
    bl_add.add_argument("booklist_name", type=str, help="Booklist name")
    bl_add.add_argument("book_id", type=int, help="Book ID to add")

    # booklist remove
    bl_rm = bl_sub.add_parser("remove", help="Remove a book from a booklist")
    bl_rm.add_argument("booklist_name", type=str, help="Booklist name")
    bl_rm.add_argument("book_id", type=int, help="Book ID to remove")

    # booklist delete
    bl_del = bl_sub.add_parser("delete", help="Delete a booklist")
    bl_del.add_argument("name", type=str, help="Booklist name")

    # ── Data Management Commands ───────────────────────────────────────────
    data_parser = subparsers.add_parser("data", help="Data management")
    data_sub = data_parser.add_subparsers(dest="action", help="Data actions")

    # data backup
    data_sub.add_parser("backup", help="Create a database backup")

    # data restore
    data_restore = data_sub.add_parser("restore", help="Restore from backup")
    data_restore.add_argument("backup_path", type=str, help="Path to backup file")

    # data info
    data_sub.add_parser("info", help="Show database info")

    # data vacuum
    data_sub.add_parser("vacuum", help="Vacuum database")

    return parser


def main(args=None):
    """Main entry point for the BookPulse CLI.

    Args:
        args: Command-line arguments (defaults to sys.argv).
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    # Handle --no-color
    if parsed.no_color:
        from . import ui
        ui.ENABLE_COLOR = False

    # If no command given, show help
    if not parsed.command:
        parser.print_help()
        return 0

    # Import modules after parsing to keep startup fast
    from .storage import Storage
    from .books import BookManager
    from .tracker import ReadingTracker
    from .analytics import Analytics
    from .booklist import BooklistManager
    from . import ui

    # Initialize storage
    storage = Storage(db_path=parsed.db)

    try:
        # ── Book Commands ──────────────────────────────────────────────────
        if parsed.command == "book":
            bm = BookManager(storage)

            if parsed.action == "add":
                tags = [t.strip() for t in parsed.tags.split(",") if t.strip()] if parsed.tags else []
                book_id = bm.add(
                    title=parsed.title,
                    author=parsed.author,
                    isbn=parsed.isbn,
                    publisher=parsed.publisher,
                    publish_year=parsed.year,
                    category=parsed.category,
                    tags=tags,
                    cover_path=parsed.cover,
                    rating=parsed.rating,
                    page_count=parsed.pages,
                )
                ui.print_success(f"Book added successfully (ID: {book_id})")

            elif parsed.action == "list":
                books, total = bm.list(
                    status=parsed.status,
                    category=parsed.category,
                    author=parsed.author,
                    sort_by=parsed.sort,
                    sort_order=parsed.order,
                    page=parsed.page,
                    page_size=parsed.limit,
                )
                bm.display_list(books)
                total_pages = (total + parsed.limit - 1) // parsed.limit
                if total_pages > 1:
                    ui.print_info(f"Page {parsed.page} of {total_pages} ({total} total books)")

            elif parsed.action == "search":
                results = bm.search(parsed.query, field=parsed.field)
                bm.display_list(results)
                ui.print_info(f"Found {len(results)} result(s) for '{parsed.query}'")

            elif parsed.action == "remove":
                book = bm.get(parsed.book_id)
                if not book:
                    ui.print_error(f"Book with ID {parsed.book_id} not found.")
                    return 1
                if not parsed.force:
                    if not ui.confirm(f"Remove '{book['title']}'?"):
                        ui.print_info("Cancelled.")
                        return 0
                if bm.remove(parsed.book_id):
                    ui.print_success(f"Book '{book['title']}' removed.")
                else:
                    ui.print_error("Failed to remove book.")

            elif parsed.action == "update":
                updates = {}
                if parsed.title is not None:
                    updates["title"] = parsed.title
                if parsed.author is not None:
                    updates["author"] = parsed.author
                if parsed.isbn is not None:
                    updates["isbn"] = parsed.isbn
                if parsed.publisher is not None:
                    updates["publisher"] = parsed.publisher
                if parsed.year is not None:
                    updates["publish_year"] = parsed.year
                if parsed.category is not None:
                    updates["category"] = parsed.category
                if parsed.tags is not None:
                    updates["tags"] = [t.strip() for t in parsed.tags.split(",") if t.strip()]
                if parsed.rating is not None:
                    updates["rating"] = parsed.rating
                if parsed.pages is not None:
                    updates["page_count"] = parsed.pages
                if parsed.status is not None:
                    updates["status"] = parsed.status

                if not updates:
                    ui.print_warning("No fields to update. Use --title, --author, etc.")
                    return 1

                if bm.update(parsed.book_id, **updates):
                    ui.print_success(f"Book ID {parsed.book_id} updated.")
                else:
                    ui.print_error(f"Book with ID {parsed.book_id} not found.")
                    return 1

            elif parsed.action == "import":
                count = bm.import_books(parsed.filepath, fmt=parsed.format)
                ui.print_success(f"Imported {count} book(s) from {parsed.filepath}")

            elif parsed.action == "export":
                bm.export_books(parsed.filepath, fmt=parsed.format)
                ui.print_success(f"Books exported to {parsed.filepath}")

            elif parsed.action == "stats":
                bm.display_stats()

            else:
                book_parser.print_help()

        # ── Read Commands ──────────────────────────────────────────────────
        elif parsed.command == "read":
            tracker = ReadingTracker(storage)

            if parsed.action == "start":
                tracker.start(parsed.book_id)
                ui.print_success(f"Started reading book ID {parsed.book_id}")

            elif parsed.action == "progress":
                result = tracker.progress(
                    parsed.book_id,
                    page=parsed.page,
                    percentage=parsed.percent,
                )
                pct = result.get("percentage", 0)
                ui.print_success(
                    f"Progress updated: {result['title']} - "
                    f"Page {result['page']}/{result['page_count']} ({pct}%)"
                )
                print(f"  {ui.progress_bar(pct)}")

            elif parsed.action == "finish":
                tracker.finish(parsed.book_id)
                ui.print_success(f"Finished reading book ID {parsed.book_id}")

            elif parsed.action == "note":
                note_text = parsed.text
                if not note_text:
                    note_text = ui.prompt_input("Enter your note")
                if not note_text:
                    ui.print_warning("No note text provided.")
                    return 1
                tracker.log_note(parsed.book_id, note_text)
                ui.print_success(f"Note added for book ID {parsed.book_id}")

            elif parsed.action == "history":
                logs = tracker.history(
                    book_id=parsed.book,
                    action=parsed.filter_action,
                    limit=parsed.limit,
                )
                tracker.display_history(logs)

            elif parsed.action == "current":
                tracker.display_current()

            elif parsed.action == "streak":
                tracker.display_streak()

            else:
                read_parser.print_help()

        # ── Analytics Commands ─────────────────────────────────────────────
        elif parsed.command == "analytics":
            analytics = Analytics(storage)

            if parsed.action == "summary":
                analytics.display_summary()

            elif parsed.action == "chart":
                if parsed.type == "monthly":
                    analytics.chart_monthly(months=parsed.months)
                elif parsed.type == "category":
                    analytics.chart_category_distribution()
                elif parsed.type == "status":
                    analytics.chart_status_distribution()

            elif parsed.action == "goal":
                if parsed.goal_action == "set":
                    if not parsed.target:
                        ui.print_error("Please specify --target for the goal.")
                        return 1
                    analytics.set_goal(parsed.type, parsed.target, parsed.period)
                    ui.print_success(
                        f"Goal set: {parsed.target} books ({parsed.type}, "
                        f"period: {parsed.period or 'current'})"
                    )
                else:
                    analytics.display_goals()

            elif parsed.action == "report":
                analytics.display_report()

            elif parsed.action == "ranking":
                analytics.display_ranking(sort_by=parsed.sort, limit=parsed.limit)

            else:
                analytics_parser.print_help()

        # ── Booklist Commands ──────────────────────────────────────────────
        elif parsed.command == "booklist":
            blm = BooklistManager(storage)

            if parsed.action == "create":
                blm.create(parsed.name, description=parsed.desc)
                ui.print_success(f"Booklist '{parsed.name}' created.")

            elif parsed.action == "list":
                blm.display_list()

            elif parsed.action == "show":
                bl_id = parsed.id
                bl_name = parsed.name
                blm.display_booklist(booklist_id=bl_id, name=bl_name)

            elif parsed.action == "add":
                bl = blm.get(name=parsed.booklist_name)
                if not bl:
                    ui.print_error(f"Booklist '{parsed.booklist_name}' not found.")
                    return 1
                blm.add_book(bl["id"], parsed.book_id)
                ui.print_success(
                    f"Book ID {parsed.book_id} added to '{parsed.booklist_name}'"
                )

            elif parsed.action == "remove":
                bl = blm.get(name=parsed.booklist_name)
                if not bl:
                    ui.print_error(f"Booklist '{parsed.booklist_name}' not found.")
                    return 1
                if blm.remove_book(bl["id"], parsed.book_id):
                    ui.print_success(
                        f"Book ID {parsed.book_id} removed from '{parsed.booklist_name}'"
                    )
                else:
                    ui.print_warning("Book was not in the booklist.")

            elif parsed.action == "delete":
                bl = blm.get(name=parsed.name)
                if not bl:
                    ui.print_error(f"Booklist '{parsed.name}' not found.")
                    return 1
                if ui.confirm(f"Delete booklist '{parsed.name}'?"):
                    blm.delete(bl["id"])
                    ui.print_success(f"Booklist '{parsed.name}' deleted.")
                else:
                    ui.print_info("Cancelled.")

            else:
                bl_parser.print_help()

        # ── Data Commands ──────────────────────────────────────────────────
        elif parsed.command == "data":
            if parsed.action == "backup":
                path = storage.backup()
                ui.print_success(f"Backup created: {path}")

            elif parsed.action == "restore":
                if not os.path.isfile(parsed.backup_path):
                    ui.print_error(f"Backup file not found: {parsed.backup_path}")
                    return 1
                if ui.confirm("Restore database from backup? Current data will be replaced."):
                    storage.restore_backup(parsed.backup_path)
                    ui.print_success("Database restored successfully.")
                else:
                    ui.print_info("Cancelled.")

            elif parsed.action == "info":
                stats = storage.db_stats()
                lines = [
                    f"Database Path:  {storage.db_path}",
                    f"Database Size:  {stats.get('db_size_human', 'N/A')}",
                    f"Books:          {stats.get('books', 0)}",
                    f"Reading Logs:   {stats.get('reading_logs', 0)}",
                    f"Booklists:      {stats.get('booklists', 0)}",
                    f"Booklist Items: {stats.get('booklist_items', 0)}",
                    f"Reading Goals:  {stats.get('reading_goals', 0)}",
                ]
                print(ui.render_panel("Database Info", lines))

            elif parsed.action == "vacuum":
                storage.vacuum()
                ui.print_success("Database vacuumed.")

            else:
                data_parser.print_help()

        else:
            parser.print_help()

    except ValueError as e:
        ui.print_error(str(e))
        return 1
    except FileNotFoundError as e:
        ui.print_error(str(e))
        return 1
    except KeyboardInterrupt:
        print()
        ui.print_info("Operation cancelled.")
        return 130
    except Exception as e:
        ui.print_error(f"Unexpected error: {e}")
        return 1

    return 0
