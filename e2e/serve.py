import html
import json
import os
import re
import socket
import socketserver
import sys
import threading
import time
from email import message_from_bytes
from typing import TypedDict, cast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
os.environ.setdefault("CAMAGRU_SECRET", "e2e-secret")
os.environ.setdefault("CAMAGRU_BASE_URL", "http://127.0.0.1:8765")
os.environ.setdefault("CAMAGRU_SMTP_HOST", "127.0.0.1")
os.environ.setdefault("CAMAGRU_SMTP_PORT", "2525")
os.environ.setdefault("CAMAGRU_BIND", "127.0.0.1")
os.environ.setdefault("CAMAGRU_PORT", "8765")
os.environ.setdefault("DATABASE_PATH", os.path.join(ROOT, "data", "e2e.sqlite3"))
os.environ.setdefault("CAMAGRU_DEBUG", "1")
os.environ.setdefault("CAMAGRU_E2E", "1")


class Recipient(TypedDict):
    Address: str


class MailItem(TypedDict):
    To: list[Recipient]
    Text: str


MESSAGES: list[MailItem] = []
LOCK = threading.Lock()
REFUSE: dict[str, bool] = {"on": False}


class SmtpHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        if REFUSE["on"]:
            REFUSE["on"] = False
            self.wfile.write(b"421 down\r\n")

            return

        self.wfile.write(b"220 catcher\r\n")
        chunks: list[bytes] = []
        reading = False

        while True:
            line = self.rfile.readline()

            if not line:
                break

            if reading:
                if line == b".\r\n":
                    self._store(b"".join(chunks))
                    chunks = []
                    reading = False
                    self.wfile.write(b"250 ok\r\n")
                else:
                    chunks.append(line)
                continue

            if line.upper().startswith(b"DATA"):
                reading = True
                self.wfile.write(b"354 go\r\n")
                continue

            if line.upper().startswith(b"QUIT"):
                self.wfile.write(b"221 bye\r\n")
                break

            self.wfile.write(b"250 ok\r\n")

    def _store(self, raw: bytes) -> None:
        parsed = message_from_bytes(raw)
        body = cast(object, parsed.get_payload())  # pyright: ignore[reportAny]

        if isinstance(body, list):
            part = cast(object, body[0] if body else "")

            if isinstance(part, str):
                body = part
            else:
                read = getattr(part, "get_payload", None)
                nested = read() if callable(read) else ""
                body = nested if isinstance(nested, str) else ""

        item: MailItem = {
            "To": [{"Address": parsed.get("To", "")}],
            "Text": body if isinstance(body, str) else "",
        }

        with LOCK:
            MESSAGES.append(item)


class Quiet:
    def log_message(self, format: str, *args: object) -> None:
        return


class MailHttp(Quiet, socketserver.BaseRequestHandler):
    def _socket(self) -> socket.socket:
        return cast(socket.socket, self.request)  # pyright: ignore[reportAny]

    def handle(self) -> None:
        data = self._socket().recv(65535)
        line = data.split(b"\r\n", 1)[0]

        if line.startswith(b"POST") and b"/api/v1/clear" in line:
            with LOCK:
                MESSAGES.clear()
            self._send(b"application/json", b"{}")

            return

        if line.startswith(b"POST") and b"/api/v1/refuse" in line:
            REFUSE["on"] = True
            self._send(b"application/json", b"{}")

            return

        with LOCK:
            messages = list(MESSAGES)

        if b" / " in line or line.endswith(b" /"):
            self._send(b"text/html; charset=utf-8", _inbox(messages))

            return

        self._send(b"application/json", json.dumps({"messages": messages}).encode())

    def _send(self, kind: bytes, payload: bytes) -> None:
        head = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: " + kind + b"\r\n"
            b"Content-Length: " + str(len(payload)).encode() + b"\r\n"
            b"Connection: close\r\n\r\n"
        )
        self._socket().sendall(head + payload)


def _inbox(messages: list[MailItem]) -> bytes:
    rows: list[str] = []

    for item in reversed(messages):
        to = html.escape(item["To"][0]["Address"])
        text = html.escape(item["Text"])
        linked = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', text)
        rows.append(f"<li><b>{to}</b><pre>{linked}</pre></li>")

    body = "".join(rows) or "<li>No mail yet.</li>"
    page = (
        "<!DOCTYPE html><meta charset=utf-8><title>Inbox</title>"
        "<h1>Inbox</h1><ul>" + body + "</ul>"
    )

    return page.encode()


def _serve(server: socketserver.BaseServer) -> None:
    server.serve_forever()


def _wait(port: int) -> None:
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), 0.2):
                return
        except OSError:
            time.sleep(0.05)

    raise SystemExit("port " + str(port) + " did not open")


def main() -> None:
    sys.path.insert(0, ROOT)
    db = os.environ["DATABASE_PATH"]
    parent = os.path.dirname(db)

    if parent:
        os.makedirs(parent, exist_ok=True)

    if os.path.exists(db):
        os.remove(db)

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    smtp = socketserver.ThreadingTCPServer(("127.0.0.1", 2525), SmtpHandler)
    http = socketserver.ThreadingTCPServer(("127.0.0.1", 8026), MailHttp)
    threading.Thread(target=_serve, args=(smtp,), daemon=True).start()
    threading.Thread(target=_serve, args=(http,), daemon=True).start()
    _wait(2525)
    _wait(8026)

    from app.__main__ import main as serve_app

    serve_app()


if __name__ == "__main__":
    main()
