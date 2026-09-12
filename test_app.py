import unittest
from app import brand_dir, result_html

class AppTests(unittest.TestCase):
    def test_brand_paths_cannot_escape_output(self):
        for slug in ('../base', '/tmp', '..', 'missing-brand'):
            with self.assertRaises(ValueError): brand_dir(slug)

    def test_editor_contains_saved_text_and_reactions(self):
        result=result_html('rihal')
        self.assertIn('name="text"',result)
        self.assertIn('reaction_confused.mp4',result)
        self.assertIn('download="rihal.mp4"',result)
        self.assertIn('no AI writing call',result)

if __name__=='__main__': unittest.main()
