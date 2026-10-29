import io
import os
import tempfile
import unittest
from typing import cast
from urllib.parse import urlencode
from wsgiref.types import StartResponse, WSGIEnvironment

from app.server import application
from app.store import confirm_user, connect, find_user, insert_user


class AccountsTest(unittest.TestCase):
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

    def tearDown(self) -> None:
        if os.path.exists(self.database):
            os.remove(self.database)

    def test_duplicate_email_is_rejected_by_the_database(self) -> None:
        conn = connect()

        self.assertIsNone(insert_user(conn, "ada2", "Ada@example.com", "Password1"))
        self.assertIsNone(insert_user(conn, "Ada", "ada2@example.com", "Password1"))
        conn.close()

    def test_editor_sends_a_visitor_to_login(self) -> None:
        status, headers, _ = self._call("GET", "/editor")

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/login")

    def test_signup_redirects_so_a_refresh_does_not_sign_up_again(self) -> None:
        status, headers, _ = self._post("/signup", {
            "username": "ada2",
            "email": "ada2@example.com",
            "password": "Password1",
        })

        self.assertEqual(status, "303 See Other")
        self.assertEqual(headers["Location"], "/signup?notice=sent")

    def test_confirm_does_not_log_the_browser_in(self) -> None:
        from app.store import issue_token

        conn = connect()
        user = find_user(conn, "ada")

        if user is None:
            raise AssertionError("ada")

        token = issue_token(conn, user["id"], "confirm")
        conn.close()
        status, headers, _ = self._call("GET", "/confirm/" + token)

        self.assertEqual(status, "303 See Other")
        self.assertNotIn("Set-Cookie", headers)

    def test_unknown_username_is_told_there_is_no_account(self) -> None:
        status, headers, _ = self._post("/login", {"username": "nobody", "password": "Password1"})

        self.assertEqual(status, "303 See Other")
        _, _, body = self._call("GET", headers["Location"])

        self.assertIn("No account uses that username.", body)
        self.assertNotIn("Set-Cookie", headers)

    def test_failed_login_redirects_so_refresh_cannot_replay_the_password(self) -> None:
        status, headers, _ = self._post("/login", {"username": "ada", "password": "wrong"})

        self.assertEqual(status, "303 See Other")
        self.assertNotIn("Set-Cookie", headers)
        status, headers, body = self._call("GET", headers["Location"])

        self.assertNotIn("Set-Cookie", headers)
        self.assertIn("That password does not match.", body)

    def test_unconfirmed_login_redirects_without_a_cookie(self) -> None:
        self._post("/signup", {
            "username": "bob",
            "email": "bob@example.com",
            "password": "Password1",
        })
        status, headers, _ = self._post("/login", {"username": "bob", "password": "Password1"})

        self.assertEqual(status, "303 See Other")
        self.assertIn("notice=unconfirmed", headers["Location"])
        self.assertNotIn("Set-Cookie", headers)

    def test_taken_email_and_a_bad_password_are_both_reported(self) -> None:
        status, headers, _ = self._post("/signup", {
            "username": "ada2",
            "email": "ada@example.com",
            "password": "Passwordzz",
        })
        _, _, body = self._call("GET", headers["Location"])

        self.assertEqual(status, "303 See Other")
        self.assertIn("that username or email is taken", body)
        self.assertIn("one digit", body)
        self.assertNotIn("one letter", body)
        self.assertNotIn("at least 8 characters", body)

    def test_reset_request_leaves_the_current_password(self) -> None:
        self._post("/reset", {"action": "request", "email": "ada@example.com"})
        _, headers, _ = self._post("/login", {"username": "ada", "password": "Password1"})

        self.assertIn("Set-Cookie", headers)

    def test_quote_in_the_password_does_not_log_in(self) -> None:
        _, headers, _ = self._post("/login", {
            "username": "ada",
            "password": "blahblah' OR 1='1",
        })

        self.assertNotIn("Set-Cookie", headers)

    def test_a_marker_in_the_username_is_not_filled_again(self) -> None:
        from app.pages import signup_page

        page = signup_page("{{email}}", "ada@example.com")

        self.assertIn('value="{{email}}"', page)
        self.assertIn('value="ada@example.com"', page)

    def test_gallery_hides_its_own_nav_link(self) -> None:
        _, _, body = self._call("GET", "/")

        self.assertNotIn('href="/">Gallery', body)
        self.assertIn('href="/signup"', body)

    def test_empty_reset_does_not_claim_a_mail_was_sent(self) -> None:
        status, headers, _ = self._post("/reset", {"action": "request", "email": ""})
        _, _, body = self._call("GET", headers["Location"])

        self.assertEqual(status, "303 See Other")
        self.assertIn("email is not valid", body)
        self.assertNotIn("on its way", body)

    def test_a_failed_password_is_labelled(self) -> None:
        status, headers, _ = self._post("/signup", {
            "username": "rule",
            "email": "rule@example.com",
            "password": "Passwordzz",
        })
        _, _, body = self._call("GET", headers["Location"])

        self.assertEqual(status, "303 See Other")
        self.assertLess(body.index("Invalid password."), body.index("one digit"))

    def test_request_page_has_no_password_field(self) -> None:
        _, _, body = self._call("GET", "/reset")

        self.assertNotIn('name="password"', body)
        self.assertIn("reset-email", body)

    def test_password_choice_without_the_link_is_refused(self) -> None:
        self._post("/reset", {"action": "request", "email": "ada@example.com"})
        self._post("/reset", {
            "action": "choose",
            "email": "ada@example.com",
            "password": "attacker1",
        })
        _, headers, _ = self._post("/login", {"username": "ada", "password": "attacker1"})

        self.assertNotIn("Set-Cookie", headers)

    def test_profile_without_the_csrf_token_does_not_save(self) -> None:
        _, headers, _ = self._post("/login", {"username": "ada", "password": "Password1"})
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        _, _, body = self._post("/profile", {
            "username": "stolen",
            "email": "stolen@example.com",
            "csrf": "nope",
        }, cookie)
        _, _, home = self._call("GET", "/", cookie)

        self.assertIn("the form was refused", body)
        self.assertIn(">ada<", home)

    def test_logout_without_the_csrf_token_keeps_the_session(self) -> None:
        _, headers, _ = self._post("/login", {"username": "ada", "password": "Password1"})
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        _, logout_headers, _ = self._post("/logout", {}, cookie)
        _, _, page = self._call("GET", "/", cookie)

        self.assertNotIn("Max-Age=0", logout_headers.get("Set-Cookie", ""))
        self.assertIn(">ada<", page)

    def test_logout_rejects_the_previous_cookie(self) -> None:
        _, headers, _ = self._post("/login", {"username": "ada", "password": "Password1"})
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        _, _, page = self._call("GET", "/profile", cookie)
        csrf = page.split('name="csrf" value="')[1].split('"', 1)[0]

        self._post("/logout", {"csrf": csrf}, cookie)
        _, _, page = self._call("GET", "/profile", cookie)

        self.assertIn("Log in to edit your profile.", page)

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
