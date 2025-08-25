from flask import Blueprint, request, jsonify
from datetime import datetime
from app.__init__ import load_data, save_data # Importa as funções auxiliares

# Cria o Blueprint de pedidos. Prefixo URL /api/pedidos
pedidos_bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')

@pedidos_bp.route('', methods=['POST'])
def create_pedido():
    data = request.json
    user_id = request.headers.get('X-User-Id')

    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    # Campos obrigatórios para qualquer pedido
    required_fields = ['clienteNome', 'dataEvento', 'quantidade', 'tipoPedido', 'dataRetirada', 'horarioRetirada']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({'message': 'Cliente, Data do Evento, Quantidade, Tipo de Pedido, Data e Horário de Retirada são obrigatórios.'}), 400

    new_pedido = {
        'id': str(datetime.now().timestamp()), # ID único baseado no timestamp
        'clienteNome': data['clienteNome'],
        'dataEvento': data['dataEvento'],
        'dataRetirada': data['dataRetirada'],
        'horarioRetirada': data['horarioRetirada'],
        'tipoPedido': data['tipoPedido'],
        'quantidade': int(data['quantidade']),
        'sabores': data.get('sabores', ''),
        'tipoEmbalagem': data.get('tipoEmbalagem', ''),
        'observacoes': data.get('observacoes', ''),
        'status': 'pendente', # Status inicial padrão
        'createdAt': datetime.now().isoformat(),
        'userId': user_id, # Associa o pedido ao usuário logado

        # --- NOVOS CAMPOS DO CONTRATO ---
        'clienteRG': data.get('clienteRG', ''),
        'clienteCPF': data.get('clienteCPF', ''),
        'nomeContratado': data.get('nomeContratado', ''),
        'cnpjContratado': data.get('cnpjContratado', ''),
        'valorTotalPedidoContrato': data.get('valorTotalPedidoContrato', ''),
        'dataPagamentoContrato': data.get('dataPagamentoContrato', ''),
        'localEvento': data.get('localEvento', ''),
        'produtosContratadosJson': data.get('produtosContratadosJson', '[]') # Salva como string JSON vazia se não houver
    }

    all_data = load_data()
    all_data['pedidos'].append(new_pedido)
    save_data(all_data)
    return jsonify({'message': 'Pedido salvo com sucesso!', 'pedido': new_pedido}), 201

@pedidos_bp.route('', methods=['GET'])
def get_pedidos():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    all_data = load_data()
    pedidos = [p for p in all_data['pedidos'] if p['userId'] == user_id]

    filtro_cliente = request.args.get('cliente', '').lower()
    filtro_data_evento = request.args.get('dataEvento', '') # Filtra por dataEvento
    filtro_data_retirada_inicio_str = request.args.get('dataInicio', '') # Novo filtro: data de retirada início
    filtro_data_retirada_fim_str = request.args.get('dataFim', '')       # Novo filtro: data de retirada fim
    filtro_status = request.args.get('status', '')
    
    # Se o filtro de status for uma lista (do exportacao.js), ajusta
    if isinstance(filtro_status, str) and ',' in filtro_status:
        filtro_status = filtro_status.split(',')


    pedidos_filtrados = []
    for pedido in pedidos:
        match = True

        if filtro_cliente and filtro_cliente not in pedido['clienteNome'].lower():
            match = False
        
        if filtro_data_evento and pedido['dataEvento'] != filtro_data_evento:
            match = False

        # Lógica para filtrar por data de retirada (intervalo)
        if filtro_data_retirada_inicio_str and filtro_data_retirada_fim_str:
            try:
                retirada_date_str = pedido.get('dataRetirada', '')
                pedido_retirada_date = None
                # Tenta parsear YYYY-MM-DD (do input date)
                try:
                    pedido_retirada_date = datetime.fromisoformat(retirada_date_str)
                except ValueError:
                    # Tenta parsear DD-MM-YYYY (do contrato)
                    try:
                        pedido_retirada_date = datetime.strptime(retirada_date_str, '%d-%m-%Y')
                    except ValueError:
                        pass # Não conseguiu parsear, então não vai dar match

                start_date_filter = datetime.fromisoformat(filtro_data_retirada_inicio_str)
                end_date_filter = datetime.fromisoformat(filtro_data_retirada_fim_str)

                if not (pedido_retirada_date and start_date_filter <= pedido_retirada_date <= end_date_filter):
                    match = False
            except ValueError:
                match = False # Se as datas do filtro forem inválidas, não há match
        
        # Lógica para filtrar por status (pode ser uma string ou uma lista de strings)
        if filtro_status:
            if isinstance(filtro_status, list):
                if pedido['status'] not in filtro_status:
                    match = False
            else: # É uma string simples
                if pedido['status'] != filtro_status:
                    match = False

        if match:
            pedidos_filtrados.append(pedido)

    return jsonify(pedidos_filtrados), 200
# def get_pedidos():
#     user_id = request.headers.get('X-User-Id')
#     if not user_id:
#         return jsonify({'message': 'Usuário não autenticado.'}), 401

#     all_data = load_data()
#     pedidos = [p for p in all_data['pedidos'] if p['userId'] == user_id]

#     # Lógica de filtro para a listagem de pedidos
#     filtro_cliente = request.args.get('cliente', '').lower()
#     filtro_data = request.args.get('data', '')
#     filtro_status = request.args.get('status', '')

#     if filtro_cliente:
#         pedidos = [p for p in pedidos if filtro_cliente in p['clienteNome'].lower()]
#     if filtro_data:
#         pedidos = [p for p in pedidos if p['dataEvento'] == filtro_data]
#     if filtro_status:
#         pedidos = [p for p in pedidos if p['status'] == filtro_status]

#     return jsonify(pedidos), 200

@pedidos_bp.route('/<pedido_id>', methods=['PUT'])
def update_pedido(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json

    all_data = load_data()
    for pedido in all_data['pedidos']:
        if pedido['id'] == pedido_id and pedido['userId'] == user_id:
            # Atualiza todos os campos fornecidos na requisição, exceto o ID e userId
            for key, value in data.items():
                if key not in ['id', 'userId', 'createdAt']: # Não permitir mudança de ID ou criador
                    pedido[key] = value

            save_data(all_data)
            return jsonify({'message': 'Pedido atualizado com sucesso!', 'pedido': pedido}), 200
    return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404

@pedidos_bp.route('/<pedido_id>', methods=['DELETE'])
def delete_pedido(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    all_data = load_data()
    initial_len = len(all_data['pedidos'])
    # Remove o pedido se o ID e o userId corresponderem
    all_data['pedidos'] = [p for p in all_data['pedidos'] if not (p['id'] == pedido_id and p['userId'] == user_id)]

    if len(all_data['pedidos']) < initial_len: # Verifica se algum pedido foi removido
        save_data(all_data)
        return jsonify({'message': 'Pedido excluído com sucesso!'}), 200
    return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404

@pedidos_bp.route('/<pedido_id>', methods=['GET'])
def get_pedido_details(pedido_id):
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    all_data = load_data()
    for pedido in all_data['pedidos']:
        if pedido['id'] == pedido_id and pedido['userId'] == user_id:
            return jsonify(pedido), 200
    return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404
