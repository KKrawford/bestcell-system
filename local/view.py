import pandas as pd
from datetime import timedelta
from datetime import date, datetime

# ======================================================
# FORMATAÇÃO DE MOEDA (EXCLUSIVO DA CAMADA DE VIEW)
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

        # ⚠️ Se NÃO houver horário explícito, é data pura → NÃO ajusta timezone
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
    
def format_mes_ano(value):
    if not value:
        return ""
    try:
        dt = pd.to_datetime(value + "-01")
        return dt.strftime("%m/%Y")
    except Exception:
        return value

def fmt_today_label(value=None):
    """
    Retorna HTML formatado para exibição da data atual ou fornecida
    """
    if value is None:
        value = date.today()

    if isinstance(value, pd.Timestamp):
        value = value.date()
    elif isinstance(value, datetime):
        value = value.date()

    return f"""
    <div style="text-align: right; padding-top: 20px; font-size: 40px;">
        <strong>{value.strftime('%d/%m/%Y')}</strong>
    </div>
    """

# ======================================================
# VENDAS — VIEW
# ======================================================
def sales_view(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["Data da Venda"] = df["data_venda"].apply(fmt_date)
    df["Registrado em"] = df["created_at"].apply(lambda x: fmt_date(x, True))

    df["Valor Total"] = df["valor_total"].map(currency)
    df["Entrada"] = df["valor_entrada"].fillna(0).map(currency)

    return df[
        [
            "cliente",
            "aparelho",
            "tipo_venda",
            "Valor Total",
            "Entrada",
            "Data da Venda",
            "Registrado em"
        ]
    ].rename(columns={
        "cliente": "Cliente",
        "aparelho": "Aparelho",
        "tipo_venda": "Tipo de Venda"
    })


# ======================================================
# PARCELAS — VIEW
# ======================================================
def parcels_view(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "Vencimento" in df.columns:
        df["Vencimento"] = df["Vencimento"].apply(fmt_date)

    for col in ["Valor Original","Acréscimos","Descontos","Pago","Saldo","Juros (info)"]:

        if col in df.columns:
            df[col] = df[col].map(currency)

    return df


# ======================================================
# AJUSTES DE PARCELAS — VIEW
# ======================================================
def adjustments_view(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["Data"] = df["created_at"].apply(fmt_date)
    df["Valor"] = df["valor"].map(currency)

    return df.rename(columns={
        "tipo": "Tipo",
        "descricao": "Descrição"
    })[["Tipo", "Valor", "Descrição", "Data"]]

# ======================================================
# RELATÓRIOS (VIEW)
# ======================================================
def reports_view(df):
    df = df.copy()

    if "Mês/Ano" in df.columns:
        df["Mês/Ano"] = df["Mês/Ano"].apply(format_mes_ano)

    for col in ["Valor Vendido", "Valor Recebido", "Saldo em Aberto", "Em Atraso"]:
        if col in df.columns:
            df[col] = df[col].apply(currency)

    return df

# ======================================================
# STATUS — STYLE (VIEW)
# ======================================================
def status_style(val):
    if val == "Pago":
        return "color: #2e7d32; font-weight: bold;"      # verde
    elif val == "Atrasado":
        return "color: #c62828; font-weight: bold;"      # vermelho
    elif val == "Em dia":
        return "color: #f9a825; font-weight: bold;"      # amarelo
    return ""

# ======================================================
# INFO BOX — VIEW (HTML CONTROLADO)
# ======================================================
def info_box(title: str, lines: list[str]) -> str:
    """
    Retorna um bloco HTML padronizado para exibição
    de informações resumidas (financeiro, alertas, etc).

    • Não executa Streamlit
    • Não acessa banco
    • Não contém regra de negócio
    """

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
