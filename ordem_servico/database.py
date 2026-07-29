import sqlite3
from config import DB_PATH
from datetime import datetime
import uuid

# ---------------- CONNECTION ----------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ---------------- INIT DATABASE ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Tabela principal da Ordem de Serviço
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS service_orders (
            id TEXT PRIMARY KEY,

            numero_os TEXT NOT NULL,

            nome TEXT NOT NULL,
            fone TEXT,
            email TEXT,

            aparelho TEXT NOT NULL,

            detalhes_servico TEXT,
            servico_realizado TEXT,

            senha_tipo TEXT,
            senha_padrao TEXT,
            senha_tela TEXT,

            valor_estimado REAL,

            status TEXT NOT NULL,

            data_entrada TEXT NOT NULL,

            started_at TEXT,
            finished_at TEXT,
            delivered_at TEXT,

            observacoes TEXT,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    # Tabela para OS arquivadas
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS os_arquivadas (
            id TEXT PRIMARY KEY,
            numero_os TEXT NOT NULL,
            nome TEXT NOT NULL,
            fone TEXT,
            email TEXT,
            aparelho TEXT NOT NULL,
            detalhes_servico TEXT,
            servico_realizado TEXT,
            senha_tipo TEXT,
            senha_padrao TEXT,
            senha_tela TEXT,
            valor_estimado REAL,
            status TEXT NOT NULL,
            data_entrada TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            delivered_at TEXT,
            observacoes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            arquivada_em TEXT NOT NULL
        );
        """
    )

    # Histórico de movimentação de status
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_status_history (
            id TEXT PRIMARY KEY,

            order_id TEXT NOT NULL,

            from_status TEXT,
            to_status TEXT NOT NULL,

            note TEXT,

            changed_at TEXT NOT NULL,

            FOREIGN KEY (order_id)
            REFERENCES service_orders(id)
            ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()

# ---------------- GERAR NÚMERO OS ----------------
def generate_os_number():
    """Gera número OS sequencial: OS-0001, OS-0002, etc."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM service_orders")
    resultado = cur.fetchone()
    total_existente = resultado["total"] if resultado else 0
    
    conn.close()
    
    next_number = total_existente + 1
    return f"OS-{next_number:04d}"

# ---------------- INSERT ----------------
def insert_order(order: dict):
    conn = get_connection()
    cur = conn.cursor()

    # Garantir que data_entrada seja sempre a data de criação
    now = datetime.utcnow().isoformat()
    if not order.get("data_entrada"):
        order["data_entrada"] = now

    cur.execute(
        """
        INSERT INTO service_orders (
            id,
            numero_os,
            nome,
            fone,
            email,
            aparelho,
            detalhes_servico,
            servico_realizado,
            senha_tipo,
            senha_padrao,
            senha_tela,
            valor_estimado,
            status,
            data_entrada,            
            started_at,
            finished_at,
            delivered_at,
            observacoes,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order["id"],
            order["numero_os"],
            order["nome"],
            order["fone"],
            order["email"],
            order["aparelho"],
            order["detalhes_servico"],
            order.get("servico_realizado"),
            order.get("senha_tipo"),
            order.get("senha_padrao"),
            order.get("senha_tela"),
            order.get("valor_estimado"),
            order["status"],
            order["data_entrada"],            
            order.get("started_at"),
            order.get("finished_at"),
            order.get("delivered_at"),
            order.get("observacoes"),
            now,
            now
        ),
    )

    conn.commit()
    conn.close()

# ---------------- ARQUIVAR OS ----------------
def arquivar_os(order_id: str, motivo: str = "Concluída"):
    """
    Move uma OS para a tabela de arquivadas e remove da tabela ativa
    """
    conn = get_connection()
    cur = conn.cursor()

    # Buscar OS completa
    cur.execute("SELECT * FROM service_orders WHERE id = ?", (order_id,))
    order = cur.fetchone()
    
    if not order:
        conn.close()
        return False

    # Inserir na tabela de arquivadas
    cur.execute(
        """
        INSERT INTO os_arquivadas (
            id, numero_os, nome, fone, email, aparelho,
            detalhes_servico, servico_realizado,
            senha_tipo, senha_padrao, senha_tela,
            valor_estimado, status,
            data_entrada, started_at, finished_at,
            delivered_at, observacoes, created_at, updated_at,
            arquivada_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order["id"],
            order["numero_os"],
            order["nome"],
            order["fone"],
            order["email"],
            order["aparelho"],
            order["detalhes_servico"],
            order["servico_realizado"],
            order["senha_tipo"],
            order["senha_padrao"],
            order["senha_tela"],
            order["valor_estimado"],
            motivo,
            order["data_entrada"],
            order["started_at"],
            order["finished_at"],
            order["delivered_at"],
            order["observacoes"],
            order["created_at"],
            order["updated_at"],
            datetime.utcnow().isoformat()
        )
    )

    # Remover da tabela ativa (e histórico por cascade)
    cur.execute("DELETE FROM service_orders WHERE id = ?", (order_id,))

    conn.commit()
    conn.close()
    return True

# ---------------- UPDATE STATUS ----------------
def update_order_status(order_id: str, new_status: str, note: str | None = None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT status, started_at, finished_at, delivered_at FROM service_orders WHERE id = ?",
        (order_id,),
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return

    previous_status = row["status"]
    now = datetime.utcnow().isoformat()

    started_at = row["started_at"]
    finished_at = row["finished_at"]
    delivered_at = row["delivered_at"]

    if new_status == "Em reparo" and not started_at:
        started_at = now

    if new_status == "Pronto" and not finished_at:
        finished_at = now

    if new_status == "Entregue" and not delivered_at:
        delivered_at = now

    cur.execute(
        """
        UPDATE service_orders
        SET status = ?,
            started_at = ?,
            finished_at = ?,
            delivered_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            new_status,
            started_at,
            finished_at,
            delivered_at,
            now,
            order_id,
        ),
    )

    # Histórico
    if previous_status != new_status:
        cur.execute(
            """
            INSERT INTO order_status_history (
                id,
                order_id,
                from_status,
                to_status,
                note,
                changed_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                order_id,
                previous_status,
                new_status,
                note,
                now,
            ),
        )

    conn.commit()
    conn.close()

# ---------------- UPDATE GENERIC FIELDS ----------------
def update_order_fields(order_id: str, fields: dict):
    if not fields:
        return

    allowed = {
        "nome",
        "fone",
        "email",
        "aparelho",
        "detalhes_servico",
        "servico_realizado",
        "senha_tipo",
        "senha_padrao",
        "senha_tela",
        "valor_estimado",
        "observacoes",
        "status",
    }

    updates = []
    values = []

    for key, value in fields.items():
        if key in allowed:
            updates.append(f"{key} = ?")
            values.append(value)

    if not updates:
        return

    updates.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(order_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        f"""
        UPDATE service_orders
        SET {', '.join(updates)}
        WHERE id = ?
        """,
        tuple(values),
    )

    conn.commit()
    conn.close()

# ---------------- FETCH ALL ----------------
def fetch_orders():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM service_orders
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]

# ---------------- FETCH BY STATUS (KANBAN) ----------------
def fetch_orders_by_status(status: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM service_orders
        WHERE status = ?
        ORDER BY created_at ASC
        """,
        (status,),
    )

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]

# ---------------- FETCH BY ID ----------------
def fetch_order_by_id(order_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM service_orders
        WHERE id = ?
        """,
        (order_id,),
    )

    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None

# ---------------- FETCH STATUS HISTORY ----------------
def fetch_order_status_history(order_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM order_status_history
        WHERE order_id = ?
        ORDER BY changed_at DESC
        """,
        (order_id,),
    )

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]

# ---------------- FETCH OS ARQUIVADAS ----------------
def fetch_os_arquivadas(filtro_cliente: str = None, filtro_aparelho: str = None):
    conn = get_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM os_arquivadas WHERE 1=1"
    params = []
    
    if filtro_cliente:
        query += " AND nome LIKE ?"
        params.append(f"%{filtro_cliente}%")
    
    if filtro_aparelho:
        query += " AND aparelho LIKE ?"
        params.append(f"%{filtro_aparelho}%")
    
    query += " ORDER BY arquivada_em DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]

# ---------------- BUSCA COMPLETA (ativas + arquivadas) ----------------
def busca_completa_os(query: str = None):
    """
    Busca em ambas as tabelas: ativas e arquivadas
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Buscar ativas
    ativas_query = """
        SELECT *, 'ativa' as tipo, status as status 
        FROM service_orders WHERE 1=1
    """
    arquivadas_query = """
        SELECT *, 'arquivada' as tipo, status_final as status 
        FROM os_arquivadas WHERE 1=1
    """
    params = []
    
    if query:
        ativas_query += " AND (nome LIKE ? OR aparelho LIKE ? OR numero_os LIKE ?)"
        arquivadas_query += " AND (nome LIKE ? OR aparelho LIKE ? OR numero_os LIKE ?)"
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
    
    # Executar ambas as queries
    cur.execute(ativas_query, params)
    ativas = [dict(row) for row in cur.fetchall()]
    
    cur.execute(arquivadas_query, params)
    arquivadas = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return ativas + arquivadas

# ---------------- DELETE ----------------
def delete_order(order_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM service_orders WHERE id = ?",
        (order_id,),
    )

    conn.commit()
    conn.close()

# ----------------- DELETE OS ARQUIVADA ----------------
def excluir_os_arquivada(order_id: str):
    """Exclui permanentemente uma OS arquivada"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        "DELETE FROM os_arquivadas WHERE id = ?",
        (order_id,)
    )
    
    conn.commit()
    conn.close()
    return True

# ---------------- ESTATÍSTICAS ----------------
def get_os_stats():
    """Retorna estatísticas rápidas para dashboard"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Contagem por status
    cur.execute(
        "SELECT status, COUNT(*) as count FROM service_orders GROUP BY status"
    )
    status_counts = {row["status"]: row["count"] for row in cur.fetchall()}
    
    # OS em andamento (não finalizadas)
    em_andamento = sum(
        count for status, count in status_counts.items() 
        if status not in ["Pronto", "Entregue", "Cancelado"]
    )
    
    # OS prontas para entrega
    prontas = status_counts.get("Pronto", 0)
    
    conn.close()
    
    return {
        "status_counts": status_counts,
        "em_andamento": em_andamento,
        "prontas": prontas,
        "total": sum(status_counts.values()),
    }

    # ---------------- ESTATÍSTICAS FINANCEIRAS POR PERÍODO ----------------
def get_os_financeiras_por_periodo(data_inicio: str = None, data_fim: str = None):
    """
    Retorna estatísticas financeiras das OSs entregues no período
    """
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            COUNT(*) as total_os,
            COALESCE(SUM(valor_estimado), 0) as valor_total
        FROM service_orders 
        WHERE status = 'Entregue'
    """
    params = []
    
    if data_inicio and data_fim:
        query += " AND date(delivered_at) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    elif data_inicio:
        query += " AND date(delivered_at) >= ?"
        params.append(data_inicio)
    elif data_fim:
        query += " AND date(delivered_at) <= ?"
        params.append(data_fim)
    
    cur.execute(query, params)
    result = cur.fetchone()
    
    conn.close()
    
    return {
        "total_os": result["total_os"] if result else 0,
        "valor_total": result["valor_total"] if result else 0.0
    }

def get_os_entregues_por_periodo(data_inicio: str = None, data_fim: str = None):
    """
    Retorna as OSs entregues no período para detalhamento
    """
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            numero_os,
            nome,
            aparelho,
            valor_estimado,
            delivered_at
        FROM service_orders 
        WHERE status = 'Entregue'
    """
    params = []
    
    if data_inicio and data_fim:
        query += " AND date(delivered_at) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    elif data_inicio:
        query += " AND date(delivered_at) >= ?"
        params.append(data_inicio)
    elif data_fim:
        query += " AND date(delivered_at) <= ?"
        params.append(data_fim)
    
    query += " ORDER BY delivered_at DESC"
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    conn.close()
    
    return [dict(row) for row in results]

def get_os_por_status_periodo(data_inicio: str = None, data_fim: str = None):
    """
    Retorna contagem de OSs por status no período
    """
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
        SELECT 
            status,
            COUNT(*) as quantidade
        FROM service_orders 
        WHERE 1=1
    """
    params = []
    
    if data_inicio and data_fim:
        query += " AND date(created_at) BETWEEN ? AND ?"
        params.extend([data_inicio, data_fim])
    elif data_inicio:
        query += " AND date(created_at) >= ?"
        params.append(data_inicio)
    elif data_fim:
        query += " AND date(created_at) <= ?"
        params.append(data_fim)
    
    query += " GROUP BY status ORDER BY quantidade DESC"
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    conn.close()
    
    return {row["status"]: row["quantidade"] for row in results}

