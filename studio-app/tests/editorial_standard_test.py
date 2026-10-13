"""Validate the editorial safeguards and every model-facing language path."""
import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.editorial import apply,clean_body,instructions
from ai import agent

class EditorialTests(unittest.TestCase):
 def test_invalid_insights_suppressed_and_evidence_preserved(self):
  body='<h2>The room is bigger than the demand</h2><p>September ranks 30th out of 29 months.</p><p>Revenue ranges from ₹10,264 to ₹10,264.</p><p>A comparison is ·-fold.</p><p>Members do not choose a channel.</p><table><tr><td>Unavailable ·</td><td>1</td></tr></table>'
  result=clean_body(body)
  self.assertNotIn('30th',result);self.assertNotIn('₹10,264',result);self.assertNotIn('·-fold',result)
  self.assertIn('Payment-channel differences may reflect',result);self.assertIn('<td>Unavailable ·</td>',result)
 def test_future_chapter_rules(self):
  ch={'id':'lapse','title':'Churn','body':'<h2>The two ways to lose a member</h2><p>Costs nothing extra to serve.</p>','summary':'Product expiry is visible.','recs':[(1,'Review expiry','CST','Confirm subsequent purchases.','Guaranteed uplift.')]}
  apply(SimpleNamespace(label='October 2026',y=2026),ch)
  self.assertIn('Membership Health',ch['title']);self.assertIn('Reading the Numbers',ch['body']);self.assertNotIn('Costs nothing',ch['body']);self.assertNotIn('Guaranteed',ch['recs'][0][4])
 def test_create_and_edit_prompts(self):
  pack={'studio':'Test','period':'October 2026','metrics':[],'chapters':[]}
  seen=[]
  def complete(messages,**kwargs):
   seen.append(messages[0]['content']);return {'text':'<p>Review attendance consistency.</p>','prompt_tokens':1,'completion_tokens':1,'cached':False}
  with patch.object(agent.llm,'complete',side_effect=complete),patch.object(agent.llm,'status',return_value={'configured':True}):
   agent.create_element('Add a paragraph',pack)
   agent.edit_element('Rewrite','<p>Review attendance.</p>',pack)
   agent.chat('Explain the engagement opportunity',pack,None,'test')
   from engine.narrate import llm
   llm('Review attendance consistency.',key='test-key')
  self.assertEqual(len(seen),4)
  for prompt in seen:
   self.assertIn('management-language-v1',prompt);self.assertIn('never forecasts',instructions());self.assertIn('expiry alone',prompt.lower());self.assertNotIn('lightly witty',prompt)

if __name__=='__main__':unittest.main()
