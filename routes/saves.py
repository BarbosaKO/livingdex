import os
import hashlib
from datetime import datetime
from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from database import db
from models import PokemonInstance, TransferLog, Game, Species, FormVariant, StorageBox, BoxSlot
from parsers.gen3 import Gen3SaveParser

saves_bp = Blueprint('saves', __name__, url_prefix='/saves')

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'sav'}

def hash_file(filepath):
    """Gera um hash SHA-256 do arquivo para rastreabilidade e evitar duplicatas exatas."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@saves_bp.route('/', methods=['GET'])
def index():
    """Página inicial de gerenciamento de saves e formulário de upload."""
    # Aqui você poderia listar os saves já enviados lendo a pasta uploads/saves/
    saves_dir = current_app.config['UPLOAD_FOLDER']
    files = os.listdir(saves_dir) if os.path.exists(saves_dir) else []
    return render_template('saves/index.html', files=files)

@saves_bp.route('/upload', methods=['POST'])
def upload_save():
    """
    Recebe o arquivo .sav, salva de forma segura, calcula o hash 
    e envia para a tela de 'staging' (comparação/diff).
    """
    if 'save_file' not in request.files:
        flash('Nenhum arquivo enviado.', 'error')
        return redirect(url_for('saves.index'))
        
    file = request.files['save_file']
    generation = request.form.get('generation') # Ex: '3' para Ruby/Sapphire/Emerald
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'error')
        return redirect(url_for('saves.index'))
        
    if file and allowed_file(file.filename):
        # Gera um nome seguro e insere um timestamp para não sobrescrever saves com o mesmo nome
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{original_filename}"
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)
        
        file_hash = hash_file(filepath)
        
        # Simulação da chamada do Parser dependendo da geração escolhida
        parsed_pokemon = []
        try:
            if generation == '3':
                parser = Gen3SaveParser(filepath)
                parsed_pokemon = parser.extract_pokemon()
                
                if not parsed_pokemon:
                    flash('Nenhum Pokémon encontrado no arquivo. Verifique se é um save válido de Gen 3.', 'warning')
                    return redirect(url_for('saves.index'))
            else:
                flash('Parser para esta geração ainda não implementado.', 'warning')
                return redirect(url_for('saves.index'))
                
        except Exception as e:
            flash(f'Erro ao processar o save: {str(e)}', 'error')
            return redirect(url_for('saves.index'))
            
        # Busca no banco quais PIDs já existem para mostrar na tela de Diff
        existing_pids = [p[0] for p in db.session.query(PokemonInstance.pid).filter(PokemonInstance.pid.isnot(None)).all()]
        
        return render_template('saves/staging.html', 
                               filename=safe_filename, 
                               file_hash=file_hash, 
                               pokemon_list=parsed_pokemon,
                               existing_pids=existing_pids)
                               
    flash('Tipo de arquivo não permitido. Apenas .sav são aceitos.', 'error')
    return redirect(url_for('saves.index'))

@saves_bp.route('/commit', methods=['POST'])
def commit_import():
    """
    Recebe os Pokémon confirmados pela tela de staging e os insere no banco.
    """
    try:
        # Espera receber um JSON com os PIDs/dados selecionados pelo usuário no frontend
        data = request.json
        selected_pokemon = data.get('selected_pokemon', [])
        source_filename = data.get('filename')
        origin_game_id = data.get('origin_game_id')
        
        if not selected_pokemon:
            return jsonify({"status": "error", "message": "Nenhum Pokémon selecionado."}), 400
            
        imported_count = 0
        
        # Função para encontrar o primeiro slot vazio
        def find_first_empty_slot():
            boxes = StorageBox.query.order_by(StorageBox.order_index).all()
            for box in boxes:
                for slot_num in range(1, 31):
                    existing_slot = BoxSlot.query.filter_by(
                        box_id=box.id, 
                        slot_number=slot_num
                    ).first()
                    if not existing_slot or not existing_slot.pokemon_instance_id:
                        return {'box_id': box.id, 'slot_number': slot_num}
            return None
        
        for pkm in selected_pokemon:
            # Dupla checagem de segurança contra duplicatas usando o PID
            exists = PokemonInstance.query.filter_by(pid=pkm['pid']).first()
            if exists:
                continue # Pula se já existir no banco
                
            # Na vida real, o parser já identificaria a form_variant correta. 
            # Aqui pegamos a forma padrão da espécie como fallback.
            default_form = FormVariant.query.filter_by(species_id=pkm['species_id'], form_identifier='normal').first()
            
            new_instance = PokemonInstance(
                species_id=pkm['species_id'],
                form_variant_id=default_form.id if default_form else 1,
                origin_game_id=origin_game_id,
                nickname=pkm.get('nickname'),
                level=pkm.get('level', 1),
                is_shiny=pkm.get('is_shiny', False),
                ot_name=pkm.get('ot_name', 'Unknown'),
                pid=pkm.get('pid')
            )
            db.session.add(new_instance)
            db.session.flush() # Necessário para gerar o ID antes de usar no TransferLog
            
            log = TransferLog(
                pokemon_instance_id=new_instance.id,
                from_game_or_system=f"Save File: {source_filename}",
                to_game_or_system="Living Dex System",
                notes="Importado automaticamente."
            )
            db.session.add(log)
            
            # Colocar na primeira box vazia
            first_empty_slot = find_first_empty_slot()
            if first_empty_slot:
                box_slot = BoxSlot.query.filter_by(
                    box_id=first_empty_slot['box_id'], 
                    slot_number=first_empty_slot['slot_number']
                ).first()
                
                if not box_slot:
                    box_slot = BoxSlot(
                        box_id=first_empty_slot['box_id'],
                        slot_number=first_empty_slot['slot_number'],
                        pokemon_instance_id=new_instance.id
                    )
                    db.session.add(box_slot)
                else:
                    box_slot.pokemon_instance_id = new_instance.id
            
            imported_count += 1
            
        db.session.commit()
        return jsonify({"status": "success", "message": f"{imported_count} Pokémon importados com sucesso!"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500