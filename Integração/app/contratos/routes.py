import os
import json # Importar json para serializar a lista de produtos
from flask import Blueprint, request, jsonify, current_app
from app.Extractor import extrair_texto_de_pdf, extrair_dados_do_contrato, gerar_relatorio_entrega
from app.__init__ import load_data

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

    if not (file.filename.endswith('.pdf') or file.filename.endswith('.docx')):
        return jsonify({'message': 'Formato de arquivo inválido. Apenas .pdf ou .docx são permitidos.'}), 400

    filepath = os.path.join(upload_folder, file.filename)
    file.save(filepath)

    try:
        if filepath.endswith('.pdf'):
            texto_extraido = extrair_texto_de_pdf(filepath)
        elif filepath.endswith('.docx'):
            return jsonify({'message': 'Extração de .docx não implementada para o MVP. Por favor, envie um PDF.'}), 400
        else:
            return jsonify({'message': 'Formato de arquivo não suportado para extração.'}), 400

        if not texto_extraido:
            return jsonify({'message': 'Não foi possível extrair texto do contrato.'}), 500

        dados_extraidos_raw = extrair_dados_do_contrato(texto_extraido)

        # --- Mapeamento EXPANDIDO dos dados extraídos para o formato do pedido ---
        extracted_data_for_pedido = {
            'clienteNome': dados_extraidos_raw.get('Contratante', {}).get('Nome', 'Cliente Desconhecido'),
            'clienteRG': dados_extraidos_raw.get('Contratante', {}).get('RG', ''),
            'clienteCPF': dados_extraidos_raw.get('Contratante', {}).get('CPF', ''),
            'nomeContratado': dados_extraidos_raw.get('Contratado', {}).get('Nome Empresa', ''),
            'cnpjContratado': dados_extraidos_raw.get('Contratado', {}).get('CNPJ', ''),
            'valorTotalPedidoContrato': dados_extraidos_raw.get('Valor Total do Pedido', ''),
            'dataPagamentoContrato': dados_extraidos_raw.get('Data de Pagamento', ''),
            'dataEvento': dados_extraidos_raw.get('Data do Evento', '').replace('/', '-'), # Converte para YYYY-MM-DD
            'localEvento': dados_extraidos_raw.get('Local do Evento', ''),
            
            # Produtos Contratados serão armazenados como uma string JSON
            'produtosContratadosJson': json.dumps(dados_extraidos_raw.get('Produtos Contratados', [])),

            # Campos padrões para o pedido (alguns podem ser sobrescritos se extraídos)
            'tipoPedido': 'Contrato', # Pode ser um valor fixo ou tentar extrair do contrato
            'quantidade': 0, # Será calculado abaixo
            'sabores': '', # Será preenchido a partir dos produtos contratados
            'tipoEmbalagem': '', # Contratos podem não especificar
            'dataRetirada': '', # Contratos geralmente não têm data de retirada
            'horarioRetirada': '', # Contratos geralmente não têm horário de retirada
            'observacoes': f"Extraído de contrato: {file.filename}. Valor Total: R${dados_extraidos_raw.get('Valor Total do Pedido', 'N/A')}",
        }

        # Calcula a quantidade total de produtos e os sabores
        total_quantidade_produtos = 0
        sabores_list = []
        if isinstance(dados_extraidos_raw.get('Produtos Contratados'), list):
            for produto_item in dados_extraidos_raw['Produtos Contratados']:
                try:
                    total_quantidade_produtos += int(produto_item.get('Quantidade', '0'))
                except ValueError:
                    pass
                if produto_item.get('Produto'):
                    sabores_list.append(produto_item['Produto'])
        
        extracted_data_for_pedido['quantidade'] = total_quantidade_produtos if total_quantidade_produtos > 0 else 0
        extracted_data_for_pedido['sabores'] = ', '.join(sabores_list)

        return jsonify({
            'message': 'Dados extraídos com sucesso! Revise para salvar como pedido.',
            'extractedData': extracted_data_for_pedido,
            'rawData': dados_extraidos_raw # Envia os dados brutos também para revisão completa
        }), 200

    except Exception as e:
        print(f"Erro ao processar o arquivo de contrato: {e}")
        return jsonify({'message': f'Erro ao processar o contrato: {e}'}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
