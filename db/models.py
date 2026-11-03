SCHEMA = '''
    CREATE TABLE IF NOT EXISTS pokemons (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        height INT,
        weight REAL,
        hp INT,
        attack INT, 
        defense INT, 
        special_attack INT, 
        special_defense INT, 
        speed INT, 
        total_stats INT,
        base_experience INT,
        types TEXT,
        primary_type TEXT,
        abilities TEXT, 
        hidden_abilities TEXT,
        is_default INT,
        species_id INT,
        sprite_url TEXT
    );
    
    CREATE TABLE IF NOT EXISTS species (
        id INTEGER PRIMARY KEY,
        name TEXT,
        gender_rate INT,
        capture_rate INT,
        base_happiness INT,
        is_baby INT,
        is_legendary INT,
        is_mythical INT,
        generation INT
    );
'''

SAVE_SCHEMA_POKEMON = '''
    INSERT OR REPLACE INTO pokemons (
        id, name, height, weight, hp, attack, defense, special_attack, special_defense, speed, total_stats,
        base_experience, types, primary_type, abilities, hidden_abilities, is_default, species_id, sprite_url
    ) VALUES (
        :id, :name, :height, :weight, :hp, :attack, :defense, :special_attack, :special_defense, :speed, :total_stats,
        :base_experience, :types, :primary_type, :abilities, :hidden_abilities, :is_default, :species_id, :sprite_url
    )
'''

SAVE_SCHEMA_SPECIES = '''
    INSERT OR REPLACE INTO species (
        id, name, gender_rate, capture_rate, base_happiness, is_baby, is_legendary, 
        is_mythical, generation
    ) VALUES (
        :species_id, :species_name, :gender_rate, :capture_rate, :base_happiness, :is_baby, :is_legendary, 
        :is_mythical, :generation
    )
'''