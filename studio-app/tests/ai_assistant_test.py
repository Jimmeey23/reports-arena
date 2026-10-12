"""AI-layer tests: the metrics pack, the deterministic question engine and
the grounding guard. Run from studio-app:

    python tests/ai_assistant_test.py

These checks pin the token-efficiency guarantees: every data question the
deterministic engine resolves costs zero model tokens, and every answer is
traceable to the computed metrics of a real run.
"""
from __future__ import annotations
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from ai import metrics_pack, qa, agent
from ai.store import SqliteStore

RUNS = os.path.join(os.path.dirname(HERE), 'runs')


def a_run():
    for rid in sorted(os.listdir(RUNS), reverse=True):
        if os.path.isfile(os.path.join(RUNS, rid, 'manifest.json')):
            return rid
    return None


class PackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rid = a_run()
        if not cls.rid:
            raise unittest.SkipTest('no saved runs')
        cls.pack = metrics_pack.load_pack(RUNS, cls.rid)

    def test_pack_has_identity_and_metrics(self):
        self.assertTrue(self.pack['studio'])
        self.assertTrue(self.pack['period'])
        self.assertGreater(len(self.pack['metrics']), 5)
        self.assertGreater(len(self.pack['chapters']), 3)

    def test_definitions_attached(self):
        self.assertIn('fill', self.pack['definitions'])
        self.assertIn('discount_rate', self.pack['definitions'])

    def test_context_is_compact(self):
        # the whole grounded context must stay small (a few KB, ~2k tokens)
        self.assertLess(agent.context_estimate(self.pack), 4000)


class QATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rid = a_run()
        if not cls.rid:
            raise unittest.SkipTest('no saved runs')
        cls.pack = metrics_pack.load_pack(RUNS, cls.rid)

    def test_metric_lookup_zero_tokens(self):
        r = qa.answer('What was the cash collected?', self.pack)
        self.assertTrue(r['ok'])
        self.assertEqual(r['mode'], 'deterministic')
        self.assertIn('cash', r['answer'].lower())

    def test_definition_question(self):
        r = qa.answer('How is the fill rate calculated?', self.pack)
        self.assertTrue(r['ok'])
        self.assertIn('attended', r['answer'].lower())

    def test_substring_safety(self):
        # 'action' inside 'transactions' must not route to recommendations
        r = qa.answer('How many transactions?', self.pack)
        self.assertTrue(r['ok'])
        self.assertNotIn('Recommended actions', r['answer'])

    def test_recommendations_by_topic(self):
        r = qa.answer('What should we fix about sales first?', self.pack)
        self.assertTrue(r['ok'])

    def test_unknown_question_fails_softly(self):
        r = qa.answer('tell me a joke', self.pack)
        self.assertFalse(r['ok'])

    def test_chapter_cited(self):
        r = qa.answer('What was the capacity utilisation?', self.pack)
        self.assertTrue(r['ok'])
        self.assertTrue(r['chapters'])


class GroundingTests(unittest.TestCase):
    def test_known_numbers_pass(self):
        pack = dict(metrics=[dict(id='cash', value=1529410)], chapters=[], tops={})
        ok, _ = agent._ground('Cash was ₹15,29,410 in the period.', pack)
        self.assertTrue(ok)

    def test_invented_numbers_rejected(self):
        pack = dict(metrics=[dict(id='cash', value=1529410)], chapters=[], tops={})
        ok, bad = agent._ground('Cash was ₹99,99,999 apparently.', pack)
        self.assertFalse(ok)
        self.assertTrue(bad)


class StoreTests(unittest.TestCase):
    def test_sqlite_roundtrip(self):
        path = os.path.join(HERE, '_ai_test.sqlite3')
        if os.path.exists(path):
            os.remove(path)
        s = SqliteStore(path)
        s.save_message('sess', 'user', 'hello')
        s.save_message('sess', 'assistant', 'hi', meta=dict(mode='deterministic'))
        h = s.history('sess', 4)
        self.assertEqual([m['role'] for m in h], ['user', 'assistant'])
        s.upsert_edit('run1', 'el1', 'set', '<p>x</p>')
        self.assertEqual(len(s.edits('run1')), 1)
        s.delete_edit('run1', 'el1', 'set')
        self.assertEqual(len(s.edits('run1')), 0)
        s.cache_put('k', dict(a=1))
        self.assertEqual(s.cache_get('k'), dict(a=1))
        os.remove(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
