# Studio Intelligence

A local Python web app that generates source-backed studio performance reviews
from freshly uploaded day-end exports. Requires Python 3 and pandas.

## Run

```sh
cd studio-app
python3 server.py --port 8017
```

Open `http://localhost:8017`. Each new page starts with an empty upload batch.
Historical uploads and bundled exports are never automatically imported.
Previously generated reviews appear in the report library. Startup does not
generate demo reports. Files are identified from their header rows.

Upload the fresh exports, select a studio/month and chapters, then generate a
review. Only the current page's upload batch contributes to those calculations.
Missing sources disable the relevant chapters. Saved reviews remain available
across reloads and server restarts in `runs/<id>/`.

## Full-view reader

Reviews open as a full document occupying the viewport. The floating icon at the
bottom right opens annotation, appearance, editing and presenter controls.
The contents panel collapses after five seconds without activity; its menu icon
reopens it. Pin navigation to keep it visible.

The toolkit includes themes, accents, layouts, text size, density, section search,
chart visibility, evidence expansion, table sorting/filtering, record details,
CSV exports, speech playback, fullscreen and print/save as PDF.
Use **Edit components** (or **Edit report text**) to edit headings, narratives, metric cards, table cells, chapter heroes and charts. Click a component for its inline controls; **Edit** enables direct editing with Save/Cancel. **Design** opens HTML and appearance controls for alignment, typography, spacing, corners and colours. Changes to displayed figures are presentation overrides; computed source records remain unchanged. **Download edited report** embeds personal
edits, annotations, speaker notes and appearance in a standalone HTML file.

## Speaker notes and teleprompter

**Speaker notes / annotations** or **Teleprompter** opens the right drawer.
`Alt+N` opens it; Escape closes the drawers. Notes are private and saved per
section. Annotations are visible to hosted participants. Selected report text
can be quoted into an annotation.

The teleprompter uses private notes when present, or that section's narrative.
It supports start/pause/reset, scroll speed, text size and mirrored text, plus a
presentation timer. Closing the drawer pauses the prompter.

## Guided sessions

Every visitor can choose **Host this report** to create an eight-character meeting
code. Another visitor can enter that code in the report library or toolkit.
Participants follow the host's report section, scroll position, evidence state,
chart visibility, table filters and sorting, edits and annotations. Copy the meeting
link from the hosting controls to share the guided view. They can choose **Explore independently**
and resume following. Only the host can change the shared presentation state or
end the meeting. Host sessions can be resumed after reload or a server restart.
Private speaker notes are never included in the meeting response.

All participants must reach the same running server URL. On another computer,
use the host machine's reachable LAN address and port, rather than `localhost`.
This is a guided report view, not an audio/video meeting service. Internet-wide
joining requires hosting this application at a shared reachable URL.

## Persistence

`data/workspace.sqlite3` stores per-browser report preferences, notes, annotations,
edits and guided session state. A random browser identity is retained in local
storage; it is not an account login. The server enforces host ownership with that
identity. Local copies and pending-save retries protect editing when the server
connection is interrupted. The browser identity must remain available to restore
that browser's private workspace. Opening in another browser creates a separate
workspace. Keep `data/` and `runs/` when moving or restarting the application.

Fresh uploads are archived under `data/batches/<batch>/`, but are not loaded into
subsequent new upload pages. Legacy files in `data/uploaded/` remain on disk and
are excluded. Reader assets are embedded for offline viewing. Hosting and server
saving require the running app; offline downloads retain their embedded workspace
and local browser notes.

The optional AI summary call sends computed facts to the selected provider.
Hosting shares the report view with participants who have the code. Avoid sharing
meeting codes outside the intended audience.

Original files from interface changes are under `backups/`. This checkout has no
Git repository, so no commit or remote deployment was performed.

## AI analyst and layout editing

Every generated run carries `metrics.json`, a compact snapshot of its headline
metrics, definitions and top lists, distilled from the same Metrics object the
chapters are built from. The in-report assistant is grounded in that pack only —
raw rows never enter a prompt.

- **Floating AI widget** (`AI` button): ask about any metric, chapter or figure.
  The deterministic metrics engine resolves data questions directly from the pack
  at **zero tokens**; a configured model only extends coverage for free-form
  questions and rewrites. Every model reply is checked against the pack — any
  figure it invents is rejected. Identical questions are served from cache.
- **Speaker notes launcher** (📝 button): opens the private speaker-notes drawer
  directly from the report interface.
- **Layout mode** (`Layout` in the report tools): hover any block to edit its
  text, add blocks above/below, delete it, or hand it to the AI (`✦`) for a
  rewrite or a new block. Structural edits persist per run via
  `POST /api/edits`, so everyone viewing that run sees the same document.
- **AI settings** (⚙ in the widget): connect any OpenAI-compatible endpoint
  (`key`, `model`, `base`). Keys stay in the server process; the browser never
  stores them. Without a key the built-in analyst keeps answering data questions.

API surface: `GET /api/ai/status`, `GET /api/ai/context?run=`,
`POST /api/ai/chat`, `POST /api/ai/edit`, `POST /api/ai/create`,
`POST /api/ai/key`, `GET|POST /api/edits`.

### Persistence and context-aware responses

Chat history, structural edits, the answer cache, **the generated reports
themselves** and non-secret **app configuration** persist through
`data/ai.sqlite3` by default. Set `SUPABASE_URL` and `SUPABASE_KEY` to mirror
everything into Supabase tables (`chat_messages`, `report_edits`, `ai_cache`,
`reports`, `app_config`); the app uses PostgREST over the standard library, so
no SDK is required, and it falls back to SQLite transparently if Supabase is
unreachable. Suggested schema is documented in `ai/store.py`. Copy
`.env.example` to `.env` and export the variables before starting the server.

Each generated review is saved with a compact metric digest (studio, period,
per-chapter KPIs and key facts). On startup, on-disk reviews are pushed into
the report store, and the AI assistant is handed the digests of earlier periods
for the same studio as comparison context — a few tokens per period, so period
questions ("how does this compare to last month?") stay grounded. Secrets stay
in the environment and are never stored.

API surface additions: `GET /api/reports/history?studio=&limit=`,
`GET /api/config`, `POST /api/config`.

### Token discipline

Answers the deterministic engine resolves cost 0 tokens; the model only sees the
~1–2k-token metrics pack plus the last four turns; context size per run is
reported by `GET /api/ai/status`; every reply keeps full content quality because
the numbers come from the engine, not the model.

## Checks

```sh
python3 -m unittest discover -s tests -p '*_test.py' -v
NODE_PATH=/path/to/jsdom/node_modules node tests/report-tools.cjs
NODE_PATH=/path/to/jsdom/node_modules node tests/presenter.cjs
NODE_PATH=/path/to/jsdom/node_modules node tests/guest-session.cjs
```

The checks exercise actual HTTP upload/generation routes, SQLite reopening,
meeting ownership, private-note separation, reader controls and simulated host/
guest DOM interactions. `tests/metrics_reconciliation_test.py` pins every
headline formula to the atlas metric dictionary, and
`tests/ai_assistant_test.py` pins the AI pack, deterministic answers, grounding
guard and persistence. Live browser rendering, speech, fullscreen, printing and
cross-device network access require verification in the target browsers.


## Chapter heroes and metric evidence explorer

On desktop, contents and speaker panels dock beside the document and reserve
exactly their own width. On narrow phones the panels sit in document flow above
the report, so neither panel covers report content. Continuous chapters include
an animated abstract contour graphic, oversized chapter number, description,
and looping metric marquee. Reduced-motion preferences stop the animation; the
toolkit also offers **Pause chapter motion**.

Metric cards, table group labels and numeric table cells open an evidence explorer.
It follows Atlas's scoped-record and grouped-breakdown approach with local report
metric definitions: capacity-weighted utilisation, revenue per session/attendance,
distinct buyers, paid memberships, trials/wins and attended visits. Search,
grouping, sortable columns, visible-column selection, 50-row pagination and CSV
export are available in the modal. Saved source scopes distinguish month records
from studio-wide lead/membership ledgers. Missing values remain `n/a`.

Newly generated reviews embed a capped preview of the frozen source records
(5,000 rows per source, so pages stay loadable) and additionally write the
**complete, uncapped file** to `records.json` next to the report. The explorer
fetches that file in the background, so drill-downs, breakdowns and totals are
computed over every record — the preview cap never hides rows. If the full file
is unavailable (older runs, offline export), the modal falls back to the
embedded preview and labels the boundary.

Drill-downs are context-aware: clicking a metric cell opens the item-level
records behind that exact cell and shows per-item analytics (count, sum, mean,
median, min, max, distinct members) for the clicked measure, not a repeat of
the chapter aggregate. Every table in every chapter renders a totals row
(currency and counts summed, percentages shown as a labelled average). Dates
are displayed in IST (`15 Sep 2026` / `15 Sep 2026, 17:45 IST`). Historical
reviews without snapshots use their actual saved supporting tables; the modal
labels this boundary and never substitutes newer uploads for historical evidence.

Additional interaction check:
`NODE_PATH=/path/to/jsdom/node_modules node tests/chapter-explorer.cjs`.

## Period scope and component authoring

Leads use the selected month’s enquiry-creation cohort. Membership detail uses the selected month’s purchase cohort, while dated churn/expiry events use their own event dates within the report month. Visit and purchase gaps, discount breakdowns and newcomer funnels use the selected month. Payroll does not fall back to another month. Same-month prior-year comparisons remain explicitly labelled. Export-state status, usage and lifetime fields cannot reconstruct historical month-end outcomes and are labelled accordingly. Saved older reviews remain frozen; generate a new review to recalculate them.

Manual component tools support paragraphs, callouts, metric cards, lists, tables and SVG charts. AI replace/add previews structured components for review before Apply. Shared structural and appearance changes save per report run. Failed saves retain a local pending copy; **Save all changes** retries them. Offline edited downloads embed structural edits and appearance.

Additional checks: `python3 tests/period_scope_test.py` and `NODE_PATH=/path/to/jsdom/node_modules node tests/report-edit.cjs`.


Report evidence and presentation controls
-----------------------------------------
Metric cards and numeric table cells open the saved studio/month source rows.
The explorer waits for the complete records file, supports dataset selection,
search across all available fields, column selection, 25/50/100/250-row pages,
CSV export and full item details. Click a computed group to inspect its items.
If a table label cannot be resolved to a source field, the explorer explicitly
shows the full source population rather than substituting one summary row.

Use Present in the report header for a section agenda, previous/next navigation,
elapsed-time pause/reset, laser pointer, fullscreen and audience blackout.
Arrow keys and Page Up/Down navigate; B toggles blackout; Escape returns from
blackout or finishes presentation. Finish restores the report and sidebar state.

AI requests reuse complete exact-input results within the current process for
24 hours (maximum 128 entries) and share identical concurrent requests. Evidence,
model, instructions, output limits and credential identity are part of the key.
Failures, incomplete provider responses and rejected grounding checks are not
retained. Report summary rewrites must retain source figures and at least the
original word and sentence counts; failed checks keep the original analysis.
Cache entries do not persist across a server restart.
