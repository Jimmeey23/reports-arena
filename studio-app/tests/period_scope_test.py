import sys, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from engine.metrics import Metrics
from engine.deep import Deep
from engine.records import snapshot
from ai.agent import component_html

class PeriodScopeTest(unittest.TestCase):
    def test_ai_component_markup_is_inert(self):
        html=component_html('<div onclick="bad()">Safe<script>bad()</script><svg viewBox="0 0 100 100"><rect width="20"/></svg></div>')
        self.assertNotIn('onclick',html);self.assertNotIn('script',html);self.assertNotIn('bad()',html)
        self.assertIn('viewBox',html)

    def data(self):
        dates = pd.to_datetime(['2026-08-31 23:59','2026-09-01','2026-09-30 23:59','2026-10-01','2025-09-01','2026-09-02'],format='mixed')
        leads = pd.DataFrame({'_dt':dates,'_loc':['A']*5+['B'],'Trial Status':['Trial Completed']*6,'won':[True,True,False,True,True,True],'Status':['Won','Won','Open','Won','Won','Won'],'LTVn':[100]*6})
        return SimpleNamespace(sessions=None,sales=None,checkins=None,new=None,lapsed=None,leads=leads,sources=[])
    def test_month_boundaries_and_studio(self):
        data=self.data(); m=Metrics(data,'A',2026,9)
        self.assertEqual(m.lead_n,2);self.assertEqual(m.lead_fun['won'],1)
        self.assertEqual(m.lead_month_prev,1)
        self.assertEqual(len(data.leads),6)
        self.assertEqual(snapshot(m)['datasets']['leads']['total'],2)
        x=Deep(m);self.assertEqual(len(x.ld['d']),2)
        self.assertEqual(x.ld['month']['prev_n'],1)
        self.assertEqual(m.open_age,0)
    def test_no_month_rows_does_not_fall_back_to_all_time(self):
        m=Metrics(self.data(),'A',2026,7)
        self.assertNotIn('leads',m.has)
        self.assertEqual(snapshot(m)['datasets']['leads']['total'],0)
    def test_membership_purchase_scope(self):
        data=self.data();data.lapsed=pd.DataFrame({'Purchase Date_d':pd.to_datetime(['2026-08-01','2026-09-01','2026-10-01']),'_loc':['A']*3,'Member ID':[1,2,3],'Membership Name':['Package']*3,'Amount Paid':[100,200,300],'Derived Status':['Active']*3,'Membership Duration (Days)':[30]*3,'Total Sessions Completed':[1]*3})
        m=Metrics(data,'A',2026,9)
        self.assertEqual(m.led['cash'],200)
        self.assertEqual(snapshot(m)['datasets']['lapsed']['total'],1)

if __name__=='__main__':unittest.main()
