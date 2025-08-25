import os
import json
from flask import Flask, jsonify, render_template
from flask_cors import CORS

# Importe o Blueprint de páginas, mas ele deve estar fora da função
# para ser usado em outras partes do código
from app.main_pages.routes import main_pages_bp

# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

# --- Funções Auxiliares para Persistência de Dados (JSON) ---
DATA_FILE = 'data.json'

def load_data():
    """Carrega os dados de usuários e pedidos do arquivo JSON."""
    if not os.path.exists(DATA_FILE):
        initial_data = {'users': {}, 'pedidos': []}
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=4, ensure_ascii=False)
        return initial_data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    """Salva os dados de usuários e pedidos no arquivo JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Garante que o arquivo de dados exista ao iniciar o módulo
load_data()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    # Carregar configurações
    app.config.from_object('app.config.Config')
    try:
        app.config.from_pyfile('config.py', silent=True)
    except FileNotFoundError:
        pass

    # Cria a pasta de upload
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads_temp')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # UPLOAD_FOLDER = 'uploads_temp'
    # if not os.path.exists(UPLOAD_FOLDER):
    #     os.makedirs(UPLOAD_FOLDER)
    # app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Registrar Blueprints
    # As importações agora acontecem aqui para evitar problemas de importação circular
    from app.auth.routes import auth_bp
    from app.pedidos.routes import pedidos_bp
    from app.contratos.routes import contratos_bp
    from app.relatorios.routes import relatorios_bp

    # Registre o Blueprint de páginas primeiro, pois ele contém a rota principal
    app.register_blueprint(main_pages_bp)
    app.register_blueprint(auth_bp) # Adicione o prefixo aqui
    app.register_blueprint(pedidos_bp) # Adicione o prefixo aqui
    app.register_blueprint(contratos_bp) # Adicione o prefixo aqui
    app.register_blueprint(relatorios_bp) # Adicione o prefixo aqui


    # Rota global para verificar o status, se for mantida
    @app.route('/status', methods=['GET'])
    def status_check():
        return jsonify({'status': 'online', 'message': 'Backend online e pronto!'}), 200

    return app