import io
import os
import tempfile
import unittest
from base64 import b64encode
from typing import TypedDict, cast
from urllib.parse import urlencode
from wsgiref.types import StartResponse, WSGIEnvironment

from app.server import application
from app.store import confirm_user, connect, find_user, list_pictures


class Member(TypedDict):
    cookie: str
    csrf: str


class EditorTest(unittest.TestCase):
    database: str
    ada: Member

    def setUp(self) -> None:
        handle, self.database = tempfile.mkstemp(suffix=".sqlite3")
        os.close(handle)
        os.environ["DATABASE_PATH"] = self.database
        os.environ["CAMAGRU_SECRET"] = "test-secret"
        os.environ["CAMAGRU_SMTP_PORT"] = "1"
        self.ada = self._member("ada")

    def tearDown(self) -> None:
        if os.path.exists(self.database):
            os.remove(self.database)

    def test_save_redirects_so_a_refresh_does_not_save_again(self) -> None:
        status, headers, _ = self._save(self.ada, {"use_sample": "1"})
        _, _, page = self._call("GET", headers["Location"], self.ada["cookie"])

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/editor?notice=picture")
        self.assertIn("Picture saved.", page)
        self.assertEqual(self._count("ada"), 1)

    def test_save_without_a_base_image_stores_nothing(self) -> None:
        status, headers, _ = self._save(self.ada, {})
        _, _, page = self._call("GET", headers["Location"], self.ada["cookie"])

        self.assertEqual(status, "303 See Other")
        self.assertIn("before saving", page)
        self.assertEqual(self._count("ada"), 0)

    def test_a_non_image_upload_stores_nothing(self) -> None:
        _, headers, _ = self._save(self.ada, {"upload_b64": "bm90LWFuLWltYWdl"})
        _, _, page = self._call("GET", headers["Location"], self.ada["cookie"])

        self.assertIn("That file is not an image.", page)
        self.assertEqual(self._count("ada"), 0)

    def test_delete_redirects_to_the_editor(self) -> None:
        self._save(self.ada, {"use_sample": "1"})
        picture_id = self._ids("ada")[0]
        status, headers, _ = self._post(
            f"/pictures/{picture_id}/delete",
            {"csrf": self.ada["csrf"]},
            self.ada["cookie"],
        )

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/editor?notice=deleted")
        self.assertEqual(self._count("ada"), 0)

    def test_deleting_someone_else_picture_leaves_it(self) -> None:
        self._save(self.ada, {"use_sample": "1"})
        picture_id = self._ids("ada")[0]
        bob = self._member("bob")
        _, headers, _ = self._post(
            f"/pictures/{picture_id}/delete",
            {"csrf": bob["csrf"]},
            bob["cookie"],
        )

        self.assertEqual(headers["Location"], "/editor?error=notyours")
        self.assertEqual(self._count("ada"), 1)

    def test_editor_page_starts_with_save_and_capture_off(self) -> None:
        _, _, page = self._call("GET", "/editor", self.ada["cookie"])

        self.assertIn('id="capture" type="button" onclick="captureOrRetake()" disabled', page)
        self.assertIn('id="save" type="submit" disabled', page)
        self.assertIn('id="gif-save"', page)
        self.assertIn("<legend>Stickers</legend>", page)

    def test_a_gif_from_the_sample_is_refused(self) -> None:
        status, headers, _ = self._save(self.ada, {"gif": "1", "use_sample": "1"})
        _, _, page = self._call("GET", headers["Location"], self.ada["cookie"])

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/editor?error=gifcamera")
        self.assertIn("live camera", page)
        self.assertEqual(self._count("ada"), 0)

    def test_three_camera_snaps_store_one_gif(self) -> None:
        root = os.path.join(os.path.dirname(__file__), "..", "public", "base.png")

        with open(root, "rb") as handle:
            snap = b64encode(handle.read()).decode()

        status, headers, _ = self._save(
            self.ada,
            {"gif": "1", "frames": "a", "snap0": snap, "snap1": snap, "snap2": snap},
        )

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/editor?notice=gif")
        self.assertEqual(self._count("ada"), 1)

    def _member(self, name: str) -> Member:
        self._post("/signup", {
            "username": name,
            "email": name + "@example.com",
            "password": "Password1",
        })
        conn = connect()
        user = find_user(conn, name)

        if user is None:
            raise AssertionError(name)

        confirm_user(conn, user["id"])
        conn.close()
        _, headers, _ = self._post("/login", {"username": name, "password": "Password1"})
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        _, _, page = self._call("GET", "/editor", cookie)
        csrf = page.split('name="csrf" value="')[1].split('"', 1)[0]

        return {"cookie": cookie, "csrf": csrf}

    def _save(self, member: Member, form: dict[str, str]) -> tuple[str, dict[str, str], str]:
        return self._post("/editor", {**form, "csrf": member["csrf"]}, member["cookie"])

    def _ids(self, name: str) -> list[int]:
        conn = connect()
        user = find_user(conn, name)

        if user is None:
            raise AssertionError(name)

        rows = list_pictures(conn, user["id"])
        conn.close()

        return [row["id"] for row in rows]

    def _count(self, name: str) -> int:
        return len(self._ids(name))

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
