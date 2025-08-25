from flask import Blueprint, request, jsonify, render_template
from app.__init__ import load_data, save_data # Importa as funções auxiliares

# Cria o Blueprint de autenticação. Prefixo URL /api/auth
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'E-mail e senha são obrigatórios.'}), 400

    users_data = load_data()
    if email in users_data['users']:
        return jsonify({'message': 'E-mail já cadastrado.'}), 409

    users_data['users'][email] = {'password': password}
    save_data(users_data)
    return jsonify({'message': 'Usuário cadastrado com sucesso!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'E-mail e senha são obrigatórios.'}), 400

    users_data = load_data()
    user = users_data['users'].get(email)

    if user and user['password'] == password:
        # Em um sistema real, você geraria e retornaria um token JWT aqui.
        # Por enquanto, retornamos o email como 'userId' para o frontend.
        return jsonify({'message': 'Login bem-sucedido!', 'userId': email}), 200
    else:
        return jsonify({'message': 'E-mail ou senha incorretos.'}), 401