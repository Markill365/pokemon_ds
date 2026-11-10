import json
import os
from pathlib import Path
from requests import get
from core.config import *


DETAILS_DIR.mkdir(parents=True, exist_ok=True)
SPECIES_DIR.mkdir(parents=True, exist_ok=True)


def get_pokemon_list(limit=100000, offset=0):
    '''
    возвращает список всех покемонов вида: {"name": "bulbasaur", "url": "..."}
    '''

    cache_file = CACHE_DIR / "pokemon_list.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)

    url = f"{BASE_URL}/pokemon/?limit={limit}&offset={offset}"
    response = get(url, timeout=30)
    response.raise_for_status()
    results = response.json()["results"]

    if USE_CACHE:
        with open(cache_file, "w") as f:
            json.dump(results, f)

    return results


def get_pokemon(name_or_id):
    '''
    возвращает информацию про одного покемона
    '''

    cache_details = DETAILS_DIR / f"{name_or_id}.json"
    if cache_details.exists() and cache_details.is_file():
        with open(cache_details, 'r') as f:
            return json.load(f)

    url = f"{BASE_URL}/pokemon/{name_or_id}"
    response = get(url, timeout=30)
    response.raise_for_status()
    results = response.json()

    if USE_CACHE:
        with open(cache_details, 'w') as f:
            json.dump(results, f)

    return results


def get_species(name_or_id):
    '''
    возвращает информацию о виде покемона
    '''

    cash_species = SPECIES_DIR / f"{name_or_id}.json"
    if cash_species.exists() and cash_species.is_file():
        with open(cash_species, 'r') as f:
            return json.load(f)

    url = f"{BASE_URL}/pokemon-species/{name_or_id}"
    response = get(url, timeout=30)
    response.raise_for_status()
    results = response.json()

    if USE_CACHE:
        with open(cash_species, 'w') as f:
            json.dump(results, f)

    return results
