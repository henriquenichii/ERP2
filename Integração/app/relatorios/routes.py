# Arquivo: app/relatorios/routes.py

import os
import openpyxl
import json
from flask import Blueprint, request, jsonify, send_file, current_app, after_this_request
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import Pedido, User
from app.Extractor import gerar_relatorio_entrega

# ESTA É A LINHA QUE ESTAVA FALTANDO
relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/api/reports')

@relatorios_bp.route('/export-selected-pedidos', methods=['POST'])
def export_selected_pedidos():
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json
    selected_pedido_ids = data.get('pedido_ids', [])

    if not selected_pedido_ids:
        return jsonify({'message': 'Nenhum ID de pedido selecionado para exportação.'}), 400

    pedidos_para_exportar = Pedido.query.filter(
        Pedido.id.in_(selected_pedido_ids)
    ).all()

    if not pedidos_para_exportar:
        return jsonify({'message': 'Nenhum pedido encontrado com os IDs fornecidos.'}), 404

    excel_data_list = []
    for p in pedidos_para_exportar:
        excel_data_list.append({
            'ID do Pedido': p.id,
            'Nome do Cliente': p.clienteNome,
            'Produto': p.tipoPedido,
            'Quantidade': p.quantidade,
            'Sabor': p.sabores,
            'Tipo Embalagem': p.tipoEmbalagem,
            'Data Evento': p.dataEvento,
            'Data de Retirada': p.dataRetirada,
            'Horário Retirada': p.horarioRetirada,
            'Status': p.status,
            'Criado Em': p.createdAt.strftime('%Y-%m-%d %H:%M:%S'),
            'Observações': p.observacoes
        })

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Pedidos Selecionados"
    
    if not excel_data_list:
        return jsonify({'message': 'Nenhum dado para exportar.'}), 404

    headers = list(excel_data_list[0].keys())
    sheet.append(headers)

    for item in excel_data_list:
        sheet.append(list(item.values()))

    export_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f"pedidos_selecionados_{export_date}.xlsx"
    temp_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], excel_filename)

    try:
        workbook.save(filename=temp_filepath)
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_filepath)
            except Exception as e:
                print(f"Erro ao remover arquivo temporário: {e}")
            return response

        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'message': f"Erro ao gerar a planilha: {e}"}), 500

@relatorios_bp.route('', methods=['GET'])
def get_relatorios():
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    current_month = datetime.now().month
    current_year = datetime.now().year
    
    pedidos_mes = db.session.query(func.count(Pedido.id)).filter(
        func.extract('month', Pedido.createdAt) == current_month,
        func.extract('year', Pedido.createdAt) == current_year
    ).scalar()

    produtos_query = db.session.query(
        Pedido.tipoPedido, func.sum(Pedido.quantidade)
    ).group_by(Pedido.tipoPedido).order_by(
        func.sum(Pedido.quantidade).desc()
    ).first()
    produtos_mais_pedidos = f"{produtos_query[0]} ({produtos_query[1]})" if produtos_query else 'N/A'

    clientes_query = db.session.query(
        Pedido.clienteNome, func.count(Pedido.id)
    ).group_by(Pedido.clienteNome).order_by(
        func.count(Pedido.id).desc()
    ).first()
    clientes_mais_pedidos = f"{clientes_query[0]} ({clientes_query[1]} pedidos)" if clientes_query else 'N/A'

    return jsonify({
        'totalPedidosMes': pedidos_mes or 0,
        'produtosMaisPedidos': produtos_mais_pedidos,
        'clientesMaisPedidos': clientes_mais_pedidos,
        'evolucaoSemanalMensal': [60, 80, 40, 90, 70]
    }), 200

@relatorios_bp.route('/generate-delivery-report/<int:pedido_id>', methods=['GET'])
def generate_delivery_report(pedido_id):
    user_email = request.headers.get('X-User-Id')
    if not user_email:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({'message': 'Pedido não encontrado.'}), 404

    dados_para_relatorio = {
        'Contratante': {'Nome': pedido.clienteNome, 'RG': pedido.clienteRG, 'CPF': pedido.clienteCPF},
        'Contratado': {'Nome Empresa': pedido.nomeContratado, 'CNPJ': pedido.cnpjContratado},
        'Data do Evento': pedido.dataEvento,
        'Local do Evento': pedido.localEvento,
        'Valor Total do Pedido': pedido.valorTotalPedidoContrato,
        'Data de Pagamento': pedido.dataPagamentoContrato,
        'Produtos Contratados': json.loads(pedido.produtosContratadosJson or '[]'),
        'Observacoes': pedido.observacoes
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"comprovante_retirada_{pedido_id}_{timestamp}.docx"
    temp_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], report_filename)

    try:
        gerar_relatorio_entrega(dados_para_relatorio, nome_arquivo=temp_filepath)
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_filepath)
            except Exception as e:
                print(f"Erro ao remover arquivo temporário: {e}")
            return response
        
        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=report_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return jsonify({'message': f"Erro ao gerar o comprovante: {str(e)}"}), 500