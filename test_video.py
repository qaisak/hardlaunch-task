import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import video

class VideoTests(unittest.TestCase):
    def test_reading_time_does_not_cut_off_long_post(self):
        self.assertGreaterEqual(video.read_time('word ' * 70), 70 / 2.6 + 2.5)
        self.assertEqual(video.read_time('hello'), 8)

    def test_explicit_mood_overrides_text(self):
        self.assertEqual(video.pick_base('madness', 'thoughtful').name, 'reaction_overthinking.mp4')

    def test_old_posts_have_repeatable_selection(self):
        self.assertEqual(video.pick_base('arguing with a robot'), video.pick_base('arguing with a robot'))
        self.assertEqual(video.infer_mood('quiet meditation'), 'thoughtful')

    def test_missing_clips(self):
        with tempfile.TemporaryDirectory() as d, patch.object(video, 'BASE_DIR', Path(d)):
            self.assertIsNone(video.pick_base('test'))

    def test_reaction_library_preferred(self):
        self.assertEqual(video.pick_base('arguing', 'disbelief').name, 'reaction_disbelief.mp4')

    def test_manual_clip_override(self):
        self.assertEqual(video.pick_base('quiet meditation', clip_name='reaction_confused.mp4').name, 'reaction_confused.mp4')
        with self.assertRaises(ValueError): video.pick_base(clip_name='../secrets.mp4')

    def test_stock_is_never_available(self):
        self.assertTrue(all(n.startswith('reaction_') for n in video.reaction_catalogue()))
        with self.assertRaises(ValueError):video.pick_base(clip_name='pexels_8496672.mp4')

    def test_situation_ranking(self):
        picks=video.recommend_clips('quiet meditation', 'thoughtful')
        self.assertEqual(picks[0]['clip'],'reaction_tea.mp4')
        self.assertEqual(len({p['clip'] for p in picks}),3)

    def test_confused_fallback(self):
        self.assertEqual(video.infer_mood('photocopy the photocopy and nothing works'), 'confused')

    def test_long_overlay_leaves_footage_clear(self):
        with tempfile.TemporaryDirectory() as d:
            path = video.text_layer('reading ' * 70, Path(d) / 'overlay.png', 'example')
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1920))
                self.assertEqual(image.crop((0, 0, 1080, 1050)).getchannel('A').getbbox(), None)

if __name__ == '__main__':
    unittest.main()
