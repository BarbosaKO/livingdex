import json
from app import create_app
from database import db
from models import Species, FormVariant, Game, AttributeCategory, LivingDexTarget, StorageBox, BoxSlot

app = create_app()

def seed_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        print("Semeando Jogos...")
        games = [
            Game(id=1, name="Ruby", generation=3, platform="GBA"),
            Game(id=2, name="Sapphire", generation=3, platform="GBA"),
            Game(id=3, name="Emerald", generation=3, platform="GBA"),
            Game(id=4, name="FireRed", generation=3, platform="GBA"),
            Game(id=5, name="LeafGreen", generation=3, platform="GBA"),
            Game(id=6, name="Diamond", generation=4, platform="NDS"),
            Game(id=7, name="Pearl", generation=4, platform="NDS"),
            Game(id=8, name="Pokemon GO", generation=0, platform="Mobile")
        ]
        db.session.bulk_save_objects(games)

        print("Semeando Categorias...")
        categories = [
            AttributeCategory(id=1, code="gigantamax", name="Gigantamax Factor"),
            AttributeCategory(id=2, code="alpha", name="Alpha"),
            AttributeCategory(id=3, code="size", name="XXL"),
            AttributeCategory(id=4, code="costume", name="Event Costume"),
            AttributeCategory(id=5, code="ribbon", name="Ribbon - Champion")
        ]
        db.session.bulk_save_objects(categories)

        print("Semeando Espécies Base e Formas do repositório Purukitto...")
        # Lendo o arquivo JSON baixado
        with open('pokedex.json', 'r', encoding='utf-8') as f:
            pokemon_list = json.load(f)
            
        for data in pokemon_list:
            species_id = data['id']
            # O repositório salva os nomes em vários idiomas, pegamos o inglês
            name = data['name']['english']
            
            # Se o JSON tiver descrição e seu model tiver a coluna description:
            description = data.get('description', 'Descrição não disponível.')
            
            # Extrair dados adicionais se disponíveis no JSON
            # Informações básicas
            description = data.get('description', 'Descrição não disponível.')
            category = data.get('species', None)
            
            # Extrair dados do perfil (profile)
            profile = data.get('profile', {})
            height_str = profile.get('height', None)
            weight_str = profile.get('weight', None)
            gender_ratio = profile.get('gender', None)
            abilities = profile.get('ability', None)
            
            # Converter altura e peso para float (removendo unidades)
            if height_str:
                try:
                    height = float(height_str.split()[0])  # Pega apenas o número antes do espaço
                except:
                    height = None
            else:
                height = None
                
            if weight_str:
                try:
                    weight = float(weight_str.split()[0])  # Pega apenas o número antes do espaço
                except:
                    weight = None
            else:
                weight = None
            
            # Extrair tipos
            types = data.get('type', None)
            
            # Os stats estão em "base" no formato atual do JSON
            base_stats = data.get('base', None)
            if base_stats:
                stats = json.dumps(base_stats)
            else:
                stats = None
            
            # Evoluções - formato atual está em "evolution.next"
            evolution_data = data.get('evolution', {})
            next_evolution = evolution_data.get('next', None)
            if next_evolution:
                # Formato: [["2", "Level 16"]]
                evolutions_list = []
                for evo in next_evolution:
                    if isinstance(evo, list) and len(evo) >= 1:
                        evo_id = evo[0]
                        evo_method = evo[1] if len(evo) > 1 else "Level"
                        evolutions_list.append({
                            "id": evo_id,
                            "method": evo_method
                        })
                evolutions = json.dumps(evolutions_list)
            else:
                evolutions = None
            
            # Converter listas para strings
            if isinstance(types, list):
                types = ', '.join(types)
            
            # Processar habilidades - formato: [["Overgrow", "false"], ["Chlorophyll", "true"]]
            if isinstance(abilities, list):
                ability_names = [ability[0] for ability in abilities if isinstance(ability, list) and len(ability) > 0]
                abilities = ', '.join(ability_names)
            
            # Processar gênero - formato: "87.5:12.5"
            # Se tiver ambos os valores, tem diferença de gênero
            if gender_ratio and ':' in gender_ratio:
                parts = gender_ratio.split(':')
                male_ratio = float(parts[0]) if parts[0] else 0
                female_ratio = float(parts[1]) if len(parts) > 1 and parts[1] else 0
                has_gender_differences = male_ratio > 0 and female_ratio > 0
            else:
                has_gender_differences = False
            
            sp = Species(
                id=species_id, 
                name=name, 
                generation_introduced=1, # Você pode ajustar para extrair do JSON se tiver
                description=description,
                height=height,
                weight=weight,
                category=category,
                abilities=abilities,
                types=types,
                weaknesses=None,  # Não está no JSON atual
                stats=stats,
                evolutions=evolutions,
                has_gender_differences=has_gender_differences
            )
            db.session.add(sp)
            
            # Usar os caminhos de imagem do JSON se disponíveis
            sprite_url = data.get('image', {}).get('sprite', None)
            thumbnail_url = data.get('image', {}).get('thumbnail', None)
            normal_form = FormVariant(
                species_id=species_id, 
                form_identifier="normal", 
                display_name="Normal",
                sprite_url=sprite_url,
                thumbnail_url=thumbnail_url
            )
            db.session.add(normal_form)

        db.session.commit()

        print("Semeando Metas da Living Dex...")
        targets = [
            LivingDexTarget(track_name="national", species_id=1, form_variant_id=1, require_shiny=False),
            LivingDexTarget(track_name="national", species_id=25, form_variant_id=4, require_shiny=False)
        ]
        db.session.bulk_save_objects(targets)

        print("Criando Boxes Iniciais...")
        for i in range(1, 11):
            box = StorageBox(id=i, name=f"Box {i}", order_index=i)
            db.session.add(box)

        db.session.commit()
        print("Banco de dados semeado com sucesso!")

if __name__ == '__main__':
    seed_data()