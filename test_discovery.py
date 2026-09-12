import unittest,tempfile,json
from unittest.mock import patch,Mock
from discovery import allowed,select_evidence,discover,trend_reference
class DiscoveryTests(unittest.TestCase):
 def data(self):
  return {'audience':[],'trends':[],'sources':[{'id':'1','kind':'audience','url':'https://www.reddit.com/r/test/comments/abc/','snippet':'I keep checking my phone instead of finishing my work.','title':'Focus problem'}]}
 def test_domain_boundary(self):
  self.assertFalse(allowed('https://reddit.com.evil.org','audience'))
  self.assertFalse(allowed('javascript:alert(1)','trends'))
  self.assertTrue(allowed('https://www.tiktok.com/@test/video/1','trends'))
 def test_only_matching_evidence_survives(self):
  d=self.data();result=select_evidence(d,{'items':[{'id':'1','summary':'A person describes distraction during work.','evidence':'I keep checking my phone'}]})
  self.assertEqual(len(result['audience']),1)
  result=select_evidence(self.data(),{'items':[{'id':'1','summary':'An invented description of a problem.','evidence':'Invented words from nowhere'}]})
  self.assertFalse(result['audience'])
 def test_unknown_source_and_duplicates_rejected(self):
  item={'id':'1','summary':'A person describes distraction during work.','evidence':'I keep checking my phone'}
  result=select_evidence(self.data(),{'items':[item,item,dict(item,id='999')]})
  self.assertEqual(len(result['audience']),1)
 def test_failure_returns_evergreen(self):
  with tempfile.TemporaryDirectory() as folder,patch('generate.call_json',side_effect=RuntimeError('offline')):
   result=discover(None,{'brand_name':'Demo'},cache_dir=folder)
   self.assertFalse(result['audience']);self.assertIn('fallback',result['status']);self.assertIsNone(trend_reference(result))
 def test_cache_avoids_repeated_network(self):
  row={'title':'Focus problem','href':'https://www.reddit.com/r/test/comments/abc/','body':'I keep checking my phone instead of finishing my work.'}
  with tempfile.TemporaryDirectory() as folder,patch('ddgs.DDGS') as search,patch('generate.call_json') as model:
   search.return_value.text.return_value=[row]
   model.side_effect=[{'audience_query':'focus','content_query':'focus'},{'items':[{'id':'1','summary':'A person describes distraction during work.','evidence':'I keep checking my phone'}]}]
   first=discover(None,{'source_url':'https://example.com'},cache_dir=folder)
   self.assertEqual(len(first['audience']),1)
   second=discover(None,{'source_url':'https://example.com'},cache_dir=folder)
   self.assertTrue(second['cached']);self.assertEqual(model.call_count,2)
if __name__=='__main__':unittest.main()
