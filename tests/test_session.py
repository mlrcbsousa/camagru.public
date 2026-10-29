import unittest

from app.session import csrf_accepts, issue_cookie, read_session, server_listens


class SessionTest(unittest.TestCase):
    def test_empty_secret_does_not_listen(self) -> None:
        self.assertFalse(server_listens(""))
        self.assertFalse(server_listens(None))

    def test_round_trip_accepts_a_signed_cookie(self) -> None:
        cookie = issue_cookie(7, 1, "secret", 1_000)

        self.assertEqual(read_session(cookie, "secret", 1_000, 1), 7)

    def test_tampered_cookie_is_rejected(self) -> None:
        cookie = issue_cookie(7, 1, "secret", 1_000)

        self.assertIsNone(read_session(cookie + "x", "secret", 1_000, 1))

    def test_expired_cookie_is_rejected(self) -> None:
        cookie = issue_cookie(7, 1, "secret", 1_000)

        self.assertIsNone(read_session(cookie, "secret", 1_000 + 12 * 3600 + 1, 1))

    def test_cookie_from_before_logout_is_rejected(self) -> None:
        cookie = issue_cookie(7, 1, "secret", 1_000)

        self.assertIsNone(read_session(cookie, "secret", 1_000, 2))

    def test_bad_csrf_is_rejected(self) -> None:
        self.assertFalse(csrf_accepts("nope", 7, 1, "secret"))
