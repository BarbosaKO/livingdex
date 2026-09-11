from database import db
from datetime import datetime
import uuid

# -------------------------------------------------------------------
# 1. TAXONOMIA E REGRAS CANÔNICAS (ESPÉCIES E VARIANTES)
# -------------------------------------------------------------------

class Species(db.Model):
    __tablename__ = 'species'
    
    id = db.Column(db.Integer, primary_key=True) # National Dex Number (ex: 25)
    name = db.Column(db.String(64), nullable=False, index=True)
    generation_introduced = db.Column(db.Integer, nullable=False)
    has_gender_differences = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    
    forms = db.relationship('FormVariant', backref='species', lazy='joined')
    allowed_attributes = db.relationship('SpeciesAllowedAttribute', backref='species')

class AttributeCategory(db.Model):
    __tablename__ = 'attribute_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False) # 'region', 'size', 'costume'
    name = db.Column(db.String(64), nullable=False)             # 'Região', 'Traje GO'

class AttributeValue(db.Model):
    __tablename__ = 'attribute_values'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('attribute_categories.id'), nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    
    category = db.relationship('AttributeCategory')

class FormVariant(db.Model):
    __tablename__ = 'form_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    form_identifier = db.Column(db.String(64), nullable=False) # 'alola', 'gigantamax'
    display_name = db.Column(db.String(64), nullable=False)    # 'Alolan Meowth'
    sprite_url = db.Column(db.String(255))
    thumbnail_url = db.Column(db.String(255))
    is_battle_only = db.Column(db.Boolean, default=False)
    is_go_costume = db.Column(db.Boolean, default=False)

class SpeciesAllowedAttribute(db.Model):
    __tablename__ = 'species_allowed_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    form_variant_id = db.Column(db.Integer, db.ForeignKey('form_variants.id'), nullable=True)
    attribute_value_id = db.Column(db.Integer, db.ForeignKey('attribute_values.id'), nullable=False)

# -------------------------------------------------------------------
# 2. INSTÂNCIA INDIVIDUAL (POKÉMON POSSUÍDO)
# -------------------------------------------------------------------

class Game(db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    generation = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(32), nullable=False)

class PokemonInstance(db.Model):
    __tablename__ = 'pokemon_instances'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    form_variant_id = db.Column(db.Integer, db.ForeignKey('form_variants.id'), nullable=False)
    
    nickname = db.Column(db.String(32))
    level = db.Column(db.Integer, nullable=False, default=1)
    gender = db.Column(db.String(1), default='U') # M, F, U
    is_shiny = db.Column(db.Boolean, default=False, nullable=False)
    
    # Origem
    origin_game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    ot_name = db.Column(db.String(32), nullable=False)
    ot_id = db.Column(db.Integer, nullable=False)
    ot_sid = db.Column(db.Integer, nullable=True)
    met_date = db.Column(db.Date, nullable=True)
    met_location = db.Column(db.String(64), nullable=True)
    pokeball = db.Column(db.String(32), default='Poké Ball')
    
    # Stats
    nature = db.Column(db.String(32))
    ability = db.Column(db.String(32))
    move_1 = db.Column(db.String(32))
    move_2 = db.Column(db.String(32))
    move_3 = db.Column(db.String(32))
    move_4 = db.Column(db.String(32))
    
    # Rastreabilidade
    pid = db.Column(db.BigInteger, nullable=True)
    
    # Relacionamentos
    species = db.relationship('Species')
    form_variant = db.relationship('FormVariant')
    attributes = db.relationship('InstanceAttributeValue', backref='pokemon', cascade='all, delete-orphan')
    transfer_history = db.relationship('TransferLog', backref='pokemon', order_by='TransferLog.timestamp', cascade='all, delete-orphan')

class InstanceAttributeValue(db.Model):
    __tablename__ = 'instance_attribute_values'
    
    instance_id = db.Column(db.String(36), db.ForeignKey('pokemon_instances.id'), primary_key=True)
    attribute_value_id = db.Column(db.Integer, db.ForeignKey('attribute_values.id'), primary_key=True)
    
    # Adicione esta linha para o SQLAlchemy encontrar o atributo mapeado:
    attribute_value = db.relationship('AttributeValue')

# -------------------------------------------------------------------
# 3. SISTEMA DE BOXES E LOGS
# -------------------------------------------------------------------

class StorageBox(db.Model):
    __tablename__ = 'storage_boxes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, unique=True)
    wallpaper = db.Column(db.String(64), default='default.png')

class BoxSlot(db.Model):
    __tablename__ = 'box_slots'
    
    box_id = db.Column(db.Integer, db.ForeignKey('storage_boxes.id'), primary_key=True)
    slot_number = db.Column(db.Integer, primary_key=True) # 1 a 30
    pokemon_instance_id = db.Column(db.String(36), db.ForeignKey('pokemon_instances.id'), unique=True, nullable=True)
    
    pokemon = db.relationship('PokemonInstance')

class TransferLog(db.Model):
    __tablename__ = 'transfer_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    pokemon_instance_id = db.Column(db.String(36), db.ForeignKey('pokemon_instances.id'), nullable=False)
    from_game_or_system = db.Column(db.String(64), nullable=False)
    to_game_or_system = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(255))

class LivingDexTarget(db.Model):
    __tablename__ = 'living_dex_targets'
    
    id = db.Column(db.Integer, primary_key=True)
    track_name = db.Column(db.String(32), nullable=False) # 'National', 'Shiny'
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    form_variant_id = db.Column(db.Integer, db.ForeignKey('form_variants.id'), nullable=False)
    require_shiny = db.Column(db.Boolean, default=False)
    required_attribute_id = db.Column(db.Integer, db.ForeignKey('attribute_values.id'), nullable=True)