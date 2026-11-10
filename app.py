import json
import logging
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from core.config import DB_PATH


ROOT_DIR = Path(__file__).parent
HOST = "127.0.0.1"
PORT = 8000
PAGE_SIZE = 24
SORT_COLUMNS = {
    "number": "p.id",
    "name": "p.name COLLATE NOCASE",
    "stats": "p.total_stats",
    "attack": "p.attack",
    "speed": "p.speed",
}
STATIC_FILES = {
    "/static/app.css": ("static/app.css", "text/css; charset=utf-8"),
    "/static/app.js": ("static/app.js", "text/javascript; charset=utf-8"),
}
POKEMON_ROUTE = re.compile(r"^/api/pokemon/(\d+)$")


def connect_database():
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Pokémon database not found: {DB_PATH}")
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        try:
            if parsed_url.path == "/":
                self.serve_file(ROOT_DIR / "static" / "index.html", "text/html; charset=utf-8")
            elif parsed_url.path in STATIC_FILES:
                file_path, content_type = STATIC_FILES[parsed_url.path]
                self.serve_file(ROOT_DIR / file_path, content_type)
            elif parsed_url.path == "/api/overview":
                self.serve_json(self.get_overview())
            elif parsed_url.path == "/api/pokemon":
                self.serve_json(self.get_pokemon(parse_qs(parsed_url.query)))
            else:
                match = POKEMON_ROUTE.fullmatch(parsed_url.path)
                if match:
                    pokemon = self.get_pokemon_detail(int(match.group(1)))
                    if pokemon is None:
                        self.serve_json({"error": "Pokémon not found."}, status=404)
                    else:
                        self.serve_json(pokemon)
                else:
                    self.send_error(404, "Not found")
        except ValueError as error:
            self.serve_json({"error": str(error)}, status=400)
        except (sqlite3.Error, OSError) as error:
            logging.exception("Request failed for %s", self.path)
            self.serve_json({"error": str(error)}, status=500)

    def serve_file(self, path, content_type):
        try:
            content = path.read_bytes()
        except OSError:
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def serve_json(self, payload, status=200):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def get_overview(self):
        with connect_database() as connection:
            summary = connection.execute(
                """
                SELECT COUNT(*) AS pokemon_count,
                       COUNT(DISTINCT s.generation) AS generation_count,
                       SUM(CASE WHEN s.is_legendary = 1 OR s.is_mythical = 1 THEN 1 ELSE 0 END) AS legendary_count,
                       ROUND(AVG(p.total_stats)) AS average_stats
                FROM pokemons p
                LEFT JOIN species s ON p.species_id = s.id
                """
            ).fetchone()
            types = connection.execute(
                """
                SELECT primary_type AS name, COUNT(*) AS count
                FROM pokemons
                WHERE primary_type IS NOT NULL
                GROUP BY primary_type
                ORDER BY count DESC, name
                """
            ).fetchall()
            generations = connection.execute(
                """
                SELECT DISTINCT generation
                FROM species
                WHERE generation IS NOT NULL
                ORDER BY generation
                """
            ).fetchall()
            top_pokemon = connection.execute(
                """
                SELECT p.id, p.name, p.total_stats, p.sprite_url, p.primary_type
                FROM pokemons p
                WHERE p.is_default = 1
                ORDER BY p.total_stats DESC, p.id
                LIMIT 5
                """
            ).fetchall()
        return {
            "summary": dict(summary),
            "types": [dict(row) for row in types],
            "generations": [row["generation"] for row in generations],
            "top_pokemon": [dict(row) for row in top_pokemon],
        }

    def get_pokemon(self, query):
        search = query.get("q", [""])[0].strip()
        pokemon_type = query.get("type", [""])[0].strip().lower()
        generation_value = query.get("generation", [""])[0].strip()
        sort = query.get("sort", ["number"])[0]
        page_value = query.get("page", ["1"])[0]

        try:
            page = max(1, int(page_value))
        except ValueError as error:
            raise ValueError("Page must be a positive integer.") from error
        if generation_value:
            try:
                generation = int(generation_value)
            except ValueError as error:
                raise ValueError("Generation must be a positive integer.") from error
            if generation < 1:
                raise ValueError("Generation must be a positive integer.")
        else:
            generation = None

        order_by = SORT_COLUMNS.get(sort)
        if order_by is None:
            raise ValueError("Unsupported sort option.")

        conditions = []
        parameters = []
        if search:
            escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append("p.name LIKE ? ESCAPE '\\'")
            parameters.append(f"%{escaped_search}%")
        if pokemon_type:
            conditions.append(
                "instr(',' || replace(lower(p.types), ', ', ',') || ',', ',' || ? || ',') > 0"
            )
            parameters.append(pokemon_type)
        if generation is not None:
            conditions.append("s.generation = ?")
            parameters.append(generation)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * PAGE_SIZE
        with connect_database() as connection:
            count = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM pokemons p
                LEFT JOIN species s ON p.species_id = s.id
                {where_clause}
                """,
                parameters,
            ).fetchone()[0]
            rows = connection.execute(
                f"""
                SELECT p.id, p.name, p.types, p.primary_type, p.total_stats,
                       p.hp, p.attack, p.defense, p.special_attack,
                       p.special_defense, p.speed, p.sprite_url,
                       s.generation, s.is_legendary, s.is_mythical
                FROM pokemons p
                LEFT JOIN species s ON p.species_id = s.id
                {where_clause}
                ORDER BY {order_by} {'DESC' if sort in ('stats', 'attack', 'speed') else 'ASC'}, p.id
                LIMIT ? OFFSET ?
                """,
                [*parameters, PAGE_SIZE, offset],
            ).fetchall()
        return {
            "items": [dict(row) for row in rows],
            "count": count,
            "page": page,
            "page_size": PAGE_SIZE,
            "pages": (count + PAGE_SIZE - 1) // PAGE_SIZE,
        }

    def get_pokemon_detail(self, pokemon_id):
        with connect_database() as connection:
            pokemon = connection.execute(
                """
                SELECT p.*, s.generation, s.gender_rate, s.capture_rate,
                       s.base_happiness, s.is_baby, s.is_legendary, s.is_mythical
                FROM pokemons p
                LEFT JOIN species s ON p.species_id = s.id
                WHERE p.id = ?
                """,
                (pokemon_id,),
            ).fetchone()
        if pokemon is None:
            return None
        return dict(pokemon)

    def log_message(self, format_string, *args):
        logging.info("%s - %s", self.address_string(), format_string % args)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Pokémon Atlas is running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Pokémon Atlas.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
