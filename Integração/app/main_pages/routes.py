from flask import Blueprint, render_template

# Este Blueprint servirá todas as suas páginas HTML.
# Não terá um prefixo de URL para que as rotas sejam simples, ex: /login, /pedidos.
main_pages_bp = Blueprint('main_pages', __name__)

@main_pages_bp.route('/')
@main_pages_bp.route('/login')
def login_page():
    """Rota para a página de login."""
    return render_template('login.html')

@main_pages_bp.route('/pedidos')
def list_pedidos_page():
    """Rota para a página de listagem de pedidos."""
    return render_template('lista_pedidos.html')

@main_pages_bp.route('/pedidos/novo')
def new_pedido_page():
    """Rota para a página de criação de um novo pedido."""
    return render_template('cadastro_pedido.html')

@main_pages_bp.route('/pedidos/<pedido_id>')
def details_pedido_page(pedido_id):
    """Rota para a página de detalhes de um pedido específico."""
    # O 'pedido_id' pode ser usado pelo JavaScript na página para buscar os dados.
    return render_template('detalhes_pedido.html')

@main_pages_bp.route('/contratos')
def upload_contratos_page():
    """Rota para a página de upload de contratos."""
    return render_template('upload_contratos.html')

@main_pages_bp.route('/exportar')
def exportar_planilha_page():
    """Rota para a página de exportação de planilhas."""
    return render_template('exportacao_planilha.html')

@main_pages_bp.route('/relatorios')
def relatorios_page():
    """Rota para a página de relatórios e indicadores."""
    return render_template('relatorios.html')