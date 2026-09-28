"""Non-blocking single-key reader for Windows and POSIX terminals."""

import sys

if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty


class KeyReader:
    """Context manager; `read()` returns a pressed key or None without blocking."""

    def __init__(self) -> None:
        self._saved = None
        self._tty = sys.stdin.isatty()

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

    def read(self) -> str | None:
        if not self._tty:
            return None
        if sys.platform == "win32":
            return msvcrt.getwch() if msvcrt.kbhit() else None
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None
