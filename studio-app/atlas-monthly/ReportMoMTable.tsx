import { useMemo, useState } from "react";
import { CalendarRange } from "lucide-react";
import { DropdownField } from "./ui/DropdownField";
import { MonthlyTableControls, type MonthlyTableState } from "./MonthlyTableControls";
import { definition, reportFmt as fmt, reportDelta as delta, exportCSV } from "./adapter";
import { monthLabel, monthShort } from "./period";
type Row = Record<string, unknown>;
const label = (id: string) => definition(id)?.label ?? id;
const shift = (key: string, months: number) => { const d = new Date(`${key}-01T00:00:00Z`); return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - months, 1)).toISOString().slice(0, 7); };
export function ReportMoMTable({ history, ids, selected, onSelect, title }: { history: Row[]; ids: string[]; selected: string; onSelect: (month: string) => void; title: string }) {
  const drill = undefined; // The local selection never changes report date filters.
  const [controls, setControls] = useState<MonthlyTableState>({ periods: 0, newest: true, dense: true, mode: "absolute" });
  const [search, setSearch] = useState(""), [measure, setMeasure] = useState("all"), [baseline, setBaseline] = useState(false);
  const all = useMemo(() => [...history].sort((a, b) => String(a.month).localeCompare(String(b.month))), [history]);
  const latest = String(all.at(-1)?.month ?? "");
  const months = all.slice(-controls.periods).map(r => String(r.month));
  if (controls.newest) months.reverse();
  const row = (key: string) => all.find(r => r.month === key);
  const prior = (key: string) => shift(key, controls.mode === "year" ? 12 : 1);
  const usable = ids.filter(id => definition(id) && all.some(r => r[id] != null));
  const visible = usable.filter(id => (measure === "all" || id === measure) && label(id).toLowerCase().includes(search.toLowerCase()));
  const first = (id: string) => all.find(r => r[id] != null)?.[id];
  const cell = (id: string, key: string) => {
    const value = row(key)?.[id], prev = row(prior(key))?.[id];
    if (controls.mode === "absolute") return fmt(id, value);
    if (typeof value !== "number" || (prev != null && typeof prev !== "number")) return "—";
    if (controls.mode === "index") return value == null || !first(id) ? "—" : (Number(value) / Number(first(id)) * 100).toFixed(0);
    return value == null || prev == null ? "—" : delta(id, value, prev);
  };
  return <>
    <MonthlyTableControls comparisons state={controls} onChange={patch => setControls(c => ({ ...c, ...patch }))}
      modes={[["absolute", "Values"], ["change", "MoM Δ"], ["year", "YoY Δ"], ["index", "Index 100"]]}
      onExport={() => exportCSV(`report-${title.toLowerCase().replaceAll(" ", "-")}-${controls.mode}`, visible.map(id => ({ Measure: label(id), ...Object.fromEntries(months.map(m => [m, cell(id, m)])) })))}>
      <label>Measure<DropdownField aria-label="Monthly metric" value={measure} onChange={e => setMeasure(e.target.value)}><option value="all">All measures</option>{usable.map(id => <option key={id} value={id}>{label(id)}</option>)}</DropdownField></label>
      <input type="search" aria-label="Search monthly measures" placeholder="Find a measure…" value={search} onChange={e => setSearch(e.target.value)} />
      <label className="monthly-check"><input type="checkbox" checked={baseline} onChange={e => setBaseline(e.target.checked)} />Show baseline</label>
    </MonthlyTableControls>
    <div className={`table-scroll mom monthly-table${controls.dense ? " compact" : " comfortable"}`} tabIndex={0} aria-label="Monthly comparison table; scroll for more periods">
      <table>
        <thead><tr><th>Performance measure</th>{months.map(m => <th key={m} className={[m === latest && "latest-month", m === selected && "deck-selected-month"].filter(Boolean).join(" ") || undefined}>{monthShort(m)}{m === latest && <small>Latest available</small>}</th>)}</tr></thead>
        <tbody>{visible.map(id => <tr key={id}>
          <th scope="row" title={definition(id)?.description}>{label(id)}</th>
          {months.map(m => {
            const value = row(m)?.[id], prev = row(prior(m))?.[id];
            const movement = value == null || prev == null ? null : Number(value) - Number(prev);
            const tone = movement == null || movement === 0 ? "neutral" : (movement > 0) === (definition(id)?.higherIsBetter ?? true) ? "positive" : "negative";
            return <td key={m} className={[m === latest && "latest-month", m === selected && "deck-selected-month"].filter(Boolean).join(" ") || undefined}>
              <button className={`monthly-value ${["change", "year"].includes(controls.mode) ? tone : ""}`} title={`${monthLabel(m)}: ${fmt(id, value)} · baseline ${fmt(id, prev)}. Click to highlight this month without changing report dates.`} onClick={() => { onSelect(m);  }}>
                {cell(id, m)}{baseline && <small>{controls.mode === "year" ? "Last year" : "Prior month"} {fmt(id, prev)}</small>}
              </button></td>;
          })}
        </tr>)}</tbody>
      </table>
    </div>
    {!visible.length && <p className="empty-state">No measures match this selection.</p>}
    <p className="ranking-foot"><CalendarRange size={12}/> Frozen at report build. Rates use percentage points; Index 100 uses the first available month. All available months are shown by default. Date filters do not change this table. Click a value to highlight its month.</p>
  </>;
}
