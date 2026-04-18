#!/usr/bin/env python3
"""
Wrapper around `expo start --go` that auto-answers the
"Log in / Proceed anonymously" prompt EVERY TIME it appears.
Expo CLI re-prompts on every device connect, so we cannot
just answer once.
"""
import os
import pty
import sys
import select
import errno
import time

PORT = os.environ.get("PORT", "18987")
CMD = [
    "/bin/bash", "-lc",
    f"pnpm exec expo start --go --lan --port {PORT} --clear",
]

PROMPT_MARKER = b"Use arrow-keys"


def main() -> int:
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(CMD[0], CMD)
        os._exit(127)

    buf = b""
    last_answer_at = 0.0
    try:
        while True:
            try:
                r, _, _ = select.select([fd], [], [], 1.0)
            except (InterruptedError, OSError):
                continue
            if fd not in r:
                continue
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
            now = time.time()
            # Re-answer every time the prompt re-appears, but rate-limit
            # to once per 1.5s to avoid spamming during prompt re-renders.
            if PROMPT_MARKER in buf and (now - last_answer_at) > 1.5:
                # DOWN arrow then ENTER → "Proceed anonymously"
                os.write(fd, b"\x1b[B\r")
                last_answer_at = now
                buf = b""
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
