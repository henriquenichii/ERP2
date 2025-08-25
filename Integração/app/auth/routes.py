# Arquivo: app/auth/routes.py

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

# O Blueprint continua o mesmo
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'E-mail e senha são obrigatórios.'}), 400

    # 1. VERIFICA NO BANCO se o usuário já existe
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'E-mail já cadastrado.'}), 409

    # 2. CRIA UM HASH SEGURO da senha
    hashed_password = generate_password_hash(password)

    # 3. CRIA UMA NOVA INSTÂNCIA do modelo User
    new_user = User(email=email, password_hash=hashed_password)

    # 4. SALVA O NOVO USUÁRIO no banco de dados
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Usuário cadastrado com sucesso!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'E-mail e senha são obrigatórios.'}), 400

    # 1. BUSCA O USUÁRIO no banco de dados pelo e-mail
    user = User.query.filter_by(email=email).first()

    # 2. VERIFICA se o usuário existe E se a senha fornecida corresponde ao hash salvo
    if user and check_password_hash(user.password_hash, password):
        # Em um sistema real, você geraria e retornaria um token JWT aqui.
        # Por enquanto, retornamos o email como 'userId' para o frontend.
        return jsonify({'message': 'Login bem-sucedido!', 'userId': user.email}), 200
    else:
        return jsonify({'message': 'E-mail ou senha incorretos.'}), 401