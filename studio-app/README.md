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
Narrative text can be edited with **Edit report text**. Computed table figures
remain tied to their source data. **Download edited report** embeds personal
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

## Checks

```sh
python3 -m unittest discover -s tests -p '*_test.py' -v
NODE_PATH=/path/to/jsdom/node_modules node tests/report-tools.cjs
NODE_PATH=/path/to/jsdom/node_modules node tests/presenter.cjs
NODE_PATH=/path/to/jsdom/node_modules node tests/guest-session.cjs
```

The checks exercise actual HTTP upload/generation routes, SQLite reopening,
meeting ownership, private-note separation, reader controls and simulated host/
guest DOM interactions. Live browser rendering, speech, fullscreen, printing and
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

Newly generated reviews embed frozen source records from the same uploaded dataset
used for the report, capped at 5,000 records per source with an explicit truncation
notice. Explorer totals describe the retained subset when truncated. Historical
reviews without snapshots use their actual saved supporting tables; the modal
labels this boundary and never substitutes newer uploads for historical evidence.

Additional interaction check:
`NODE_PATH=/path/to/jsdom/node_modules node tests/chapter-explorer.cjs`.
