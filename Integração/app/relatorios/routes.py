import os
from flask import Blueprint, request, jsonify, send_file, current_app, after_this_request 
from datetime import datetime
from app.__init__ import load_data
import time
import openpyxl
import json

from app.Extractor import gerar_relatorio_entrega

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/api/reports')


@relatorios_bp.route('/export-planilha', methods=['GET'])
def export_planilha():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data_inicio_str = request.args.get('dataInicio')
    data_fim_str = request.args.get('dataFim')
    tipo_produto = request.args.get('tipoProduto', '')

    if not data_inicio_str or not data_fim_str:
        return jsonify({'message': 'Datas de início e fim são obrigatórias.'}), 400

    all_data = load_data()
    pedidos_confirmados = [p for p in all_data['pedidos'] if p['userId'] == user_id and p['status'] == 'confirmado']

    pedidos_filtrados = []
    for pedido in pedidos_confirmados:
        try:
            start_date = datetime.fromisoformat(data_inicio_str)
            end_date = datetime.fromisoformat(data_fim_str)

            retirada_date_str = pedido.get('dataRetirada', '')
            pedido_retirada_date = None
            try:
                pedido_retirada_date = datetime.fromisoformat(retirada_date_str)
            except ValueError:
                try:
                    pedido_retirada_date = datetime.strptime(retirada_date_str, '%d-%m-%Y')
                except ValueError:
                    print(f"Warning: Could not parse dataRetirada '{retirada_date_str}' for pedido ID {pedido.get('id')}")
                    continue

            if retirada_date and start_date <= retirada_date <= end_date:
                if not tipo_produto or pedido['tipoPedido'] == tipo_produto:
                    pedidos_filtrados.append(pedido)
        except ValueError as ve:
            print(f"Erro de valor ao processar data: {pedido.get('dataRetirada')} - {ve}. Pedido ignorado.")
            continue

    if not pedidos_filtrados:
        return jsonify({'message': 'Nenhum pedido confirmado encontrado para o período selecionado.'}), 404

    excel_data_list = []
    for p in pedidos_filtrados:
        excel_data_list.append({
            'ID do Pedido': p.get('id', ''),
            'Nome do Cliente': p.get('clienteNome', ''),
            'Produto': p.get('tipoPedido', ''),
            'Quantidade': p.get('quantidade', ''),
            'Sabor': p.get('sabores', ''),
            'Tipo Embalagem': p.get('tipoEmbalagem', ''),
            'Data Evento': p.get('dataEvento', ''),
            'Data de Retirada': p.get('dataRetirada', ''),
            'Horário Retirada': p.get('horarioRetirada', ''),
            'Status': p.get('status', ''),
            'Criado Em': p.get('createdAt', ''),
            'Observações': p.get('observacoes', '')
        })

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Pedidos Confirmados"

    headers = list(excel_data_list[0].keys()) if excel_data_list else []
    if headers:
        sheet.append(headers)

    for item in excel_data_list:
        row_data = [item[header] for header in headers]
        sheet.append(row_data)

    excel_filename = f"pedidos_confirmados_{data_inicio_str}_a_{data_fim_str}.xlsx"
    temp_filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER'), excel_filename)

    try:
        workbook.save(filename=temp_filepath)
        @after_this_request
        def remove_file(response):
            max_retries = 5
            base_delay = 0.1 # segundos
            for i in range(max_retries):
                try:
                    os.remove(temp_filepath)
                    print(f"Arquivo temporário removido com sucesso: {temp_filepath}")
                    break # Sai do loop se a remoção for bem-sucedida
                except Exception as e:
                    print(f"Tentativa {i+1}/{max_retries}: Erro ao remover arquivo temporário {temp_filepath}: {e}")
                    time.sleep(base_delay * (2 ** i)) # Atraso exponencial
            else: # Executa se o loop terminar sem um 'break'
                print(f"ATENÇÃO: Não foi possível remover o arquivo temporário após {max_retries} tentativas: {temp_filepath}")
            return response

        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"\n[ERRO] Não foi possível salvar ou enviar a planilha: {e}")
        return jsonify({'message': f"Erro ao gerar a planilha: {e}"}), 500


@relatorios_bp.route('/export-selected-pedidos', methods=['POST'])
def export_selected_pedidos():
    """
    Gera uma planilha (XLSX) com base em uma lista de IDs de pedidos fornecidos.
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    data = request.json
    selected_pedido_ids = data.get('pedido_ids', [])

    if not selected_pedido_ids:
        return jsonify({'message': 'Nenhum ID de pedido selecionado para exportação.'}), 400

    all_data = load_data()
    all_pedidos = all_data['pedidos']

    # Filtra os pedidos que correspondem aos IDs selecionados e ao usuário logado
    pedidos_para_exportar = [
        p for p in all_pedidos 
        if p['id'] in selected_pedido_ids and p['userId'] == user_id
    ]

    if not pedidos_para_exportar:
        return jsonify({'message': 'Nenhum pedido encontrado com os IDs fornecidos ou não autorizado.'}), 404

    # Preparar dados para o Excel (mesma estrutura da função anterior)
    excel_data_list = []
    for p in pedidos_para_exportar:
        excel_data_list.append({
            'ID do Pedido': p.get('id', ''),
            'Nome do Cliente': p.get('clienteNome', ''),
            'Produto': p.get('tipoPedido', ''),
            'Quantidade': p.get('quantidade', ''),
            'Sabor': p.get('sabores', ''),
            'Tipo Embalagem': p.get('tipoEmbalagem', ''),
            'Data Evento': p.get('dataEvento', ''),
            'Data de Retirada': p.get('dataRetirada', ''),
            'Horário Retirada': p.get('horarioRetirada', ''),
            'Status': p.get('status', ''),
            'Criado Em': p.get('createdAt', ''),
            'Observações': p.get('observacoes', '')
        })

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Pedidos Selecionados"

    headers = list(excel_data_list[0].keys()) if excel_data_list else []
    if headers:
        sheet.append(headers)

    for item in excel_data_list:
        row_data = [item[header] for header in headers]
        sheet.append(row_data)

    # Nome do arquivo de saída (pode ser mais genérico já que não tem filtro de data)
    export_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f"pedidos_selecionados_{export_date}.xlsx"
    temp_filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER'), excel_filename)

    try:
        workbook.save(filename=temp_filepath)
        # NOVO: Agendar a remoção do arquivo após o envio da resposta
        @after_this_request
        def remove_file(response):
            max_retries = 5
            base_delay = 0.1 # segundos
            for i in range(max_retries):
                try:
                    os.remove(temp_filepath)
                    print(f"Arquivo temporário removido com sucesso: {temp_filepath}")
                    break # Sai do loop se a remoção for bem-sucedida
                except Exception as e:
                    print(f"Tentativa {i+1}/{max_retries}: Erro ao remover arquivo temporário {temp_filepath}: {e}")
                    time.sleep(base_delay * (2 ** i)) # Atraso exponencial
            else: # Executa se o loop terminar sem um 'break'
                print(f"ATENÇÃO: Não foi possível remover o arquivo temporário após {max_retries} tentativas: {temp_filepath}")
            return response

        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=excel_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"\n[ERRO] Não foi possível salvar ou enviar a planilha: {e}")
        return jsonify({'message': f"Erro ao gerar a planilha: {e}"}), 500


@relatorios_bp.route('', methods=['GET'])
def get_relatorios():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    all_data = load_data()
    user_pedidos = [p for p in all_data['pedidos'] if p['userId'] == user_id]

    current_month = datetime.now().month
    current_year = datetime.now().year
    pedidos_mes = 0
    for pedido in user_pedidos:
        try:
            created_at_date = datetime.fromisoformat(pedido['createdAt'])
            if created_at_date.month == current_month and created_at_date.year == current_year:
                pedidos_mes += 1
        except ValueError:
            continue

    produto_counts = {}
    for pedido in user_pedidos:
        tipo = pedido.get('tipoPedido', 'Não especificado')
        quantidade = int(pedido.get('quantidade', 0))
        produto_counts[tipo] = produto_counts.get(tipo, 0) + quantidade
    sorted_produtos = sorted(produto_counts.items(), key=lambda item: item[1], reverse=True)
    produtos_mais_pedidos = f"{sorted_produtos[0][0]} ({sorted_produtos[0][1]})" if sorted_produtos else 'N/A'

    cliente_counts = {}
    for pedido in user_pedidos:
        cliente = pedido.get('clienteNome', 'Anônimo')
        cliente_counts[cliente] = cliente_counts.get(cliente, 0) + 1
    sorted_clientes = sorted(cliente_counts.items(), key=lambda item: item[1], reverse=True)
    clientes_mais_pedidos = f"{sorted_clientes[0][0]} ({sorted_clientes[0][1]} pedidos)" if sorted_clientes else 'N/A'

    return jsonify({
        'totalPedidosMes': pedidos_mes,
        'produtosMaisPedidos': produtos_mais_pedidos,
        'clientesMaisPedidos': clientes_mais_pedidos,
        'evolucaoSemanalMensal': [60, 80, 40, 90, 70]
    }), 200


@relatorios_bp.route('/generate-delivery-report/<pedido_id>', methods=['GET'])
def generate_delivery_report(pedido_id):
    """
    Gera um relatório de entrega em .docx para um pedido específico
    e o envia para download.
    """
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    all_data = load_data()
    pedido_encontrado = None
    for p in all_data['pedidos']:
        if p['id'] == pedido_id and p['userId'] == user_id:
            pedido_encontrado = p
            break

    if not pedido_encontrado:
        return jsonify({'message': 'Pedido não encontrado ou não autorizado.'}), 404

    # --- Mapeamento dos dados do pedido para o formato esperado pelo Extractor.py ---
    # A função gerar_relatorio_entrega espera um dicionário com chaves como 'Contratante', 'Produtos Contratados' etc.
    # Precisamos mapear os campos do pedido_encontrado (do data.json) para esse formato.

    # Informações do Contratante
    contratante_info = {
        'Nome': pedido_encontrado.get('clienteNome', 'N/A'),
        'RG': pedido_encontrado.get('clienteRG', 'N/A'),
        'CPF': pedido_encontrado.get('clienteCPF', 'N/A'),
        'Telefone': pedido_encontrado.get('clienteTelefone', 'N/A'), # Adicionado para o DOCX
        'Email': pedido_encontrado.get('clienteEmail', 'N/A'),     # Adicionado para o DOCX
    }

    # Informações do Contratado (Divino Doces Finos)
    contratado_info = {
        'Nome Empresa': pedido_encontrado.get('nomeContratado', 'Divino Doces Finos'),
        'CNPJ': pedido_encontrado.get('cnpjContratado', 'N/A'),
    }

    # Produtos Contratados (Parse da string JSON)
    produtos_contratados_list = []
    try:
        if pedido_encontrado.get('produtosContratadosJson'):
            produtos_contratados_list = json.loads(pedido_encontrado['produtosContratadosJson'])
    except json.JSONDecodeError:
        print(f"Erro ao decodificar produtosContratadosJson para o pedido {pedido_id}")
        produtos_contratados_list = [] # Garante que seja uma lista vazia em caso de erro

    # Formato final dos dados para a função gerar_relatorio_entrega
    dados_para_relatorio = {
        'Contratante': contratante_info,
        'Contratado': contratado_info,
        'Data do Evento': pedido_encontrado.get('dataEvento', 'N/A'),
        'Local do Evento': pedido_encontrado.get('localEvento', 'Não Informado'),
        'Valor Total do Pedido': pedido_encontrado.get('valorTotalPedidoContrato', 'N/A'),
        'Data de Pagamento': pedido_encontrado.get('dataPagamentoContrato', 'N/A'),
        'Produtos Contratados': produtos_contratados_list,
        'Observacoes': pedido_encontrado.get('observacoes', 'N/A'),
    }

    # Nome do arquivo temporário
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"comprovante_retirada_{pedido_id}_{timestamp}.docx"
    temp_filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER'), report_filename)

    try:
        # Chama a função do Extractor para gerar o arquivo DOCX
        gerar_relatorio_entrega(dados_para_relatorio, nome_arquivo=temp_filepath)

        # Agendar a remoção do arquivo após o envio da resposta
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_filepath)
            except Exception as e:
                print(f"Erro ao remover arquivo temporário (generate_delivery_report): {e}")
            return response
        
        # Envia o arquivo gerado para o cliente
        return send_file(
            temp_filepath,
            as_attachment=True,
            download_name=report_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        print(f"\n[ERRO] Não foi possível gerar ou enviar o relatório de entrega: {e}")
        # Retorna uma mensagem de erro mais detalhada para o frontend
        return jsonify({'message': f"Erro ao gerar o comprovante: {e}"}), 500