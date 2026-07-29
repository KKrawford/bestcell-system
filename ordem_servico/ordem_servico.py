import streamlit as st
import uuid
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta

from core import StateManager, OSState
from .database import (
    init_db,
    insert_order,
    fetch_orders,
    fetch_orders_by_status,
    fetch_order_by_id,
    fetch_order_status_history,
    update_order_status,
    update_order_fields,
    generate_os_number,
    get_os_stats,
    get_os_financeiras_por_periodo,
    get_os_por_status_periodo,
    get_os_entregues_por_periodo,
    delete_order,
    excluir_os_arquivada,
    arquivar_os,
    fetch_os_arquivadas,
    busca_completa_os, 
)

from .utils import (
    build_new_order,
    status_list_kanban,
    status_list_completa,
    dias_na_loja,
    build_whatsapp_message,
    build_pdf_bytes,
    widget_key,
)

from .view import (
    currency,
    fmt_date,
    info_box,
    fmt_date_short,
)

from .pattern import (
    pattern_editor_modal,
    render_pattern_grid,
    validate_pattern,
    format_pattern_for_display,
)

# =========================================================
# CALLBACKS PARA MODIFICAÇÃO DE ESTADO
# =========================================================
def open_pattern_editor(order_id: str):
    """Callback para abrir o editor de padrão"""
    st.session_state[f"edit_pattern_{order_id}"] = True

def close_pattern_editor(order_id: str):
    """Callback para fechar o editor de padrão"""
    st.session_state[f"edit_pattern_{order_id}"] = False


MODULE = "ordem_servico"

def app():
    """
    Função principal do módulo de Ordem de Serviço
    Segue o padrão do sistema de vendas: código direto nas tabs
    """
    
    # ======================================================
    # STATE INIT
    # ======================================================
    StateManager.init(MODULE, OSState.FILTRO_STATUS, "Todos")
    StateManager.init(MODULE, OSState.OS_SELECIONADA, None)
    
    # Inicializar banco de dados
    init_db()
    
    # ======================================================
    # HEADER COM ESTATÍSTICAS
    # ======================================================
    st.header("Ordem de Serviço")
    
    # Estatísticas rápidas
    stats = get_os_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total OS", stats["total"])
    
    with col2:
        em_andamento = stats["status_counts"].get("Em reparo", 0) + \
                      stats["status_counts"].get("Em análise", 0)
        st.metric("Em andamento", em_andamento)
    
    with col3:
        pronto = stats["status_counts"].get("Pronto", 0)
        st.metric("Prontos para entrega", pronto)
    
    with col4:
        arquivadas = len(fetch_os_arquivadas())
        st.metric("OS Arquivadas", arquivadas)
    
    st.markdown("---")
    
    # ======================================================
    # TABS PRINCIPAIS - CÓDIGO DIRETO (PADRÃO VENDAS)
    # ======================================================
    tab_nova, tab_kanban, tab_busca, tab_relatorios = st.tabs([
        "📋 Nova OS", 
        "📊 Quadro de OS", 
        "🔍 Buscar", 
        "📈 Relatórios"
    ])
    
    # ======================================================
    # 📋 TAB 1: NOVA ORDEM DE SERVIÇO
    # ======================================================
    with tab_nova:
        st.subheader("Nova Ordem de Serviço")
        
        with st.form("nova_os_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Cliente*", placeholder="Nome completo")
                fone = st.text_input("Telefone", placeholder="(14) 99999-9999")
                aparelho = st.text_input("Aparelho*", placeholder="Marca + Modelo")
            
            with col2:
                
                email = st.text_input("E-mail", placeholder="email@exemplo.com")
                valor_estimado = st.number_input(
                    "Valor estimado (R$)",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f"
                )
                # Data de entrada fixa (não editável)
                data_entrada = date.today()
                st.text_input(
                    "Data de entrada*", 
                    value=data_entrada.strftime("%d/%m/%Y"),
                    disabled=True,
                    help="Data automática da criação da OS"
                )
            
            detalhes_servico = st.text_area(
                "Problema relatado*",
                placeholder="Descreva o problema relatado pelo cliente",
                height=100
            )
            
            observacoes = st.text_area(
                "Observações",
                placeholder="Observações adicionais",
                height=80
            )
                        
            # Senha/Pattern Lock
            st.markdown("#### Senha do Aparelho")
            senha_col1, senha_col2 = st.columns(2)

            with senha_col1:
                senha_tipo = st.selectbox(
                    "Tipo de senha",
                    ["Alfanumérica", "Padrão 3x3", "Sem senha"]
                )

            with senha_col2:
                # Inicializar as variáveis
                senha_tela = None
                senha_padrao = None

                senha_tela = st.text_input(
                        "Senha", 
                        placeholder="Digite a senha alfanumérica",
                        type="password"  # Para ocultar a senha durante a digitação
                    )
                if senha_tipo == "Alfanumérica":
                    senha_tela = senha_tela if senha_tela else None
                elif senha_tipo == "Padrão 3x3":
                    # Mantemos o campo para o padrão, mas não mostramos input
                    # O padrão será editado através do modal posteriormente
                    senha_padrao = None
                    st.info("Use o editor de padrão após criar a OS")
                else:
                    senha_tela = None
                    senha_padrao = None

            
            submit = st.form_submit_button("Criar Ordem de Serviço")
            
            if submit:
                if not nome or not aparelho or not detalhes_servico:
                    st.error("Preencha os campos obrigatórios (*)")
                    return
                
                numero_os = generate_os_number()
                
                order = build_new_order(
                    numero_os=numero_os,
                    nome=nome,
                    fone=fone,
                    email=email,
                    aparelho=aparelho,
                    detalhes_servico=detalhes_servico,
                    valor_estimado=valor_estimado,
                    senha_tipo=senha_tipo,
                    senha_padrao=senha_padrao,
                    senha_tela=senha_tela,
                    observacoes=observacoes,
                )
                
                order["data_entrada"] = data_entrada.isoformat()
                
                insert_order(order)
                
                st.success(f"Ordem de Serviço {numero_os} criada com sucesso!")
                st.rerun()
    
    # ======================================================
    # 📊 TAB 2: QUADRO KANBAN (CÓDIGO DIRETO)
    # ======================================================
    with tab_kanban:
        st.subheader("Quadro Kanban")
        
        # Status que aparecem no kanban (apenas ativos)
        statuses = status_list_kanban()
        cols = st.columns(len(statuses))
        
        for i, status in enumerate(statuses):
            with cols[i]:
                # Header da coluna
                st.markdown(f"### {status}")
                
                # Buscar OS deste status
                orders = fetch_orders_by_status(status)
                
                if not orders:
                    st.caption("Sem ordens")
                    continue
                
                # Renderizar cada card
                for order in orders:
                    with st.container(border=True):
                        # LINHA 1: NOME CLICKÁVEL (ocupa toda a largura)
                        if st.button(
                            f"**{order['numero_os']}** - {order['nome']}",
                            key=f"kanban_open_{order['id']}",
                            width="stretch"
                        ):
                            StateManager.set(MODULE, OSState.OS_SELECIONADA, order["id"])
                            st.rerun()
                        
                        # LINHA 2: INFORMAÇÕES EM DUAS COLUNAS
                        col_info, col_valor = st.columns([3, 1])
                        
                        with col_info:
                            # Aparelho
                            st.caption(f"📱 {order['aparelho']}")
                        
                        with col_valor:
                            # Valor estimado (ocupa espaço vertical das duas linhas)
                            valor = order.get("valor_estimado") or 0
                            if valor > 0:
                                # Container para centralizar verticalmente
                                st.markdown(
                                    f"""
                                    <div style="display: flex; align-items: center; height: 100%; justify-content: center;">
                                        <span style="font-weight: bold; font-size: 14px;">{currency(valor)}</span>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            else:
                                st.caption("Sem valor")

                        # Dias na loja
                        dias = dias_na_loja(order["data_entrada"])
                        if dias >= 6:
                            st.error(f"🔴 {dias} dias na loja")
                        elif dias >= 3:
                            st.warning(f"⚠️ {dias} dias na loja")
                        else:
                            st.caption(f"⏱️ {dias} dia(s) na loja")
                        
                        # LINHA 3: CONTROLE DE STATUS
                        status_options = status_list_kanban()
                        novo_status = st.selectbox(
                            "Status",
                            status_options,
                            index=status_options.index(order["status"]),
                            key=f"kanban_status_{order['id']}",
                            label_visibility="collapsed"
                        )
                        
                        if novo_status != order["status"]:
                            update_order_status(order["id"], novo_status)
                            st.rerun()
    
    # ======================================================
    # 🔍 TAB 3: BUSCAR
    # ======================================================
    with tab_busca:
        st.subheader("Buscar Ordem de Serviço")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            query = st.text_input(
                "Buscar por cliente, aparelho ou número",
                placeholder="Digite para buscar..."
            )
        
        with col2:
            filtro_tipo = st.radio(
                "Tipo",
                ["Ativas", "Arquivadas"],
                index=0,
                horizontal=True,
                key="filtro_tipo_radio"
            )
        
        with col3:
            # Selectbox de status apenas para arquivadas
            if filtro_tipo == "Arquivadas":
                # Opções de status para arquivadas (motivos)
                status_options = ["Todos", "Entregue ao cliente", "Cancelado pelo cliente", "Outro"]
                filtro_status = st.selectbox(
                    "Status", 
                    status_options, 
                    index=0,
                    key="filtro_status_arquivadas"
                )
            else:
                # Para ativas, não mostrar selectbox de status
                filtro_status = "Todos"
            
            StateManager.set(MODULE, OSState.FILTRO_STATUS, filtro_status)
        
        # Buscar dados baseado nos filtros
        if filtro_tipo == "Arquivadas":
            resultados = fetch_os_arquivadas(query)

            # Adicionar campo 'tipo' para cada resultado
            for result in resultados:
                result['tipo'] = 'arquivada'
        
            # Aplicar filtro de motivo se selecionado
            if filtro_status != "Todos":
                resultados = [r for r in resultados if r.get("status") == filtro_status]

        else:  # Ativas
            resultados = fetch_orders()
            # Adicionar campo 'tipo' para cada resultado
            for result in resultados:
                result['tipo'] = 'ativa'

            if query:
                query_lower = query.lower()
                resultados = [
                    o for o in resultados
                    if (query_lower in o["nome"].lower() or
                        query_lower in o["aparelho"].lower() or
                        query_lower in o["numero_os"].lower())
                ]
        
        # Exibir resultados
        if not resultados:
            st.info("Nenhuma ordem de serviço encontrada.")
        else:
            st.info(f"Encontradas {len(resultados)} OS{'s' if len(resultados) > 1 else ''}")
            
            for result in resultados:
                tipo = result.get('tipo', 'ativa')
                
                with st.container(border=True):
                    # Indicador de tipo
                    if tipo == 'arquivada':
                        st.markdown("🗄️ **ARQUIVADA**", help="OS finalizada ou cancelada")
                    
                    col_a, col_b, col_c = st.columns([3, 1, 1])
                    
                    with col_a:
                        st.write(f"**{result['numero_os']}** - {result['nome']}")
                        st.caption(f"📱 {result['aparelho']}")
                        
                        status = result['status']
                        st.caption(f"📊 {status}")
                    
                    with col_b:
                        if tipo == 'ativa':
                            if st.button("Abrir", key=f"busca_open_{result['id']}"):
                                StateManager.set(MODULE, OSState.OS_SELECIONADA, result["id"])
                                st.rerun()
                        else:
                            st.caption(f"Arquivada: {fmt_date_short(result.get('arquivada_em'))}")
                    
                    with col_c:
                        if tipo == 'arquivada':
                            # Botão para visualizar OS arquivada
                            if st.button("👁️ Visualizar", key=f"view_{result['id']}"):
                                st.session_state[f"view_arquivada_{result['id']}"] = True
                    
                    # Renderizar modal de visualização se solicitado
                    if tipo == 'arquivada' and st.session_state.get(f"view_arquivada_{result['id']}"):
                        render_detalhes_os_arquivada(result, 'busca')
    
    # ======================================================
    # 📈 TAB 4: RELATÓRIOS (CÓDIGO DIRETO)
    # ======================================================
    with tab_relatorios:
        st.subheader("📈 Relatórios e Analytics")
        
        # Período de análise
        st.markdown("### 📅 Período de Análise")
        col_periodo1, col_periodo2 = st.columns(2)
        
        with col_periodo1:
            periodo_tipo = st.selectbox(
                "Tipo de Período",
                ["Este mês", "Mês anterior", "Trimestre", "Semestre", "Ano", "Personalizado"],
                index=0
            )
        
        # Calcular datas com base no período selecionado
        hoje = date.today()
        data_inicio = None
        data_fim = None
        
        if periodo_tipo == "Este mês":
            data_inicio = date(hoje.year, hoje.month, 1)
            data_fim = hoje
        elif periodo_tipo == "Mês anterior":
            if hoje.month == 1:
                data_inicio = date(hoje.year - 1, 12, 1)
                data_fim = date(hoje.year - 1, 12, 31)
            else:
                data_inicio = date(hoje.year, hoje.month - 1, 1)
                data_fim = date(hoje.year, hoje.month, 1) - timedelta(days=1)
        elif periodo_tipo == "Trimestre":
            trimestre = (hoje.month - 1) // 3 + 1
            data_inicio = date(hoje.year, 3 * (trimestre - 1) + 1, 1)
            data_fim = hoje
        elif periodo_tipo == "Semestre":
            semestre = 1 if hoje.month <= 6 else 2
            data_inicio = date(hoje.year, 6 * (semestre - 1) + 1, 1)
            data_fim = hoje
        elif periodo_tipo == "Ano":
            data_inicio = date(hoje.year, 1, 1)
            data_fim = hoje
        else:  # Personalizado
            with col_periodo2:
                data_inicio = st.date_input("Data Inicial", value=date(hoje.year, hoje.month, 1))
                data_fim = st.date_input("Data Final", value=hoje)
        
        # Converter para string no formato ISO
        data_inicio_str = data_inicio.isoformat() if data_inicio else None
        data_fim_str = data_fim.isoformat() if data_fim else None
        
        # Obter dados
        stats_financeiras = get_os_financeiras_por_periodo(data_inicio_str, data_fim_str)
        stats_status = get_os_por_status_periodo(data_inicio_str, data_fim_str)
        os_entregues = get_os_entregues_por_periodo(data_inicio_str, data_fim_str)
        
        # Métricas Principais
        st.markdown("### 📊 Métricas Principais")
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        
        with col_metric1:
            total_os = sum(stats_status.values())
            st.metric("Total de OSs", total_os)
        
        with col_metric2:
            os_entregues_count = stats_status.get("Entregue", 0)
            st.metric("OSs Entregues", os_entregues_count)
        
        with col_metric3:
            valor_total = stats_financeiras["valor_total"]
            st.metric("Valor Total (R$)", f"{valor_total:,.2f}")
        
        # Gráficos
        st.markdown("### 📈 Visualizações")
        
        # Gráfico 1: Distribuição por Status
        if stats_status:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                df_status = pd.DataFrame({
                    "Status": list(stats_status.keys()),
                    "Quantidade": list(stats_status.values())
                })
                fig_status = px.pie(
                    df_status, 
                    values="Quantidade", 
                    names="Status",
                    title="Distribuição de OSs por Status"
                )
                st.plotly_chart(fig_status, width='stretch')
        
        # Gráfico 2: Evolução Temporal (se houver dados)
        if os_entregues:
            with col_chart2:
                df_entregues = pd.DataFrame(os_entregues)
                df_entregues["delivered_at"] = pd.to_datetime(df_entregues["delivered_at"])
                df_entregues["data"] = df_entregues["delivered_at"].dt.date
                
                # Agrupar por data
                df_agrupado = df_entregues.groupby("data").agg({
                    "numero_os": "count",
                    "valor_estimado": "sum"
                }).reset_index()
                df_agrupado.rename(columns={"numero_os": "Quantidade", "valor_estimado": "Valor"}, inplace=True)
                
                fig_evolucao = px.line(
                    df_agrupado,
                    x="data",
                    y="Valor",
                    title="Evolução do Valor de OSs Entregues",
                    labels={"data": "Data", "Valor": "Valor (R$)"}
                )
                st.plotly_chart(fig_evolucao, width='stretch')
        
        # Tabela de OSs Entregues
        st.markdown("### 📋 OSs Entregues no Período")
        if os_entregues:
            df_detalhes = pd.DataFrame(os_entregues)
            df_detalhes["delivered_at"] = pd.to_datetime(df_detalhes["delivered_at"]).dt.strftime("%d/%m/%Y")
            
            # Formatar valor
            df_detalhes["valor_estimado"] = df_detalhes["valor_estimado"].apply(
                lambda x: f"R$ {x:,.2f}" if x else "R$ 0,00"
            )
            
            # Renomear colunas
            df_detalhes.rename(columns={
                "numero_os": "OS",
                "nome": "Cliente",
                "aparelho": "Aparelho",
                "valor_estimado": "Valor",
                "delivered_at": "Data Entrega"
            }, inplace=True)
            
            st.dataframe(
                df_detalhes[["OS", "Cliente", "Aparelho", "Valor", "Data Entrega"]],
                width='stretch',
                hide_index=True
            )
            
            # Botão de exportação
            csv = df_detalhes.to_csv(index=False)
            st.download_button(
                "💾 Exportar para CSV",
                csv,
                file_name=f"os_entregues_{data_inicio_str}_{data_fim_str}.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhuma OS entregue no período selecionado.")
        
        # Ação Rápida (Opcional)
        st.markdown("### ⚡ Ação Rápida")
        if st.button("🔄 Atualizar Dados", help="Recalcular todas as estatísticas"):
            st.rerun()
    
    # ======================================================
    # DETALHES DA OS (função separada - componente complexo)
    # ======================================================
    os_selecionada = StateManager.get(MODULE, OSState.OS_SELECIONADA)
    if os_selecionada:
        render_detalhes_os(os_selecionada)

# ======================================================
# FUNÇÃO SEPARADA PARA DETALHES DA OS (componente complexo)
# ======================================================
def render_detalhes_os(order_id):
    """Renderiza os detalhes de uma OS específica"""
    order = fetch_order_by_id(order_id)
    
    if not order:
        st.error("Ordem de Serviço não encontrada.")
        StateManager.set(MODULE, OSState.OS_SELECIONADA, None)
        return
    
    st.markdown("---")
    
    # Header dos detalhes
    col_title, col_actions = st.columns([3, 1])
    
    with col_title:
        st.header(f"Ordem de Serviço {order['numero_os']}")
    
    with col_actions:
        if st.button("✖️ Fechar"):
            StateManager.set(MODULE, OSState.OS_SELECIONADA, None)
            st.rerun()
    
    # Informações principais em abas
    tab_info, tab_servico, tab_historico, tab_acoes = st.tabs([
        "📋 Informações", 
        "🔧 Serviço", 
        "📜 Histórico",
        "⚙️ Ações"
    ])
    
    with tab_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cliente")
            st.write(f"**Nome:** {order['nome']}")
            st.write(f"**Telefone:** {order['fone']}")
            
            st.subheader("Aparelho")
            st.write(order["aparelho"])
            
            if order.get("senha_tipo") and order["senha_tipo"] != "Sem senha":
                st.subheader("Senha")
                st.write(f"Tipo: {order['senha_tipo']}")
                
                if order["senha_tipo"] == "Padrão 3x3" and order.get("senha_padrao"):
                    # Visualização interativa do padrão
                    st.html(render_pattern_grid(order["senha_padrao"]))
                elif order["senha_tipo"] == "Alfanumérica" and order.get("senha_tela"):
                    # Exibir a senha alfanumérica (com opção para mostrar/ocultar)
                    if st.checkbox("Mostrar senha", key=f"show_pwd_{order_id}"):
                        st.write(f"Senha: {order['senha_tela']}")
                    else:
                        st.write("Senha: ••••••••")
                else:
                    st.info("Nenhuma senha definida para este tipo")
        
        with col2:
            st.subheader("Datas")
            st.write(f"**Entrada:** {fmt_date(order['data_entrada'])}")
            if order.get("started_at"):
                st.write(f"**Início reparo:** {fmt_date(order['started_at'], True)}")
            if order.get("finished_at"):
                st.write(f"**Concluído:** {fmt_date(order['finished_at'], True)}")
            if order.get("delivered_at"):
                st.write(f"**Entregue:** {fmt_date(order['delivered_at'], True)}")
            
            st.subheader("Financeiro")
            valor = order.get("valor_estimado") or 0
            st.write(f"**Valor estimado:** {currency(valor)}")
            
            st.subheader("Status")
            st.write(f"**Atual:** {order['status']}")
    
    with tab_servico:
        st.subheader("Problema Relatado")
        st.write(order["detalhes_servico"])
        
        st.markdown("---")
        st.subheader("Serviço Realizado")
        
        servico = st.text_area(
            "Descreva o serviço executado",
            value=order.get("servico_realizado") or "",
            key=widget_key("servico", order["id"]),
            height=150
        )
        
        if st.button("💾 Salvar serviço realizado"):
            update_order_fields(order_id, {"servico_realizado": servico})
            st.success("Serviço atualizado!")
            st.rerun()
        
        st.markdown("---")
        st.subheader("Observações")
        
        obs = st.text_area(
            "Observações adicionais",
            value=order.get("observacoes") or "",
            key=widget_key("observacoes", order["id"]),
            height=100
        )
        
        if st.button("💾 Salvar observações"):
            update_order_fields(order_id, {"observacoes": obs})
            st.success("Observações salvas!")
            st.rerun()
    
    with tab_historico:
        st.subheader("Histórico de Status")
        
        history = fetch_order_status_history(order_id)
        
        if not history:
            st.info("Nenhum histórico registrado.")
        else:
            for h in history:
                with st.container(border=True):
                    col_h1, col_h2 = st.columns([3, 1])
                    with col_h1:
                        if h["from_status"]:
                            st.write(f"**{h['from_status']}** → **{h['to_status']}**")
                        else:
                            st.write(f"**Criado como {h['to_status']}**")
                        
                        if h.get("note"):
                            st.caption(f"Nota: {h['note']}")
                    
                    with col_h2:
                        st.caption(fmt_date(h["changed_at"], True))
    
    with tab_acoes:
                
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.subheader("Ações Administrativas")
            # Editar informações básicas
            if st.button("✏️ Editar informações", width="stretch"):
                st.session_state[f"edit_mode_{order_id}"] = True

            if st.session_state.get(f"edit_mode_{order_id}"):
                st.markdown("##### Editar")
                
                novo_nome = st.text_input("Nome", value=order["nome"])
                novo_fone = st.text_input("Telefone", value=order["fone"])
                novo_aparelho = st.text_input("Aparelho", value=order["aparelho"])
                novo_valor = st.number_input(
                    "Valor estimado",
                    value=float(order.get("valor_estimado") or 0),
                    min_value=0.0,
                    step=10.0,
                    format="%.2f"
                )
                
                if st.button("💾 Salvar alterações"):
                    update_data = {
                        "nome": novo_nome,
                        "fone": novo_fone,
                        "aparelho": novo_aparelho,
                        "valor_estimado": novo_valor
                    }
                    update_order_fields(order_id, update_data)
                    st.session_state[f"edit_mode_{order_id}"] = False
                    st.success("Informações atualizadas!")
                    st.rerun()
                
                if st.button("❌ Cancelar edição"):
                    st.session_state[f"edit_mode_{order_id}"] = False
                    st.rerun()
                
            st.markdown("---")
            st.subheader("🔒 Gerenciar Senha")

            # Seletor de tipo de senha
            novo_tipo_senha = st.selectbox(
                "Tipo de senha",
                ["Sem senha", "Alfanumérica", "Padrão 3x3"],
                index=["Sem senha", "Alfanumérica", "Padrão 3x3"].index(order.get("senha_tipo", "Sem senha")),
                key=f"senha_tipo_edit_{order_id}"
            )

            # Campos específicos para cada tipo de senha
            if novo_tipo_senha == "Alfanumérica":
                st.markdown("**Senha Alfanumérica**")
                nova_senha = st.text_input(
                    "Digite a senha",
                    value=order.get("senha_tela", ""),
                    type="password",
                    key=f"senha_alfanumerica_{order_id}",
                    help="Senha pode conter letras, números e caracteres especiais"
                )
                
                # Botão para salvar
                if st.button("💾 Salvar Senha Alfanumérica", key=f"save_senha_alfa_{order_id}"):
                    update_data = {
                        "senha_tipo": novo_tipo_senha,
                        "senha_tela": nova_senha if nova_senha else None,
                        "senha_padrao": None  # Limpar padrão se existir
                    }
                    update_order_fields(order_id, update_data)
                    st.success("Senha alfanumérica salva!")
                    st.rerun()

            elif novo_tipo_senha == "Padrão 3x3":
                st.markdown("**Padrão Android 3x3**")
                
                col_status, col_action = st.columns([1, 1])
                
                with col_status:
                    st.markdown("**Status atual:**")
                    current_pattern = order.get("senha_padrao", "")
                    if current_pattern:
                        st.html(render_pattern_grid(current_pattern))
                        is_valid, msg = validate_pattern(current_pattern)
                        if is_valid:
                            st.success("✅ Padrão válido")
                        else:
                            st.error(f"⚠️ {msg}")
                    else:
                        st.info("Nenhum padrão definido")
                
                with col_action:
                    st.markdown("**Ações:**")
                    # Usar callback para abrir o editor
                    st.button(
                        "🎯 Editor de Padrão", 
                        key=f"edit_pattern_btn_{order_id}",
                        on_click=open_pattern_editor,
                        args=(order_id,),
                        width='stretch'
                    )
                
                # Modal de edição de padrão
                if st.session_state.get(f"edit_pattern_{order_id}", False):
                    novo_padrao = pattern_editor_modal(
                        order_id=order_id,
                        current_pattern=order.get("senha_padrao", "")
                    )
                    
                    if novo_padrao is not None:
                        if novo_padrao:  # Padrão foi aplicado
                            update_data = {
                                "senha_tipo": novo_tipo_senha,
                                "senha_padrao": novo_padrao,
                                "senha_tela": None  # Limpar senha alfanumérica se existir
                            }
                            update_order_fields(order_id, update_data)
                            st.success("✅ Padrão atualizado!")
                            st.session_state[f"edit_pattern_{order_id}"] = False
                            st.rerun()
                        else:  # Padrão foi cancelado
                            st.session_state[f"edit_pattern_{order_id}"] = False
                            st.rerun()
                    
                    # Botão para cancelar fora do modal
                    if st.button(
                        "❌ Cancelar Edição", 
                        key=f"cancel_pattern_{order_id}",
                        on_click=close_pattern_editor,
                        args=(order_id,),
                        width='stretch'
                    ):
                        st.rerun()

            else:  # Sem senha
                st.info("Aparelho sem senha de desbloqueio")
                
                # Se havia uma senha anterior, oferecer opção para remover
                if order.get("senha_tipo") != "Sem senha":
                    if st.button("🗑️ Remover senha atual", key=f"remove_senha_{order_id}"):
                        update_data = {
                            "senha_tipo": "Sem senha",
                            "senha_padrao": None,
                            "senha_tela": None
                        }
                        update_order_fields(order_id, update_data)
                        st.success("Senha removida!")
                        st.rerun()

            # Botão para aplicar mudanças de tipo (para casos onde apenas o tipo muda)
            if novo_tipo_senha != order.get("senha_tipo"):
                if st.button("🔄 Aplicar Tipo de Senha", key=f"apply_senha_type_{order_id}"):
                    update_data = {"senha_tipo": novo_tipo_senha}
                    
                    # Limpar campos não utilizados
                    if novo_tipo_senha != "Alfanumérica":
                        update_data["senha_tela"] = None
                    if novo_tipo_senha != "Padrão 3x3":
                        update_data["senha_padrao"] = None
                        
                    update_order_fields(order_id, update_data)
                    st.success("Tipo de senha atualizado!")
                    st.rerun()
                    
                    # Botão para cancelar
                    if st.button("❌ Cancelar Edição", width="stretch"):
                        st.session_state[f"edit_pattern_{order_id}"] = False
                        st.rerun()   
        
        with col_a2:
            # Exportar/Compartilhar
            st.subheader("Exportar / Compartilhar")
            
            # WhatsApp
            if st.button("📱 Gerar mensagem WhatsApp", width="stretch"):
                msg = build_whatsapp_message(order)
                st.code(msg, language=None)
                st.caption("Copie e cole no WhatsApp")
            
            # PDF
            pdf_bytes = build_pdf_bytes(order)
            st.download_button(
                "📄 Baixar PDF",
                pdf_bytes,
                file_name=f"{order['numero_os']}.pdf",
                mime="application/pdf",
                width="stretch"
            )        
            
            st.markdown("---")
            # Arquivar OS
            st.warning("Arquivar OS")
            motivo = st.selectbox(
                "Motivo do arquivamento",
                ["Entregue ao cliente", "Cancelado pelo cliente", "Outro"],
                key=f"motivo_{order_id}"
            )
            
            if st.button("🗄️ Arquivar OS", width="stretch"):
                arquivar_os(order_id, motivo)
                StateManager.set(MODULE, OSState.OS_SELECIONADA, None)
                st.success("OS arquivada com sucesso!")
                st.rerun()

            # Exclusão Permanente            
            st.error("🚫 Exclusão Permanente")

            # Adicionar confirmação para evitar exclusões acidentais
            confirmar_exclusao = st.checkbox(
                "Confirmar exclusão permanente", 
                key=f"confirm_delete_{order_id}",
                help="Esta ação não pode ser desfeita. Todos os dados serão perdidos."
            )

            if st.button(
                "💣 Excluir Permanentemente", 
                disabled=not confirmar_exclusao,
                key=f"delete_perm_{order_id}",
                help="Exclui permanentemente a OS e todos os seus dados",
                width='stretch'
            ):
                try:
                    delete_order(order_id)
                    st.success("OS excluída permanentemente!")
                    StateManager.set(MODULE, OSState.OS_SELECIONADA, None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir OS: {str(e)}")


# ======================================================
# DETALHES DE OS ARQUIVADA (função separada - componente complexo)
# ======================================================
def render_detalhes_os_arquivada(os_arquivada, contexto='default'):
    """Renderiza os detalhes de uma OS arquivada em um modal"""
    os_id = os_arquivada['id']

    # Gerar ID único baseado no timestamp
    unique_id = str(datetime.now().timestamp()).replace('.', '')[-8:]
    
    # Usar container com key única para isolar completamente
    with st.container(key=f"os_detail_{os_id}_{unique_id}"):
        st.markdown(f"### 📋 OS Arquivada: {os_arquivada['numero_os']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Cliente**")
            st.write(f"Nome: {os_arquivada['nome']}")
            st.write(f"Telefone: {os_arquivada['fone'] or '-'}")
            st.write(f"Email: {os_arquivada['email'] or '-'}")
            
            st.markdown("**📱 Aparelho**")
            st.write(os_arquivada["aparelho"])
            
            st.markdown("**💰 Financeiro**")
            valor = os_arquivada.get("valor_estimado") or 0
            st.write(f"Valor estimado: {currency(valor)}")
        
        with col2:
            st.markdown("**📅 Datas**")
            st.write(f"Entrada: {fmt_date(os_arquivada['data_entrada'])}")
            if os_arquivada.get("started_at"):
                st.write(f"Início reparo: {fmt_date(os_arquivada['started_at'], True)}")
            if os_arquivada.get("finished_at"):
                st.write(f"Concluído: {fmt_date(os_arquivada['finished_at'], True)}")
            if os_arquivada.get("delivered_at"):
                st.write(f"Entregue: {fmt_date(os_arquivada['delivered_at'], True)}")
            st.write(f"Arquivada: {fmt_date(os_arquivada['arquivada_em'], True)}")
            
            st.markdown("**📊 Status**")
            st.write(f"Status: {os_arquivada['status']}")            
        
        st.markdown("---")
        
        # Problema relatado
        st.markdown("**🔧 Problema Relatado**")
        st.text_area(
            "Problema",
            value=os_arquivada["detalhes_servico"],
            height=100,
            disabled=True,
            key=f"problema_{os_id}_{unique_id}"
        )
        
        # Serviço realizado
        st.markdown("**🛠️ Serviço Realizado**")
        st.text_area(
            "Serviço",
            value=os_arquivada.get("servico_realizado") or "Não informado",
            height=100,
            disabled=True,
            key=f"servico_{os_id}_{unique_id}"
        )
        
        # Observações
        if os_arquivada.get("observacoes"):
            st.markdown("**📝 Observações**")
            st.text_area(
                "Observações",
                value=os_arquivada["observacoes"],
                height=80,
                disabled=True,
                key=f"obs_{os_id}_{unique_id}"
            )
        
        # Senha do aparelho
        if os_arquivada.get("senha_tipo") and os_arquivada["senha_tipo"] != "Sem senha":
            st.markdown("**🔒 Senha do Aparelho**")
            st.write(f"Tipo: {os_arquivada['senha_tipo']}")
            if os_arquivada.get("senha_padrao"):
                st.html(render_pattern_grid(os_arquivada["senha_padrao"]))
            if os_arquivada.get("senha_tela"):
                st.write(f"Senha: {os_arquivada['senha_tela']}")
        
        st.markdown("---")
        
        # Botões com keys baseadas apenas no OS_ID
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("📋 Gerar mensagem WhatsApp", key=f"w_{os_id}_{contexto}", width="stretch"):
                msg = build_whatsapp_message(os_arquivada)
                st.code(msg, language=None)
                st.caption("Copie e cole no WhatsApp")        
        
            if st.button("✖️ Fechar", key=f"f_{os_id}_{contexto}", width="stretch"):
                st.session_state[f"view_arquivada_{os_id}"] = False
                st.rerun()

        with col_btn2:
            # EXCLUSÃO PERMANENTE PARA OS ARQUIVADA            
            confirmar_exclusao = st.checkbox(
                "Confirmar exclusão",
                key=f"confirm_delete_arq_{os_id}_{contexto}",
                help="Esta ação não pode ser desfeita. Todos os dados serão perdidos."
            )
            
            if st.button(
                "💣 Excluir Permanentemente",
                disabled=not confirmar_exclusao,
                key=f"delete_arq_{os_id}_{contexto}",
                help="Exclui permanentemente esta OS arquivada",
                width='stretch'
            ):
                try:
                    excluir_os_arquivada(os_id)
                    st.success("OS arquivada excluída permanentemente!")
                    st.session_state[f"view_arquivada_{os_id}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir OS arquivada: {str(e)}")