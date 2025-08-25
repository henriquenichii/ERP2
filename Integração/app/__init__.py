# Arquivo: app/__init__.py
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env ANTES de tudo.
# Isso garante que a Config encontre a DATABASE_URL.
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(basedir, '.env'))

db = SQLAlchemy()

def create_app():
    """
    Função Application Factory: configura e retorna a instância da aplicação Flask.
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)

    # Carrega as configurações do nosso objeto Config
    app.config.from_object('app.config.Config')

    # --- DEBUG: Imprime a URI do banco para confirmar que está correta ---
    print("*" * 80)
    print(f"INFO: Conectando ao banco de dados: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("*" * 80)
    
    db.init_app(app)

    # ... (o resto do seu código de criação de pasta e registro de blueprints continua igual) ...
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads_temp')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    from .main_pages.routes import main_pages_bp
    from .auth.routes import auth_bp
    from .pedidos.routes import pedidos_bp
    from .contratos.routes import contratos_bp
    from .relatorios.routes import relatorios_bp

    app.register_blueprint(main_pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(relatorios_bp)
    
    with app.app_context():
        db.create_all()
        print("Banco de dados inicializado e tabelas criadas (se necessário).")

    @app.route('/status', methods=['GET'])
    def status_check():
        return jsonify({'status': 'online', 'message': 'Backend online e pronto!'}), 200

    return app