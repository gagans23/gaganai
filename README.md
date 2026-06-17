# gagansachdeva.com

Static personal website and writing hub.

## Local preview

Open `index.html` in a browser, or run:

```bash
python3 -m http.server 8080
```

The project also has a small `make` workflow:

```bash
make validate   # validate generated data before publishing
make bake       # validate, then rebuild radar.html, feed.xml, and radar archive pages
make serve      # preview locally on port 8080
```

## Automation setup

Create a local Python environment for the daily intelligence pipeline:

```bash
make setup
cp .env.example .env
```

Then add `PARALLEL_API_KEY` in `.env` or export it in your shell.

Run the daily pipeline:

```bash
./automation/gcc-ai-newsletter/run_today.sh --dry-run
```

Publish only validated data changes:

```bash
./automation/update_daily_intelligence.sh
```

GitHub Actions validates `data/radar-signals.js`, `data/podcast-intelligence.js`, and `data/signal-archive.json` before baking crawlable static outputs.

## Deploy

This site is designed for GitHub Pages.
