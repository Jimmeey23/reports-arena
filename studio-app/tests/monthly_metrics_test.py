import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import monthly


class MonthlyTests(unittest.TestCase):
    def test_calendar_window_crosses_year(self):
        self.assertEqual(monthly.periods(2026, 2)[0], (2025, 3))
        self.assertEqual(monthly.periods(2026, 2)[-1], (2026, 2))

    def test_percent_changes_are_percentage_points(self):
        self.assertEqual(monthly.change('60%', '50%'), '+10.0 pp MoM')
        self.assertEqual(monthly.change('₹1,200', '₹1,000'), '+20.0% MoM')
        self.assertIn('% change unavailable', monthly.change('10', '0'))
        self.assertEqual(monthly.change('Name', 'Another'), '')

    def test_dynamic_period_labels_align(self):
        self.assertEqual(monthly.key('Churned in September'), monthly.key('Churned in August'))

    def test_missing_month_is_not_zero_or_previous_available_month(self):
        data = dict(studio='Bandra', year=2026, month=9, provenance='Saved reports', chapters=dict(
            sales=dict(title='Sales', slug='sales', months={
                '2026-07': {'Revenue': '₹100'}, '2026-09': {'Revenue': '₹200'}})))
        html = monthly.table(data, 'sales')
        self.assertIn('Unavailable', html)
        self.assertNotIn('+100.0% MoM', html)
        self.assertNotIn('<details open', html)

    def test_refresh_is_idempotent_and_each_chapter_gets_toggle(self):
        data = dict(studio='Bandra', year=2026, month=9, provenance='Saved reports', chapters={
            c: dict(title=c.title(), slug=c, months={'2026-09': {'Count': '10'}})
            for c in ('sales', 'class')})
        html = '<section id="sales"><h2>Sales</h2></section><section id="class"><h2>Classes</h2></section>'
        result = monthly.inject(html, data=data)
        self.assertEqual(result.count('class="p57-monthly"'), 2)
        self.assertEqual(monthly.inject(result, data=data), result)

    def test_saved_history_is_studio_scoped_and_uses_same_snapshot_for_every_view(self):
        with tempfile.TemporaryDirectory() as root:
            def write(name, studio, value):
                folder = Path(root, name); folder.mkdir()
                folder.joinpath('manifest.json').write_text(json.dumps(dict(
                    studio=studio, year=2026, month=9, chapters=[dict(
                        id='sales', title='Sales', slug='sales', kpis=[dict(label='Revenue', value=value)])])))
                return folder
            current = write('a', 'Bandra', '₹100')
            write('b', 'Bandra', '₹200')
            write('c', 'Kemps', '₹999')
            data = monthly.saved_history(current)
            self.assertEqual(data['chapters']['sales']['months']['2026-09']['Revenue'], '₹200')

    def test_full_source_history_ignores_selected_report_period(self):
        frame = pd.DataFrame({'_loc':['Bandra']*3,
                              '_dt':pd.to_datetime(['2023-01-01','2025-02-01','2026-10-01'])})
        D = SimpleNamespace(sales=frame)
        class FakeMetrics:
            def __init__(self, dataset, studio, y, m):
                self.D, self.y, self.m = dataset, y, m
            def _sl(self, frame, y):
                return frame[(frame['_dt'].dt.year==y)&(frame['_dt'].dt.month==self.m)]
        ch = [dict(id='sales',title='Sales',slug='sales')]
        builders = dict(sales=lambda metric: dict(kpis=[dict(label='Count',value=metric.y*100+metric.m)]))
        with patch.object(monthly,'Metrics',FakeMetrics):
            a=monthly.capture(D,'Bandra',2025,2,ch,builders,builders,lambda *args:None)
            b=monthly.capture(D,'Bandra',2026,9,ch,builders,builders,lambda *args:None)
        self.assertEqual(a['chapters'],b['chapters'])
        self.assertEqual(a['periods'],b['periods'])
        self.assertEqual(a['periods'][0],'2023-01')
        self.assertEqual(a['periods'][-1],'2026-10')
        self.assertEqual(len(a['periods']),46)
        self.assertNotIn('2024-01',a['chapters']['sales']['months'])


if __name__ == '__main__':
    unittest.main()
