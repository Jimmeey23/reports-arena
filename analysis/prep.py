import pandas as pd, numpy as np

SRC = '/home/user/uploads/Day End Report - Part 1 - New (9).csv'

def load():
    df = pd.read_csv(SRC, low_memory=False)

    # ---- normalise the cohort month (mixed "Sep-2026" / "September-2025" formats)
    m = df['Month Year'].astype(str)
    df['cohort'] = pd.to_datetime(m, format='%b-%Y', errors='coerce')
    mask = df['cohort'].isna()
    df.loc[mask, 'cohort'] = pd.to_datetime(m[mask], format='%B-%Y', errors='coerce')

    def num(s):
        return pd.to_numeric(s.astype(str).str.replace(r'[₹,\s]', '', regex=True), errors='coerce')

    df['ltv']         = num(df['Ltv'])
    df['ltv_pt']      = num(df['Ltv Post Trial'])
    df['first_pv']    = num(df['First Purchase Value'])
    df['last_pv']     = num(df['Last Purchase Value'])
    df['avg_pv']      = num(df['Avg Purchase Value Post Trial'])
    df['days_active'] = num(df['Days Active'])
    df['days_since']  = num(df['Days Since Last Visit'])
    df['conv_span']   = num(df['Conversion Span (Days)'])
    df['days_2nd']    = num(df['Days To Second Visit'])
    df['latecancel']  = pd.to_numeric(df['Late Cancel Rate Post Trial'].astype(str).str.rstrip('%'), errors='coerce') / 100

    df['fvd'] = pd.to_datetime(df['First Visit Date'], errors='coerce')
    df['lvd'] = pd.to_datetime(df['Last Visit Date'], errors='coerce')
    df['lpd'] = pd.to_datetime(df['Last Purchase Date'], errors='coerce')
    df['fpd'] = pd.to_datetime(df['First Purchase Date'], errors='coerce')

    df['is_import']   = df['First Visit Entity Name'].eq('Import Visits')
    df['bandra_home'] = df['Home Location'].eq('Supreme HQ, Bandra')
    df['bandra_fv']   = df['First Visit Location'].eq('Supreme HQ, Bandra')
    df['converted']   = df['Conversion Status'].eq('Converted')
    df['revenue']     = df['ltv'].fillna(0)

    # dedupe: legacy 'Import Visits' placeholder rows (first visit 2020-01-01) that
    # duplicate a member who also has a real tracked first visit
    df['placeholder'] = df['fvd'].eq(pd.Timestamp('2020-01-01 17:30'))
    return df


if __name__ == '__main__':
    df = load()
    print('rows', len(df))
    print('snapshot: max last visit', df['lvd'].max(), '| max last purchase', df['lpd'].max())
    print('import rows', df['is_import'].sum(), '| placeholder-2020 rows', df['placeholder'].sum())
    print('bandra home', df['bandra_home'].sum(), '| bandra first visit', df['bandra_fv'].sum())
    print()
    print('=== Sep-2026 cohort by First Visit Location ===')
    s = df[df['cohort'] == pd.Timestamp('2026-09-01')]
    print(s['First Visit Location'].value_counts(dropna=False))
    print()
    print('=== cohort sizes 2026 by month ===')
    t = df[df['cohort'].dt.year == 2026]
    print(t.groupby(t['cohort'].dt.to_period('M')).size())
