import sys
import os

# Adiciona o diretório atual ao path para que o Python encontre seu app
sys.path.append(os.getcwd())

# Importa o objeto 'app' do seu arquivo 'app.py' e o renomeia para 'application'
# O Passenger exige que o objeto se chame 'application'
from app import app as application
