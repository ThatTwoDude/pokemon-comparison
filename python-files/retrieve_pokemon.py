import requests
import pandas as pd
from tqdm import tqdm
import time
import os

# Save path for partial csv
SAVE_PATH = "data/raw/pokemon_partial.csv"

# Only return JSOn if it is safe
def safe_json(response):
    # Safely return JSON, or return None if invalid.
    try:
        # Return Json
        return response.json()
    except:
        # Don't return Json
        return None

# Retrieve all pokemon (limit is 1025 because that is the total amount of pokemon)
def fetch_pokemon_data(limit=1025):
    # Dataframe with all Pokemon data
    all_data = []

    # I had some issues with rate limiting and it not saving.
    # Check if partial file exist
    if os.path.exists(SAVE_PATH):
        # Resume from file if file exist
        print(f"Resuming from previous file: {SAVE_PATH}")
        # Grab existing file and turn to panda dataframe
        df_existing = pd.read_csv(SAVE_PATH)

        # This is a list of ids in the data frame so it will continue without breaking
        completed_ids = set(df_existing["id"])
        all_data = df_existing.to_dict("records")
    else:
        # No completed ids
        completed_ids = set()

    print("Fetching Pokémon data from the PokeAPI...")

    # Go through every pokemon and retrieve data
    for pokemon_id in tqdm(range(1, limit + 1)):
        # Check if pokemon_id is already in the partial file
        if pokemon_id in completed_ids:
            continue  # already have this Pokémon

        # Attempt 3 times if not produce a fail message
        for attempt in range(3):
            try:
                # Attempt to grab data and wait
                r = requests.get(
                    f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}",
                    timeout=5
                )
                # If data exist leave for loop
                data = safe_json(r)
                if data:
                    break
            except:
                pass
            time.sleep(1)  # wait and retry
        else:
            # If unable to get pokemon produce error message and contiue
            print(f"Failed Pokémon #{pokemon_id}, skipping.")
            continue

        # Fetch species url for Legendary status
        species_url = data["species"]["url"]
        species_data = None
        
        # Attempt 3 times if not produce a fail message
        for attempt in range(3):
            try:
                # Try to request data
                species_resp = requests.get(species_url, timeout=5)
                # If you successfully get data do not attempt again
                species_data = safe_json(species_resp)
                if species_data:
                    break
            except:
                pass # If you receive error code try again
            # Sleep for one second to try to get around rate limiting
            time.sleep(1)

        # If failed to grab species data assume not legendary and skip for now
        if species_data is None:
            # Print error message and skip for now
            print(f"Failed species #{pokemon_id}, skipping legendary info.")
            # set legendary for false for now
            is_legendary = False
        else:
            # If succeded in retrieving data find if it is legendary or mythical
            is_legendary = species_data["is_legendary"] or species_data["is_mythical"]

        # Extract Stats
        stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
        types = [t["type"]["name"] for t in data["types"]]

        entry = {
            "id": pokemon_id,
            "name": data["name"],
            "type1": types[0],
            "type2": types[1] if len(types) > 1 else None,
            "height": data["height"],
            "weight": data["weight"],
            "hp": stats.get("hp"),
            "attack": stats.get("attack"),
            "defense": stats.get("defense"),
            "special_attack": stats.get("special-attack"),
            "special_defense": stats.get("special-defense"),
            "speed": stats.get("speed"),
            "total_stats": sum(stats.values()),
            "is_legendary": is_legendary,
        }

        # Append data
        all_data.append(entry)

        # Periodically save data in case of failure
        if pokemon_id % 50 == 0:
            pd.DataFrame(all_data).to_csv(SAVE_PATH, index=False)
            print(f"Autosaved progress at Pokémon #{pokemon_id}")

        time.sleep(0.2)  # gentle delay to avoid rate limiting

    # Final save when you finsh getting all pokemon
    df = pd.DataFrame(all_data)
    df.to_csv("data/raw/pokemon_raw.csv", index=False)
    print("Saved full dataset to data/raw/pokemon_raw.csv")


if __name__ == "__main__":
    fetch_pokemon_data()