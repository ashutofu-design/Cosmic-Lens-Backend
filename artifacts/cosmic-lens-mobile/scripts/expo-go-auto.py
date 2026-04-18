#!/usr/bin/env python3
"""
Wrapper around `expo start --go` that auto-answers the
"Log in / Proceed anonymously" prompt by sending DOWN+ENTER
the first time it appears. Required because the prompt has no
non-interactive bypass flag.
"""
import os
import pty
import sys
import select
import errno

PORT = os.environ.get("PORT", "18987")
CMD = [
    "/bin/bash", "-lc",
    f"pnpm exec expo start --go --lan --port {PORT} --clear",
]

answered = False


def main() -> int:
    global answered
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(CMD[0], CMD)
        os._exit(127)

    buf = b""
    try:
        while True:
            try:
                r, _, _ = select.select([fd], [], [], 1.0)
            except (InterruptedError, OSError):
                continue
            if fd in r:
                try:
                    chunk = os.read(fd, 4096)
                except OSError as e:
                    if e.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                buf += chunk
                if not answered and b"Proceed anonymously" in buf:
                    # DOWN arrow then ENTER → selects "Proceed anonymously"
                    os.write(fd, b"\x1b[B\r")
                    answered = True
                    buf = b""
                # keep buffer bounded
                if len(buf) > 16384:
                    buf = buf[-4096:]
    finally:
        try:
            _, status = os.waitpid(pid, 0)
            return os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1
        except ChildProcessError:
            return 0


if __name__ == "__main__":
    sys.exit(main())
