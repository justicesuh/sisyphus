# sisyphus

A job search automation tool built with Django.

## Stack

- Python 3.14, Django 6, Celery, Redis, PostgreSQL
- Playwright + BeautifulSoup for scraping
- OpenAI for job fit scoring
- HTMX frontend

## Setup

```sh
make build
make up
make migrate
```

## Usage

```sh
make serve        # Start dev server
make test         # Run tests with coverage
make lint         # Lint with ruff
make migrations   # Generate migrations
make migrate      # Apply migrations
make shell        # Open a shell in the container
make logs         # Tail container logs
```

## Search Pipeline

1. **Scrape** — Parse job listings from configured sources
2. **Rules** — Apply user-defined rules to filter/categorize jobs
3. **Populate** — Fetch full job descriptions
4. **Rules** — Re-apply rules with full descriptions available
5. **Score** — Score remaining new jobs against the user's resume
