# Copilot instructions

## Project overview

This is a Python 3.11 data-collection, analysis, and local web-dashboard project for Pokémon data from PokeAPI. `main.py` coordinates the ingestion pipeline: it gets the Pokémon list, fetches each Pokémon and its species, parses both responses, and saves the combined records to SQLite in batches. `app.py` serves that local database through JSON endpoints and a browser UI.

The project is divided by responsibility:

- `scraper/api_client.py` requests the Pokémon list, Pokémon details, and species details. It reads cached JSON from `data/cache/` when present; its module-level `USE_CACHE` controls writing fetched responses.
- `scraper/parsers.py` converts PokeAPI responses into flat dictionaries consumed by persistence. `parse_pokemon` supplies `species_name`; `main.py` combines it with the result of `parse_species`.
- `db/models.py` defines the SQLite tables and parameterized insert statements. `db/storage.py` initializes the schema and writes batches to `data/pokemon.db`, whose path is defined in `core/config.py`.
- `app.py` uses Python's built-in `http.server` to expose overview, paginated/filterable Pokémon-list, and Pokémon-detail JSON endpoints. It queries the same SQLite tables used by ingestion.
- `static/index.html`, `static/app.css`, and `static/app.js` implement the dashboard with vanilla HTML, CSS, and JavaScript. The browser fetches data from `app.py`; keep API response fields and frontend rendering in sync when changing either side.
- `research_data.ipynb` loads the SQLite tables into pandas and explores Pokémon stats and experience with plots. `analyze/reports.py` contains a small DataFrame reporting function.

`data/` is gitignored and holds the generated database and API cache; do not treat its contents as source code.

## Commands

The Conda environment is declared in `environment.yml` (Python 3.11):

```powershell
conda env create -f environment.yml
conda activate pokemon-analyze
```

Run the scraper from the repository root:

```powershell
python main.py
```

After the database has been populated, start the dashboard from the repository root:

```powershell
python app.py
```

Open `http://127.0.0.1:8000` in a browser. The server reads `data/pokemon.db`; it does not populate the database itself.

There is no configured build, lint, or test runner, and no test suite currently exists. Consequently, there is no single-test command.

## Repository-specific conventions

- Keep API response handling in `scraper/api_client.py` and field extraction/normalization in `scraper/parsers.py`; database schema and SQL belong in `db/models.py`, with connection and batch operations in `db/storage.py`.
- Parser outputs are dictionaries keyed to the SQLite insert parameters. When changing a parsed field, update the matching schema/insert statement and any downstream DataFrame usage as needed.
- Pokémon height is converted from PokeAPI decimeters to centimeters and weight from hectograms to kilograms. Types and non-hidden abilities are stored as comma-separated strings; the first type is `primary_type`.
- Pokémon and species rows are written together from the same parsed batch. The Pokémon `species_id` and species table `id` refer to the PokeAPI species identifier.
- `core/config.py` owns the database path and ingestion batch size. The API client currently defines its own URL, cache paths, timeout, and cache-write flag; account for that split when changing configuration behavior.
- `app.py` keeps SQL query logic in the request handler and uses bound parameters for user-supplied search/filter values. Sort columns are selected from a fixed allowlist; preserve that constraint when extending sorting.
- The frontend builds HTML for Pokémon and insight cards dynamically. Escape data-derived text with the existing `escapeHtml` helper, and update the static UI and JSON endpoint together when adding or renaming fields.
