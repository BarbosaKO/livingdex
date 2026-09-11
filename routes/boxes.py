from flask import Blueprint, render_template, request, jsonify
from database import db
from models import StorageBox, BoxSlot, PokemonInstance

boxes_bp = Blueprint('boxes', __name__, url_prefix='/boxes')

@boxes_bp.route('/')
def index():
    """
    Renderiza a lista de todas as Boxes.
    """
    boxes = StorageBox.query.order_by(StorageBox.order_index).all()
    return render_template('boxes/index.html', boxes=boxes)

@boxes_bp.route('/<int:box_id>')
def view_box(box_id):
    """
    Visualiza os 30 slots de uma Box específica.
    """
    box = StorageBox.query.get_or_404(box_id)
    # Busca os slots já associados a esta box
    slots = BoxSlot.query.filter_by(box_id=box_id).order_by(BoxSlot.slot_number).all()
    
    # Organiza em um dicionário para facilitar o render no template (slot_number -> BoxSlot)
    slots_dict = {slot.slot_number: slot for slot in slots}
    
    # Busca todas as boxes para o seletor de movimento
    all_boxes = StorageBox.query.order_by(StorageBox.order_index).all()
    
    return render_template('boxes/view.html', box=box, slots_dict=slots_dict, boxes=all_boxes)

@boxes_bp.route('/move', methods=['POST'])
def move_pokemon():
    """
    Move um Pokémon de um slot/box para outro. Suporta troca (swap) se o destino estiver ocupado.
    Esperado via JSON: pokemon_id, to_box_id, to_slot
    """
    data = request.json
    pokemon_id = data.get('pokemon_id')
    to_box_id = data.get('to_box_id')
    to_slot_num = data.get('to_slot')

    if not all([pokemon_id, to_box_id, to_slot_num]):
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    try:
        # Encontra onde o Pokémon está atualmente
        current_slot = BoxSlot.query.filter_by(pokemon_instance_id=pokemon_id).first()
        
        # Encontra o slot de destino
        target_slot = BoxSlot.query.filter_by(box_id=to_box_id, slot_number=to_slot_num).first()
        
        # Se o slot de destino não existir na tabela ainda, cria
        if not target_slot:
            target_slot = BoxSlot(box_id=to_box_id, slot_number=to_slot_num)
            db.session.add(target_slot)
        
        # Lógica de Troca (Swap): Se houver um Pokémon no destino
        if target_slot.pokemon_instance_id:
            # O Pokémon que estava no destino vai para o slot antigo
            if current_slot:
                current_slot.pokemon_instance_id = target_slot.pokemon_instance_id
            else:
                # Se não tinha slot antigo (veio solto), apenas remove do destino original
                pass
        else:
            # Limpa o slot antigo se não houve troca
            if current_slot:
                current_slot.pokemon_instance_id = None
                
        # Define o Pokémon selecionado no novo slot
        target_slot.pokemon_instance_id = pokemon_id
        
        db.session.commit()
        return jsonify({"status": "success"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@boxes_bp.route('/move_to_box', methods=['POST'])
def move_to_box():
    """
    Move um Pokémon para a primeira slot vazia de uma box específica.
    Esperado via JSON: pokemon_id, to_box_id
    """
    data = request.json
    pokemon_id = data.get('pokemon_id')
    to_box_id = data.get('to_box_id')

    if not all([pokemon_id, to_box_id]):
        return jsonify({"status": "error", "message": "Dados incompletos"}), 400

    try:
        # Encontra onde o Pokémon está atualmente
        current_slot = BoxSlot.query.filter_by(pokemon_instance_id=pokemon_id).first()
        
        # Encontra o primeiro slot vazio na box de destino
        target_slot = None
        for slot_num in range(1, 31):
            slot = BoxSlot.query.filter_by(box_id=to_box_id, slot_number=slot_num).first()
            if not slot or not slot.pokemon_instance_id:
                if not slot:
                    slot = BoxSlot(box_id=to_box_id, slot_number=slot_num)
                    db.session.add(slot)
                target_slot = slot
                break
        
        if not target_slot:
            return jsonify({"status": "error", "message": "A box de destino está cheia"}), 400
        
        # Limpa o slot antigo
        if current_slot:
            current_slot.pokemon_instance_id = None
        
        # Coloca o Pokémon no novo slot
        target_slot.pokemon_instance_id = pokemon_id
        
        db.session.commit()
        return jsonify({"status": "success"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500