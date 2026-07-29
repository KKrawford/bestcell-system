import streamlit as st
import pandas as pd


# ======================================================
# IPHONES
# ======================================================

def exibir_iphones(iphones: list):
    if not iphones:
        st.info("Nenhum iPhone cadastrado.")
        return

    dados = []
    for a in iphones:
        dados.append({
            "Modelo":        a["modelo"],
            "Armazenamento": a["armazenamento"],
            "Cor":           a["cor"],
            "Bateria (%)":   a["bateria"] if a["bateria"] else "-",
            "Disponível":    "✅" if a["disponivel"] else "—",
            "Preço à Vista": f"R$ {a['preco_avista']:.2f}",
            "Observações":   a["observacoes"] or "-",
        })

    st.dataframe(
        pd.DataFrame(dados),
        width='stretch',
        hide_index=True,
    )


# ======================================================
# ANDROIDS
# ======================================================

def exibir_androids(androids: list):
    if not androids:
        st.info("Nenhum Android cadastrado.")
        return

    dados = []
    for a in androids:
        dados.append({
            "Marca":         a["marca"],
            "Modelo":        a["modelo"],
            "RAM":           a["ram"],
            "Armazenamento": a["armazenamento"],
            "Estado":        a["estado"].capitalize(),
            "Preço à Vista": f"R$ {a['preco_avista']:.2f}",
            "Observações":   a["observacoes"] or "-",
        })

    st.dataframe(
        pd.DataFrame(dados),
        width='stretch',
        hide_index=True,
    )


# ======================================================
# PERFUMES
# ======================================================

def exibir_perfumes(perfumes: list):
    if not perfumes:
        st.info("Nenhum perfume cadastrado.")
        return

    dados = []
    for p in perfumes:
        dados.append({
            "Marca":       p["marca"],
            "Nome":        p["nome"],
            "Preço":       f"R$ {p['preco']:.2f}",
            "Observações": p["observacoes"] or "-",
        })

    st.dataframe(
        pd.DataFrame(dados),
        width='stretch',
        hide_index=True,
    )


# ======================================================
# PODS
# ======================================================

def exibir_pods(pods: list):
    if not pods:
        st.info("Nenhum POD cadastrado.")
        return

    dados = []
    for p in pods:
        dados.append({
            "Marca":       p["marca"],
            "Nome":        p["nome"],
            "Puffs":       p["puffs"],
            "Preço":       f"R$ {p['preco']:.2f}",
            "Observações": p["observacoes"] or "-",
        })

    st.dataframe(
        pd.DataFrame(dados),
        width='stretch',
        hide_index=True,
    )
