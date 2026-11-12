from pathlib import Path

# --- Пути ---
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "pokemon.db"
DETAILS_DIR = CACHE_DIR / "details"
SPECIES_DIR = CACHE_DIR / "species"

# --- API ---
BASE_URL = "https://pokeapi.co/api/v2"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 5
RETRY_DELAY = 2

# --- Парсинг ---
BATCH_SIZE = 600
POKEMON_LIMIT = 100000

# --- Флаги ---
USE_CACHE = True
DEBUG = False
