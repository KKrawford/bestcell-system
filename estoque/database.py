import sqlite3
import json
from datetime import datetime
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # Tabela de peças
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque_pecas (
            id TEXT PRIMARY KEY,
            descricao TEXT NOT NULL,
            modelo TEXT,
            quantidade INTEGER NOT NULL DEFAULT 0,
            observacoes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Tabela de capas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque_capas (
            id TEXT PRIMARY KEY,
            modelo TEXT NOT NULL,
            cor TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Tabela de películas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estoque_peliculas (
            id TEXT PRIMARY KEY,
            modelo TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            compatibilidade TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Tabela de compatibilidade de películas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS compatibilidade_peliculas (
            id TEXT PRIMARY KEY,
            modelo_principal TEXT NOT NULL,
            modelo_compativel TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(modelo_principal, modelo_compativel)
        )
    """)
    
    conn.commit()
    conn.close()

# Funções para Peças
def inserir_peca(peca):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO estoque_pecas 
        (id, descricao, modelo, quantidade, observacoes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        peca['id'],
        peca['descricao'],
        peca.get('modelo'),
        peca.get('quantidade', 0),
        peca.get('observacoes'),
        peca['created_at'],
        peca['updated_at']
    ))
    
    conn.commit()
    conn.close()

def buscar_pecas():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque_pecas ORDER BY descricao")
    pecas = cur.fetchall()
    conn.close()
    return [dict(peca) for peca in pecas]

def buscar_peca_por_id(peca_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque_pecas WHERE id = ?", (peca_id,))
    peca = cur.fetchone()
    conn.close()
    return dict(peca) if peca else None

def atualizar_peca(peca_id, descricao, modelo, quantidade, observacoes):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE estoque_pecas 
        SET descricao = ?, modelo = ?, quantidade = ?, observacoes = ?, updated_at = ?
        WHERE id = ?
    """, (descricao, modelo, quantidade, observacoes, datetime.utcnow().isoformat(), peca_id))
    
    conn.commit()
    conn.close()

def excluir_peca(peca_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM estoque_pecas WHERE id = ?", (peca_id,))
    
    conn.commit()
    conn.close()

# Funções para Capas
def inserir_capa(capa):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO estoque_capas 
        (id, modelo, cor, quantidade, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        capa['id'],
        capa['modelo'],
        capa['cor'],
        capa.get('quantidade', 0),
        capa['created_at'],
        capa['updated_at']
    ))
    
    conn.commit()
    conn.close()

def buscar_capas():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque_capas ORDER BY modelo, cor")
    capas = cur.fetchall()
    conn.close()
    return [dict(capa) for capa in capas]

def buscar_capa_por_id(capa_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque_capas WHERE id = ?", (capa_id,))
    capa = cur.fetchone()
    conn.close()
    return dict(capa) if capa else None

def atualizar_capa(capa_id, modelo, cor, quantidade):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE estoque_capas 
        SET modelo = ?, cor = ?, quantidade = ?, updated_at = ?
        WHERE id = ?
    """, (modelo, cor, quantidade, datetime.utcnow().isoformat(), capa_id))
    
    conn.commit()
    conn.close()

def excluir_capa(capa_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM estoque_capas WHERE id = ?", (capa_id,))
    
    conn.commit()
    conn.close()

# Funções para Películas
def inserir_pelicula(pelicula):
    conn = get_connection()
    cur = conn.cursor()
    
    compatibilidade = pelicula.get('compatibilidade')
    if isinstance(compatibilidade, list):
        compatibilidade = json.dumps(compatibilidade)
    
    cur.execute("""
        INSERT INTO estoque_peliculas 
        (id, modelo, quantidade, compatibilidade, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        pelicula['id'],
        pelicula['modelo'],
        pelicula.get('quantidade', 0),
        compatibilidade,
        pelicula['created_at'],
        pelicula['updated_at']
    ))
    
    conn.commit()
    conn.close()

def buscar_peliculas():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque_peliculas ORDER BY modelo")
    peliculas = cur.fetchall()
    conn.close()
    
    # Converter compatibilidade de JSON para lista
    peliculas_dict = []
    for pelicula in peliculas:
        peli_dict = dict(pelicula)
        if peli_dict.get('compatibilidade'):
            try:
                peli_dict['compatibilidade'] = json.loads(peli_dict['compatibilidade'])
            except:
                peli_dict['compatibilidade'] = []
        peliculas_dict.append(peli_dict)
    
    return peliculas_dict

def buscar_pelicula_por_id(pelicula_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque_peliculas WHERE id = ?", (pelicula_id,))
    pelicula = cur.fetchone()
    conn.close()
    
    if pelicula:
        peli_dict = dict(pelicula)
        if peli_dict.get('compatibilidade'):
            try:
                peli_dict['compatibilidade'] = json.loads(peli_dict['compatibilidade'])
            except:
                peli_dict['compatibilidade'] = []
        return peli_dict
    return None

def atualizar_pelicula(pelicula_id, modelo, quantidade, compatibilidade):
    conn = get_connection()
    cur = conn.cursor()
    
    if isinstance(compatibilidade, list):
        compatibilidade = json.dumps(compatibilidade)
    
    cur.execute("""
        UPDATE estoque_peliculas 
        SET modelo = ?, quantidade = ?, compatibilidade = ?, updated_at = ?
        WHERE id = ?
    """, (modelo, quantidade, compatibilidade, datetime.utcnow().isoformat(), pelicula_id))
    
    conn.commit()
    conn.close()

def excluir_pelicula(pelicula_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM estoque_peliculas WHERE id = ?", (pelicula_id,))
    
    conn.commit()
    conn.close()

# Funções para compatibilidade
def inserir_compatibilidade(compatibilidade):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO compatibilidade_peliculas 
            (id, modelo_principal, modelo_compativel, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            compatibilidade['id'],
            compatibilidade['modelo_principal'],
            compatibilidade['modelo_compativel'],
            compatibilidade['created_at']
        ))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Relação já existe
        return False
    finally:
        conn.close()

def buscar_compatibilidades_por_modelo(modelo_principal):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT modelo_compativel 
        FROM compatibilidade_peliculas 
        WHERE modelo_principal = ?
        ORDER BY modelo_compativel
    """, (modelo_principal,))
    
    resultados = cur.fetchall()
    conn.close()
    return [row['modelo_compativel'] for row in resultados]

def buscar_todas_compatibilidades():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * 
        FROM compatibilidade_peliculas 
        ORDER BY modelo_principal, modelo_compativel
    """)
    
    resultados = cur.fetchall()
    conn.close()
    return [dict(row) for row in resultados]

def excluir_compatibilidade(compatibilidade_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM compatibilidade_peliculas WHERE id = ?", (compatibilidade_id,))
    
    conn.commit()
    conn.close()

def buscar_modelos_principais():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT DISTINCT modelo_principal 
        FROM compatibilidade_peliculas 
        ORDER BY modelo_principal
    """)
    
    resultados = cur.fetchall()
    conn.close()
    return [row['modelo_principal'] for row in resultados]

# Busca unificada
def buscar_estoque(termo):
    conn = get_connection()
    cur = conn.cursor()
    
    termo_like = f'%{termo}%'
    
    # Busca em peças
    cur.execute("""
        SELECT 
            'peca' as tipo,
            id,
            descricao as descricao,
            modelo,
            quantidade,
            observacoes as informacao_adicional,
            NULL as cor,
            NULL as compatibilidade
        FROM estoque_pecas
        WHERE descricao LIKE ? OR modelo LIKE ? OR observacoes LIKE ?
    """, (termo_like, termo_like, termo_like))
    
    pecas = cur.fetchall()
    
    # Busca em capas
    cur.execute("""
        SELECT 
            'capa' as tipo,
            id,
            modelo as descricao,
            modelo,
            quantidade,
            NULL as informacao_adicional,
            cor,
            NULL as compatibilidade
        FROM estoque_capas
        WHERE modelo LIKE ? OR cor LIKE ?
    """, (termo_like, termo_like))
    
    capas = cur.fetchall()
    
    # Busca em películas
    cur.execute("""
        SELECT 
            'pelicula' as tipo,
            id,
            modelo as descricao,
            modelo,
            quantidade,
            NULL as informacao_adicional,
            NULL as cor,
            compatibilidade
        FROM estoque_peliculas
        WHERE modelo LIKE ? OR compatibilidade LIKE ?
    """, (termo_like, termo_like))
    
    peliculas = cur.fetchall()
    
    conn.close()
    
    # Combinar resultados
    resultados = []
    for item in pecas + capas + peliculas:
        resultados.append(dict(item))
    
    # Converter compatibilidade de JSON para lista, se houver
    for resultado in resultados:
        if resultado.get('compatibilidade'):
            try:
                resultado['compatibilidade'] = json.loads(resultado['compatibilidade'])
            except:
                resultado['compatibilidade'] = []
    
    return resultados


# Funções para dashboard
def contar_produtos_por_tipo():
    conn = get_connection()
    cur = conn.cursor()
    
    # Contar peças
    cur.execute("SELECT COUNT(*) as total FROM estoque_pecas")
    total_pecas = cur.fetchone()['total']
    
    # Contar capas
    cur.execute("SELECT COUNT(*) as total FROM estoque_capas")
    total_capas = cur.fetchone()['total']
    
    # Contar películas
    cur.execute("SELECT COUNT(*) as total FROM estoque_peliculas")
    total_peliculas = cur.fetchone()['total']
    
    conn.close()
    
    return {
        "pecas": total_pecas,
        "capas": total_capas,
        "peliculas": total_peliculas
    }

def somar_quantidade_total():
    conn = get_connection()
    cur = conn.cursor()
    
    # Somar quantidade de peças
    cur.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM estoque_pecas")
    total_pecas = cur.fetchone()['total']
    
    # Somar quantidade de capas
    cur.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM estoque_capas")
    total_capas = cur.fetchone()['total']
    
    # Somar quantidade de películas
    cur.execute("SELECT COALESCE(SUM(quantidade), 0) as total FROM estoque_peliculas")
    total_peliculas = cur.fetchone()['total']
    
    conn.close()
    
    return {
        "pecas": total_pecas,
        "capas": total_capas,
        "peliculas": total_peliculas,
        "geral": total_pecas + total_capas + total_peliculas
    }

def obter_capas_sem_estoque():
    conn = get_connection()
    cur = conn.cursor()
    
    # Buscar capas com quantidade zero
    cur.execute("""
        SELECT modelo, cor, quantidade 
        FROM estoque_capas 
        WHERE quantidade = 0
        ORDER BY modelo, cor
    """)
    
    capas_sem_estoque = cur.fetchall()
    
    # Buscar informações sobre cores disponíveis por modelo
    cur.execute("""
        SELECT modelo, GROUP_CONCAT(cor, ', ') as cores_disponiveis
        FROM estoque_capas 
        WHERE quantidade > 0
        GROUP BY modelo
        ORDER BY modelo
    """)
    
    cores_por_modelo = {row['modelo']: row['cores_disponiveis'] for row in cur.fetchall()}
    
    conn.close()
    
    return [dict(capa) for capa in capas_sem_estoque], cores_por_modelo

def obter_peliculas_com_estoque_baixo(estoque_minimo=5):
    conn = get_connection()
    cur = conn.cursor()
    
    # Buscar películas com quantidade abaixo do mínimo
    cur.execute("""
        SELECT modelo, quantidade, compatibilidade
        FROM estoque_peliculas 
        WHERE quantidade < ?
        ORDER BY modelo
    """, (estoque_minimo,))
    
    peliculas = cur.fetchall()
    
    # Converter compatibilidade de JSON para lista
    peliculas_dict = []
    for pelicula in peliculas:
        peli_dict = dict(pelicula)
        if peli_dict.get('compatibilidade'):
            try:
                peli_dict['compatibilidade'] = json.loads(peli_dict['compatibilidade'])
            except:
                peli_dict['compatibilidade'] = []
        peliculas_dict.append(peli_dict)
    
    conn.close()
    
    return peliculas_dict

def buscar_todos_modelos_peliculas():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT modelo FROM estoque_peliculas ORDER BY modelo")
    resultados = cur.fetchall()
    conn.close()
    return [row['modelo'] for row in resultados]

def atualizar_compatibilidade_peliculas(modelo_principal):
    """Atualiza a compatibilidade de todas as películas com o modelo principal especificado"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Buscar todas as compatibilidades para este modelo
    compatibilidades = buscar_compatibilidades_por_modelo(modelo_principal)
    
    # Atualizar todas as películas com este modelo
    if compatibilidades:
        compatibilidades_json = json.dumps(compatibilidades)
        cur.execute("""
            UPDATE estoque_peliculas 
            SET compatibilidade = ?, updated_at = ?
            WHERE modelo = ?
        """, (compatibilidades_json, datetime.utcnow().isoformat(), modelo_principal))
    else:
        # Se não houver compatibilidades, definir como lista vazia
        cur.execute("""
            UPDATE estoque_peliculas 
            SET compatibilidade = ?, updated_at = ?
            WHERE modelo = ?
        """, ("[]", datetime.utcnow().isoformat(), modelo_principal))
    
    conn.commit()
    conn.close()

# Adicionar ao database.py

def atualizar_todas_compatibilidades_peliculas():
    """Atualiza a compatibilidade de todas as películas com base nas relações cadastradas"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Buscar todos os modelos de películas
    cur.execute("SELECT DISTINCT modelo FROM estoque_peliculas")
    modelos = [row['modelo'] for row in cur.fetchall()]
    
    # Para cada modelo, atualizar suas compatibilidades
    for modelo in modelos:
        compatibilidades = buscar_compatibilidades_por_modelo(modelo)
        
        if compatibilidades:
            compatibilidades_json = json.dumps(compatibilidades)
            cur.execute("""
                UPDATE estoque_peliculas 
                SET compatibilidade = ?, updated_at = ?
                WHERE modelo = ?
            """, (compatibilidades_json, datetime.utcnow().isoformat(), modelo))
        else:
            # Se não houver compatibilidades, definir como lista vazia
            cur.execute("""
                UPDATE estoque_peliculas 
                SET compatibilidade = ?, updated_at = ?
                WHERE modelo = ?
            """, ("[]", datetime.utcnow().isoformat(), modelo))
    
    conn.commit()
    conn.close()
