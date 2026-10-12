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

    def test_report_and_config_roundtrip(self):
        path = os.path.join(HERE, '_ai_test.sqlite3')
        if os.path.exists(path):
            os.remove(path)
        s = SqliteStore(path)
        meta = dict(run_id='r1', studio='Bandra', label='September 2026', built='12 October 2026',
                    chapters=[dict(id='lapse', title='Lapsed', kpis=[dict(label='Churned in Sep', value=164)])])
        s.save_report('r1', meta)
        got = s.report('r1')
        self.assertEqual(got['studio'], 'Bandra')
        self.assertEqual(got['meta']['chapters'][0]['kpis'][0]['value'], 164)
        rows = s.list_reports(studio='Bandra')
        self.assertEqual(len(rows), 1)
        self.assertEqual(s.list_reports(studio='Nowhere'), [])
        s.config_put('ai', dict(model='gpt-4o-mini'))
        self.assertEqual(s.config_get('ai'), dict(model='gpt-4o-mini'))
        self.assertIn('ai', s.config_all())
        os.remove(path)


class PeriodKpiTests(unittest.TestCase):
    """The deterministic engine must resolve the period-scoped KPIs the lapse
    chapter now leads with, without any model tokens."""

    PACK = dict(studio='Bandra', period='September 2026', year=2026, month=9,
                metrics=[], definitions={}, tops={},
                chapters=[dict(id='lapse', title='Memberships Lapsed and Churned', summary='',
                               kpis=[dict(label='Churned in September', value=164, detail='closed out'),
                                     dict(label='Bought in September', value=121, detail='new money'),
                                     dict(label='Expiring next 30 days', value=298, detail='at risk')],
                               facts=[], recs=[])])

    def test_period_churn_resolves_zero_tokens(self):
        r = qa.answer('how many memberships churned in September?', self.PACK)
        self.assertIn('164', r['answer'])
        self.assertEqual(r['mode'], 'deterministic')

    def test_period_bought_via_generic_period(self):
        r = qa.answer('memberships bought in the period', self.PACK)
        self.assertIn('121', r['answer'])

    def test_expiring_resolves(self):
        r = qa.answer('expiring next 30 days', self.PACK)
        self.assertIn('298', r['answer'])

    def test_history_block_lists_prior_periods(self):
        path = os.path.join(HERE, '_ai_test.sqlite3')
        if os.path.exists(path):
            os.remove(path)
        from ai.store import SqliteStore
        s = SqliteStore(path)
        s.save_report('old', dict(run_id='old', studio='Bandra', label='August 2026',
                                  chapters=[dict(id='sales', title='Sales',
                                                 kpis=[dict(label='Cash taken', value='₹1,000,000')])]))
        block = agent.history_block(s, 'Bandra', exclude_rid='current')
        self.assertIn('August 2026', block)
        os.remove(path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
