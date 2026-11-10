from scraper.api_client import get_pokemon_list, get_pokemon, get_species
from scraper.parsers import parse_pokemon, parse_species
from db.storage import init_db, save_pokemon_batch
from analyze.reports import some_works
from core.config import BATCH_SIZE
from time import perf_counter


def run():
    pokemon_names = [p["name"] for p in get_pokemon_list()]
    batch = []

    for i, name in enumerate(pokemon_names, 1):
        pokemon_data = get_pokemon(name)
        parsed_pokemon_data = parse_pokemon(pokemon_data)

        species_data = get_species(parsed_pokemon_data["species_name"])
        parsed_species_data = parse_species(species_data)

        parsed_data = parsed_pokemon_data | parsed_species_data
        batch.append(parsed_data)

        if i >= BATCH_SIZE:
            save_pokemon_batch(batch)
            batch = []

    if batch:
        save_pokemon_batch(batch)


if __name__ == "__main__":
    init_db()
    run()