from __future__ import annotations

import io
import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

    try:
        if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if isinstance(sys.stderr, io.TextIOWrapper) and sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class C:
    """ANSI color escape codes for vibrant terminal logging."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground standard
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Backgrounds
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


def cyan(text: str) -> str:
    return f"{C.BRIGHT_CYAN}{text}{C.RESET}"

def green(text: str) -> str:
    return f"{C.BRIGHT_GREEN}{text}{C.RESET}"

def yellow(text: str) -> str:
    return f"{C.BRIGHT_YELLOW}{text}{C.RESET}"

def red(text: str) -> str:
    return f"{C.BRIGHT_RED}{text}{C.RESET}"

def magenta(text: str) -> str:
    return f"{C.BRIGHT_MAGENTA}{text}{C.RESET}"

def blue(text: str) -> str:
    return f"{C.BRIGHT_BLUE}{text}{C.RESET}"

def dim(text: str) -> str:
    return f"{C.DIM}{text}{C.RESET}"

def bold(text: str) -> str:
    return f"{C.BOLD}{text}{C.RESET}"

def header(text: str) -> str:
    return f"{C.BOLD}{C.BRIGHT_CYAN}{text}{C.RESET}"
