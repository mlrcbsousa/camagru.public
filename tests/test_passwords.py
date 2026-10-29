import unittest

from app.passwords import (
    ITERATIONS,
    accept_password,
    hash_password,
    password_codes,
    verify_password,
)


class PasswordsTest(unittest.TestCase):
    def test_rejects_weak_passwords(self) -> None:
        self.assertFalse(accept_password("password"))
        self.assertFalse(accept_password("12345678"))
        self.assertFalse(accept_password("AAAAAAAA"))
        self.assertFalse(accept_password("Abcdef1"))
        self.assertFalse(accept_password("a" * 129))

    def test_passwordzz_fails_only_the_digit_rule(self) -> None:
        self.assertEqual(password_codes("Passwordzz"), ["digit"])

    def test_short_and_long_are_separate_rules(self) -> None:
        self.assertEqual(password_codes("Abcdef1"), ["short"])
        self.assertIn("long", password_codes("a" * 129))
        self.assertNotIn("short", password_codes("a" * 129))

    def test_accepts_password1(self) -> None:
        self.assertTrue(accept_password("Password1"))
        self.assertNotEqual(hash_password("Password1"), "Password1")

    def test_stored_secret_is_not_the_password(self) -> None:
        stored = hash_password("Password1")

        self.assertNotEqual(stored, "Password1")
        self.assertEqual(ITERATIONS, 600000)

    def test_wrong_password_does_not_verify(self) -> None:
        stored = hash_password("Password1")

        self.assertTrue(verify_password("Password1", stored))
        self.assertFalse(verify_password("password1", stored))
