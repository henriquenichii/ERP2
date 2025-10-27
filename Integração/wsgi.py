# Ficheiro: wsgi.py
# Este ficheiro serve como o ponto de entrada para o servidor de produção Gunicorn.

from app import create_app

app = create_app()