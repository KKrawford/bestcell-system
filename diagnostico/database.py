import sqlite3
import json
from config import DB_PATH


# ---------------- CONNECTION ----------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- INIT ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnosticos (
            id TEXT PRIMARY KEY,
            tipo TEXT NOT NULL,                 -- software | hardware
            cliente TEXT NOT NULL,
            aparelho TEXT NOT NULL,
            status TEXT NOT NULL,               -- concluido | erro
            resumo TEXT,
            alertas_total INTEGER NOT NULL DEFAULT 0,
            resultado_json TEXT,
            laudo_path TEXT,
            erro TEXT,
            created_at TEXT NOT NULL
        );
        """
    )    

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnostico_modelos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fabricante TEXT NOT NULL,
            modelo_tecnico TEXT NOT NULL COLLATE NOCASE UNIQUE,
            modelo_comercial TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT
        );
        """
    )

    conn.commit()
    conn.close()

# ---------------- INSERT ----------------
def inserir_diagnostico(diagnostico: dict):
    conn = get_connection()
    cur = conn.cursor()

    resultado_json = diagnostico.get("resultado_json")

    if isinstance(resultado_json, (dict, list)):
        resultado_json = json.dumps(resultado_json, ensure_ascii=False)

    cur.execute(
        """
        INSERT INTO diagnosticos (
            id,
            tipo,
            cliente,
            aparelho,
            status,
            resumo,
            alertas_total,
            resultado_json,
            laudo_path,
            erro,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            diagnostico["id"],
            diagnostico["tipo"],
            diagnostico["cliente"],
            diagnostico["aparelho"],
            diagnostico["status"],
            diagnostico.get("resumo"),
            diagnostico.get("alertas_total", 0),
            resultado_json,
            diagnostico.get("laudo_path"),
            diagnostico.get("erro"),
            diagnostico["created_at"],
        )
    )

    conn.commit()
    conn.close()


# ---------------- FETCH ----------------
def buscar_diagnosticos():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM diagnosticos
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    diagnosticos = []

    for row in rows:
        item = dict(row)

        if item.get("resultado_json"):
            try:
                item["resultado_json"] = json.loads(item["resultado_json"])
            except Exception:
                item["resultado_json"] = {}

        diagnosticos.append(item)

    return diagnosticos


def buscar_diagnostico_por_id(diagnostico_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM diagnosticos
        WHERE id = ?
        """,
        (diagnostico_id,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    item = dict(row)

    if item.get("resultado_json"):
        try:
            item["resultado_json"] = json.loads(item["resultado_json"])
        except Exception:
            item["resultado_json"] = {}

    return item


# ---------------- DELETE ----------------
def excluir_diagnostico(diagnostico_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM diagnosticos
        WHERE id = ?
        """,
        (diagnostico_id,)
    )

    conn.commit()
    conn.close()

# ======================================================
# MODELOS DE APARELHOS
# ======================================================

def buscar_modelo_por_codigo(modelo_tecnico: str):
    modelo_tecnico = (modelo_tecnico or "").strip()

    if not modelo_tecnico:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM diagnostico_modelos
        WHERE modelo_tecnico = ? COLLATE NOCASE
        """,
        (modelo_tecnico,)
    )

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


def cadastrar_modelo_aparelho(
    fabricante: str,
    modelo_tecnico: str,
    modelo_comercial: str
):
    fabricante = (fabricante or "").strip() or "Não identificado"
    modelo_tecnico = (modelo_tecnico or "").strip()
    modelo_comercial = (modelo_comercial or "").strip()

    if not modelo_tecnico:
        raise ValueError("O modelo técnico não foi informado.")

    if not modelo_comercial:
        raise ValueError("O modelo comercial não foi informado.")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO diagnostico_modelos (
            fabricante,
            modelo_tecnico,
            modelo_comercial
        )
        VALUES (?, ?, ?)
        """,
        (
            fabricante,
            modelo_tecnico,
            modelo_comercial,
        )
    )

    modelo_id = cur.lastrowid

    conn.commit()
    conn.close()

    return modelo_id


def listar_modelos_aparelhos():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM diagnostico_modelos
        ORDER BY fabricante, modelo_comercial
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def atualizar_modelo_aparelho(
    modelo_id: int,
    fabricante: str,
    modelo_tecnico: str,
    modelo_comercial: str
):
    fabricante = (fabricante or "").strip() or "Não identificado"
    modelo_tecnico = (modelo_tecnico or "").strip()
    modelo_comercial = (modelo_comercial or "").strip()

    if not modelo_tecnico:
        raise ValueError("O modelo técnico não foi informado.")

    if not modelo_comercial:
        raise ValueError("O modelo comercial não foi informado.")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE diagnostico_modelos
        SET
            fabricante = ?,
            modelo_tecnico = ?,
            modelo_comercial = ?,
            updated_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        (
            fabricante,
            modelo_tecnico,
            modelo_comercial,
            modelo_id,
        )
    )

    conn.commit()
    conn.close()


def excluir_modelo_aparelho(modelo_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM diagnostico_modelos
        WHERE id = ?
        """,
        (modelo_id,)
    )

    conn.commit()
    conn.close()
    