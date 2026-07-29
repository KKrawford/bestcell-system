from datetime import date, datetime
import uuid
import pandas as pd
from fpdf import FPDF
from pathlib import Path

# =========================================================
# DATAS
# =========================================================

def normalize_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().date()
    if isinstance(value, str):
        return datetime.fromisoformat(value[:10]).date()
    raise TypeError(f"Tipo inválido para data: {type(value)}")

def normalize_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Tipo inválido para data: {type(value)}")

# =========================================================
# STATUS (KANBAN)
# =========================================================

def status_list_kanban():
    """Status que aparecem no kanban (apenas ativos)"""
    return [
        "Recebido",
        "Em análise",
        "Em reparo", 
        "Pronto"
    ]

def status_list_completa():
    """Todos os status incluindo os finais"""
    return [
        "Recebido",
        "Em análise",
        "Em reparo",
        "Pronto",
        "Entregue",
        "Cancelado"
    ]

def status_list():
    """Função original mantida para compatibilidade"""
    return status_list_completa()

def is_finished(status: str) -> bool:
    return status in {"Entregue", "Cancelado"}

def is_overdue(data_prevista, status):
    if is_finished(status):
        return False
    if not data_prevista:
        return False
    prev = normalize_date(data_prevista)
    return prev < date.today()

# =========================================================
# WIDGET KEYS
# =========================================================

def widget_key(field, order_id):
    return f"os_{field}_{order_id}"

# =========================================================
# BUILDER DA ORDEM DE SERVIÇO
# =========================================================

def build_new_order(
    numero_os: str,
    nome: str,
    fone: str,
    email: str | None,
    aparelho: str,
    detalhes_servico: str,
    valor_estimado: float | None = None,    
    senha_tipo: str | None = None,
    senha_padrao: str | None = None,
    senha_tela: str | None = None,
    observacoes: str | None = None,
) -> dict:
    now = datetime.utcnow().isoformat()

    # Garantir que apenas o tipo correto de senha seja salvo
    if senha_tipo != "Padrão 3x3":
        senha_padrao = None
    if senha_tipo != "Alfanumérica":
        senha_tela = None
    
    return {
        "id": str(uuid.uuid4()),
        "numero_os": numero_os,
        "nome": nome,
        "fone": fone,
        "email": email,
        "aparelho": aparelho,
        "detalhes_servico": detalhes_servico,
        "servico_realizado": None,
        "senha_tipo": senha_tipo,
        "senha_padrao": senha_padrao,
        "senha_tela": senha_tela,
        "valor_estimado": valor_estimado,
        "status": "Recebido",
        "data_entrada": now,
        "started_at": None,
        "finished_at": None,
        "delivered_at": None,
        "observacoes": observacoes,
        "created_at": now,
        "updated_at": now,
    }

# =========================================================
# WHATSAPP
# =========================================================

def build_whatsapp_message(order: dict) -> str:
    return (
        "*Ordem de Serviço - Bestcell*\n\n"
        f"OS: {order['numero_os']}\n"
        f"Cliente: {order['nome']}\n"
        f"Telefone: {order['fone'] or '-'}\n"
        f"Email: {order['email'] or '-'}\n"
        f"Aparelho: {order['aparelho']}\n\n"
        f"Problema relatado:\n{order['detalhes_servico']}\n\n"
        f"Serviço realizado:\n{order.get('servico_realizado') or '-'}\n\n"
        f"Valor estimado: R$ {order.get('valor_estimado') or 0:.2f}\n"
        f"Status: {order['status']}\n"
    )

# =========================================================
# PDF DA ORDEM DE SERVIÇO
# =========================================================

def build_pdf_bytes(order: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Tentar encontrar logo
    base_dir = Path(__file__).resolve().parent.parent
    logo_candidates = [
        base_dir / "assets" / "logo.png",
        base_dir / "assets" / "logo.jpg",
        base_dir / "assets" / "logo.jpeg",
    ]

    for logo_path in logo_candidates:
        if logo_path.exists():
            try:
                pdf.image(str(logo_path), x=10, y=10, w=40)
                break
            except:
                pass

    pdf.set_xy(55, 10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 7, "Bestcell - Ordem de Serviço", ln=True)

    pdf.set_x(55)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "WhatsApp: (14) 99639-4412", ln=True)
    pdf.set_x(55)
    pdf.cell(0, 6, "Rua Duque de Caxias, 135 - Centro", ln=True)
    pdf.set_x(55)
    pdf.cell(0, 6, "Ourinhos - SP", ln=True)

    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, f"OS: {order['numero_os']}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    
    lines = [
        f"Cliente: {order['nome']}",
        f"Telefone: {order['fone'] or '-'}",
        f"Email: {order['email'] or '-'}",
        f"Aparelho: {order['aparelho']}",
        f"Data de entrada: {order['data_entrada'][:10]}",
        f"Status: {order['status']}",
        "",
        f"Problema relatado:",
        f"{order['detalhes_servico']}",
        "",
        f"Serviço realizado:",
        f"{order.get('servico_realizado') or 'Aguardando'}",
        "",
        f"Valor estimado: R$ {order.get('valor_estimado') or 0:.2f}",
    ]
    
    for line in lines:
        if line:
            pdf.multi_cell(0, 7, line)
        else:
            pdf.ln(5)

    return pdf.output(dest="S").encode("latin1")

# =========================================================
# SENHA / PATTERN LOCK
# =========================================================

def format_senha(order: dict) -> str:
    senha_tipo = order.get("senha_tipo")
    if senha_tipo == "Padrão 3x3":
        padrao = order.get("senha_padrao") or "-"
        return f"Padrão 3x3: {padrao}"
    if senha_tipo == "Numérica":
        return order.get("senha_tela") or "-"
    if senha_tipo == "Sem senha":
        return "-"
    return order.get("senha_tela") or "-"

def render_pattern_grid(seq: str, empty_char: str = "•") -> str:
    digits = []
    for part in (seq or "").replace(",", "-").split("-"):
        part = part.strip()
        if part.isdigit() and part not in digits:
            digits.append(part)
    
    grid = []
    for i in range(1, 10):
        if str(i) in digits:
            grid.append(str(i))
        else:
            grid.append(empty_char)
    
    return (
        f"{grid[0]} {grid[1]} {grid[2]}\n"
        f"{grid[3]} {grid[4]} {grid[5]}\n"
        f"{grid[6]} {grid[7]} {grid[8]}"
    )

# =========================================================
# CONTADOR DE DIAS NA LOJA
# =========================================================    

def dias_na_loja(data_entrada) -> int:
    if not data_entrada:
        return 0
    
    # Converter para datetime se for string
    if isinstance(data_entrada, str):
        try:
            entrada = datetime.fromisoformat(data_entrada)
        except ValueError:
            # Formato alternativo para compatibilidade
            entrada = datetime.strptime(data_entrada[:10], "%Y-%m-%d")
    else:
        entrada = data_entrada
    
    # Garantir que é um objeto de data
    if isinstance(entrada, datetime):
        entrada = entrada.date()
    
    return (date.today() - entrada).days
