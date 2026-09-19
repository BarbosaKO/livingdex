from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from database import db
from models import (
    PokemonInstance, Species, FormVariant, Game, 
    InstanceAttributeValue, AttributeValue, SpeciesAllowedAttribute, TransferLog, 
    StorageBox, BoxSlot
)
from sqlalchemy.orm import joinedload

pokemon_bp = Blueprint('pokemon', __name__, url_prefix='/pokemon')

# Pokédex routes (sem prefixo /pokemon)
pokedex_bp = Blueprint('pokedex', __name__, url_prefix='/pokedex')

def calculate_weaknesses(types_list):
    """Calcula fraquezas baseado nos tipos do Pokémon considerando múltiplos tipos"""
    if not types_list:
        return []
    
    # Tabela completa de interações de tipo (multiplicadores de dano)
    # Formato: {atacante: {defensor: multiplicador}}
    TYPE_CHART = {
        'Normal': {'Normal': 1, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 1, 
                   'Fighting': 1, 'Poison': 1, 'Ground': 1, 'Flying': 1, 'Psychic': 1, 'Bug': 1, 
                   'Rock': 0.5, 'Ghost': 0, 'Dragon': 1, 'Dark': 1, 'Steel': 0.5, 'Fairy': 1},
        'Fire': {'Normal': 1, 'Fire': 0.5, 'Water': 0.5, 'Electric': 1, 'Grass': 2, 'Ice': 2, 
                 'Fighting': 1, 'Poison': 1, 'Ground': 1, 'Flying': 1, 'Psychic': 1, 'Bug': 2, 
                 'Rock': 0.5, 'Ghost': 1, 'Dragon': 0.5, 'Dark': 1, 'Steel': 2, 'Fairy': 0.5},
        'Water': {'Normal': 1, 'Fire': 2, 'Water': 0.5, 'Electric': 1, 'Grass': 0.5, 'Ice': 1, 
                  'Fighting': 1, 'Poison': 1, 'Ground': 2, 'Flying': 1, 'Psychic': 1, 'Bug': 1, 
                  'Rock': 2, 'Ghost': 1, 'Dragon': 0.5, 'Dark': 1, 'Steel': 1, 'Fairy': 1},
        'Electric': {'Normal': 1, 'Fire': 1, 'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ice': 1, 
                     'Fighting': 1, 'Poison': 1, 'Ground': 0, 'Flying': 2, 'Psychic': 1, 'Bug': 1, 
                     'Rock': 1, 'Ghost': 1, 'Dragon': 0.5, 'Dark': 1, 'Steel': 1, 'Fairy': 1},
        'Grass': {'Normal': 1, 'Fire': 0.5, 'Water': 2, 'Electric': 1, 'Grass': 0.5, 'Ice': 1, 
                  'Fighting': 1, 'Poison': 0.5, 'Ground': 2, 'Flying': 0.5, 'Psychic': 1, 'Bug': 0.5, 
                  'Rock': 2, 'Ghost': 1, 'Dragon': 0.5, 'Dark': 1, 'Steel': 0.5, 'Fairy': 1},
        'Ice': {'Normal': 1, 'Fire': 0.5, 'Water': 0.5, 'Electric': 1, 'Grass': 2, 'Ice': 0.5, 
                'Fighting': 1, 'Poison': 1, 'Ground': 2, 'Flying': 2, 'Psychic': 1, 'Bug': 1, 
                'Rock': 1, 'Ghost': 1, 'Dragon': 2, 'Dark': 1, 'Steel': 0.5, 'Fairy': 1},
        'Fighting': {'Normal': 2, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 2, 
                     'Fighting': 1, 'Poison': 0.5, 'Ground': 1, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 
                     'Rock': 2, 'Ghost': 0, 'Dragon': 1, 'Dark': 2, 'Steel': 2, 'Fairy': 0.5},
        'Poison': {'Normal': 1, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 2, 'Ice': 1, 
                   'Fighting': 1, 'Poison': 0.5, 'Ground': 0.5, 'Flying': 1, 'Psychic': 2, 'Bug': 1, 
                   'Rock': 0.5, 'Ghost': 0.5, 'Dragon': 1, 'Dark': 1, 'Steel': 0, 'Fairy': 2},
        'Ground': {'Normal': 1, 'Fire': 2, 'Water': 1, 'Electric': 2, 'Grass': 0.5, 'Ice': 1, 
                   'Fighting': 1, 'Poison': 2, 'Ground': 1, 'Flying': 0, 'Psychic': 1, 'Bug': 1, 
                   'Rock': 2, 'Ghost': 1, 'Dragon': 1, 'Dark': 1, 'Steel': 2, 'Fairy': 1},
        'Flying': {'Normal': 1, 'Fire': 1, 'Water': 1, 'Electric': 2, 'Grass': 2, 'Ice': 1, 
                   'Fighting': 2, 'Poison': 1, 'Ground': 1, 'Flying': 1, 'Psychic': 1, 'Bug': 2, 
                   'Rock': 0.5, 'Ghost': 1, 'Dragon': 1, 'Dark': 1, 'Steel': 0.5, 'Fairy': 1},
        'Psychic': {'Normal': 1, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 1, 
                    'Fighting': 2, 'Poison': 2, 'Ground': 1, 'Flying': 1, 'Psychic': 0.5, 'Bug': 1, 
                    'Rock': 1, 'Ghost': 2, 'Dragon': 1, 'Dark': 0, 'Steel': 0.5, 'Fairy': 1},
        'Bug': {'Normal': 1, 'Fire': 0.5, 'Water': 1, 'Electric': 1, 'Grass': 2, 'Ice': 1, 
                'Fighting': 0.5, 'Poison': 0.5, 'Ground': 1, 'Flying': 0.5, 'Psychic': 2, 'Bug': 1, 
                'Rock': 1, 'Ghost': 0.5, 'Dragon': 1, 'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5},
        'Rock': {'Normal': 1, 'Fire': 2, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 2, 
                 'Fighting': 0.5, 'Poison': 1, 'Ground': 0.5, 'Flying': 2, 'Psychic': 1, 'Bug': 2, 
                 'Rock': 1, 'Ghost': 1, 'Dragon': 1, 'Dark': 1, 'Steel': 0.5, 'Fairy': 1},
        'Ghost': {'Normal': 0, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 1, 
                  'Fighting': 1, 'Poison': 1, 'Ground': 1, 'Flying': 1, 'Psychic': 2, 'Bug': 1, 
                  'Rock': 1, 'Ghost': 2, 'Dragon': 1, 'Dark': 2, 'Steel': 1, 'Fairy': 1},
        'Dragon': {'Normal': 1, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 1, 
                   'Fighting': 1, 'Poison': 1, 'Ground': 1, 'Flying': 1, 'Psychic': 1, 'Bug': 1, 
                   'Rock': 1, 'Ghost': 1, 'Dragon': 2, 'Dark': 1, 'Steel': 0.5, 'Fairy': 2},
        'Dark': {'Normal': 1, 'Fire': 1, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 1, 
                 'Fighting': 0.5, 'Poison': 1, 'Ground': 1, 'Flying': 1, 'Psychic': 2, 'Bug': 1, 
                 'Rock': 1, 'Ghost': 2, 'Dragon': 1, 'Dark': 0.5, 'Steel': 1, 'Fairy': 0.5},
        'Steel': {'Normal': 1, 'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Grass': 1, 'Ice': 2, 
                  'Fighting': 1, 'Poison': 0, 'Ground': 1, 'Flying': 1, 'Psychic': 1, 'Bug': 1, 
                  'Rock': 2, 'Ghost': 1, 'Dragon': 1, 'Dark': 1, 'Steel': 0.5, 'Fairy': 2},
        'Fairy': {'Normal': 1, 'Fire': 0.5, 'Water': 1, 'Electric': 1, 'Grass': 1, 'Ice': 1, 
                  'Fighting': 2, 'Poison': 0.5, 'Ground': 1, 'Flying': 1, 'Psychic': 1, 'Bug': 1, 
                  'Rock': 1, 'Ghost': 1, 'Dragon': 2, 'Dark': 2, 'Steel': 0.5, 'Fairy': 1}
    }
    
    all_types = list(TYPE_CHART.keys())
    weaknesses = []
    
    for attacking_type in all_types:
        total_multiplier = 1
        
        for defending_type in types_list:
            if defending_type in TYPE_CHART and attacking_type in TYPE_CHART[defending_type]:
                multiplier = TYPE_CHART[defending_type][attacking_type]
                total_multiplier *= multiplier
        
        # Fraqueza = multiplicador > 1
        if total_multiplier > 1:
            weaknesses.append(attacking_type)
    
    return sorted(weaknesses)

@pokemon_bp.route('/')
def list_pokemon():
    """
    Lista todos os Pokémon da coleção com paginação.
    Inclui carregamento otimizado (joinedload) das relações para evitar o problema de N+1 queries.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Busca paginada trazendo já a espécie e a forma para otimizar o render
    pagination = PokemonInstance.query.options(
        joinedload(PokemonInstance.species),
        joinedload(PokemonInstance.form_variant)
    ).order_by(PokemonInstance.species_id.asc(), PokemonInstance.level.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('pokemon/list.html', pagination=pagination)

@pokemon_bp.route('/<string:instance_id>')
def view_pokemon(instance_id):
    """
    Exibe a ficha técnica detalhada de um indivíduo específico.
    Inclui histórico de transferências e atributos customizados.
    """
    pokemon = PokemonInstance.query.options(
        joinedload(PokemonInstance.species),
        joinedload(PokemonInstance.form_variant),
        joinedload(PokemonInstance.attributes).joinedload(InstanceAttributeValue.attribute_value),
        joinedload(PokemonInstance.transfer_history)
    ).get_or_404(instance_id)
    
    game = Game.query.get(pokemon.origin_game_id)
    
    return render_template('pokemon/view.html', pokemon=pokemon, origin_game=game)

@pokemon_bp.route('/add', methods=['GET', 'POST'])
def add_pokemon():
    """
    Interface e lógica para cadastro manual de um Pokémon.
    Executa a validação rigorosa de atributos permitidos.
    """
    if request.method == 'POST':
        try:
            species_id = int(request.form.get('species_id'))
            form_variant_id = int(request.form.get('form_variant_id'))
            origin_game_id = int(request.form.get('origin_game_id'))
            is_shiny = request.form.get('is_shiny') == 'on'
            
            # Validação básica de existência
            species = Species.query.get_or_404(species_id)
            form = FormVariant.query.filter_by(id=form_variant_id, species_id=species_id).first()
            
            if not form:
                flash("Forma selecionada não pertence a esta espécie.", "error")
                return redirect(url_for('pokemon.add_pokemon'))
                
            # Criação da instância base
            new_pokemon = PokemonInstance(
                species_id=species_id,
                form_variant_id=form_variant_id,
                origin_game_id=origin_game_id,
                nickname=request.form.get('nickname'),
                level=int(request.form.get('level', 1)),
                gender=request.form.get('gender', 'U'),
                is_shiny=is_shiny,
                ot_name=request.form.get('ot_name', 'Unknown'),
                ot_id=int(request.form.get('ot_id', 00000)),
                pokeball=request.form.get('pokeball', 'Poké Ball'),
                nature=request.form.get('nature'),
                ability=request.form.get('ability')
            )
            
            db.session.add(new_pokemon)
            db.session.flush() # Gera o UUID da instância antes do commit final
            
            # Processamento de atributos dinâmicos (ex: Mark, Size, TeraType)
            selected_attributes = request.form.getlist('attributes') # Lista de IDs do form HTML
            if selected_attributes:
                # Busca a matriz de permissões desta espécie e forma
                allowed_ids_query = db.session.query(SpeciesAllowedAttribute.attribute_value_id).filter(
                    SpeciesAllowedAttribute.species_id == species_id,
                    (SpeciesAllowedAttribute.form_variant_id == form_variant_id) | 
                    (SpeciesAllowedAttribute.form_variant_id.is_(None))
                ).all()
                allowed_set = {row[0] for row in allowed_ids_query}
                
                for attr_id_str in selected_attributes:
                    attr_id = int(attr_id_str)
                    if attr_id not in allowed_set:
                        db.session.rollback()
                        flash(f"Atributo {attr_id} não é permitido para esta espécie/forma. Cadastro cancelado.", "error")
                        return redirect(url_for('pokemon.add_pokemon'))
                        
                    new_attr = InstanceAttributeValue(
                        instance_id=new_pokemon.id,
                        attribute_value_id=attr_id
                    )
                    db.session.add(new_attr)

            # Encontrar a primeira box vazia e colocar o Pokémon lá
            first_empty_slot = find_first_empty_slot()
            if first_empty_slot:
                # Criar ou atualizar o slot
                box_slot = BoxSlot.query.filter_by(
                    box_id=first_empty_slot['box_id'], 
                    slot_number=first_empty_slot['slot_number']
                ).first()
                
                if not box_slot:
                    box_slot = BoxSlot(
                        box_id=first_empty_slot['box_id'],
                        slot_number=first_empty_slot['slot_number'],
                        pokemon_instance_id=new_pokemon.id
                    )
                    db.session.add(box_slot)
                else:
                    box_slot.pokemon_instance_id = new_pokemon.id

            # Registro automático no histórico de transferências
            log = TransferLog(
                pokemon_instance_id=new_pokemon.id,
                from_game_or_system='Manual Entry',
                to_game_or_system='Living Dex System',
                notes='Adicionado manualmente via painel web.'
            )
            db.session.add(log)
            
            db.session.commit()
            flash(f"{species.name} cadastrado com sucesso!", "success")
            return redirect(url_for('pokemon.list_pokemon'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao cadastrar: {str(e)}", "error")

    # Renderiza o formulário no método GET
    species_list = Species.query.options(
        joinedload(Species.forms)
    ).order_by(Species.id).all()
    games_list = Game.query.order_by(Game.generation).all()
    categories = AttributeValue.query.all() # Idealmente agrupados por categoria
    
    return render_template('pokemon/add.html', species_list=species_list, games_list=games_list, categories=categories)

@pokemon_bp.route('/<string:instance_id>/delete', methods=['POST'])
def delete_pokemon(instance_id):
    """
    Remove fisicamente um Pokémon da coleção.
    Remove também da box onde estiver armazenado.
    Graças ao cascade='all, delete-orphan' definido nos models, logs e atributos serão limpos.
    """
    pokemon = PokemonInstance.query.get_or_404(instance_id)
    name = pokemon.species.name
    
    try:
        # Remover da box onde estiver armazenado
        box_slot = BoxSlot.query.filter_by(pokemon_instance_id=instance_id).first()
        if box_slot:
            box_slot.pokemon_instance_id = None
        
        # Remover o Pokémon
        db.session.delete(pokemon)
        db.session.commit()
        flash(f"{name} foi removido permanentemente da sua coleção.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao remover: {str(e)}", "error")
        
    return redirect(url_for('pokemon.list_pokemon'))

def find_first_empty_slot():
    """
    Encontra o primeiro slot vazio em todas as boxes.
    Retorna dicionário com box_id e slot_number, ou None se não houver espaço.
    """
    # Busca todas as boxes em ordem
    boxes = StorageBox.query.order_by(StorageBox.order_index).all()
    
    for box in boxes:
        # Verifica cada slot (1-30) desta box
        for slot_num in range(1, 31):
            existing_slot = BoxSlot.query.filter_by(
                box_id=box.id, 
                slot_number=slot_num
            ).first()
            
            # Se o slot não existe ou está vazio, é um espaço disponível
            if not existing_slot or not existing_slot.pokemon_instance_id:
                return {'box_id': box.id, 'slot_number': slot_num}
    
    return None  # Não há espaço disponível

# -------------------------------------------------------------------
# POKÉDEX ROUTES
# -------------------------------------------------------------------

@pokedex_bp.route('/')
def pokedex_index():
    """
    Lista todos os Pokémon disponíveis na Pokédex com seus sprites.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 151  # Primeira geração por página, pode ser ajustado
    
    pagination = Species.query.options(
        joinedload(Species.forms)
    ).order_by(Species.id.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('pokedex/index.html', pagination=pagination)

@pokedex_bp.route('/<int:species_id>')
def pokedex_detail(species_id):
    """
    Mostra detalhes de um Pokémon específico incluindo descrição e formas.
    """
    species = Species.query.options(
        joinedload(Species.forms)
    ).get_or_404(species_id)
    
    # Processar campos de tipos e fraquezas (separados por vírgula)
    if species.types:
        species.types_list = [t.strip() for t in species.types.split(',')]
    else:
        species.types_list = ['Normal']
    
    # Calcular fraquezas dinamicamente baseado nos tipos
    species.weaknesses_list = calculate_weaknesses(species.types_list)
    
    # Processar estatísticas (JSON)
    if species.stats:
        try:
            import json
            species.stats_dict = json.loads(species.stats)
        except:
            species.stats_dict = {}
    else:
        species.stats_dict = {}
    
    # Processar evoluções (JSON)
    if species.evolutions:
        try:
            import json
            species.evolutions_list = json.loads(species.evolutions)
        except:
            species.evolutions_list = []
    else:
        species.evolutions_list = []
    
    # Encontrar o ID anterior e próximo
    previous_id = Species.query.filter(Species.id < species_id).order_by(Species.id.desc()).first()
    next_id = Species.query.filter(Species.id > species_id).order_by(Species.id.asc()).first()
    
    # Obter nomes do anterior e próximo
    previous_name = previous_id.name if previous_id else None
    next_name = next_id.name if next_id else None
    
    return render_template('pokedex/detail.html', species=species, 
                          previous_id=previous_id.id if previous_id else None,
                          previous_name=previous_name,
                          next_id=next_id.id if next_id else None,
                          next_name=next_name)