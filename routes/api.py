from flask import Blueprint, jsonify
from models import PokemonInstance, db

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/esp32/summary', methods=['GET'])
def esp32_summary():
    """
    Retorna uma visão compacta da coleção otimizada para o display do ESP32.
    """
    try:
        total_owned = db.session.query(PokemonInstance).count()
        
        # Conta espécies únicas que você possui
        unique_species = db.session.query(PokemonInstance.species_id).distinct().count()
        
        # Pega os 5 Pokémon mais recentes adicionados à coleção
        latest_instances = PokemonInstance.query.order_by(
            PokemonInstance.id.desc()
        ).limit(5).all()

        latest_list = []
        for instance in latest_instances:
            latest_list.append({
                "dex": instance.species_id,
                "name": instance.species.name if instance.species else "Unknown",
                "shiny": 1 if instance.is_shiny else 0,
                "lvl": instance.level,
                "ot": instance.ot_name
            })

        return jsonify({
            "status": "success",
            "data": {
                "total": total_owned,
                "unique": unique_species,
                "latest": latest_list
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500