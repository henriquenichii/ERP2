# Arquivo: app/config.py
import os

class Config:
    """
    Classe de configuração da aplicação Flask.
    Lê as configurações a partir das variáveis de ambiente.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma_chave_secreta_padrao_para_desenvolvimento'

    # A URI do banco de dados será lida diretamente da variável de ambiente
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    SQLALCHEMY_TRACK_MODIFICATIONS = False