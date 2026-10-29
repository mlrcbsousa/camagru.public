"""Process entry. `python -m app` runs this file.

`app` is the folder `app/` beside this file's parent. It is a package because
`__init__.py` is in it. `from app.server` loads `app/server.py`.
https://docs.python.org/3/tutorial/modules.html#packages

The long form of the cookie, WSGI, and thread notes is docs/code/01-main.md.
"""

import os
import socketserver
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

from app.server import application
from app.session import server_listens


# socketserver accepts TCP connections. ThreadingMixIn gives each one a thread
# so a slow browser does not block the rest.
# https://docs.python.org/3/library/socketserver.html#socketserver.ThreadingMixIn
class ThreadingServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads: bool = True


# WSGI is the call shape between a Python HTTP server and the app:
# application(environ, start_response). PEP 3333.
# wsgiref is that HTTP adapter. socketserver, above, is the TCP part under it.
# https://docs.python.org/3/library/wsgiref.html#wsgiref.simple_server.WSGIRequestHandler
# https://peps.python.org/pep-3333/
class QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        # The default prints one stderr line per request. Any log line during the defense counts as an error.
        return


def main() -> None:
    """Listen until Ctrl+C. Exit first when CAMAGRU_SECRET is empty.

    The login cookie is an HMAC signed with that secret. An empty key is public,
    so anyone could write a cookie that says they are a given user.
    https://docs.python.org/3/library/hmac.html#hmac.new
    https://docs.python.org/3/library/os.html#os.environ
    """
    secret = os.environ.get("CAMAGRU_SECRET", "")

    if not server_listens(secret):
        # https://docs.python.org/3/library/exceptions.html#SystemExit
        raise SystemExit(1)

    host = os.environ.get("CAMAGRU_BIND", "0.0.0.0")
    port = int(os.environ.get("CAMAGRU_PORT", "8765"))
    server = ThreadingServer((host, port), QuietHandler)
    server.set_app(application)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # Ctrl+C. https://docs.python.org/3/library/exceptions.html#KeyboardInterrupt
        return


if __name__ == "__main__":
    main()
