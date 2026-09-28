"""Non-blocking key reader for Windows and POSIX terminals."""

import os
import sys

if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty

# Arrow-key escape sequences (POSIX terminals send either form)
POSIX_ARROWS = {"\x1b[A": "up", "\x1b[B": "down", "\x1bOA": "up", "\x1bOB": "down"}
WINDOWS_ARROWS = {"H": "up", "P": "down"}  # second char after a \x00 / \xe0 prefix


class KeyReader:
    """Context manager; `read_key()` returns a key without blocking: a character, "up", "down" or None."""

    def __init__(self) -> None:
        self._saved = None
        self._tty = sys.stdin.isatty()
        self._pending = ""  # POSIX: bytes read but not yet returned

    def __enter__(self) -> "KeyReader":
        if self._tty and sys.platform != "win32":
            fd = sys.stdin.fileno()
            self._saved = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        return self

    def __exit__(self, *exc) -> None:
        if self._saved is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._saved)
            self._saved = None

    def read_key(self) -> str | None:
        if not self._tty:
            return None
        if sys.platform == "win32":
            return self._read_windows()
        return self._read_posix()

    def _read_windows(self) -> str | None:
        if not msvcrt.kbhit():
            return None
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):  # special key: the code follows immediately
            return WINDOWS_ARROWS.get(msvcrt.getwch())
        return ch

    def _read_posix(self) -> str | None:
        # Read raw bytes from the fd: sys.stdin's buffer would hide the rest of an
        # escape sequence from select().
        fd = sys.stdin.fileno()
        while select.select([fd], [], [], 0)[0]:
            chunk = os.read(fd, 64)
            if not chunk:
                break
            self._pending += chunk.decode(errors="ignore")
        return self._next_pending()

    def _next_pending(self) -> str | None:
        """Pop one key from the POSIX input buffer, decoding arrow escape sequences."""
        if not self._pending:
            return None
        if self._pending.startswith("\x1b"):
            for seq, name in POSIX_ARROWS.items():
                if self._pending.startswith(seq):
                    self._pending = self._pending[len(seq) :]
                    return name
            # Some other escape sequence (or a lone Esc): drop it.
            end = 3 if self._pending[1:2] in ("[", "O") else 1
            self._pending = self._pending[end:]
            return None
        ch, self._pending = self._pending[0], self._pending[1:]
        return ch
