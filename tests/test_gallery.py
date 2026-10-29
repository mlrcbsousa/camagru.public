import io
import os
import tempfile
import unittest
from typing import cast
from urllib.parse import urlencode
from wsgiref.types import StartResponse, WSGIEnvironment

from app.server import application
from app.store import (
    confirm_user,
    connect,
    find_user,
    gallery_rows,
    insert_picture,
    insert_user,
    like_once,
)


class GalleryTest(unittest.TestCase):
    database: str

    def setUp(self) -> None:
        handle, self.database = tempfile.mkstemp(suffix=".sqlite3")
        os.close(handle)
        os.environ["DATABASE_PATH"] = self.database
        os.environ["CAMAGRU_SECRET"] = "test-secret"

    def tearDown(self) -> None:
        if os.path.exists(self.database):
            os.remove(self.database)

    def test_page_is_five_newest_then_id(self) -> None:
        conn = connect()
        user_id = insert_user(conn, "ada", "ada@example.com", "Password1")

        if user_id is None:
            raise AssertionError("ada")

        for stamp in (10, 10, 9, 8, 7, 6):
            insert_picture(conn, user_id, b"png", stamp)

        first = gallery_rows(conn, 1, 5)
        second = gallery_rows(conn, 2, 5)
        conn.close()

        self.assertEqual([item["id"] for item in first], [2, 1, 3, 4, 5])
        self.assertEqual([item["id"] for item in second], [6])

    def test_past_the_last_page_returns_no_rows(self) -> None:
        conn = connect()
        user_id = insert_user(conn, "ada", "ada@example.com", "Password1")

        if user_id is None:
            raise AssertionError("ada")

        insert_picture(conn, user_id, b"png", 1)
        rows = gallery_rows(conn, 3, 5)
        conn.close()

        self.assertEqual(rows, [])

    def test_second_like_does_not_insert(self) -> None:
        conn = connect()
        user_id = insert_user(conn, "ada", "ada@example.com", "Password1")

        if user_id is None:
            raise AssertionError("ada")

        picture_id = insert_picture(conn, user_id, b"png", 1)

        if picture_id is None:
            raise AssertionError("picture")

        like_once(conn, user_id, picture_id)
        like_once(conn, user_id, picture_id)
        rows = gallery_rows(conn, 1, 5)
        conn.close()

        self.assertEqual(rows[0]["likes"], 1)


class GalleryRouteTest(unittest.TestCase):
    database: str

    def setUp(self) -> None:
        handle, self.database = tempfile.mkstemp(suffix=".sqlite3")
        os.close(handle)
        os.environ["DATABASE_PATH"] = self.database
        os.environ["CAMAGRU_SECRET"] = "test-secret"
        os.environ["CAMAGRU_SMTP_PORT"] = "1"
        self._post("/signup", {
            "username": "ada",
            "email": "ada@example.com",
            "password": "Password1",
        })
        conn = connect()
        user = find_user(conn, "ada")

        if user is None:
            raise AssertionError("ada")

        confirm_user(conn, user["id"])
        conn.close()
        _, headers, _ = self._post("/login", {"username": "ada", "password": "Password1"})
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        _, _, editor = self._call("GET", "/editor", cookie)
        csrf = editor.split('name="csrf" value="')[1].split('"', 1)[0]
        self.cookie = cookie
        self.csrf = csrf

    def tearDown(self) -> None:
        if os.path.exists(self.database):
            os.remove(self.database)

    def test_a_page_past_the_end_redirects_to_the_last_page(self) -> None:
        self._post("/editor", {"use_sample": "1", "csrf": self.csrf}, self.cookie)
        status, headers, _ = self._call("GET", "/?page=23")

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/")

        for _ in range(5):
            self._post("/editor", {"use_sample": "1", "csrf": self.csrf}, self.cookie)

        status, headers, _ = self._call("GET", "/?page=23&notice=nomail")
        _, _, page_html = self._call("GET", headers["Location"])

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/?page=2&notice=nomail")
        self.assertIn("the mail was not sent", page_html)
        self.assertIn('data-testid="gallery-previous"', page_html)
        self.assertNotIn('data-testid="gallery-next"', page_html)

    def test_a_fragment_past_the_end_stays_a_fragment(self) -> None:
        self._post("/editor", {"use_sample": "1", "csrf": self.csrf}, self.cookie)
        status, headers, _ = self._call("GET", "/?page=23&fragment=1")
        _, _, fragment = self._call("GET", headers["Location"])

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/?fragment=1")
        self.assertNotIn("<html", fragment)

    def _post(self, path: str, form: dict[str, str], cookie: str = "") -> tuple[str, dict[str, str], str]:
        return self._call("POST", path, cookie, form)

    def _call(
        self,
        method: str,
        path: str,
        cookie: str = "",
        form: dict[str, str] | None = None,
    ) -> tuple[str, dict[str, str], str]:
        body = urlencode(form or {}).encode()
        path, _, query = path.partition("?")
        environ: WSGIEnvironment = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
            "HTTP_COOKIE": cookie,
        }
        status_seen = ""
        headers_seen: dict[str, str] = {}

        def start(status: str, headers: list[tuple[str, str]], exc_info: object = None) -> None:
            nonlocal status_seen, headers_seen
            status_seen = status
            headers_seen = dict(headers)

        text = b"".join(application(environ, cast(StartResponse, start))).decode()

        return status_seen, headers_seen, text
