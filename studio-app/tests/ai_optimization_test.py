import sys, unittest, concurrent.futures, time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai import llm, agent

class OptimizationTest(unittest.TestCase):
    def setUp(self):
        llm._cache.clear()
    def test_duplicate_generations_share_one_full_result(self):
        calls=[]
        def request(*args):
            calls.append(args);time.sleep(.03)
            return {'text':'Full original generation','prompt_tokens':120,'completion_tokens':800}
        with patch.dict('os.environ',{'OPENAI_API_KEY':'test-placeholder'}),patch.object(llm,'_request',side_effect=request):
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                results=list(pool.map(lambda _:llm.complete([{'role':'user','content':'Same grounded request'}],max_tokens=2600),range(4)))
            self.assertEqual(len(calls),1)
            self.assertTrue(all(r['text']=='Full original generation' for r in results))
            self.assertEqual(sum(r['completion_tokens'] for r in results),800)
            llm.complete([{'role':'user','content':'Changed evidence'}],max_tokens=2600)
            self.assertEqual(len(calls),2)
    def test_failures_are_not_cached(self):
        with patch.dict('os.environ',{'OPENAI_API_KEY':'test-placeholder'}),patch.object(llm,'_request',side_effect=llm.AIUnavailable('Unavailable')) as request:
            for _ in range(2):
                with self.assertRaises(llm.AIUnavailable):llm.complete([{'role':'user','content':'retry'}])
            self.assertEqual(request.call_count,2)
    def test_small_invented_figures_are_rejected(self):
        self.assertFalse(agent._ground('Won 7 members',{'won':12})[0])
        self.assertTrue(agent._ground('Won 12 members',{'won':12})[0])
    def test_top_rows_include_values_not_only_names(self):
        text=agent._pack_text({'tops':{'sources':[['Website',189,46.0]]}})
        self.assertIn('189',text);self.assertIn('46.0',text)

    def test_summary_rewrite_cannot_drop_content(self):
        from engine.narrate import llm as rewrite
        text='There were 189 leads in September 2026. Trial outcomes reflect the uploaded export.'
        with patch.object(llm,'complete',return_value={'text':'There were 189 leads.', 'prompt_tokens':1,'completion_tokens':1}),patch.object(llm,'discard') as discard:
            with self.assertRaises(ValueError):rewrite(text,'test-placeholder')
            discard.assert_called_once()

    def test_summary_rewrite_retains_full_detail(self):
        from engine.narrate import llm as rewrite
        text='There were 189 leads in September 2026. Trial outcomes reflect the uploaded export.'
        with patch.object(llm,'complete',return_value={'text':text, 'prompt_tokens':1,'completion_tokens':1}):
            self.assertEqual(rewrite(text,'test-placeholder'),text)
