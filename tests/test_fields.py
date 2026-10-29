import unittest

from app.boundary import gallery_query, signup_form


class FieldTest(unittest.TestCase):
    def test_gallery_query_omits_a_login_field(self) -> None:
        query = gallery_query({
            "page": ["2"],
            "username": ["ada"],
            "notice": ["nomail"],
            "drop": ["1"],
        })

        self.assertEqual(set(query), {"page", "notice", "fragment"})
        self.assertEqual(query["page"], "2")
        self.assertEqual(query["notice"], "nomail")

    def test_signup_form_omits_a_profile_field(self) -> None:
        form = signup_form({
            "username": ["ada"],
            "email": ["ada@example.com"],
            "password": ["Password1"],
            "mail_ok": ["1"],
            "page": ["2"],
        })

        self.assertEqual(set(form), {"username", "email", "password"})
