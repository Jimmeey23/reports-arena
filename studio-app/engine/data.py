"""Generic loader for the studio's day-end exports.

Every file the studio produces is identified by its header row rather than by
its filename, so a user can drop any mix of exports into the app in any order
and the engine will sort them out. Nothing here is specific to a location or a
period: the frames carry a location column and a date column, and the metrics
layer cuts them.
"""
from __future__ import annotations
import os, io, glob, json, re
import pandas as pd, numpy as np

# --------------------------------------------------------------------- helpers
# Google Sheets exports store some numeric cells as dates: a value like
# 1417.5 arrives as "1903-11-17, 12:00:00", the number of days (and fraction
# of a day) since the Sheets epoch of 1899-12-30. The recovery below matches
# the atlas normaliser so amounts such as Amount Paid and Total Sessions
# Completed read as money and counts instead of dropping out as NaN.
_SERIAL = r'^(1[89]\d\d|190\d)-(\d\d)-(\d\d), (\d\d):(\d\d):(\d\d)$'
_SHEETS_EPOCH = pd.Timestamp('1899-12-30')


def num(s):
    if s is None:
        return pd.Series(dtype='float64')
    scalar = not isinstance(s, pd.Series)
    sr = pd.Series([s]) if scalar else s
    st = sr.astype(str).str.strip()
    serial = st.str.match(_SERIAL, na=False)
    cleaned = st.str.replace(r'[₹,\s]', '', regex=True).replace({'nan': None, '-': '', '': None})
    out = pd.to_numeric(cleaned, errors='coerce')
    if serial.any():
        ts = pd.to_datetime(st[serial].str.replace(',', '', regex=False), errors='coerce')
        out = out.copy()
        out.loc[serial] = ((ts - _SHEETS_EPOCH).dt.total_seconds() / 86400).round(2)
    return out.iloc[0] if scalar else out


def is_new_label(v):
    """Atlas rule for the New file's Is New column: any label containing the
    word 'new' is a trial newcomer ('Not New' excluded first); labels naming a
    known non-trial visit are false; anything unrecognised stays None."""
    if v is None:
        return None
    t = str(v).strip()
    if not t or t.lower() in ('nan', '-', 'none'):
        return None
    if re.match(r'^not\b', t, re.I):
        return False
    if re.search(r'\bnew\b', t, re.I):
        return True
    if re.match(r'^(existing|returning|repeat|staff|family)', t, re.I):
        return False
    low = t.lower()
    if low in ('true', 'yes', '1'):
        return True
    if low in ('false', 'no', '0'):
        return False
    return None

def dparse(s, dayfirst=False):
    """Two-pass date parse. These exports mix two conventions in one column -
    '2024-01-18, 17:45:31' and '15/06/2024 07:05:49' - and a single call gets
    one of them wrong, which is enough to move a median lifetime by weeks."""
    s = pd.Series(s).astype(str).str.strip().replace({'nan': None, 'NaT': None, '': None})
    out = pd.Series(pd.NaT, index=s.index, dtype='datetime64[ns]')
    iso = s.str.match(r'^\d{4}-\d{2}-\d{2}', na=False)
    if iso.any():
        out[iso] = pd.to_datetime(s[iso].str.replace(',', '', regex=False), errors='coerce')
    rest = (~iso) & s.notna()
    if rest.any():
        out[rest] = pd.to_datetime(s[rest], errors='coerce', dayfirst=True)
    return out

# --------------------------------------------------------------------- kinds
KINDS = [
    # name, required-ish columns, date column, location column
    ('sessions',     ['session id', 'capacity', 'booked', 'checkedin'], 'date', 'location'),
    ('teacher',      ['teacher', 'recurring'],                          None,   'location'),
    ('payroll',      ['total sessions', 'month year'],                   None,   'location'),
    ('newmembers',   ['first visit location', 'ltv'],                   'first visit date', 'first visit location'),
    ('sales',        ['sale id', 'calculated location'],                'created at', 'calculated location'),
    ('lapsed',       ['membership name', 'derived status'],             'purchase date', 'primary location'),
    ('leads',        ['source name', 'trial status'],                   'created at', 'center'),
    ('checkins',     ['checked in', 'is late cancelled'],               'date (ist)', 'location'),
]

def sniff(path: str) -> str | None:
    """Return the kind of an export from its header row alone."""
    try:
        head = pd.read_csv(path, nrows=3, low_memory=False)
    except Exception:
        return None
    cols = {str(c).strip().lower() for c in head.columns}
    best, score = None, 0
    for kind, need, _, _ in KINDS:
        hit = sum(1 for n in need if n in cols)
        if hit and hit / len(need) > score:
            best, score = kind, hit / len(need)
    return best if score >= 0.75 else None

# --------------------------------------------------------------------- loader
class Source:
    """One uploaded file plus what we worked out about it."""
    def __init__(self, path, kind, df):
        self.path, self.kind, self.df = path, kind, df
        self.rows = len(df)
    @property
    def name(self):
        return os.path.basename(self.path)

class Dataset:
    """A bag of sources with the frames the metrics layer needs."""

    def __init__(self, paths, log=print, priority=None):
        self.log, self.sources, self.warnings = log, [], []
        priority = priority or {}
        def rank(p):
            for i, (pref, sc) in enumerate(priority.items()):
                if p.startswith(pref):
                    return sc
            return 0
        self._rank = rank
        for p in sorted(paths, key=lambda x: -rank(x)):
            k = sniff(p)
            if not k:
                self.warnings.append(f'{os.path.basename(p)}: not recognised, skipped')
                continue
            try:
                df = pd.read_csv(p, low_memory=False)
            except Exception as e:
                self.warnings.append(f'{os.path.basename(p)}: could not be read ({e})')
                continue
            # Prefer fresh uploads, retaining the full session export over summaries.
            dup = next((s for s in self.sources if s.kind == k), None)
            if dup:
                same_rank = rank(p) == rank(dup.path)
                newer_upload = same_rank and rank(p) == 2 and os.stat(p).st_mtime_ns > os.stat(dup.path).st_mtime_ns
                bigger_seed = same_rank and rank(p) != 2 and len(df) > dup.rows
                better = (rank(p) > rank(dup.path)) or newer_upload or bigger_seed
                if same_rank and k == 'sessions':
                    summary = lambda frame: any(str(c).lower().replace(' ', '') == 'totalcheckedinsum' for c in frame.columns)
                    if summary(df) != summary(dup.df):
                        better = not summary(df)
                if better:
                    self.sources.remove(dup); self.sources.append(Source(p, k, df))
                    self.warnings.append(f'{os.path.basename(p)}: the {k} data already on file was superseded by this export')
                else:
                    self.warnings.append(f'{os.path.basename(p)}: {k} data already covered by {os.path.basename(dup.path)}')
                continue
            self.sources.append(Source(p, k, df))
            log(f'  {k:<12} {os.path.basename(p)[:44]:<46} {len(df):>7,} rows')
        self.kinds = {s.kind: s for s in self.sources}
        self._prepare()

    # ------------------------------------------------------------------ frames
    def get(self, kind) -> pd.DataFrame | None:
        s = self.kinds.get(kind)
        return None if s is None else s.df

    def _prepare(self):
        col = lambda df, *names: next((c for c in df.columns if str(c).strip().lower() in names), None)

        # ---- sessions ------------------------------------------------
        X = self.get('sessions')
        if X is not None:
            X = X.copy()
            c_date = col(X, 'date', 'date (ist)')
            c_loc = col(X, 'location')
            X['_dt'] = dparse(X[c_date])
            X['_loc'] = X[c_loc].astype(str).str.strip()
            for a, b in [('Capacity', 'Capacity'), ('Booked', 'Booked'), ('CheckedIn', 'CheckedIn'),
                         ('LateCancelled', 'LateCancelled'), ('Complimentary', 'Complimentary'),
                         ('Revenue', 'Revenue'), ('Classes', 'Classes')]:
                if a in X.columns:
                    X[a] = num(X[a])
            for c in ['Capacity', 'Booked', 'CheckedIn', 'LateCancelled', 'Complimentary', 'Revenue',
                      'Classes', 'NonPaid', 'Memberships', 'Packages', 'IntroOffers', 'SingleClasses']:
                if c in X.columns:
                    X[c] = num(X[c]).fillna(0)
                else:
                    X[c] = 0.0
            X['Classes'] = X['Classes'].replace(0, 1)
            X['_cls'] = (X[col(X, 'class')] if col(X, 'class') else X[col(X, 'sessionname')]).astype(str).str.strip()
            X['_trainer'] = X[col(X, 'trainer')].astype(str).str.strip() if col(X, 'trainer') else ''
            X['_day'] = X[col(X, 'day')].astype(str).str.strip() if col(X, 'day') else ''
            c_t = col(X, 'time')
            X['_hr'] = pd.to_numeric(X[c_t].astype(str).str[:2], errors='coerce') if c_t else np.nan
            X['_type'] = X[col(X, 'type')].astype(str).str.strip() if col(X, 'type') else X['_cls']
            X = X[X['_dt'].notna()]
            X['_cap'] = X['Capacity'] / X['Classes'].clip(lower=1)
            self.sessions = X

        # ---- check-ins ------------------------------------------------
        CK = self.get('checkins')
        if CK is not None:
            CK = CK.copy()
            c_date = col(CK, 'date (ist)', 'date')
            c_loc = col(CK, 'location')
            CK['_dt'] = dparse(CK[c_date])
            CK['_loc'] = CK[c_loc].astype(str).str.strip()
            for c in ['Checked In', 'Is Late Cancelled', 'Complementary']:
                if c in CK.columns:
                    CK[c] = CK[c].astype(str).str.strip().str.lower().isin(['true', '1', 'yes'])
            # Paid is a monetary amount, not an attendance/payment flag.
            CK['Paid'] = num(CK['Paid']) if 'Paid' in CK.columns else np.nan
            CK['Paid Amount'] = CK['Paid']
            # Recorded teaching hours: durations arrive as Sheets serials or
            # plain minutes; implausible values are excluded rather than read.
            if 'Duration (Minutes)' in CK.columns:
                du = num(CK['Duration (Minutes)'])
                CK['Duration Minutes'] = du.where((du > 0) & (du <= 240))
            else:
                CK['Duration Minutes'] = np.nan
            CK['Class No'] = num(CK['Class No']) if 'Class No' in CK.columns else np.nan
            self.checkins = CK

        # ---- sales ----------------------------------------------------
        S = self.get('sales')
        if S is not None:
            S = S.copy()
            # Cash belongs to payment dates (atlas: sales are dated on
            # Payment Date, with Created At only as a fallback).
            c_date = col(S, 'payment date', 'created at', 'date')
            c_loc = col(S, 'calculated location', 'location')
            S['_dt'] = dparse(S[c_date], dayfirst=True)
            S['_loc'] = S[c_loc].astype(str).str.strip()
            c_val = col(S, 'payment value', 'value', 'sale value', 'amount')
            S['val'] = num(S[c_val]).fillna(0) if c_val else 0.0
            # VAT and net: collected net is payment value minus payment VAT on
            # the same lines. The Price Excluding VAT column is repeated at
            # sale grain and is never summed directly.
            c_vat = col(S, 'payment vat', 'vat')
            S['vat'] = num(S[c_vat]).fillna(0) if c_vat else 0.0
            S['net'] = S['val'] - S['vat']
            # Discounts: sale-level discount values repeat on every item row,
            # so the item-level figure (unit discount x quantity) is the one
            # that can be summed. Falls back to zero where the item columns
            # are absent.
            c_udisc = col(S, 'sale item unit discount value')
            c_qty = col(S, 'sale item quantity')
            if c_udisc and c_qty:
                ud = num(S[c_udisc]); qt = num(S[c_qty])
                S['disc'] = (ud * qt).where(ud.notna() & qt.notna(), 0.0).fillna(0.0)
            else:
                S['disc'] = 0.0
            S['units'] = num(S[c_qty]).fillna(0) if c_qty else 1.0
            S['gross'] = S['val'] + S['disc']
            S['has_disc'] = S['disc'] > 0
            # Cash collection counts successful, non-voided payments only.
            status = S[col(S, 'payment status', 'status')].astype(str).str.strip().str.lower() \
                if col(S, 'payment status', 'status') else pd.Series('succeeded', index=S.index)
            c_void = col(S, 'sec. is voided')
            voided = S[c_void].astype(str).str.strip().str.lower().isin(['true', '1', 'yes']) if c_void else False
            S['ok'] = status.isin(['succeeded', 'success', 'paid']) & ~voided
            self.sales = S

        # ---- new members ---------------------------------------------
        N = self.get('newmembers')
        if N is not None:
            N = N.copy()
            c_date = col(N, 'first visit date')
            N['_dt'] = dparse(N[c_date])
            N['_loc'] = N[col(N, 'first visit location')].astype(str).str.strip()
            for c in ['Ltv', 'No of Visits', 'Days To Second Visit', 'Visits Per Month',
                      'Visits Post Trial', 'First Purchase Value', 'Conversion Span (Days)',
                      'Total Purchases All Time', 'Days Since Last Visit', 'Days Active']:
                if c in N.columns:
                    N[c] = num(N[c])
            # Explicit newcomer flag: acquisition metrics must run on the
            # newcomer population only, not on every first-visit record.
            if 'Is New' in N.columns:
                N['is_new'] = N['Is New'].map(is_new_label)
            else:
                N['is_new'] = None
            self.new = N

        # ---- lapsed ---------------------------------------------------
        L = self.get('lapsed')
        if L is not None:
            L = L.copy()
            for src, dst in [('purchase date', 'Purchase Date_d'), ('churned date', 'Churned Date_d'),
                             ('end date', 'End Date_d'), ('last visit date', 'Last Visit Date_d')]:
                c = col(L, src)
                if c:
                    L[dst] = dparse(L[c], dayfirst=True)
            c_loc = col(L, 'primary location')
            L['_loc'] = L[c_loc].astype(str).str.strip()
            for c in ['Amount Paid', 'Original Amount (Before Discount)', 'Discount Value',
                      'Sessions Limit', 'Total Sessions Completed', 'Remaining Sessions', 'Late Cancellations',
                      'No Shows', 'Days Since Last Visit', 'Cancellation Rate %', 'Sessions Used %',
                      'Attendance Rate %', 'Membership Duration (Days)']:
                if c in L.columns:
                    L[c] = num(L[c])
            self.lapsed = L

        # ---- leads ----------------------------------------------------
        Ld = self.get('leads')
        if Ld is not None:
            Ld = Ld.copy()
            c_date = col(Ld, 'created at', 'created at_d')
            Ld['_dt'] = dparse(Ld[c_date])
            c_ctr = col(Ld, 'center', 'location')
            Ld['_loc'] = Ld[c_ctr].astype(str).str.strip()
            Ld['LTVn'] = num(Ld['LTV']) if 'LTV' in Ld.columns else np.nan
            Ld['won'] = Ld['Status'].astype(str).str.strip().eq('Won') if 'Status' in Ld.columns else False
            self.leads = Ld

        # ---- payroll / teacher ---------------------------------------
        for k, c_loc in [('payroll', 'location'), ('teacher', 'location')]:
            df = self.get(k)
            if df is not None:
                df = df.copy()
                c = col(df, c_loc)
                if c:
                    df['_loc'] = df[c].astype(str).str.strip()
                for c2 in df.columns:
                    if str(c2).lower().startswith(('total ', 'cycle ', 'strength ', 'barre ', 'recurring')):
                        df[c2] = num(df[c2])
                setattr(self, k, df)

    # ------------------------------------------------------------------ studios
    def studios(self):
        """Every location label the uploads carry, with a count of rows behind it."""
        out = {}
        for kind in ('sessions', 'sales', 'checkins', 'newmembers', 'lapsed', 'leads', 'payroll'):
            df = getattr(self, kind, None)
            if df is None or '_loc' not in df.columns:
                continue
            vc = df['_loc'].replace({'nan': np.nan, '': np.nan}).dropna().value_counts()
            for k, v in vc.items():
                out[k] = out.get(k, 0) + int(v)
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def months(self, studio):
        """Which months have session data for a studio - the periods worth offering."""
        df = self.sessions
        s = df[df['_loc'] == studio]
        if s.empty:
            return []
        per = s['_dt'].dt.to_period('M').dropna().value_counts().sort_index()
        # only offer months with real coverage
        return [(int(str(p)[:4]), int(str(p)[5:7]), int(n)) for p, n in per.items() if n >= 5]


# --------------------------------------------------------------------- discovery
def discover(dirpath):
    """Every readable export in a folder. Files are matched on their header
    row, so exports saved without a .csv extension are picked up too."""
    files = []
    for ext in ('*.csv', '*.CSV', '*.tsv', '*.txt'):
        files += glob.glob(os.path.join(dirpath, ext))
    for f in sorted(os.listdir(dirpath)):
        full = os.path.join(dirpath, f)
        if os.path.isdir(full) or f.startswith('.') or full in files:
            continue
        if os.path.splitext(f)[1].lower() in ('.csv', '.tsv', '.txt'):
            continue
        if os.path.getsize(full) < 500 or os.path.getsize(full) > 400_000_000:
            continue
        if sniff(full):
            files.append(full)
    return sorted(set(files))
