# Atlas monthly components

Copied directly from https://github.com/Jimmeey23/atlas/tree/2de9206a340e4d6a320a38f09022fea48a94f202:
- `src/components/report/deck/ReportTrends.tsx` (`ReportMoMTable`)
- `src/components/MonthlyTableControls.tsx`
- `src/components/ui/DropdownField.tsx`
- `src/report/period.ts` (month labels)
- `src/design/refinement.css` (monthly table styles)

Local adapters replace Atlas metric definitions, export and filter-store dependencies with the report’s embedded full-history snapshot. All months is the default period setting. Clicking a month only highlights it. There is no connection to report date filters. Non-numeric metrics are shown in Values mode and have no numerical comparisons. Missing values remain unavailable.

Build with `npm install` then `npm run build`. The checked-in bundle is embedded in standalone HTML downloads; it needs no CDN or runtime Node server.
