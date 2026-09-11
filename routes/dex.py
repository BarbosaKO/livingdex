from flask import Blueprint, render_template
from database import db
from models import LivingDexTarget, PokemonInstance, InstanceAttributeValue

dex_bp = Blueprint('dex', __name__, url_prefix='/dex')

def calculate_living_dex_progress(track_name):
    """
    Calcula a porcentagem de completude de uma trilha específica (Ex: 'National', 'Shiny').
    """
    targets = LivingDexTarget.query.filter_by(track_name=track_name).all()
    total_targets = len(targets)
    completed = 0

    if total_targets == 0:
        return {"track": track_name, "completed": 0, "total": 0, "percentage": 0}

    for target in targets:
        # Monta a query base (Espécie + Forma)
        query = db.session.query(PokemonInstance).filter(
            PokemonInstance.species_id == target.species_id,
            PokemonInstance.form_variant_id == target.form_variant_id
        )
        
        # Aplica filtro shiny se a meta exigir
        if target.require_shiny:
            query = query.filter(PokemonInstance.is_shiny == True)
            
        # Aplica filtro de atributo especial (Ex: Costume, Tamanho XXL) se a meta exigir
        if target.required_attribute_id:
            query = query.join(InstanceAttributeValue).filter(
                InstanceAttributeValue.attribute_value_id == target.required_attribute_id
            )
            
        # Verifica se o jogador possui ao menos 1 indivíduo que atenda aos requisitos
        if query.first() is not None:
            completed += 1
            
    percentage = (completed / total_targets * 100) if total_targets > 0 else 0
    return {
        "track": track_name,
        "completed": completed,
        "total": total_targets,
        "percentage": round(percentage, 2)
    }

@dex_bp.route('/')
def dashboard():
    """
    Renderiza o dashboard da Living Dex com as barras de progresso.
    """
    # Você pode ter várias trilhas de coleção cadastradas
    tracks = ['National', 'Shiny', 'GO_Costumes', 'Gigantamax']
    progress_stats = []
    
    for track in tracks:
        stats = calculate_living_dex_progress(track)
        if stats['total'] > 0: # Só exibe se existirem metas configuradas
            progress_stats.append(stats)
            
    return render_template('dex/dashboard.html', progress_stats=progress_stats)