from datetime import date


# ======================================================
# SIMULADOR DE VENDAS
# ======================================================

def calcular_parcelas(valor_avista: float, juros: float, entrada: float, num_parcelas: int) -> dict:
    """
    Fórmula: (valor_avista × (1 + juros/100) - entrada) / num_parcelas
    """
    valor_com_juros  = valor_avista * (1 + juros / 100)
    valor_financiado = valor_com_juros - entrada
    valor_parcela    = valor_financiado / num_parcelas if num_parcelas > 0 else 0
    total_pago       = entrada + (valor_parcela * num_parcelas)

    return {
        "valor_com_juros":  round(valor_com_juros,  2),
        "valor_financiado": round(valor_financiado, 2),
        "valor_parcela":    round(valor_parcela,    2),
        "total_pago":       round(total_pago,       2),
    }


# ======================================================
# CALCULADORA DE JUROS
# ======================================================

TAXA_DIARIA = 3.90


def calcular_juros_atraso(data_inicio: date, data_fim: date) -> dict:
    """
    Taxa fixa de R$3,90 por dia de atraso.
    """
    dias = (data_fim - data_inicio).days

    return {
        "dias":        dias,
        "taxa_diaria": TAXA_DIARIA,
        "total_juros": round(dias * TAXA_DIARIA, 2),
    }
