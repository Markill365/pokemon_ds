def parse_pokemon(json):
    '''
    парсит сырой json с данными о покемоне в словарь с keys = ['id', 'name', 'species_name', 'height', 'weight', 'base_experience', 'is_default', 'sprite_url', 'types', 'primary_type', 'abilities', 'hidden_abilities', 'hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed', 'total_stats']
    '''

    columns = {"id": json["id"], "name": json["name"], "species_name": json["species"]["name"], "height": int(json["height"]) * 10,
               "weight": int(json["weight"]) / 10, "base_experience": json["base_experience"],
               "is_default": json["is_default"], "sprite_url": json["sprites"]["front_default"],
               "types": ", ".join(t["type"]["name"] for t in json["types"]),
               "primary_type": json["types"][0]["type"]["name"] if json["types"] else None}

    abilities = [a["ability"]["name"] for a in json["abilities"] if not a["is_hidden"]]
    hidden_abilities = [a["ability"]["name"] for a in json["abilities"] if a["is_hidden"]]
    columns["abilities"] = ", ".join(abilities)
    columns["hidden_abilities"] = hidden_abilities[0] if hidden_abilities else None

    stats_map = {s["stat"]["name"]: s["base_stat"] for s in json["stats"]}
    columns["hp"] = stats_map.get("hp", 0)
    columns["attack"] = stats_map.get("attack", 0)
    columns["defense"] = stats_map.get("defense", 0)
    columns["special_attack"] = stats_map.get("special-attack", 0)
    columns["special_defense"] = stats_map.get("special-defense", 0)
    columns["speed"] = stats_map.get("speed", 0)

    columns["total_stats"] = sum([
        columns["hp"], columns["attack"], columns["defense"],
        columns["special_attack"], columns["special_defense"], columns["speed"]
    ])

    return columns


def parse_species(json):
    '''
    парсит сырой json с данными о виде покемона в словарь с keys = ['species_id', 'gender_rate', 'capture_rate', 'base_happiness', 'is_baby', 'is_legendary', 'is_mythical', 'generation']
    '''

    columns = {"species_id": json["id"], "gender_rate": json["gender_rate"], "capture_rate": json["capture_rate"],
               "base_happiness": json["base_happiness"], "is_baby": json["is_baby"],
               "is_legendary": json["is_legendary"], "is_mythical": json["is_mythical"],
               'generation': int(json["generation"]["url"].rstrip("/").split("/")[-1])}

    return columns
