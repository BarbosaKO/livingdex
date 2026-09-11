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
            
            sp = Species(
                id=species_id, 
                name=name, 
                generation_introduced=1, # Você pode ajustar para extrair do JSON se tiver
                description=description
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