# Arquivo: app/contratos/routes.py

import os
import json
from flask import Blueprint, request, jsonify, current_app

# Importa as funções do nosso módulo Extractor
from app.Extractor import extrair_texto_de_pdf, extrair_dados_do_contrato

# O Blueprint continua o mesmo
contratos_bp = Blueprint('contratos', __name__, url_prefix='/api/contracts')

@contratos_bp.route('/upload', methods=['POST'])
def upload_contract():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return jsonify({'message': 'Usuário não autenticado.'}), 401

    if 'file' not in request.files:
        return jsonify({'message': 'Nenhum arquivo enviado.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Nenhum arquivo selecionado.'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return jsonify({'message': 'Pasta de upload não configurada.'}), 500

    if not file.filename.endswith('.pdf'):
         return jsonify({'message': 'Formato de arquivo inválido. Apenas .pdf é permitido.'}), 400

    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)

    try:
        texto_extraido = extrair_texto_de_pdf(filepath)
        if not texto_extraido:
            return jsonify({'message': 'Não foi possível extrair texto do contrato.'}), 500

        dados_extraidos_raw = extrair_dados_do_contrato(texto_extraido)

        # Mapeia os dados extraídos para o formato que o formulário de pedido espera
        # Isso permite que o frontend pré-preencha o formulário de criação de pedido
        extracted_data_for_pedido = {
            'clienteNome': dados_extraidos_raw.get('Contratante', {}).get('Nome', 'Cliente Desconhecido'),
            'clienteRG': dados_extraidos_raw.get('Contratante', {}).get('RG', ''),
            'clienteCPF': dados_extraidos_raw.get('Contratante', {}).get('CPF', ''),
            'nomeContratado': dados_extraidos_raw.get('Contratado', {}).get('Nome Empresa', ''),
            'cnpjContratado': dados_extraidos_raw.get('Contratado', {}).get('CNPJ', ''),
            'valorTotalPedidoContrato': dados_extraidos_raw.get('Valor Total do Pedido', ''),
            'dataPagamentoContrato': dados_extraidos_raw.get('Data de Pagamento', ''),
            'dataEvento': dados_extraidos_raw.get('Data do Evento', '').replace('/', '-'),
            'localEvento': dados_extraidos_raw.get('Local do Evento', ''),
            'produtosContratadosJson': json.dumps(dados_extraidos_raw.get('Produtos Contratados', [])),
            'observacoes': f"Extraído de contrato: {file.filename}. Valor Total: R${dados_extraidos_raw.get('Valor Total do Pedido', 'N/A')}",
        }
        
        # Calcula a quantidade total de produtos e os sabores
        total_quantidade_produtos = 0
        sabores_list = []
        if isinstance(dados_extraidos_raw.get('Produtos Contratados'), list):
            for produto_item in dados_extraidos_raw['Produtos Contratados']:
                try:
                    total_quantidade_produtos += int(produto_item.get('Quantidade', '0'))
                except (ValueError, TypeError):
                    pass # Ignora se a quantidade não for um número válido
                if produto_item.get('Produto'):
                    sabores_list.append(produto_item['Produto'])
        
        extracted_data_for_pedido['quantidade'] = total_quantidade_produtos
        extracted_data_for_pedido['sabores'] = ', '.join(sabores_list)
        
        # A resposta agora envia os dados mapeados para o frontend usar
        return jsonify({
            'message': 'Dados extraídos com sucesso! Revise para salvar como pedido.',
            'extractedData': extracted_data_for_pedido,
        }), 200

    except Exception as e:
        print(f"Erro ao processar o arquivo de contrato: {e}")
        return jsonify({'message': f'Erro ao processar o contrato: {str(e)}'}), 500
    finally:
        # Garante que o arquivo temporário seja sempre removido
        if os.path.exists(filepath):
            os.remove(filepath)