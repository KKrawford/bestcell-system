import sqlite3
from pathlib import Path
from datetime import datetime
import os

# =============================
# DATABASE PATH (VPS)
# =============================

BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = BASE_DIR / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

DB_PATH = RUNTIME_DIR / "bestsystem.db"

# =============================
# CONNECTION
# =============================

def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,                 # ⏱️ espera escrita
        check_same_thread=False     # VPS / Streamlit safe
    )
    conn.row_factory = sqlite3.Row

    # 🔒 PRAGMAS DE PRODUÇÃO
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")

    return conn

# ---------------- INIT ----------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ---- SALES (ATIVAS) ----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id TEXT PRIMARY KEY,
            cliente TEXT NOT NULL,
            aparelho TEXT NOT NULL,            
            valor_entrada REAL NOT NULL,
            tipo_venda TEXT NOT NULL,
            valor_total REAL NOT NULL,
            data_venda TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    # ---- PARCELS ----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parcels (
        id TEXT PRIMARY KEY,
        sale_id TEXT NOT NULL,
        parcela_num INTEGER NOT NULL,
        valor_original REAL NOT NULL,
        vencimento TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE
        );
        """
    )

    # ---- PARCEL ADJUSTMENTS ----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS parcel_adjustments (
            id TEXT PRIMARY KEY,
            parcel_id TEXT NOT NULL,
            tipo TEXT NOT NULL,             -- pagamento | acrescimo | desconto
            valor REAL NOT NULL,
            descricao TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (parcel_id) REFERENCES parcels(id) ON DELETE CASCADE
        );
        """
    )

    # ---- SALES ARCHIVE ----
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_archive (
            id TEXT PRIMARY KEY,
            cliente TEXT NOT NULL,
            aparelho TEXT NOT NULL,            
            valor_entrada REAL NOT NULL,
            tipo_venda TEXT NOT NULL,
            valor_total REAL NOT NULL,
            data_venda TEXT NOT NULL,
            created_at TEXT NOT NULL,
            archived_at TEXT NOT NULL
        );
        """
    )

    # ---- SALES CLOSED ----
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS sales_closed (
            id TEXT PRIMARY KEY,
            cliente TEXT NOT NULL,
            aparelho TEXT NOT NULL,

            valor_total REAL NOT NULL,
            valor_recebido REAL NOT NULL,
            valor_perdido REAL NOT NULL,
            valor_recuperado REAL NOT NULL DEFAULT 0,

            data_venda TEXT NOT NULL,
            created_at TEXT NOT NULL,
            closed_at TEXT NOT NULL,

            motivo TEXT NOT NULL
        );
        """
    )

    ensure_sales_closed_columns(cur)
    
    conn.commit()
    conn.close()

# ---------------- MIGRATIONS ----------------
def ensure_sales_closed_columns(cur):
    cur.execute("PRAGMA table_info(sales_closed)")
    columns = [row["name"] for row in cur.fetchall()]

    if "valor_recuperado" not in columns:
        cur.execute("""
            ALTER TABLE sales_closed
            ADD COLUMN valor_recuperado REAL DEFAULT 0
        """)

# ---------------- INSERTS ----------------
def insert_sale(sale: dict):
    conn = get_connection()
    cur = conn.cursor()

    # 🔒 Garantia absoluta de string (sem timezone, sem hora)
    data_venda = str(sale["data_venda"])[:10]
    created_at = str(sale["created_at"])

    cur.execute(
        """
        INSERT INTO sales (
            id,
            cliente,
            aparelho,
            valor_entrada,
            tipo_venda,
            valor_total,
            data_venda,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sale["id"],
            sale["cliente"],
            sale["aparelho"],
            sale["valor_entrada"],
            sale["tipo_venda"],
            sale["valor_total"],
            data_venda,   # 🔹 STRING YYYY-MM-DD
            created_at,
        )
    )

    conn.commit()
    conn.close()

def insert_parcels(parcels: list[dict]):
    conn = get_connection()
    cur = conn.cursor()

    cur.executemany("""
        INSERT INTO parcels (
            id,
            sale_id,
            parcela_num,
            valor_original,
            vencimento,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (
            p["id"],
            p["sale_id"],
            p["parcela_num"],
            p["valor_original"],
            p["vencimento"],
            p["created_at"],
        )
        for p in parcels
    ])

    conn.commit()
    conn.close()


def add_parcel_adjustment(adjustment: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO parcel_adjustments (
            id, parcel_id, tipo, valor, descricao, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            adjustment["id"],
            adjustment["parcel_id"],
            adjustment["tipo"],
            adjustment["valor"],
            adjustment["descricao"],
            adjustment["created_at"],
        )
    )

    conn.commit()
    conn.close()

# ---------------- FETCH ----------------
def fetch_sales():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales ORDER BY data_venda DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_parcels():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.id,
            p.sale_id,
            p.parcela_num,
            p.valor_original,
            p.vencimento,
            p.created_at,
            s.cliente,
            s.aparelho
        FROM parcels p
        JOIN sales s ON s.id = p.sale_id
        ORDER BY p.vencimento, p.parcela_num
    """)

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_parcel_adjustments(parcel_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            parcel_id,
            tipo,
            valor,
            descricao,
            created_at
        FROM parcel_adjustments
        WHERE parcel_id = ?
        ORDER BY created_at ASC
        """,
        (parcel_id,)
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_all_parcel_adjustments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id,
            parcel_id,
            tipo,
            valor,
            descricao,
            created_at
        FROM parcel_adjustments
        ORDER BY created_at ASC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_sales_archive():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales_archive")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def fetch_closed_sales():
    """
    Retorna vendas encerradas (inadimplência, acordo, devolução, etc)
    diretamente da tabela sales_closed.
    """

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            cliente,
            aparelho,
            valor_total,
            valor_recebido,
            valor_perdido,
            valor_recuperado,
            data_venda,
            closed_at,
            motivo
        FROM sales_closed
        ORDER BY closed_at DESC
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ---------------- ARCHIVE ----------------
def archive_sale(sale_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
    sale = cur.fetchone()
    if not sale:
        conn.close()
        return

    cur.execute(
        """
        INSERT INTO sales_archive (
            id, cliente, aparelho, valor_entrada,
            tipo_venda, valor_total, data_venda, created_at, archived_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sale["id"],
            sale["cliente"],
            sale["aparelho"],            
            sale["valor_entrada"],
            sale["tipo_venda"],
            sale["valor_total"],
            sale["data_venda"],
            sale["created_at"],
            datetime.utcnow().isoformat(),
        )
    )

    cur.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
    conn.commit()
    conn.close()

# ---------------- DELETE ----------------
def delete_sale(sale_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
    conn.commit()
    conn.close()

# ---------------- DELETE ----------------
def delete_parcel_adjustments(sale_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM parcel_adjustments
        WHERE parcel_id IN (
            SELECT id FROM parcels WHERE sale_id = ?
        )
        """,
        (sale_id,)
    )

    conn.commit()
    conn.close()

#---------------- CLOSE SALE CRITICAL ----------------
def close_sale_critical(sale_id: str, motivo: str):
    conn = get_connection()
    cur = conn.cursor()

    # ---------------- VENDA ----------------
    cur.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
    sale = cur.fetchone()

    if not sale:
        conn.close()
        raise ValueError("Venda não encontrada ou já encerrada.")

    # ---------------- PARCELAS ----------------
    cur.execute(
        "SELECT id, valor_original FROM parcels WHERE sale_id = ?",
        (sale_id,)
    )
    parcels = cur.fetchall()

    parcel_ids = [p["id"] for p in parcels]

    # ---------------- PAGAMENTOS ----------------
    if parcel_ids:
        placeholders = ",".join("?" for _ in parcel_ids)
        cur.execute(
            f"""
            SELECT SUM(valor) as total_pago
            FROM parcel_adjustments
            WHERE tipo = 'pagamento'
              AND parcel_id IN ({placeholders})
            """,
            parcel_ids
        )
        total_pago = cur.fetchone()["total_pago"] or 0.0
    else:
        total_pago = 0.0

    # ---------------- VALORES ----------------
    valor_total = sale["valor_total"]
    valor_recebido = round(total_pago, 2)
    valor_perdido = round(valor_total - valor_recebido, 2)

    # ---------------- INSERIR EM SALES_CLOSED ----------------
    cur.execute(
        """
        INSERT INTO sales_closed (
            id, cliente, aparelho,
            valor_total, valor_recebido, valor_perdido,
            data_venda, created_at, closed_at, motivo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sale["id"],
            sale["cliente"],
            sale["aparelho"],
            valor_total,
            valor_recebido,
            valor_perdido,
            sale["data_venda"],
            sale["created_at"],
            datetime.utcnow().isoformat(),
            motivo,
        )
    )

    # ---------------- LIMPEZA OPERACIONAL ----------------
    cur.execute(
        "DELETE FROM parcel_adjustments WHERE parcel_id IN (SELECT id FROM parcels WHERE sale_id = ?)",
        (sale_id,)
    )
    cur.execute("DELETE FROM parcels WHERE sale_id = ?", (sale_id,))
    cur.execute("DELETE FROM sales WHERE id = ?", (sale_id,))

    conn.commit()
    conn.close()

# ---------------- UPDATE CLOSED SALE RECOVERY ----------------
def update_closed_sale_recovery(sale_id, valor):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE sales_closed
        SET valor_recuperado = valor_recuperado + ?
        WHERE id = ?
        """,
        (valor, sale_id)
    )
    
    conn.commit()
    conn.close()

#--- development utility function ---
def delete_closed_sale(cliente):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM sales_closed WHERE cliente = ?",
        (cliente,)
    )

    conn.commit()
    conn.close()
