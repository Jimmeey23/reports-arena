import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai import agent, evidence
from engine.records import member_tables
import pandas as pd


class MemberTableTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(member_id=str(i), name=f'Member <{i}>', visits=i % 12 + 1,
                          previous_visits=i % 15 + 1) for i in range(78)]
        self.evidence = dict(returning_core=self.rows, all=self.rows, previous_year=2025, period='September 2026')
        self.pack = dict(studio='Test', period='September 2026', metrics=[])

    def test_exact_prompt_renders_all_rows_without_model(self):
        with patch.object(agent.llm, 'complete', side_effect=AssertionError('model must not be called')):
            out = agent.edit_element('replace with a table displaying the names of these 78 members along with visits',
                                     '<p>The same 78 members attended in both Septembers.</p>', self.pack, self.evidence)
        self.assertEqual(out['html'].count('<tr>'), 79)
        self.assertIn('Member &lt;77&gt;', out['html'])
        self.assertIn('2025 visits', out['html'])
        self.assertEqual(out['tokens'], 0)

    def test_creation_uses_selected_cohort(self):
        out = agent.create_element('create a table of members and visits', self.pack, self.evidence,
                                   'The same 78 members attended in both Septembers')
        self.assertIn('2025 visits', out['html'])

    def test_missing_core_does_not_substitute_current_members(self):
        out = agent.edit_element('replace with a table of these 78 members and visits',
                                 '78 returning members', self.pack, dict(all=self.rows))
        self.assertIn('Regenerate', out['error'])

    def test_count_mismatch_never_truncates_or_invents(self):
        out = agent.create_element('table of 79 members and visits', self.pack, self.evidence)
        self.assertIn('rather than 79', out['error'])

    def test_snapshot_intersects_ids_and_counts_attended_rows(self):
        class Metrics:
            y = 2026
            label = 'September 2026'
            def _ck(self, year):
                ids = [1, 1, 2, 3] if year == 2026 else [1, 2, 2, 4]
                return pd.DataFrame([{'Member ID': i, 'First Name': f'Person{i}', 'Last Name': 'Test'} for i in ids])
        table = member_tables(Metrics())
        self.assertEqual(len(table['all']), 3)
        core = {r['member_id']: r for r in table['returning_core']}
        self.assertEqual(set(core), {'1', '2'})
        self.assertEqual(core['1']['visits'], 2)
        self.assertEqual(core['2']['previous_visits'], 2)

    def test_legacy_truncated_evidence_refused(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, 'run').mkdir()
            data = dict(studio='Test', period='September 2026', datasets=dict(checkins=dict(
                total=6000, truncated=True, rows=[])))
            Path(root, 'run', 'records.json').write_text(json.dumps(data))
            self.assertEqual(evidence.load(root, 'run', self.pack), {})

    def test_explicit_replacement_can_omit_unrelated_old_figures(self):
        pack = dict(metrics=[dict(id='attendances', value=461)])
        out = dict(text='<table><tr><td>Visits</td><td>461</td></tr></table>',
                   prompt_tokens=10, completion_tokens=10)
        with patch.object(agent.llm, 'status', return_value=dict(configured=True)), \
             patch.object(agent.llm, 'complete', return_value=out):
            result = agent.edit_element('replace with a visits summary table', '<p>78 members: 461 visits, down 35.3%</p>', pack)
        self.assertIn('html', result)

    def test_unknown_figures_still_rejected_on_replacement(self):
        out = dict(text='<p>999999 visits</p>', prompt_tokens=10, completion_tokens=10)
        with patch.object(agent.llm, 'status', return_value=dict(configured=True)), \
             patch.object(agent.llm, 'complete', return_value=out), \
             patch.object(agent.llm, 'discard'):
            result = agent.edit_element('replace this block', '<p>78 members</p>', self.pack)
        self.assertIn('unsupported', result['error'])


if __name__ == '__main__':
    unittest.main()
