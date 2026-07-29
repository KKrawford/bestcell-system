import streamlit as st
import uuid
import pandas as pd

from core import StateManager, VendasState
from datetime import date, datetime

from .database import (
    fetch_all_parcel_adjustments,
    insert_sale,
    insert_parcels,
    archive_sale,
    delete_sale,
    delete_parcel_adjustments,
    fetch_sales,
    fetch_sales_archive,
    fetch_parcels,
    fetch_parcel_adjustments,
    add_parcel_adjustment,
    close_sale_critical,
    fetch_closed_sales,
    update_closed_sale_recovery,
)

from .utils import (
    normalize_date,
    normalize_datetime,
    add_months_safe,
    calculate_due_dates,
    parcel_financial_summary,    
    sale_is_fully_paid,
    system_health_summary,
)

from .view import (
    sales_view,
    parcels_view,
    adjustments_view,
    reports_view,
    status_style,
    fmt_date,
    currency,
    format_mes_ano,
    info_box,
    hide_value,
)

MODULE = "vendas"


def app():

    # ======================================================
    # STATE INIT
    # ======================================================

    StateManager.init(MODULE, VendasState.FILTRO_CLIENTE, "")
    StateManager.init(MODULE, VendasState.VENDA_SELECIONADA, None)

    tabs = st.tabs(["🧾 Vendas", "💰 Parcelas", "📊 Relatórios"])

# ======================================================
# 🧾 VENDAS
# ======================================================

    with tabs[0]:

        st.header("Cadastro de Venda")

        # Inicializar estado do formulário
        if 'form_key' not in st.session_state:
            st.session_state.form_key = 0

        with st.form(f"cadastro_venda_{st.session_state.form_key}", clear_on_submit=True):
            col1, col2 = st.columns(2)

            cliente = col1.text_input("Cliente")
            aparelho = col1.text_input("Aparelho (marca + modelo)")

            tipo_venda = col2.selectbox(
                "Tipo de venda",
                ["Parcelada", "À vista"],
                index=0
            )

            # Campo para frequência de pagamento
            frequencia_pagamento = col2.selectbox(
                "Frequência de Pagamento",
                ["Mensal", "Quinzenal", "Semanal"],
                index=0
            )
            
            # Inicializar variáveis condicionais
            valor_entrada = 0.0
            num_parcelas = 0
            valor_parcela = 0.0

            # Campos condicionais para vendas parceladas
            if tipo_venda == "Parcelada":
                valor_entrada = col1.number_input(
                    "Valor da entrada (Parcela 0)",
                    min_value=0.0,
                    format="%.2f"
                )

                num_parcelas = col2.number_input(
                    "Quantidade de parcelas",
                    min_value=1,
                    step=1
                )

                valor_parcela = col1.number_input(
                    "Valor de cada parcela (R$)",
                    min_value=0.01,
                    format="%.2f"
                )

            data_venda = col2.date_input(
                "Data da venda",
                value=date.today()
            )

            submit = st.form_submit_button("Salvar venda")

            if submit:
                if not cliente or not aparelho:
                    st.error("Cliente e aparelho são obrigatórios.")
                    st.stop()

                sale_id = str(uuid.uuid4())

                if tipo_venda == "À vista":
                    valor_total = valor_entrada
                    valor_entrada_final = valor_entrada
                    tipo_db = "avista"
                else:
                    valor_total = round(valor_entrada + (num_parcelas * valor_parcela), 2)
                    valor_entrada_final = valor_entrada
                    tipo_db = "parcelada"

                data_venda = normalize_date(data_venda)

                sale = {
                    "id": sale_id,
                    "cliente": cliente,
                    "aparelho": aparelho,
                    "valor_entrada": valor_entrada_final,
                    "tipo_venda": tipo_db,
                    "valor_total": valor_total,
                    "data_venda": data_venda.isoformat(),
                    "frequencia_pagamento": frequencia_pagamento,
                    "created_at": datetime.utcnow().isoformat(),
                }

                insert_sale(sale)

                parcels = []

                # Parcela 0 (sempre paga)
                parcela0_id = str(uuid.uuid4())
                parcels.append({
                    "id": parcela0_id,
                    "sale_id": sale_id,
                    "parcela_num": 0,
                    "valor_original": valor_entrada_final,
                    "vencimento": normalize_date(data_venda).isoformat(),
                    "created_at": datetime.utcnow().isoformat(),
                })

                if tipo_venda == "Parcelada":
                    # Calcular datas de vencimento com base na frequência
                    due_dates = calculate_due_dates(data_venda, frequencia_pagamento, num_parcelas)

                    for i, due_date in enumerate(due_dates, 1):
                        
                        parcels.append({
                            "id": str(uuid.uuid4()),
                            "sale_id": sale_id,
                            "parcela_num": i,
                            "valor_original": valor_parcela,
                            "vencimento": normalize_date(due_date).isoformat(),
                            "created_at": datetime.utcnow().isoformat(),
                        })

                insert_parcels(parcels)

                add_parcel_adjustment({
                    "id": str(uuid.uuid4()),
                    "parcel_id": parcela0_id,
                    "tipo": "pagamento",
                    "valor": valor_entrada_final,
                    "descricao": "Entrada / Pagamento à vista",
                    "created_at": datetime.combine(data_venda, datetime.min.time()).isoformat(),
                })

                # 🔒 Venda à vista já nasce quitada → arquiva imediatamente
                if tipo_venda == "À vista":
                    archive_sale(sale_id)

                st.success("Venda cadastrada com sucesso!")
                st.session_state.form_key += 1
                st.rerun()

        st.markdown("---")
        st.subheader("Vendas")

        filtro = st.radio("Exibir", ["Ativas", "Arquivadas"], horizontal=True)

        sales = fetch_sales() if filtro == "Ativas" else fetch_sales_archive()

        if not sales:
            st.info("Nenhuma venda encontrada.")
        else:
            df_sales = pd.DataFrame([dict(s) for s in sales])

            df_view = sales_view(df_sales)

            st.dataframe(df_view, width="stretch")

            if filtro == "Ativas":
                st.markdown("### Excluir venda (definitivo)")
                options = {
                    f"{s['cliente']} | {s['aparelho']} | {fmt_date(s['data_venda'])}": s["id"]
                    for s in sales
                }

                option_keys = list(options.keys())
                saved_selection = StateManager.get(MODULE, VendasState.VENDA_SELECIONADA)

                index = 0
                if saved_selection in option_keys:
                    index = option_keys.index(saved_selection)

                sel = st.selectbox("Venda", option_keys, index=index)
                StateManager.set(MODULE, VendasState.VENDA_SELECIONADA, sel)
                confirm = st.checkbox("Confirmo exclusão definitiva")

                if st.button("Excluir"):
                    if confirm:
                        sale_id = options[sel]

                        delete_parcel_adjustments(sale_id)  # 🔹 remove histórico financeiro
                        delete_sale(sale_id)                # 🔹 remove venda + parcelas

                        st.success("Venda excluída.")
                        st.rerun()
                    else:
                        st.warning("Confirme a exclusão.")

# ======================================================
# 💰 PARCELAS
# ======================================================
    with tabs[1]:
        st.header("Parcelas")

        parcels = fetch_parcels()
        sales = fetch_sales() + fetch_sales_archive()
        sale_cliente = {s["id"]: s["cliente"] for s in sales}

        # INICIALIZAR df COMO DATAFRAME VAZIO
        df = pd.DataFrame()

        if not parcels:
            st.info("Nenhuma parcela cadastrada.")
        else:
            rows = []

            for p in parcels:
                resumo = parcel_financial_summary(
                    p["id"],
                    p["valor_original"],
                    p["vencimento"]
                )

                rows.append({
                    "Cliente": sale_cliente.get(p["sale_id"], ""),
                    "Parcela": p["parcela_num"],
                    "Vencimento": p["vencimento"],
                    "Valor Original": p["valor_original"],
                    "Acréscimos": resumo["acrescimo"],
                    "Descontos": resumo["desconto"],
                    "Pago": resumo["pago"],
                    "Saldo": resumo["saldo"],
                    "Status": resumo["status"],
                    "Juros (info)": resumo["juros"],
                    "parcel_id": p["id"],       # 🔹 necessário para lógica
                    "sale_id": p["sale_id"],    # 🔹 uso interno
                })

            df = pd.DataFrame(rows)

            # ---------------- FILTRO ----------------
            filtro_key = (
                f"{MODULE}.{VendasState.FILTRO_CLIENTE}"
            )

            col_filtro, col_limpar = st.columns(
                [5, 1],
                vertical_alignment="bottom"
            )

            with col_filtro:
                filtro_cliente = st.text_input(
                    "Filtrar por cliente",
                    key=filtro_key,
                    placeholder="Digite o nome do cliente"
                )

            with col_limpar:
                st.button(
                    "Limpar",
                    key="vendas_limpar_filtro_cliente",
                    width="stretch",
                    disabled=not filtro_cliente,
                    on_click=StateManager.set,
                    args=(
                        MODULE,
                        VendasState.FILTRO_CLIENTE,
                        "",
                    )
                )

            termo_filtro = filtro_cliente.strip()

            if termo_filtro:
                df = df[
                    df["Cliente"].str.contains(
                        termo_filtro,
                        case=False,
                        na=False,
                        regex=False
                    )
                ]

            #----------------- EXIBIÇÃO ----------------
            df_display = df.drop(columns=["parcel_id", "sale_id"]).copy()
            df_display = parcels_view(df_display)

            styled_df = df_display.style.map(
                status_style,
                subset=["Status"]
            )

            st.dataframe(styled_df, width="stretch")
        
        # ---------------- DETALHES DA PARCELA ----------------
        st.markdown("### Detalhes da parcela")

        # Verificar se há parcelas antes de criar o selectbox
        if not df.empty:        
            # Seleção de parcela
            parcel_options = {
            f"{row['Cliente']} | Parcela {row['Parcela']} | Venc: {fmt_date(row['Vencimento'])}": row["parcel_id"]
            for row in df.to_dict("records")
            }

            if parcel_options:
                selected_label = st.selectbox(
                    "Selecionar parcela para visualizar ajustes",
                    list(parcel_options.keys())
                )

                selected_parcel_id = parcel_options[selected_label]

                # ---------------- HISTÓRICO ----------------
                with st.expander("📜 Ver histórico de ajustes"):

                    ajustes = fetch_parcel_adjustments(selected_parcel_id)

                    if not ajustes:
                        st.info("Nenhum ajuste registrado.")
                    else:
                        df_ajustes = pd.DataFrame(ajustes)

                        if "created_at" in df_ajustes.columns:
                            df_ajustes = df_ajustes.sort_values("created_at")
                        # View responsável apenas pela formatação visual
                        df_ajustes_view = adjustments_view(df_ajustes)

                        st.dataframe(df_ajustes_view, width="stretch")           

            # ---------------- AJUSTES ----------------
            st.markdown("### Ajustar parcela")

            # Apenas parcelas com saldo em aberto
            df_ajustavel = df[df["Saldo"] > 0]

            if df_ajustavel.empty:
                st.info("Não há parcelas em aberto para ajuste.")
            else:

                pid = st.selectbox(
                    "Parcela",
                    df_ajustavel["parcel_id"],
                    format_func=lambda x: (
                        f"{df_ajustavel[df_ajustavel['parcel_id'] == x]['Cliente'].values[0]}"
                        f" | Parcela {df_ajustavel[df_ajustavel['parcel_id'] == x]['Parcela'].values[0]}"
                        f" | Saldo: {currency(df_ajustavel[df_ajustavel['parcel_id'] == x]['Saldo'].values[0])}"
                        f" | {df_ajustavel[df_ajustavel['parcel_id'] == x]['Status'].values[0].upper()}"
                    )
                )

                tipo = st.selectbox("Tipo", ["pagamento", "acrescimo", "desconto"])
                valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
                descricao = st.text_input("Descrição")

                if st.button("Registrar ajuste"):
                    add_parcel_adjustment({
                        "id": str(uuid.uuid4()),
                        "parcel_id": pid,
                        "tipo": tipo,
                        "valor": valor,
                        "descricao": descricao,
                        "created_at": datetime.utcnow().isoformat(),
                    })

                    # ---------------- VERIFICAÇÃO AUTOMÁTICA ----------------
                    row = df[df["parcel_id"] == pid].iloc[0]
                    sale_id = row["sale_id"]

                    if sale_is_fully_paid(sale_id):
                        archive_sale(sale_id)

                    st.success("Ajuste registrado.")
                    st.rerun()
        else:
            st.info("Nenhuma parcela disponível para exibir detalhes.")

# ======================================================
# 📊 RELATÓRIOS
# ======================================================
    with tabs[2]:
        st.header("Relatórios")

        with st.expander("🧠 Saúde do Sistema", expanded=True):

            summary = system_health_summary()

            if "show_values" not in st.session_state:
                st.session_state.show_values = True

            st.toggle(
                "👁️ Mostrar valores",
                key="show_values"
            )

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.metric(
                "💰 Total Vendido",
                hide_value(currency(summary["total_vendido"]), st.session_state.show_values)
            )

            col2.metric(
                "✅ Total Recebido",
                hide_value(currency(summary["total_recebido"]), st.session_state.show_values)
            )

            col3.metric(
                "⏳ Saldo em Aberto",
                hide_value(currency(summary["saldo_aberto"]), st.session_state.show_values)
            )

            col4.metric(
                "⚠️ Em Atraso",
                hide_value(currency(summary["em_atraso"]), st.session_state.show_values)
            )

            col5.metric(
                "📅 Recebível Futuro",
                hide_value(currency(summary["recebivel_futuro"]), st.session_state.show_values)
            )

            st.caption("Multa diária informativa: R$ 3,90")
            st.caption("Juros não são incorporados automaticamente")

        # ======================================================
        # FILTRO / CONTEXTO
        # ======================================================
        with st.container():
            st.subheader("Resumo Mensal")

            col1, col2 = st.columns(2)

            data_inicio = col1.date_input(
                "Data inicial",
                value=date(date.today().year, 1, 1)
            )

            data_fim = col2.date_input(
                "Data final",
                value=date.today()
            )

        if data_inicio > data_fim:
            st.error("Data inicial não pode ser maior que a data final.")
            st.stop()

        # ======================================================
        # DADOS BASE
        # ======================================================
        sales_ativas = fetch_sales()
        sales_arquivadas = fetch_sales_archive()
        all_sales = sales_ativas + sales_arquivadas

        parcels = fetch_parcels()
        adjustments = fetch_all_parcel_adjustments()

        hoje = date.today()

        # ======================================================
        # DATAFRAMES (NORMALIZADOS)
        # ======================================================
        if not all_sales:
            st.info("Nenhuma venda registrada no período.")
            st.stop()

        df_sales = pd.DataFrame(all_sales).fillna(0)
        df_parcels = pd.DataFrame([dict(p) for p in parcels]) if parcels else pd.DataFrame()
        df_adj = pd.DataFrame([dict(a) for a in adjustments]) if adjustments else pd.DataFrame()
            
        if not df_adj.empty:
            df_adj["created_at"] = df_adj["created_at"].apply(normalize_datetime)
            df_adj = df_adj.dropna(subset=["created_at"])

        if not df_parcels.empty:
            df_parcels["vencimento"] = df_parcels["vencimento"].apply(normalize_date)

        # ======================================================
        # FILTRO DE PERÍODO (VENDAS)
        # ======================================================
        df_sales["data_venda"] = df_sales["data_venda"].apply(normalize_date)

        df_sales = df_sales[
            (df_sales["data_venda"] >= data_inicio) &
            (df_sales["data_venda"] <= data_fim)
        ]

        if df_sales.empty:
            st.info("Nenhuma venda encontrada no período selecionado.")
            st.stop()

        # ======================================================
        # AGRUPAMENTO MENSAL
        # ======================================================
        df_sales["mes_ano"] = df_sales["data_venda"].apply(lambda d: f"{d.year}-{d.month:02d}")

        resumo = []

        for mes in sorted(df_sales["mes_ano"].unique()):
            vendas_mes = df_sales[df_sales["mes_ano"] == mes]

            qtd_vendas = len(vendas_mes)
            valor_vendido = vendas_mes["valor_total"].sum()

            # ---------------- RECEBIDO NO MÊS ----------------
            if not df_adj.empty:
                valor_recebido = df_adj[
                    (df_adj["tipo"] == "pagamento") &
                    (df_adj["created_at"].dt.to_period("M").astype(str) == mes)
                ]["valor"].sum()
            else:
                valor_recebido = 0

            # ---------------- SALDOS POR MÊS ----------------
            saldo_aberto = 0
            atraso = 0

            if not df_parcels.empty:
                # vendas do mês
                sale_ids_mes = vendas_mes["id"].tolist()

                parcelas_mes = df_parcels[df_parcels["sale_id"].isin(sale_ids_mes)]

                for _, p in parcelas_mes.iterrows():
                    resumo_parcela = parcel_financial_summary(
                        p["id"],
                        p["valor_original"],
                        p["vencimento"]
                    )

                    saldo_aberto += resumo_parcela["saldo"]

                    if normalize_date(p["vencimento"]) < hoje and resumo_parcela["saldo"] > 0:
                        atraso += resumo_parcela["saldo"]

            resumo.append({
                "Mês/Ano": mes,
                "Vendas": qtd_vendas,
                "Valor Vendido": valor_vendido,
                "Valor Recebido": valor_recebido,
                "Saldo em Aberto": saldo_aberto,
                "Em Atraso": atraso,
            })

        # ======================================================
        # EXIBIÇÃO
        # ======================================================
        df_relatorio = pd.DataFrame(resumo)
        df_display = reports_view(df_relatorio)

        st.dataframe(df_display, width="stretch")

        # ======================================================
        # ANÁLISE DETALHADA DO MÊS - DRILL DOWN
        # ======================================================
        st.markdown("---")

        # Referência de período (date-driven)
        ano_ref = data_fim.year
        mes_ref = data_fim.month

        # Apenas exibição (aqui PODE formatar)
        st.markdown(f"### Detalhamento do período: {mes_ref:02d}/{ano_ref}")

        tipo_analise = st.radio(
            "Visualizar",
            [
                "Vendas do mês",
                "Parcelas em Aberto",
                "Parcelas em Atraso",
                "Clientes Críticos",
            ],
            index=0,
            horizontal=True
        )

        if tipo_analise == "Vendas do mês":

            df_vendas_mes = df_sales[
                (df_sales["data_venda"].apply(lambda d: d.year) == ano_ref) &
                (df_sales["data_venda"].apply(lambda d: d.month) == mes_ref)
            ]

            if df_vendas_mes.empty:
                st.info("Nenhuma venda registrada neste mês.")
            else:
                df_view = sales_view(df_vendas_mes)
                st.dataframe(df_view, width="stretch")

        elif tipo_analise == "Parcelas em Aberto":

            if df_parcels.empty:
                st.info("Não há parcelas cadastradas.")
            else:
                rows_aberto = []

                for _, p in df_parcels.iterrows():
                    resumo = parcel_financial_summary(
                        p["id"],
                        p["valor_original"],
                        p["vencimento"]
                    )

                    if resumo["saldo"] > 0:
                        rows_aberto.append({
                            "Cliente": sale_cliente.get(p["sale_id"], ""),
                            "Parcela": p["parcela_num"],
                            "Vencimento": p["vencimento"],
                            "Valor Original": p["valor_original"],
                            "Acréscimos": resumo["acrescimo"],
                            "Descontos": resumo["desconto"],
                            "Pago": resumo["pago"],
                            "Saldo": resumo["saldo"],
                            "Status": resumo["status"],
                        })

                if not rows_aberto:
                    st.info("Não há parcelas em aberto.")
                else:
                    df_aberto = pd.DataFrame(rows_aberto)
                    df_view = parcels_view(df_aberto)
                    st.dataframe(df_view, width="stretch")

        elif tipo_analise == "Parcelas em Atraso":

            if df_parcels.empty:
                st.info("Não há parcelas cadastradas.")
            else:
                rows_atraso = []

                for _, p in df_parcels.iterrows():
                    resumo = parcel_financial_summary(
                        p["id"],
                        p["valor_original"],
                        p["vencimento"]
                    )

                    if resumo["saldo"] > 0 and resumo["status"] == "Atrasado":
                        rows_atraso.append({
                            "Cliente": sale_cliente.get(p["sale_id"], ""),
                            "Parcela": p["parcela_num"],
                            "Vencimento": p["vencimento"],
                            "Valor Original": p["valor_original"],
                            "Acréscimos": resumo["acrescimo"],
                            "Descontos": resumo["desconto"],
                            "Pago": resumo["pago"],
                            "Saldo": resumo["saldo"],
                            "Status": resumo["status"],
                        })

                if not rows_atraso:
                    st.info("Não há parcelas em atraso.")
                else:
                    df_atraso = pd.DataFrame(rows_atraso)
                    df_view = parcels_view(df_atraso)
                    st.dataframe(df_view, width="stretch")

        elif tipo_analise == "Clientes Críticos":

            if df_parcels.empty:
                st.info("Não há parcelas cadastradas.")
            else:
                # ======================================================
                # MAPEAR VENDAS CRÍTICAS 
                # ======================================================
                vendas_criticas = {}

                for _, p in df_parcels.iterrows():
                    resumo = parcel_financial_summary(
                        p["id"],
                        p["valor_original"],
                        p["vencimento"]
                    )

                    if resumo["saldo"] > 0 and resumo["status"] == "Atrasado":
                        sale_id = p["sale_id"]
                        cliente = sale_cliente.get(sale_id, "Desconhecido")

                        if sale_id not in vendas_criticas:
                            vendas_criticas[sale_id] = {
                                "Cliente": cliente,
                                "Parcelas em Atraso": 0,
                                "Valor em Atraso": 0.0,
                                "Maior Atraso (dias)": 0,
                            }

                        vendas_criticas[sale_id]["Parcelas em Atraso"] += 1
                        vendas_criticas[sale_id]["Valor em Atraso"] += resumo["saldo"]
                        vendas_criticas[sale_id]["Maior Atraso (dias)"] = max(
                            vendas_criticas[sale_id]["Maior Atraso (dias)"],
                            resumo.get("dias_atraso", 0)
                        )

                if not vendas_criticas:
                    st.info("Nenhum cliente crítico identificado.")
                else:
                    # ======================================================
                    # TABELA DE CLIENTES CRÍTICOS (visual)
                    # ======================================================
                    df_criticos = pd.DataFrame(
                        [
                            {
                                "sale_id": sale_id,
                                **dados,
                                "Status": "Crítico",
                            }
                            for sale_id, dados in vendas_criticas.items()
                        ]
                    )

                    df_view = df_criticos.drop(columns=["sale_id"]).copy()
                    df_view["Valor em Atraso"] = df_view["Valor em Atraso"].apply(currency)

                    st.dataframe(df_view, width="stretch")

                    # ======================================================
                    # AÇÃO ADMINISTRATIVA (EXCEÇÃO)
                    # ======================================================
                    st.markdown("---")
                    st.caption("⚠️ Ações administrativas (exceção)")

                    with st.expander("Encerrar venda crítica", expanded=False):

                        # -------- seleção da venda --------
                        sale_id_sel = st.selectbox(
                            "Venda",
                            df_criticos["sale_id"].tolist(),
                            format_func=lambda x: (
                                f"{df_criticos[df_criticos['sale_id'] == x]['Cliente'].values[0]}"
                                f" | Em atraso: "
                                f"{currency(df_criticos[df_criticos['sale_id'] == x]['Valor em Atraso'].values[0])}"
                                f" | Parcelas: "
                                f"{df_criticos[df_criticos['sale_id'] == x]['Parcelas em Atraso'].values[0]}"
                            )
                        )

                        # -------- motivo --------
                        motivo = st.selectbox(
                            "Motivo do encerramento",
                            [
                                "Inadimplência (cliente inacessível)",
                                "Acordo financeiro",
                                "Devolução do aparelho",
                                "Troca de aparelho",
                                "Cancelamento com perda",
                            ]
                        )

                        # -------- resumo financeiro --------
                        parcels_sale = df_parcels[df_parcels["sale_id"] == sale_id_sel]

                        valor_recebido = 0.0
                        valor_perdido = 0.0

                        for _, p in parcels_sale.iterrows():
                            resumo = parcel_financial_summary(
                                p["id"],
                                p["valor_original"],
                                p["vencimento"]
                            )
                            valor_recebido += resumo["pago"]
                            valor_perdido += resumo["saldo"]

                        valor_total = valor_recebido + valor_perdido

                        st.markdown(
                            info_box(
                                "Resumo financeiro da venda",
                                [
                                    f"Valor total: {currency(valor_total)}",
                                    f"Valor recebido: {currency(valor_recebido)}",
                                    f"Valor em aberto (perda): {currency(valor_perdido)}",
                                ]
                            ),
                            unsafe_allow_html=True
                        )

                        # -------- confirmação --------
                        confirm = st.checkbox(
                            "Confirmo que esta venda será encerrada e não voltará ao operacional"
                        )

                        if st.button("Encerrar venda"):
                            if not confirm:
                                st.warning("Confirmação obrigatória para encerrar a venda.")
                            else:
                                try:
                                    close_sale_critical(sale_id_sel, motivo)
                                    st.success("Venda encerrada por exceção com sucesso.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao encerrar venda: {str(e)}")

            # ======================================================
            # HISTÓRICO DE VENDAS ENCERRADAS
            # ======================================================
            
            with st.expander("📂 Histórico de Vendas Encerradas", expanded=False):

                closed_sales = fetch_closed_sales()

                if not closed_sales:
                    st.info("Nenhuma venda encerrada registrada.")
                else:
                    for sale in closed_sales:

                        # ---------------- CÁLCULOS ----------------
                        valor_recuperado = sale.get("valor_recuperado", 0) or 0
                        perda_final = max(sale["valor_perdido"] - valor_recuperado, 0)

                        # ---------------- INFO BOX ----------------
                        st.markdown(
                            info_box(
                                f"Venda #{sale['id']} — {sale['cliente']}",
                                [
                                    f"Aparelho: {sale['aparelho']}",
                                    f"Data da venda: {fmt_date(sale['data_venda'])}",
                                    f"Data do encerramento: {fmt_date(sale['closed_at'])}",
                                    f"Motivo: {sale['motivo']}",
                                    f"Valor total: {currency(sale['valor_total'])}",
                                    f"Valor recebido: {currency(sale['valor_recebido'])}",
                                    f"Valor recuperado após encerramento: {currency(valor_recuperado)}",
                                    f"Perda final: {currency(perda_final)}",
                                ]
                            ),
                            unsafe_allow_html=True
                        )

                        # ---------------- RECUPERAÇÃO DE VALOR ----------------
                        if perda_final > 0:
                            with st.expander("➕ Registrar recuperação de valor", expanded=False):

                                valor_input = st.number_input(
                                    "Valor recebido após encerramento",
                                    min_value=0.0,
                                    max_value=float(perda_final),
                                    step=10.0,
                                    format="%.2f",
                                    key=f"recuperacao_{sale['id']}"
                                )

                                if st.button(
                                    "Confirmar abatimento",
                                    key=f"btn_recuperacao_{sale['id']}"
                                ):
                                    update_closed_sale_recovery(sale["id"], valor_input)
                                    st.success("Valor abatido da perda com sucesso.")
                                    st.rerun()

                        st.markdown("<br>", unsafe_allow_html=True)