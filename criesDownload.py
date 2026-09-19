import json
import os
import urllib.request

# Arquivos e pastas
JSON_FILE = "pokedex.json"
OUTPUT_DIR = "cries"

# URL base oficial da PokeAPI para os cries (sons) dos Pokémon
BASE_URL = (
    "https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/"
)

# Cria a pasta de destino caso ela não exista
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Carrega a lista do JSON
with open(JSON_FILE, "r", encoding="utf-8") as f:
    pokemons = json.load(f)

print(f"Iniciando o download de {len(pokemons)} áudios...\n")

for pokemon in pokemons:
    poke_id = pokemon["id"]
    audio_url = f"{BASE_URL}{poke_id}.ogg"
    file_path = os.path.join(OUTPUT_DIR, f"{poke_id}.ogg")

    try:
        urllib.request.urlretrieve(audio_url, file_path)
        print(f"[✓] Baixado: {poke_id}.ogg ({pokemon['name']['english']})")
    except Exception as e:
        print(f"[X] Falha no download do ID {poke_id}: {e}")

print("\nProcesso finalizado!")