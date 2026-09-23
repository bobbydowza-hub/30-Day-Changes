# 30 Day Changes

Homepage for *30 Day Changes* — one self-help book at a time, thirty days actually trying to live it, filed honestly across Health, Wealth, Family, and Sh*ts & Giggles.

## Structure

- `index.html` — the homepage. All CSS and JS inline, hero photo embedded as a data URI.
- `books.html` — the full 20-book reading queue, cover art per book.
- `covers/` — book cover images (sourced from Open Library's covers API).
- `fetch_covers.py` — re-run this (`python3 fetch_covers.py`) to re-fetch/update cover art if the reading queue changes. Needs normal internet access (a real Terminal, not a restricted sandbox).

No build step, no framework — plain static files, deployed as-is.

## Deploying

Drop this repo into Netlify (or GitHub Pages) as a static site — the publish directory is the repo root, there's no build command to run.
