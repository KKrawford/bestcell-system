import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from database import (
    fetch_parcels,
    fetch_parcel_adjustments,
    fetch_all_parcel_adjustments,
    fetch_sales,
    fetch_sales_archive,    
)

DAILY_FINE = 3.90

# ================= DATAS =================

def normalize_date(value) -> date:
    """
    Normaliza qualquer entrada para datetime.date
    SEM timezone, SEM hora, SEM pandas UTC.
    """

    if value is None:
        return None

    # Já é date (caso do st.date_input)
    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    # datetime -> date
    if isinstance(value, datetime):
        return value.date()

    # pandas Timestamp
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().date()

    # string ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)
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

def add_months_safe(orig_date, months):
    return orig_date + relativedelta(months=months)

# ================= PARCELAS =================
def parcel_financial_summary(parcel_id, valor_original, vencimento):
    """
    Calcula o resumo financeiro de uma parcela.
    Juros são apenas informativos e NÃO alteram o saldo.
    """

    # ---------------- NORMALIZAR DATA ----------------
    venc = normalize_date(vencimento)
    hoje = date.today()

    # ---------------- AJUSTES ----------------
    ajustes = fetch_parcel_adjustments(parcel_id)

    pago = sum(
        a["valor"] for a in ajustes
        if a["tipo"] == "pagamento"
    )

    acrescimo = sum(
        a["valor"] for a in ajustes
        if a["tipo"] == "acrescimo"
    )

    desconto = sum(
        a["valor"] for a in ajustes
        if a["tipo"] == "desconto"
    )

    # ---------------- SALDO ----------------
    total_base = valor_original + acrescimo - desconto
    saldo = round(total_base - pago, 2)

    # ---------------- ATRASO / JUROS (INFORMATIVO) ----------------
    dias_atraso = max((hoje - venc).days, 0) if saldo > 0 else 0
    juros = round(dias_atraso * DAILY_FINE, 2)

    # ---------------- STATUS ----------------
    if saldo <= 0:
        status = "Pago"
    elif dias_atraso > 0:
        status = "Atrasado"
    else:
        status = "Em dia"

    return {
        "valor_original": round(valor_original, 2),
        "pago": round(pago, 2),
        "acrescimo": round(acrescimo, 2),
        "desconto": round(desconto, 2),
        "saldo": saldo,
        "dias_atraso": dias_atraso,
        "juros": juros,   # apenas informativo
        "status": status,
    }

def sale_is_fully_paid(sale_id: str) -> bool:
    parcels = fetch_parcels()

    for p in parcels:
        if p["sale_id"] != sale_id:
            continue

        resumo = parcel_financial_summary(
            p["id"],
            p["valor_original"],
            p["vencimento"]
        )

        if resumo["saldo"] > 0:
            return False

    return True

# ================= SAÚDE DO SISTEMA =================

def system_health_summary():
    # -------- vendas --------
    sales = fetch_sales()
    sales_archive = fetch_sales_archive()

    total_vendido = (
        sum(s["valor_total"] for s in sales) +
        sum(s["valor_total"] for s in sales_archive)
    )

    # -------- pagamentos --------
    adjustments = fetch_all_parcel_adjustments()
    total_recebido = sum(
        a["valor"] for a in adjustments if a["tipo"] == "pagamento"
    )

    # -------- parcelas --------
    parcels = fetch_parcels()
    hoje = date.today()

    saldo_aberto = 0.0
    em_atraso = 0.0
    recebivel_futuro = 0.0

    for p in parcels:
        resumo = parcel_financial_summary(
            p["id"],
            p["valor_original"],
            p["vencimento"]
        )

        saldo = resumo["saldo"]
        vencimento = normalize_date(p["vencimento"])

        if saldo > 0:
            # Exposição total atual
            saldo_aberto += saldo

            # Parte vencida
            if vencimento < hoje:
                em_atraso += saldo
            else:
                # Parte futura
                recebivel_futuro += saldo

    return {
        "total_vendido": round(total_vendido, 2),
        "total_recebido": round(total_recebido, 2),
        "saldo_aberto": round(saldo_aberto, 2),
        "em_atraso": round(em_atraso, 2),
        "recebivel_futuro": round(recebivel_futuro, 2),
    }
