import os
from flask import Flask, render_template
from config import Config
from database import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa o banco de dados com a aplicação
    db.init_app(app)

    # Garante que a pasta de uploads exista
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Registro dos Blueprints (rotas)
    # Como as rotas ainda serão criadas, importamos dentro de try/except ou 
    # apenas preparamos o terreno. O correto em Flask é importá-las aqui.
    from routes.api import api_bp
    from routes.boxes import boxes_bp
    from routes.dex import dex_bp
    from routes.pokemon import pokemon_bp, pokedex_bp
    from routes.saves import saves_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(boxes_bp)
    app.register_blueprint(dex_bp)
    app.register_blueprint(pokemon_bp)
    app.register_blueprint(pokedex_bp)
    app.register_blueprint(saves_bp)

    # Cria as tabelas no banco de dados se não existirem
    with app.app_context():
        import models  # Garante que o SQLAlchemy conheça os modelos
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)