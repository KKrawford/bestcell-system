import pandas as pd
from datetime import timedelta
from datetime import date, datetime

# ======================================================
# FORMATAÇÃO DE MOEDA
# ======================================================
def currency(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return v

# ======================================================
# FORMATAÇÃO DE DATAS (UTC → LOCAL)
# ======================================================
def fmt_date(value, with_time=False):
    if not value:
        return ""

    try:
        dt = pd.to_datetime(value, format="mixed")

        # Se não houver horário explícito, é data pura
        if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and not with_time:
            return dt.strftime("%d/%m/%Y")

        # Caso tenha horário, converte UTC → Brasília
        dt_local = dt - timedelta(hours=3)

        return (
            dt_local.strftime("%d/%m/%Y %H:%M")
            if with_time
            else dt_local.strftime("%d/%m/%Y")
        )

    except Exception:
        return str(value)

# ======================================================
# FORMATAÇÃO DE DATA CURTA (DD/MM)
# ======================================================
def fmt_date_short(value):
    """Formata data no formato DD/MM"""
    if not value:
        return ""
    try:
        dt = pd.to_datetime(value, format="mixed")
        return dt.strftime("%d/%m")
    except Exception:
        return str(value)

# ======================================================
# INFO BOX
# ======================================================
def info_box(title: str, lines: list[str]) -> str:
    html_lines = "<br>".join(f"• {line}" for line in lines)

    return f"""
    <div style="
        background-color: #0e2a47;
        padding: 14px 18px;
        border-radius: 8px;
        color: #ffffff;
        font-size: 15px;
        line-height: 1.6;
    ">
        <strong>{title}</strong><br><br>
        {html_lines}
    </div>
    """
