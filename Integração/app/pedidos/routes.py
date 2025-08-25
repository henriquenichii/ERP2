# Arquivo: app/pedidos/routes.py

from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Pedido, User

# A variável é definida aqui, no topo do arquivo
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')

# Função auxiliar para converter um objeto Pedido em um dicionário
def pedido_to_dict(pedido):
    return {
        'id': pedido.id,
        'clienteNome': pedido.clienteNome,
        'dataEvento': pedido.dataEvento,
        'dataRetirada': pedido.dataRetirada,
        'horarioRetirada': pedido.horarioRetirada,
        'tipoPedido': pedido.tipoPedido,
        'quantidade': pedido.quantidade,
        'sabores': pedido.sabores,
        'tipoEmbalagem': pedido.tipoEmbalagem,
        'observacoes': pedido.observacoes,
        'status': pedido.status,
        'createdAt': pedido.createdAt.isoformat(),
        'userId': pedido.user_id,
        'clienteRG': pedido.clienteRG,
        'clienteCPF': pedido.clienteCPF,
        'nomeContratado': pedido.nomeContratado,
        'cnpjContratado': pedido.cnpjContratado,
        'valorTotalPedidoContrato': pedido.valorTotalPedidoContrato,
        'dataPagamentoContrato': pedido.dataPagamentoContrato,
        'localEvento': pedido.localEvento,
        'produtosContratadosJson': pedido.produtosContratadosJson,
    }

@pedidos_bp.route('', methods=['POST'])
def create_pedido():
    data = request.json
    user_email = request.headers.get('X-User-Id')

    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401
    
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({'message': 'Usuário inválido.'}), 401

    required_fields = ['clienteNome', 'dataEvento', 'quantidade', 'tipoPedido', 'dataRetirada', 'horarioRetirada']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({'message': 'Campos obrigatórios faltando.'}), 400

    new_pedido = Pedido(
        clienteNome=data['clienteNome'],
        dataEvento=data['dataEvento'],
        dataRetirada=data['dataRetirada'],
        horarioRetirada=data['horarioRetirada'],
        tipoPedido=data['tipoPedido'],
        quantidade=int(data['quantidade']),
        sabores=data.get('sabores', ''),
        tipoEmbalagem=data.get('tipoEmbalagem', ''),
        observacoes=data.get('observacoes', ''),
        status='pendente',
        user_id=user.id,
        clienteRG=data.get('clienteRG', ''),
        clienteCPF=data.get('clienteCPF', ''),
        nomeContratado=data.get('nomeContratado', ''),
        cnpjContratado=data.get('cnpjContratado', ''),
        valorTotalPedidoContrato=data.get('valorTotalPedidoContrato', ''),
        dataPagamentoContrato=data.get('dataPagamentoContrato', ''),
        localEvento=data.get('localEvento', ''),
        produtosContratadosJson=data.get('produtosContratadosJson', '[]')
    )

    db.session.add(new_pedido)
    db.session.commit()
    
    return jsonify({'message': 'Pedido salvo com sucesso!', 'pedido': pedido_to_dict(new_pedido)}), 201

@pedidos_bp.route('', methods=['GET'])
def get_pedidos():
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401
    
    query = Pedido.query

    if 'cliente' in request.args and request.args['cliente']:
        query = query.filter(Pedido.clienteNome.ilike(f"%{request.args['cliente']}%"))
    if 'dataEvento' in request.args and request.args['dataEvento']:
        query = query.filter_by(dataEvento=request.args['dataEvento'])
    if 'status' in request.args and request.args['status']:
        status_filter = request.args['status']
        if ',' in status_filter:
            query = query.filter(Pedido.status.in_(status_filter.split(',')))
        else:
            query = query.filter_by(status=status_filter)
    
    pedidos = query.order_by(Pedido.createdAt.desc()).all()
    pedidos_list = [pedido_to_dict(p) for p in pedidos]
    
    return jsonify(pedidos_list), 200

@pedidos_bp.route('/<int:pedido_id>', methods=['GET'])
def get_pedido_details(pedido_id):
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.get(pedido_id)
    
    if pedido:
        return jsonify(pedido_to_dict(pedido)), 200
    return jsonify({'message': 'Pedido não encontrado.'}), 404

@pedidos_bp.route('/<int:pedido_id>', methods=['PUT'])
def update_pedido(pedido_id):
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'message': 'Pedido não encontrado.'}), 404

    data = request.json
    for key, value in data.items():
        if hasattr(pedido, key) and key not in ['id', 'user_id', 'createdAt']:
            setattr(pedido, key, value)
            
    db.session.commit()
    return jsonify({'message': 'Pedido atualizado com sucesso!', 'pedido': pedido_to_dict(pedido)}), 200

@pedidos_bp.route('/<int:pedido_id>', methods=['DELETE'])
def delete_pedido(pedido_id):
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'message': 'Pedido não encontrado.'}), 404

    db.session.delete(pedido)
    db.session.commit()
    return jsonify({'message': 'Pedido excluído com sucesso!'}), 200