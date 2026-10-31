# Design system — Liga MX para aficionados

## Product context
- Product: public web dashboard of Mexican first-division football (Liga MX), 2012–2026, built with **Streamlit** (Python). URL: ligamx-analytics.streamlit.app.
- Audience: **football fans** (aficionados), not analysts. Language: Mexican Spanish, sports-press tone. No analyst jargon.
- Job to be done: "Open the app, pick a tournament (e.g. Apertura 2025) and in seconds know who won / who leads, how the table looks, how my team is doing, and how the big rivalries (clásicos) stand."
- Data: match results only (no players, no xG). Every sentence and number is computed from real data. Never show invented stats.

## Information architecture (single page)
1. Header row: small brand mark "⚽ Liga MX" (left) + tournament selector (right).
2. Hero: computed headline (h1), e.g. "Toluca, campeón del Apertura 2025", plus a one-line deck ("Le ganó la final a Tigres UANL en penales…").
3. For finished tournaments: two big indicators "🏆 Campeón" and "Subcampeón".
4. Four tournament stats: Partidos jugados, Goles por partido, Ganó el local (%), Empates (%).
5. Source caption (football-data.co.uk + Wikipedia, dates).
6. Tabs: **Tabla** (sub-tabs General / 🏠 Local / ✈️ Visitante) · **Lo destacado** (5 headline-style bullet facts) · **Mi equipo** (team selector, position, points, gap to leader, record "8G-4E-2P", last 5 with ✅➖❌, results table, cumulative-points chart in an expander, team history with titles, bar chart of points per tournament with 🏆 over title bars) · **Cara a cara** (clásico selector, wins A / draws / wins B, facts, last 5) · **Partidos** (week selector "Del 23 al 25 de octubre (9 partidos)", table: Cuándo, Local, Marcador, Visitante, Fase).
7. Footer caption with data license note.

## Standings table
Columns: Pos, Equipo, PTS, JJ, JG, JE, JP, GF, GC, DIF, Últimos 5 (✅ ➖ ❌), Zona, Final.
Zone rows tinted: green (Cuartos de final / Liguilla) rgba(34,160,80,0.18); amber (Play-in / Reclasificación) rgba(237,161,0,0.22). Pos and Equipo pinned on mobile.

## Typography
- Headings: **Barlow Condensed** 600/700 (sports-press / scoreboard feel). h1 3rem, h2 2rem, h3 1.5rem, h4 1.25rem.
- Body: **Barlow** 400/500/600, 16px.
- Metric values: Barlow 600, 2.25rem.
- Sentence case everywhere. No all-caps labels, no tracked-out eyebrows.

## Color
Light theme: background #ffffff; secondary surfaces #eef3ef; borders #d6dfd9; text Streamlit default dark gray (#31333f); primary/accent **#2a78d6** (blue = "your team / selection").
Dark theme (night pitch): background **#0b1310**; secondary surfaces #15201b; borders #24332c; text #e6ece8; primary #3987e5.
Chart series: team #2a78d6, comparison #d95926, incomplete tournaments gray #8a8984. Validated for color-blind safety and contrast on both backgrounds.
Status icons are emoji: ✅ win, ➖ draw, ❌ loss, 🏆 title.

## Shape, spacing, motion
- Border radius 6px (0.375rem). Thin 1px borders, no heavy shadows, no gradients as decoration.
- Generous vertical rhythm between sections; content max width ~1200px; left-aligned.
- No decorative motion.

## Hard constraints (implementation is Streamlit)
- Available building blocks: st.title/markdown headings, st.caption, st.metric (label, value, help tooltip), st.tabs, st.selectbox, st.dataframe (with row tinting and pinned columns), st.expander, st.columns / horizontal containers, Plotly charts, st.info/st.warning boxes, limited custom CSS.
- Designs must be buildable from those blocks plus light CSS. Avoid complex custom widgets, carousels, hover-only interactions, images/photos or team crests (we do not have licensed logos).
- Must work at 400px mobile width and on light and dark themes.
- Use ONLY the fonts, colors, spacing and component styles defined here.
