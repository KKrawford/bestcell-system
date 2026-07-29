from datetime import datetime
import uuid

from .database import (
    buscar_compatibilidades_por_modelo,
    buscar_modelos_principais,
    buscar_todos_modelos_peliculas
)

# Manter o dicionário como fallback/backup
COMPATIBILIDADE_PELICULAS = {
    "iPhone 12": ["iPhone 12 Pro", "iPhone 12 Mini"],
    "iPhone 13": ["iPhone 13 Pro", "iPhone 13 Mini"],
    "Samsung Galaxy S21": ["Samsung Galaxy S21 Plus", "Samsung Galaxy S21 Ultra"],
    "Samsung Galaxy S22": ["Samsung Galaxy S22 Plus", "Samsung Galaxy S22 Ultra"],
}

def sugerir_compatibilidade(modelo_principal):
    """Sugere modelos compatíveis com base no banco de dados e fallback para o dicionário"""
    # Primeiro tenta buscar do banco de dados
    compatibilidades_db = buscar_compatibilidades_por_modelo(modelo_principal)
    
    if compatibilidades_db:
        return compatibilidades_db
    
    # Fallback para o dicionário se não encontrar no banco
    return COMPATIBILIDADE_PELICULAS.get(modelo_principal, [])

def obter_modelos_principais():
    """Obtém todos os modelos principais do banco de dados e das películas cadastradas"""
    modelos_db = buscar_modelos_principais()
    
    # Adiciona modelos do dicionário que não estão no banco
    modelos_dict = list(COMPATIBILIDADE_PELICULAS.keys())
    
    # Adiciona modelos das películas cadastradas
    modelos_peliculas = buscar_todos_modelos_peliculas()
    
    # Combina e remove duplicatas
    todos_modelos = list(set(modelos_db + modelos_dict + modelos_peliculas))
    todos_modelos.sort()
    
    return todos_modelos

def calcular_quantidade_total_pelicula(pelicula, todas_peliculas):
    """
    Soma a quantidade do modelo principal com a quantidade
    de todos os modelos compatíveis que também estão cadastrados
    como modelo principal no estoque.
    """
    quantidade_total = pelicula['quantidade']
    
    modelos_compatíveis = pelicula.get('compatibilidade', [])
    
    # Mapeia modelo -> quantidade para busca rápida
    estoque_por_modelo = {p['modelo']: p['quantidade'] for p in todas_peliculas}
    
    for modelo_compat in modelos_compatíveis:
        quantidade_total += estoque_por_modelo.get(modelo_compat, 0)
    
    return quantidade_total

# Adicionar a função auxiliar
def filtrar_valores_validos(opcoes, valores):
    """Filtra valores para garantir que todos estejam presentes nas opções"""
    return [v for v in valores if v in opcoes]