import unittest
import tempfile,json
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
from trends import trend_input,validate_direction
import app
URL='https://www.instagram.com/reel/example/'
NOTES='A fictional test observation about a repeated setup followed by a surprising payoff.'
class TrendTests(unittest.TestCase):
 def test_optional_input(self):self.assertIsNone(trend_input())
 def test_links_alone_are_not_evidence(self):
  with self.assertRaises(ValueError):trend_input(URL)
 def test_bad_hosts_and_future_dates(self):
  for url in ['https://www.instagram.com.evil.com/reel/x/','javascript:alert(1)','https://user@www.tiktok.com/test']:
   with self.assertRaises(ValueError):trend_input(url,NOTES,date.today().isoformat(),'UK / English')
  with self.assertRaises(ValueError):trend_input(URL,NOTES,(date.today()+timedelta(days=1)).isoformat(),'UK / English')
 def test_old_reference_label(self):
  data=trend_input(URL,NOTES,(date.today()-timedelta(days=30)).isoformat(),'UK / English')
  self.assertIn('Older',data['status']);self.assertIn('not automatically watched',data['method'])
 def test_invalid_model_output(self):
  for data in [None,{}, {'text':'short','caption':'a','adaptation':'b','why_this_brand':'c','reaction':'happy'}]:
   with self.assertRaises(ValueError):validate_direction(data)
 def test_comparison_escapes_source_notes(self):
  with tempfile.TemporaryDirectory() as directory:
   d=Path(directory);ref=trend_input(URL,NOTES,date.today().isoformat(),'UK / English');ref['notes']='<script>alert(1)</script>'
   (d/'trends.json').write_text(json.dumps(ref));draft={'text':'hello <img>','caption':'caption'}
   (d/'directions.json').write_text(json.dumps({'evergreen':draft,'trend':draft}))
   rendered=app.trends_html(d);self.assertNotIn('<script>',rendered);self.assertIn('Use trend-inspired draft',rendered)
 def test_selected_direction_uses_its_own_mood(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(app,'render_mp4',return_value=(None,'rendered')) as render:
   root=Path(directory);d=root/'demo';d.mkdir();(d/'post.mp4').write_bytes(b'test');(d/'post.md').write_text('> old story\n**Caption:** old')
   draft={'text':'word '*30,'caption':'caption','reaction':'thoughtful','why_this_brand':'new reason'}
   for name,value in [('final',{'text':'old '*30,'reaction':'confused'}),('profile',{'brand_name':'Demo'}),('directions',{'trend':draft})]:
    (d/(name+'.json')).write_text(json.dumps(value))
   with patch.object(app,'OUT',root):app.rebuild({'slug':'demo','direction':'trend','text':draft['text'],'caption':'caption'},lambda x:None)
   self.assertEqual(render.call_args.kwargs['reaction'],'thoughtful')
   self.assertEqual(json.loads((d/'final.json').read_text())['direction'],'trend')
if __name__=='__main__':unittest.main()
