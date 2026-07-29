import sqlite3
from config import DB_PATH


def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


# ======================================================
# INICIALIZAÇÃO
# ======================================================

def init_db():
    con = get_connection()
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS catalogo_iphones (
            id           TEXT PRIMARY KEY,
            modelo       TEXT NOT NULL,
            armazenamento TEXT NOT NULL,
            cor          TEXT NOT NULL,
            bateria      INTEGER,
            disponivel   INTEGER NOT NULL DEFAULT 0,
            preco_avista REAL NOT NULL,
            observacoes  TEXT,
            created_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS catalogo_androids (
            id            TEXT PRIMARY KEY,
            marca         TEXT NOT NULL,
            modelo        TEXT NOT NULL,
            ram           TEXT NOT NULL,
            armazenamento TEXT NOT NULL,
            estado        TEXT NOT NULL CHECK(estado IN ('novo', 'usado')),
            preco_avista  REAL NOT NULL,
            observacoes   TEXT,
            created_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS catalogo_perfumes (
            id          TEXT PRIMARY KEY,
            marca       TEXT NOT NULL,
            nome        TEXT NOT NULL,
            preco       REAL NOT NULL,
            observacoes TEXT,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS catalogo_pods (
            id          TEXT PRIMARY KEY,
            marca       TEXT NOT NULL,
            nome        TEXT NOT NULL,
            puffs       INTEGER NOT NULL,
            preco       REAL NOT NULL,
            observacoes TEXT,
            created_at  TEXT NOT NULL
        );
    """)

    con.commit()
    con.close()


# ======================================================
# IPHONES
# ======================================================

def inserir_iphone(dados: dict):
    con = get_connection()
    con.execute(
        """INSERT INTO catalogo_iphones (
            id, modelo, armazenamento, cor, bateria,
            disponivel, preco_avista, observacoes, created_at
        ) VALUES (
            :id, :modelo, :armazenamento, :cor, :bateria,
            :disponivel, :preco_avista, :observacoes, :created_at
        )""",
        dados
    )
    con.commit()
    con.close()


def buscar_iphones(apenas_disponiveis: bool = False):
    con = get_connection()
    query = "SELECT * FROM catalogo_iphones"
    if apenas_disponiveis:
        query += " WHERE disponivel = 1"
    query += " ORDER BY modelo, armazenamento, cor"
    rows = con.execute(query).fetchall()
    con.close()
    return [dict(r) for r in rows]


def buscar_iphone_por_id(iphone_id: str):
    con = get_connection()
    row = con.execute(
        "SELECT * FROM catalogo_iphones WHERE id = ?", (iphone_id,)
    ).fetchone()
    con.close()
    return dict(row) if row else None


def atualizar_iphone(iphone_id: str, dados: dict):
    con = get_connection()
    con.execute(
        """UPDATE catalogo_iphones SET
            modelo        = :modelo,
            armazenamento = :armazenamento,
            cor           = :cor,
            bateria       = :bateria,
            disponivel    = :disponivel,
            preco_avista  = :preco_avista,
            observacoes   = :observacoes
        WHERE id = :id""",
        {**dados, "id": iphone_id}
    )
    con.commit()
    con.close()


def excluir_iphone(iphone_id: str):
    con = get_connection()
    con.execute("DELETE FROM catalogo_iphones WHERE id = ?", (iphone_id,))
    con.commit()
    con.close()


# ======================================================
# ANDROIDS
# ======================================================

def inserir_android(dados: dict):
    con = get_connection()
    con.execute(
        """INSERT INTO catalogo_androids (
            id, marca, modelo, ram, armazenamento,
            estado, preco_avista, observacoes, created_at
        ) VALUES (
            :id, :marca, :modelo, :ram, :armazenamento,
            :estado, :preco_avista, :observacoes, :created_at
        )""",
        dados
    )
    con.commit()
    con.close()


def buscar_androids():
    con = get_connection()
    rows = con.execute(
        "SELECT * FROM catalogo_androids ORDER BY marca, modelo"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def buscar_android_por_id(android_id: str):
    con = get_connection()
    row = con.execute(
        "SELECT * FROM catalogo_androids WHERE id = ?", (android_id,)
    ).fetchone()
    con.close()
    return dict(row) if row else None


def atualizar_android(android_id: str, dados: dict):
    con = get_connection()
    con.execute(
        """UPDATE catalogo_androids SET
            marca         = :marca,
            modelo        = :modelo,
            ram           = :ram,
            armazenamento = :armazenamento,
            estado        = :estado,
            preco_avista  = :preco_avista,
            observacoes   = :observacoes
        WHERE id = :id""",
        {**dados, "id": android_id}
    )
    con.commit()
    con.close()


def excluir_android(android_id: str):
    con = get_connection()
    con.execute("DELETE FROM catalogo_androids WHERE id = ?", (android_id,))
    con.commit()
    con.close()


# ======================================================
# PERFUMES
# ======================================================

def inserir_perfume(dados: dict):
    con = get_connection()
    con.execute(
        """INSERT INTO catalogo_perfumes (
            id, marca, nome, preco, observacoes, created_at
        ) VALUES (
            :id, :marca, :nome, :preco, :observacoes, :created_at
        )""",
        dados
    )
    con.commit()
    con.close()


def buscar_perfumes():
    con = get_connection()
    rows = con.execute(
        "SELECT * FROM catalogo_perfumes ORDER BY marca, nome"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def buscar_perfume_por_id(perfume_id: str):
    con = get_connection()
    row = con.execute(
        "SELECT * FROM catalogo_perfumes WHERE id = ?", (perfume_id,)
    ).fetchone()
    con.close()
    return dict(row) if row else None


def atualizar_perfume(perfume_id: str, dados: dict):
    con = get_connection()
    con.execute(
        """UPDATE catalogo_perfumes SET
            marca       = :marca,
            nome        = :nome,
            preco       = :preco,
            observacoes = :observacoes
        WHERE id = :id""",
        {**dados, "id": perfume_id}
    )
    con.commit()
    con.close()


def excluir_perfume(perfume_id: str):
    con = get_connection()
    con.execute("DELETE FROM catalogo_perfumes WHERE id = ?", (perfume_id,))
    con.commit()
    con.close()


# ======================================================
# PODS
# ======================================================

def inserir_pod(dados: dict):
    con = get_connection()
    con.execute(
        """INSERT INTO catalogo_pods (
            id, marca, nome, puffs, preco, observacoes, created_at
        ) VALUES (
            :id, :marca, :nome, :puffs, :preco, :observacoes, :created_at
        )""",
        dados
    )
    con.commit()
    con.close()


def buscar_pods():
    con = get_connection()
    rows = con.execute(
        "SELECT * FROM catalogo_pods ORDER BY marca, nome"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def buscar_pod_por_id(pod_id: str):
    con = get_connection()
    row = con.execute(
        "SELECT * FROM catalogo_pods WHERE id = ?", (pod_id,)
    ).fetchone()
    con.close()
    return dict(row) if row else None


def atualizar_pod(pod_id: str, dados: dict):
    con = get_connection()
    con.execute(
        """UPDATE catalogo_pods SET
            marca       = :marca,
            nome        = :nome,
            puffs       = :puffs,
            preco       = :preco,
            observacoes = :observacoes
        WHERE id = :id""",
        {**dados, "id": pod_id}
    )
    con.commit()
    con.close()


def excluir_pod(pod_id: str):
    con = get_connection()
    con.execute("DELETE FROM catalogo_pods WHERE id = ?", (pod_id,))
    con.commit()
    con.close()
