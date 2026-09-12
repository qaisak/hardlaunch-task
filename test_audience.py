import unittest
from unittest.mock import Mock
from audience import collect_sources, validate_insights, writing_context, reddit_url
URL='https://www.reddit.com/r/productivity/comments/mea5en/'
EXCERPT='Everytime I delete the app I reinstall it after somedays.'
class AudienceTests(unittest.TestCase):
 def test_malformed_model_response_is_rejected(self):
  for result in [None, [], {'themes':None}, {'themes':[None, {'evidence':None}]}]:
   with self.assertRaises(ValueError):validate_insights(result,collect_sources(URL,EXCERPT))
 def test_readable_public_page_retains_method(self):
  response=Mock(status_code=200,text='<shreddit-post><div slot="text-body">'+EXCERPT+'</div></shreddit-post>')
  self.assertEqual(collect_sources(URL,getter=Mock(return_value=response))[0]['method'],'public page')
 def test_pasted_source_needs_no_network(self):
  getter=Mock(side_effect=AssertionError('network'))
  sources=collect_sources(URL,EXCERPT,getter)
  self.assertEqual(sources[0]['method'],'pasted excerpt');getter.assert_not_called()
 def test_unreadable_page_is_explicit(self):
  response=Mock(status_code=200,text='<title>Reddit</title>')
  with self.assertRaisesRegex(ValueError,'Paste'):collect_sources(URL,getter=Mock(return_value=response))
 def test_sources_are_restricted(self):
  for url in ['http://www.reddit.com/r/a/comments/b/','https://evil.com/r/a/comments/b/','https://www.reddit.com/r/a/']:
   with self.assertRaises(ValueError):reddit_url(url)
 def test_invented_evidence_rejected(self):
  sources=collect_sources(URL,EXCERPT)
  with self.assertRaises(ValueError):validate_insights({'themes':[{'theme':'a','angle':'b','evidence':[{'source_id':'s1','quote':'This quote never existed'}]}]},sources)
 def test_verified_excerpt_is_not_passed_to_writer(self):
  data=validate_insights({'themes':[{'theme':'Reinstall cycle','angle':'An original scene about returning to an app','evidence':[{'source_id':'s1','quote':EXCERPT}]}]},collect_sources(URL,EXCERPT))
  self.assertEqual(data['themes'][0]['evidence'][0]['url'],URL)
  self.assertNotIn(EXCERPT,writing_context(data))
if __name__=='__main__':unittest.main()
