import unittest

from app.mail import comment, confirmation, reset


class MailTest(unittest.TestCase):
    def test_confirmation_has_one_link_and_the_recipient(self) -> None:
        body = confirmation("ada", "ada@example.com", "https://camagru.test/confirm/1")

        self.assertEqual(body["plain"].count("https://camagru.test/confirm/1"), 1)
        self.assertIn("ada@example.com", body["plain"])
        self.assertIn("https://camagru.test/confirm/1", body["html"])

    def test_reset_has_one_link_and_the_recipient(self) -> None:
        body = reset("ada", "ada@example.com", "https://camagru.test/reset/1")

        self.assertEqual(body["plain"].count("https://camagru.test/reset/1"), 1)
        self.assertIn("ada@example.com", body["plain"])

    def test_comment_mail_is_a_letter_like_the_others(self) -> None:
        body = comment("ada", "ada@example.com", "https://camagru.test/p/1", "bob", True)

        if body is None:
            self.fail("expected a comment message")

        self.assertEqual(body["subject"], "New comment on your camagru picture")
        self.assertTrue(body["plain"].startswith("Hi ada,"))
        self.assertIn("bob commented", body["plain"])
        self.assertEqual(body["plain"].count("https://camagru.test/p/1"), 1)
        self.assertIn("ada@example.com", body["plain"])
        self.assertIn('href="https://camagru.test/p/1"', body["html"])

    def test_preference_off_builds_no_message(self) -> None:
        self.assertIsNone(comment("ada", "ada@example.com", "https://camagru.test/p/1", "bob", False))
