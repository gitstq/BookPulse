"""
BookPulse - Terminal UI Module
Provides colorful output, table rendering, progress bars, and interactive selection
using only ANSI escape codes (no external dependencies).
"""

import os
import sys
import shutil


# ── ANSI Color Codes ──────────────────────────────────────────────────────────

class Color:
    """ANSI color and style constants."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def supports_color():
    """Check if the terminal supports color output."""
    if os.getenv("NO_COLOR"):
        return False
    if os.getenv("TERM") in ("dumb", ""):
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            return kernel32.GetConsoleMode(kernel32.GetStdHandle(-11)) & 0x0004
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# Global flag to disable color output
ENABLE_COLOR = supports_color()


def style(text, *styles):
    """Apply ANSI styles to text. Automatically strips if color is disabled."""
    if not ENABLE_COLOR:
        return text
    return "".join(styles) + text + Color.RESET


def bold(text):
    """Return bold text."""
    return style(text, Color.BOLD)


def dim(text):
    """Return dimmed text."""
    return style(text, Color.DIM)


def red(text):
    """Return red text."""
    return style(text, Color.RED)


def green(text):
    """Return green text."""
    return style(text, Color.GREEN)


def yellow(text):
    """Return yellow text."""
    return style(text, Color.YELLOW)


def blue(text):
    """Return blue text."""
    return style(text, Color.BLUE)


def magenta(text):
    """Return magenta text."""
    return style(text, Color.MAGENTA)


def cyan(text):
    """Return cyan text."""
    return style(text, Color.CYAN)


def white(text):
    """Return white text."""
    return style(text, Color.WHITE)


def gray(text):
    """Return gray text."""
    return style(text, Color.GRAY)


def underline(text):
    """Return underlined text."""
    return style(text, Color.UNDERLINE)


def colored(text, color_name):
    """Return text in the specified color by name."""
    color_map = {
        "red": Color.RED,
        "green": Color.GREEN,
        "yellow": Color.YELLOW,
        "blue": Color.BLUE,
        "magenta": Color.MAGENTA,
        "cyan": Color.CYAN,
        "white": Color.WHITE,
        "gray": Color.GRAY,
        "black": Color.BLACK,
    }
    code = color_map.get(color_name.lower(), Color.WHITE)
    return style(text, code)


# ── Status Color Helpers ──────────────────────────────────────────────────────

def status_color(status):
    """Return colored status text based on book status."""
    status_styles = {
        "unread": (Color.CYAN, "Unread"),
        "reading": (Color.GREEN, "Reading"),
        "finished": (Color.BLUE, "Finished"),
        "dropped": (Color.RED, "Dropped"),
    }
    code, label = status_styles.get(status.lower(), (Color.WHITE, status))
    return style(label, code)


def rating_stars(rating):
    """Return a star rating string like '★★★★☆'."""
    if rating is None:
        return gray("N/A")
    rating = max(0, min(5, rating))
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    empty = 5 - full - half
    stars = "\u2605" * full + "\u00BD" * half + "\u2606" * empty
    return style(stars, Color.YELLOW)


# ── Progress Bar ──────────────────────────────────────────────────────────────

def progress_bar(percentage, width=30, fill_char="\u2588", empty_char="\u2591"):
    """Render a terminal progress bar.

    Args:
        percentage: Float between 0 and 100.
        width: The character width of the bar.
        fill_char: Character for filled portion.
        empty_char: Character for empty portion.

    Returns:
        A string representation of the progress bar with percentage.
    """
    percentage = max(0.0, min(100.0, percentage))
    filled = int(width * percentage / 100)
    empty = width - filled

    if percentage >= 100:
        bar_color = Color.GREEN
    elif percentage >= 50:
        bar_color = Color.YELLOW
    else:
        bar_color = Color.CYAN

    bar = fill_char * filled + empty_char * empty
    if ENABLE_COLOR:
        return f"{bar_color}{bar}{Color.RESET} {bold(f'{percentage:.1f}%')}"
    return f"{bar} {percentage:.1f}%"


# ── Table Rendering ───────────────────────────────────────────────────────────

def render_table(headers, rows, title=None, max_col_width=40):
    """Render a formatted table in the terminal.

    Args:
        headers: List of column header strings.
        rows: List of lists, each inner list is a row of values.
        title: Optional title displayed above the table.
        max_col_width: Maximum width for any column.

    Returns:
        A formatted string representation of the table.
    """
    if not rows:
        if title:
            return f"\n  {bold(title)}\n  {dim('No data to display.')}\n"
        return dim("No data to display.")

    # Convert all values to strings
    str_rows = [[str(cell) if cell is not None else "" for cell in row] for row in rows]

    # Truncate long values
    str_rows = [
        [cell[:max_col_width - 3] + "..." if len(cell) > max_col_width else cell for cell in row]
        for row in str_rows
    ]

    # Calculate column widths
    col_count = len(headers)
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < col_count:
                widths[i] = max(widths[i], len(cell))

    # Build separator line
    def separator(char="-"):
        parts = []
        for w in widths:
            parts.append(char * (w + 2))
        return "+" + "+".join(parts) + "+"

    # Build format string
    def format_row(values, is_header=False):
        parts = []
        for i, val in enumerate(values):
            if i < col_count:
                parts.append(f" {val:<{widths[i]}} ")
        return "|" + "|".join(parts) + "|"

    lines = []

    if title:
        lines.append(f"\n  {bold(cyan(title))}")

    lines.append(separator())
    lines.append(format_row(headers))
    lines.append(separator("="))

    for row in str_rows:
        # Pad row if it has fewer columns than headers
        padded = row + [""] * (col_count - len(row))
        lines.append(format_row(padded[:col_count]))

    lines.append(separator())

    # Add row count
    lines.append(dim(f"  Total: {len(rows)} row(s)"))

    return "\n".join(lines)


# ── Box / Panel Rendering ─────────────────────────────────────────────────────

def render_panel(title, content_lines, border_color=None):
    """Render a bordered panel with a title.

    Args:
        title: Panel title string.
        content_lines: List of strings for the panel content.
        border_color: ANSI color code for the border (default: cyan).

    Returns:
        A formatted string representation of the panel.
    """
    if border_color is None:
        border_color = Color.CYAN

    if not content_lines:
        content_lines = ["(empty)"]

    inner_width = max(len(line) for line in content_lines)
    title_len = len(title) + 4  # " title "
    box_width = max(inner_width + 4, title_len)

    lines = []
    # Top border with title
    top = "\u2500" * box_width
    if ENABLE_COLOR:
        lines.append(f"{border_color}\u250c{top}\u2510{Color.RESET}")
    else:
        lines.append(f"+{top}+")

    # Title line
    title_line = f" {title} "
    padding = box_width - len(title_line) - 2
    left_pad = padding // 2
    right_pad = padding - left_pad
    title_str = "\u2502" + " " * left_pad + title_line + " " * right_pad + "\u2502"
    if ENABLE_COLOR:
        lines.append(f"{border_color}{bold(title_str)}{Color.RESET}")
    else:
        lines.append(f"|{title_str}|")

    # Separator
    sep = "\u2500" * box_width
    if ENABLE_COLOR:
        lines.append(f"{border_color}\u251c{sep}\u2524{Color.RESET}")
    else:
        lines.append(f"+{sep}+")

    # Content lines
    for line in content_lines:
        pad = box_width - len(line) - 2
        content_str = f"\u2502 {line}{' ' * pad}\u2502"
        if ENABLE_COLOR:
            lines.append(f"{border_color}{content_str}{Color.RESET}")
        else:
            lines.append(f"| {line}{' ' * pad}|")

    # Bottom border
    if ENABLE_COLOR:
        lines.append(f"{border_color}\u2514{top}\u2518{Color.RESET}")
    else:
        lines.append(f"+{top}+")

    return "\n".join(lines)


# ── Interactive Selection ─────────────────────────────────────────────────────

def select_from_list(items, prompt="Select an item", display_func=None):
    """Display a numbered list and let the user select an item.

    Args:
        items: List of items to choose from.
        prompt: Prompt text shown to the user.
        display_func: Optional function to format each item for display.
                      If None, str(item) is used.

    Returns:
        The selected item, or None if the user cancels.
    """
    if not items:
        print(yellow("No items available."))
        return None

    if display_func is None:
        display_func = str

    print(f"\n  {bold(prompt)}")
    print(dim("  Enter number to select, or 'q' to cancel.\n"))

    for i, item in enumerate(items, 1):
        print(f"  {cyan(f'[{i}]')} {display_func(item)}")

    while True:
        try:
            choice = input(f"\n  {green('>')} ").strip()
            if choice.lower() == "q":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
            print(yellow(f"  Please enter a number between 1 and {len(items)}."))
        except (ValueError, EOFError):
            print(yellow("  Invalid input. Please enter a number or 'q'."))


def confirm(prompt="Are you sure?", default=False):
    """Ask the user a yes/no question.

    Args:
        prompt: The question to ask.
        default: Default value if user presses Enter.

    Returns:
        True for yes, False for no.
    """
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"  {prompt} {hint} ").strip().lower()
    except EOFError:
        return default

    if not answer:
        return default
    return answer in ("y", "yes")


def prompt_input(prompt, default=None):
    """Prompt the user for input with an optional default value.

    Args:
        prompt: The prompt text.
        default: Default value if user presses Enter.

    Returns:
        The user's input, or the default value.
    """
    if default is not None:
        hint = f" [{default}]"
    else:
        hint = ""
    try:
        answer = input(f"  {prompt}{hint}: ").strip()
    except EOFError:
        return default
    if not answer and default is not None:
        return default
    return answer


# ── Misc Output Helpers ───────────────────────────────────────────────────────

_CHECK = "\u2713"
_CROSS = "\u2717"
_WARN = "\u26A0"
_INFO = "\u2139"


def print_success(msg):
    """Print a success message."""
    print(f"  {green(_CHECK)} {msg}")


def print_error(msg):
    """Print an error message."""
    print(f"  {red(_CROSS)} {msg}", file=sys.stderr)


def print_warning(msg):
    """Print a warning message."""
    print(f"  {yellow(_WARN)} {msg}")


def print_info(msg):
    """Print an info message."""
    print(f"  {blue(_INFO)} {msg}")


_DASH = "\u2500"


def print_header(title):
    """Print a section header."""
    term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    print(f"\n  {bold(cyan(title))}")
    sep = _DASH * min(len(title), term_width - 4)
    print(f"  {cyan(sep)}")


def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def get_terminal_width():
    """Get the current terminal width."""
    return shutil.get_terminal_size(fallback=(80, 24)).columns
