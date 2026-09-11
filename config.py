import os

class Config:
    # Chave de segurança para sessões e cookies do Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'livingdex-secret-key-dev'
    
    # Configuração do banco de dados SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'livingdex.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração de uploads de saves
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'saves')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB para o upload