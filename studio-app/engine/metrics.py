"""Every number the reports are built from, computed for whichever studio and
month the user picked, with the same month in the two prior years where the
uploads cover them.

The rule followed throughout: if a source is missing, its metrics are reported
as absent rather than faked, and the chapter that needs them says so.
"""
from __future__ import annotations
import numpy as np, pandas as pd

MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
               'August', 'September', 'October', 'November', 'December']
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def rng(y, m):
    a = pd.Timestamp(f'{y}-{m:02d}-01')
    return a, a + pd.offsets.MonthBegin(1)


class Metrics:
    def __init__(self, D, studio, year, month, log=lambda *a: None):
        self.D, self.studio, self.y, self.m = D, studio, year, month
        self.prev = [year - 1, year - 2]
        self.label = f'{MONTH_NAMES[month - 1]} {year}'
        self.has = {}
        log(f'metrics: {studio} / {self.label}')
        self._room(); self._sales(); self._people(); self._formats(); self._trainers()
        self._timing(); self._cancel(); self._discount(); self._lapse(); self._leads(); self._behaviour()

    # ------------------------------------------------------------------ utils
    def _sl(self, df, y, m=None, loc='_loc'):
        m = m or self.m
        a, b = rng(y, m)
        d = df[(df[loc] == self.studio)]
        return d[(d['_dt'] >= a) & (d['_dt'] < b)]

    def _ck(self, y, m=None, attended=True, cancelled=False):
        CK = getattr(self.D, 'checkins', None)
        if CK is None:
            return None
        d = self._sl(CK, y, m)
        if attended:
            d = d[d['Checked In'] == True]
        if cancelled:
            d = d[d['Is Late Cancelled'] == True]
        return d

    # ------------------------------------------------------------------ room
    def _room(self):
        X = self.D.sessions
        if X is None:
            return
        self.has['sessions'] = True
        self.room = {}
        for y in [self.y] + self.prev:
            s = self._sl(X, y)
            if s.empty:
                continue
            seats = float(s['Capacity'].sum()); att = float(s['CheckedIn'].sum())
            self.room[y] = dict(
                sessions=len(s), seats=seats, att=att, book=float(s['Booked'].sum()),
                lc=float(s['LateCancelled'].sum()), comp=float(s['Complimentary'].sum()),
                rev=float(s['Revenue'].sum()),
                nonpaid=float(s['NonPaid'].sum()) if 'NonPaid' in s else 0.0,
                fill=att / seats * 100 if seats else 0,
                rpc=float(s['Revenue'].sum()) / len(s) if len(s) else 0,
                rph=float(s['Revenue'].sum()) / att if att else 0,
                classavg=att / len(s) if len(s) else 0)
            self.room[y]['book_pct'] = self.room[y]['book'] / seats * 100 if seats else 0
            self.room[y]['conv'] = att / self.room[y]['book'] * 100 if self.room[y]['book'] else 0
        self.F = self.room.get(self.y, {})

        # room size bands
        s = self._sl(X, self.y)
        if not s.empty:
            band = pd.cut(s['_cap'], [0, 11, 13, 100], labels=['10 to 11 seats', '12 to 13 seats', '14 or more seats'])
            self.rooms = s.assign(band=band).groupby('band', observed=True).agg(
                sessions=('_cap', 'size'), seats=('_cap', 'mean'), att=('CheckedIn', 'mean'),
                rev=('Revenue', 'mean')).reset_index()
            self.rooms['fill'] = self.rooms['att'] / self.rooms['seats'] * 100

    # ------------------------------------------------------------------ sales
    def _sales(self):
        S = getattr(self.D, 'sales', None)
        if S is None:
            return
        self.has['sales'] = True
        self.sales = {}
        for y in [self.y] + self.prev:
            s = self._sl(S, y)
            if s.empty:
                continue
            self.sales[y] = dict(lines=len(s), cash=float(s['val'].sum()), buyers=int(s['Member ID'].nunique()),
                                 disc=float(s['disc'].sum()), gross=float(s['gross'].sum()))
            self.sales[y]['ticket'] = self.sales[y]['cash'] / max(self.sales[y]['buyers'], 1)
            self.sales[y]['depth'] = self.sales[y]['disc'] / self.sales[y]['gross'] * 100 if self.sales[y]['gross'] else 0
            self.sales[y]['spread'] = float(s['has_disc'].mean() * 100)
        f = self._sl(S, self.y)
        if not f.empty:
            cat = 'Cleaned Category' if 'Cleaned Category' in f.columns else None
            if cat:
                g = f.groupby(cat)['val'].agg(['size', 'sum']).sort_values('sum', ascending=False)
                self.cats = g
            kh = f['_dt'].dt.hour
            self.sale_hours = f.assign(h=kh).groupby('h')['val'].agg(['size', 'sum'])

    # ------------------------------------------------------------------ people
    def _people(self):
        self.people = {}
        for y in [self.y] + self.prev:
            a = self._ck(y)
            if a is None or a.empty:
                continue
            v = a.groupby('Member ID').size()
            self.people[y] = dict(members=int(a['Member ID'].nunique()), visits=len(a),
                                  per=len(a) / max(a['Member ID'].nunique(), 1), v=v)
        self.V = self.people.get(self.y, {}).get('v')

        # the returning core: same month, two years running
        if self.y in self.people and (self.y - 1) in self.people:
            vn, vp = self.people[self.y]['v'], self.people[self.y - 1]['v']
            core = set(vn.index) & set(vp.index)
            self.core = dict(n=len(core), prev=float(vp.reindex(list(core)).sum()),
                             now=float(vn.reindex(list(core)).sum()),
                             gone=len(set(vp.index) - set(vn.index)),
                             new=len(set(vn.index) - set(vp.index)))
            self.core['lost'] = self.core['prev'] - self.core['now']
            self.core['drop_pct'] = self.core['lost'] / self.core['prev'] * 100 if self.core['prev'] else 0
            self.core['share_of_month'] = self.core['lost'] / max(self.people[self.y]['visits'], 1) * 100
            gone = list(set(vp.index) - set(vn.index))
            if gone:
                self.core['gone_one_visit'] = int((vp.reindex(gone) == 1).sum())
                self.core['gone_mean'] = float(vp.reindex(gone).mean())
                self.core['core_mean'] = float(vp.reindex(list(core)).mean()) if core else 0

    # ------------------------------------------------------------------ formats
    def _formats(self):
        X = self.D.sessions
        if X is None:
            return
        s = self._sl(X, self.y)
        if s.empty:
            return
        g = s.groupby('_cls').agg(sessions=('SessionID', 'size'), seats=('_cap', 'sum'), att=('CheckedIn', 'sum'),
                                  book=('Booked', 'sum'), lc=('LateCancelled', 'sum'), comp=('Complimentary', 'sum'),
                                  rev=('Revenue', 'sum'))
        g['fill'] = g['att'] / g['seats'] * 100
        g['rpc'] = g['rev'] / g['sessions']
        g['rph'] = g['rev'] / g['att'].replace(0, np.nan)
        g['share_sessions'] = g['sessions'] / len(s) * 100
        self.formats = g.sort_values('att', ascending=False)
        self.formats_main = g[g['sessions'] >= 3].sort_values('att', ascending=False)
        # members per format, from check-ins when available
        a = self._ck(self.y)
        if a is not None and 'Cleaned Class' in a.columns:
            mf = a.groupby('Cleaned Class').agg(members=('Member ID', 'nunique'), att=('Member ID', 'size'))
            mf['per'] = mf['att'] / mf['members']
            self.fmt_members = mf
        # the multi-format ladder, all time
        N = getattr(self.D, 'new', None)
        if N is not None and 'No of Formats' in N.columns:
            pass

    # ------------------------------------------------------------------ trainers
    def _trainers(self):
        X = self.D.sessions
        if X is None:
            return
        s = self._sl(X, self.y)
        if s.empty or not s['_trainer'].notna().any():
            return
        t = s.groupby('_trainer').agg(sessions=('SessionID', 'size'), att=('CheckedIn', 'sum'),
                                      seats=('_cap', 'sum'), book=('Booked', 'sum'),
                                      lc=('LateCancelled', 'sum'), rev=('Revenue', 'sum'))
        t['fill'] = t['att'] / t['seats'] * 100
        t['rpc'] = t['rev'] / t['sessions']
        t['rph'] = t['rev'] / t['att'].replace(0, np.nan)
        t['lc_rate'] = t['lc'] / t['book'].replace(0, np.nan) * 100
        t['formats'] = s.groupby('_trainer')['_cls'].nunique()
        self.trainers = t.sort_values('rev', ascending=False)

    # ------------------------------------------------------------------ timing
    def _timing(self):
        X = self.D.sessions
        if X is None:
            return
        s = self._sl(X, self.y)
        if s.empty:
            return
        h = s.groupby(s['_hr'].astype('Int64')).agg(sessions=('SessionID', 'size'), seats=('_cap', 'sum'),
                                                    att=('CheckedIn', 'sum'), rev=('Revenue', 'sum'))
        h['fill'] = h['att'] / h['seats'] * 100
        self.hours = h
        d = s.groupby('_day').agg(sessions=('SessionID', 'size'), seats=('_cap', 'sum'), att=('CheckedIn', 'sum'),
                                  rev=('Revenue', 'sum')).reindex(DAYS)
        d['fill'] = d['att'] / d['seats'] * 100
        self.days = d

    # ------------------------------------------------------------------ cancels
    def _cancel(self):
        X = self.D.sessions
        if X is None:
            return
        self.lc_year = {}
        for y in [self.y] + self.prev:
            s = self._sl(X, y)
            if s.empty:
                continue
            self.lc_year[y] = dict(lc=float(s['LateCancelled'].sum()), book=float(s['Booked'].sum()),
                                   att=float(s['CheckedIn'].sum()))
            self.lc_year[y]['rate'] = self.lc_year[y]['lc'] / self.lc_year[y]['book'] * 100 if self.lc_year[y]['book'] else 0
        s = self._sl(X, self.y)
        if not s.empty:
            self.lc_fmt = s.groupby('_cls')['LateCancelled'].sum().sort_values(ascending=False)
            a = self._ck(self.y)
            if a is not None and len(a):
                att = a.groupby('Cleaned Class').size()
                self.lc_fmt = pd.DataFrame({'lc': self.lc_fmt, 'att': att.reindex(self.lc_fmt.index)})
                self.lc_fmt['per100'] = self.lc_fmt['lc'] / self.lc_fmt['att'].replace(0, np.nan) * 100
        ck = self._ck(self.y, attended=False, cancelled=True)
        if ck is not None and len(ck):
            self.lc_members = ck.groupby('Member ID').size().sort_values(ascending=False)
            self.lc_n = int(len(ck))
            self.lc_conc = dict(members=len(self.lc_members), per=self.lc_members.sum(),
                                three_plus=int((self.lc_members >= 3).sum()),
                                top10_share=float(self.lc_members.nlargest(10).sum() / self.lc_members.sum() * 100))
            self.lc_hour = ck.groupby(ck['_dt'].dt.hour).size()
            self.lc_dow = ck.groupby(ck['_dt'].dt.day_name()).size().reindex(DAYS).fillna(0)

    # ------------------------------------------------------------------ discount
    def _discount(self):
        S = getattr(self.D, 'sales', None)
        if S is None:
            return
        d = S[S['_loc'] == self.studio].copy()
        self.disc_year = {}
        for y in [self.y] + self.prev + [self.y - 3, self.y - 4]:
            s = d[d['_dt'].dt.year == y]
            if s.empty:
                continue
            self.disc_year[y] = dict(lines=len(s), disc=float(s['disc'].sum()), gross=float(s['gross'].sum()),
                                     spread=float(s['has_disc'].mean() * 100))
            self.disc_year[y]['depth'] = (self.disc_year[y]['disc'] / self.disc_year[y]['gross'] * 100
                                          if self.disc_year[y]['gross'] else 0)
        yr = d[d['_dt'].dt.year == self.y]
        if not yr.empty:
            for key, col in [('disc_prod', 'Cleaned Product'), ('disc_seller', 'Sold By')]:
                if col in yr.columns:
                    g = yr.groupby(col).agg(lines=('val', 'size'), disc=('disc', 'sum'), gross=('gross', 'sum'),
                                            spread=('has_disc', 'mean'))
                    g['depth'] = g['disc'] / g['gross'].replace(0, np.nan) * 100
                    g['spread'] = g['spread'] * 100
                    setattr(self, key, g[g['lines'] >= 8].sort_values('depth', ascending=False))

    # ------------------------------------------------------------------ lapse
    def _lapse(self):
        L = getattr(self.D, 'lapsed', None)
        if L is None:
            return
        d = L[L['_loc'] == self.studio]
        if d.empty:
            return
        self.has['lapsed'] = True
        self.led = dict(rows=len(d), members=int(d['Member ID'].nunique()))
        pay = d[d['Membership Name'].astype(str).str.contains('Complimentary|Staff', case=False, na=False) == False]
        if 'Amount Paid' in d.columns:
            pay = d[d['Amount Paid'].fillna(0) > 0]
        self.led['paid'] = len(pay); self.led['paid_members'] = int(pay['Member ID'].nunique()) if len(pay) else 0
        self.led['cash'] = float(pay['Amount Paid'].sum()) if 'Amount Paid' in pay else 0
        if 'Derived Status' in d.columns:
            self.status_mix = d['Derived Status'].value_counts()
        if len(pay) and 'Amount Paid' in pay.columns:
            self.ticket = float(pay['Amount Paid'].mean())
            lapsed = pay[pay['Derived Status'] == 'Lapsed'] if 'Derived Status' in pay else pay
            self.led['lapsed_cash'] = float(lapsed['Amount Paid'].sum())
            self.led['lapsed_share'] = self.led['lapsed_cash'] / self.led['cash'] * 100 if self.led['cash'] else 0
        # survival curve
        if 'Purchase Date_d' in pay.columns and len(pay):
            p = pay[pay['Purchase Date_d'].notna()].copy()
            ends = [c for c in ['Churned Date_d', 'End Date_d'] if c in p.columns]
            p['ended'] = p[ends].min(axis=1) if ends else pd.NaT
            p['life'] = (p['ended'] - p['Purchase Date_d']).dt.days
            p['life'] = p['life'].where(p['life'] >= 0)
            p['cens'] = (pd.Timestamp.today().normalize() - p['Purchase Date_d']).dt.days
            p['obs'] = p['life'].fillna(p['cens'])
            pts = [7, 14, 30, 60, 90, 180, 365]
            self.surv = pd.DataFrame({'Point': [f'Day {k}' for k in pts[:-1]] + ['One year'],
                                      'still': [(p['obs'] > k).mean() * 100 for k in pts]})
            self.surv['ended'] = 100 - self.surv['still']
            self.surv_n = len(p)
            self.median_life = float(p['obs'].median())
        if 'Membership Duration (Days)' in pay.columns and len(pay):
            q = pay[pay['Membership Duration (Days)'] >= 0]
            self.dur = q.groupby(pd.cut(q['Membership Duration (Days)'], [-1, 1, 7, 30, 60, 90, 180, 400, 99999],
                     labels=['same day', '2 to 7 days', '8 to 30 days', '31 to 60 days', '61 to 90 days',
                             '91 to 180 days', '181 to 365 days', 'over a year']), observed=True).agg(
                n=('Member ID', 'size'), ticket=('Amount Paid', 'mean'), cls=('Total Sessions Completed', 'mean')).reset_index()
        if 'Membership Name' in pay.columns and len(pay):
            r = pay.assign(fam=pay['Membership Name'].astype(str).str.replace(r'^Studio\s*', '', regex=True).str.strip())
            g = r.groupby('fam').agg(sold=('Member ID', 'size'), members=('Member ID', 'nunique'),
                                     cash=('Amount Paid', 'sum'), ticket=('Amount Paid', 'mean'),
                                     days=('Membership Duration (Days)', 'mean'),
                                     live=('Derived Status', lambda x: x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100))
            self.products = g[g['sold'] >= 10].sort_values('sold', ascending=False)
        if 'Sessions Used %' in pay.columns:
            u = pay[pay['Sessions Used %'].notna()]
            if len(u):
                self.unused_n = len(u)
                self.unused_left = float(u['Remaining Sessions'].sum())
                self.unused_low = int((u['Sessions Used %'] <= 25).sum())
                self.unused_full = int((u['Sessions Used %'] >= 100).sum())
        if 'Days Since Last Visit' in d.columns:
            rc = d[d['Days Since Last Visit'].notna()]
            if len(rc):
                self.recency = rc.groupby(pd.cut(rc['Days Since Last Visit'], [-1, 60, 180, 99999],
                                          labels=['warm \u2014 60 days or less', 'cooling \u2014 61 to 180 days',
                                                  'gone \u2014 over 180 days']), observed=True).agg(
                    members=('Member ID', 'nunique'), cash=('Amount Paid', 'mean')).reset_index()
        if 'Cancellation Rate %' in pay.columns:
            c = pay.copy(); c['b'] = pd.cut(c['Cancellation Rate %'], [-1, 0, 25, 50, 1000],
                                            labels=['never cancels', 'up to 25%', '26 to 50%', 'over 50%'])
            self.cancel_bands = c.groupby('b', observed=True).agg(
                n=('Member ID', 'size'), cls=('Total Sessions Completed', 'mean'),
                late=('Late Cancellations', 'mean'), live=('Derived Status', lambda x: x.isin(['Renewed', 'Active', 'Renewal Grace Period']).mean() * 100)).reset_index()

    # ------------------------------------------------------------------ leads
    def _leads(self):
        Ld = getattr(self.D, 'leads', None)
        if Ld is None:
            return
        d = Ld[Ld['_loc'] == self.studio]
        if d.empty:
            return
        self.has['leads'] = True
        self.LD = d
        self.lead_n = len(d)
        self.lead_fun = dict(leads=len(d), trial=int((d['Trial Status'] == 'Trial Completed').sum()),
                             won=int(d['won'].sum()),
                             retained=int((d['Retention Status'] == 'Retained').sum()) if 'Retention Status' in d else 0)
        self.lead_fun['trial_pct'] = self.lead_fun['trial'] / len(d) * 100
        self.lead_fun['won_pct'] = self.lead_fun['won'] / len(d) * 100
        self.lead_fun['retained_pct'] = self.lead_fun['retained'] / len(d) * 100
        if 'Status' in d.columns:
            self.lead_status = d['Status'].value_counts()
        if 'Channel' in d.columns:
            self.lead_ch = d.groupby('Channel').agg(leads=('ID', 'size') if 'ID' in d else ('Status', 'size'),
                    trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100),
                    won=('won', lambda x: x.mean() * 100), ltv=('LTVn', 'mean')).sort_values('leads', ascending=False)
        if 'Source Name' in d.columns:
            self.lead_src = d.groupby('Source Name').agg(
                    leads=('won', 'size'), trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100),
                    won=('won', lambda x: x.mean() * 100), ltv=('LTVn', 'mean')).sort_values('leads', ascending=False)
            self.lead_src = self.lead_src[self.lead_src['leads'] >= 20]
        if 'Associate' in d.columns:
            self.lead_assoc = d.groupby('Associate').agg(
                    leads=('won', 'size'), trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100),
                    won=('won', lambda x: x.mean() * 100), ltv=('LTVn', 'mean')).sort_values('won', ascending=False)
            self.lead_assoc = self.lead_assoc[self.lead_assoc['leads'] >= 20]
        c_conv = next((c for c in ['Converted To Customer At_d', 'Converted To Customer At'] if c in d.columns), None)
        if c_conv and '_dt' in d.columns:
            w = d[d['won'] & d[c_conv].notna() & d['_dt'].notna()].copy()
            w['span'] = (pd.to_datetime(w[c_conv], errors='coerce') - w['_dt']).dt.days
            w = w[w['span'] >= 0]
            if len(w):
                b = pd.cut(w['span'], [-1, 0, 1, 3, 7, 14, 30, 90, 100000],
                           labels=['same day', 'next day', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days',
                                   '31 to 90 days', '91 days or more'])
                self.lead_span = w.assign(b=b).groupby('b', observed=True).agg(
                    n=('span', 'size'), ltv=('LTVn', 'mean'), visits=('Visits', 'mean') if 'Visits' in w else ('span', 'mean')).reset_index()
                self.lead_same = float((w['span'] == 0).mean() * 100)
        if 'Class Type' in d.columns:
            g = d.groupby('Class Type').agg(leads=('won', 'size'), trial=('Trial Status', lambda x: (x == 'Trial Completed').mean() * 100),
                                            won=('won', lambda x: x.mean() * 100)).sort_values('leads', ascending=False)
            self.lead_class = g[g['leads'] >= 30]
        if 'Trial Status' in d.columns:
            self.trial_gate = d.groupby('Trial Status').agg(leads=('won', 'size'), won=('won', 'sum'),
                                                            won_pct=('won', lambda x: x.mean() * 100),
                                                            ltv=('LTVn', 'mean'))
        # the period the user asked for, inside the lead file
        if '_dt' in d.columns:
            self.lead_month = int(((d['_dt'] >= rng(self.y, self.m)[0]) & (d['_dt'] < rng(self.y, self.m)[1])).sum())
            m = d[(d['_dt'] >= rng(self.y - 1, self.m)[0]) & (d['_dt'] < rng(self.y - 1, self.m)[1])]
            self.lead_month_prev = int(len(m))
            mo = d.groupby(d['_dt'].dt.to_period('M')).agg(leads=('won', 'size'), won=('won', 'sum'),
                                                           won_pct=('won', lambda x: x.mean() * 100))
            self.lead_trend = mo[mo.index >= pd.Period(f'{self.y-1}-01')]
            op = d[d['Status'].astype(str).str.strip() == 'Open']
            if len(op):
                age = (pd.Timestamp.today().normalize() - op['_dt']).dt.days
                self.open_n = len(op)
                self.open_age = float(age.mean())
                self.open_fresh = int((age <= 30).sum())
                self.open_stale = int((age > 180).sum())
                if 'Stage Name' in op.columns:
                    self.open_stage = op['Stage Name'].value_counts().head(8)

    # ------------------------------------------------------------------ behaviour
    def _behaviour(self):
        a = self._ck(self.y)
        if a is None or a.empty:
            return
        self.has['checkins'] = True
        self.beh = {}
        self.beh['hours'] = a.groupby(a['_dt'].dt.hour).size()
        self.beh['days'] = a.groupby(a['_dt'].dt.day_name()).size().reindex(DAYS).fillna(0)
        if self.V is not None and len(self.V):
            self.beh['freq'] = self.V.value_counts().sort_index()
            top = self.V.nlargest(max(int(len(self.V) * .1), 1))
            self.beh['top_share'] = float(top.sum() / self.V.sum() * 100)
            self.beh['once'] = int((self.V == 1).sum())
            self.beh['once_share'] = self.beh['once'] / len(self.V) * 100
            self.beh['top_n'] = len(top)
        # hourly preference per member
        h = a.assign(h=a['_dt'].dt.hour).groupby('Member ID')['h'].agg(lambda s: s.mode().iloc[0])
        self.beh['pref'] = h
        self.beh['morning'] = int((h < 12).sum()); self.beh['evening'] = int((h >= 17).sum())
        self.beh['midday'] = int(((h >= 12) & (h < 17)).sum())
        for k, sel in [('morning', h < 12), ('evening', h >= 17), ('midday', (h >= 12) & (h < 17))]:
            grp = a[a['Member ID'].isin(sel[sel].index)]
            self.beh[k + '_per'] = grp.groupby('Member ID').size().mean() if len(grp) else 0
        # gaps - the whole ledger, not just this month
        CK = self.D.checkins
        al = CK[(CK['_loc'] == self.studio) & (CK['Checked In'] == True)].sort_values('_dt')
        g = al.groupby('Member ID')['_dt'].diff().dt.days.dropna()
        if len(g):
            GB = ['the same day', 'one day later', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days',
                  '31 to 90 days', 'over 90 days']
            self.beh['gap'] = pd.cut(g, [-1, 0, 1, 3, 7, 14, 30, 90, 100000], labels=GB).value_counts().reindex(GB)
            self.beh['gap_med'] = float(g.median())
            self.beh['gap_week'] = float((g <= 7).mean() * 100)
        # purchase gaps
        S = getattr(self.D, 'sales', None)
        if S is not None:
            s = S[S['_loc'] == self.studio].sort_values('_dt')
            at = pd.to_datetime(s['Created At'] if 'Created At' in s else s['_dt'], errors='coerce')
            pg = s.assign(_at=at).groupby('Member ID')['_at'].diff().dt.days.dropna()
            if len(pg):
                PB = ['30 days or less', '31 to 60 days', '61 to 90 days', '91 to 180 days', '181 to 365 days', 'over a year']
                self.beh['pgap'] = pd.cut(pg, [-1, 30, 60, 90, 180, 365, 100000], labels=PB).value_counts().reindex(PB)
                self.beh['pgap_med'] = float(pg.median())
                self.beh['pgap_month'] = float((pg <= 30).mean() * 100)
            n = s.groupby('Member ID')['Sale ID'].nunique() if 'Sale ID' in s.columns else s.groupby('Member ID').size()
            self.beh['one_buy'] = float((n == 1).mean() * 100)
        # month-by-month frequency, whole ledger
        al2 = al[al['_dt'] >= f'{self.y-2}-01-01'].copy()
        al2['mo'] = al2['_dt'].dt.to_period('M')
        mo = al2.groupby('mo').agg(visits=('Member ID', 'size'), members=('Member ID', 'nunique'))
        mo['per'] = mo['visits'] / mo['members']
        self.beh['monthly'] = mo
        # formats used per member this month
        if 'Cleaned Class' in a.columns:
            mfo = a.groupby('Member ID')['Cleaned Class'].nunique()
            self.beh['multi'] = float((mfo >= 2).mean() * 100)
            loy = a.groupby(['Member ID', 'Cleaned Class']).size()
            self.beh['same3_members'] = int(loy[loy >= 3].reset_index()['Member ID'].nunique())

    # ------------------------------------------------------------------ new
    def newfile(self):
        N = getattr(self.D, 'new', None)
        if N is None:
            return {}
        d = N[N['_loc'] == self.studio]
        out = {}
        if 'First Purchase Post Trial' in d.columns:
            g = d.dropna(subset=['First Purchase Post Trial']).groupby('First Purchase Post Trial').agg(
                n=('Member Id', 'size'), ltv=('Ltv', 'mean'), visits=('No of Visits', 'mean'))
            out['first'] = g[g['n'] >= 20].sort_values('ltv', ascending=False)
        if 'Days To Second Visit' in d.columns:
            dd = d.dropna(subset=['Days To Second Visit'])
            if len(dd):
                b = pd.cut(dd['Days To Second Visit'], [-1, 1, 3, 7, 14, 30, 100000],
                           labels=['next day or sooner', '2 to 3 days', '4 to 7 days', '8 to 14 days', '15 to 30 days', '31 days or more'])
                out['speed'] = dd.assign(b=b).groupby('b', observed=True).agg(n=('Ltv', 'size'), ltv=('Ltv', 'mean')).reset_index()
        if 'Source' in d.columns:
            g = d.groupby('Source').agg(n=('Ltv', 'size'), ltv=('Ltv', 'mean'), visits=('No of Visits', 'mean'))
            g['conv'] = d.groupby('Source')['Conversion Status'].apply(lambda x: (x == 'Converted').mean() * 100)
            out['source'] = g[g['n'] >= 20].sort_values('n', ascending=False)
        out['n'] = len(d)
        return out
