from db.models import SCHEMA, SAVE_SCHEMA_POKEMON, SAVE_SCHEMA_SPECIES
from core.config import DB_PATH
import sqlite3


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def save_pokemon_batch(batch):
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(SAVE_SCHEMA_POKEMON, batch)
        conn.executemany(SAVE_SCHEMA_SPECIES, batch)
        conn.commit()
