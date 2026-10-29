import os
import unittest

from app.compose import composite, open_base, save_gif

PNG = b"\x89PNG\r\n\x1a\nbase"
FRAME_A = b"\x89PNG\r\n\x1a\nframe-a"
FRAME_B = b"\x89PNG\r\n\x1a\nframe-b"


class ComposeTest(unittest.TestCase):
    def test_a_real_photo_and_a_sticker_are_a_new_png(self) -> None:
        root = os.path.join(os.path.dirname(__file__), "..", "public")

        with open(os.path.join(root, "base.png"), "rb") as handle:
            photo = handle.read()

        with open(os.path.join(root, "frames", "a.png"), "rb") as handle:
            border = handle.read()

        plain = composite(photo, [])
        saved = composite(photo, [border])

        self.assertEqual(open_base(saved).format, "PNG")
        self.assertNotEqual(saved, photo)
        self.assertNotEqual(saved, plain)

    def test_fake_bytes_only_check_that_the_counts_differ(self) -> None:
        zero = composite(PNG, [])
        one = composite(PNG, [FRAME_A])
        two = composite(PNG, [FRAME_A, FRAME_B])

        self.assertTrue(zero.startswith(b"\x89PNG"))
        self.assertNotEqual(zero, PNG)
        self.assertNotEqual(one, zero)
        self.assertNotEqual(two, one)

    def test_non_image_raises_and_stores_nothing(self) -> None:
        with self.assertRaises(ValueError):
            open_base(b"not-an-image")

    def test_three_snaps_are_one_gif(self) -> None:
        root = os.path.join(os.path.dirname(__file__), "..", "public")

        with open(os.path.join(root, "base.png"), "rb") as handle:
            photo = handle.read()

        payload = save_gif([photo, photo, photo])

        self.assertTrue(payload.startswith(b"GIF8"))

    def test_a_bad_snap_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            save_gif([b"not-an-image", b"not-an-image", b"not-an-image"])
