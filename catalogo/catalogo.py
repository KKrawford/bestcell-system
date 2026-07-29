import streamlit as st
import uuid
from datetime import datetime, date

from .database import (
    inserir_iphone, buscar_iphones, buscar_iphone_por_id,
    atualizar_iphone, excluir_iphone,
    inserir_android, buscar_androids, buscar_android_por_id,
    atualizar_android, excluir_android,
    inserir_perfume, buscar_perfumes, buscar_perfume_por_id,
    atualizar_perfume, excluir_perfume,
    inserir_pod, buscar_pods, buscar_pod_por_id,
    atualizar_pod, excluir_pod,
)
from .utils import calcular_parcelas, calcular_juros_atraso
from .view import exibir_iphones, exibir_androids, exibir_perfumes, exibir_pods


def app():
    st.subheader("📋 Catálogo de Produtos")

    tab1, tab2, tab3 = st.tabs([
        "🏷️ Tabela de Preços",
        "📱 Simulador de Vendas",
        "📅 Calculadora de Juros",        
    ])

    # ======================================================
    # TAB 1: CATÁLOGO
    # ======================================================
    with tab1:
        st.subheader("🏷️ Tabela de Preços")

        cat_tab1, cat_tab2, cat_tab3, cat_tab4 = st.tabs([
            "🍎 iPhones",
            "🤖 Androids",
            "🌸 Perfumes",
            "💨 PODs",
        ])

        # --------------------------------------------------
        # IPHONES
        # --------------------------------------------------
        with cat_tab1:
            col_lista, col_form = st.columns([3, 2])

            with col_lista:
                st.markdown("##### iPhones")
                apenas_disponiveis = st.toggle(
                    "Mostrar apenas disponíveis",
                    value=False,
                    key="toggle_iphones",
                )
                iphones = buscar_iphones(apenas_disponiveis=apenas_disponiveis)
                exibir_iphones(iphones)

            with col_form:
                st.markdown("##### Gerenciar iPhone")

                opcao_ip = st.radio(
                    "Ação", ["Cadastrar", "Editar", "Excluir"],
                    horizontal=True, key="radio_iphone",
                )

                if opcao_ip == "Cadastrar":
                    modelo_ip      = st.text_input("Modelo (ex: iPhone 13)", key="ip_modelo")
                    armazenamento_ip = st.selectbox(
                        "Armazenamento",
                        ["64GB", "128GB", "256GB", "512GB", "1TB"],
                        key="ip_arm",
                    )
                    cor_ip         = st.text_input("Cor", key="ip_cor")
                    disponivel_ip  = st.toggle("Disponível na loja", value=False, key="ip_disp")
                    bateria_ip     = None
                    if disponivel_ip:
                        bateria_ip = st.number_input(
                            "Bateria (%)", min_value=0, max_value=100,
                            value=100, step=1, key="ip_bat",
                        )
                    preco_ip       = st.number_input(
                        "Preço à vista (R$)", min_value=0.0,
                        step=50.0, format="%.2f", key="ip_preco",
                    )
                    obs_ip         = st.text_area("Observações", key="ip_obs", height=80)

                    if st.button("💾 Cadastrar iPhone", key="btn_cad_ip"):
                        if not modelo_ip or not cor_ip or preco_ip <= 0:
                            st.warning("Preencha modelo, cor e preço.")
                        else:
                            inserir_iphone({
                                "id":            str(uuid.uuid4()),
                                "modelo":        modelo_ip,
                                "armazenamento": armazenamento_ip,
                                "cor":           cor_ip,
                                "bateria":       bateria_ip,
                                "disponivel":    int(disponivel_ip),
                                "preco_avista":  preco_ip,
                                "observacoes":   obs_ip or None,
                                "created_at":    datetime.now().isoformat(),
                            })
                            st.success("iPhone cadastrado com sucesso!")
                            st.rerun()

                elif opcao_ip == "Editar":
                    iphones_todos = buscar_iphones()
                    if not iphones_todos:
                        st.info("Nenhum iPhone cadastrado.")
                    else:
                        opcoes_ip = {
                            f"{a['modelo']} {a['armazenamento']} {a['cor']}": a["id"]
                            for a in iphones_todos
                        }
                        sel_ip = st.selectbox("Selecione o iPhone", list(opcoes_ip.keys()), key="ip_edit_sel")
                        ip = buscar_iphone_por_id(opcoes_ip[sel_ip])

                        if ip:
                            modelo_ipe       = st.text_input("Modelo", value=ip["modelo"], key="ip_edit_modelo")
                            arm_opcoes       = ["64GB", "128GB", "256GB", "512GB", "1TB"]
                            arm_idx          = arm_opcoes.index(ip["armazenamento"]) if ip["armazenamento"] in arm_opcoes else 1
                            armazenamento_ipe = st.selectbox("Armazenamento", arm_opcoes, index=arm_idx, key="ip_edit_arm")
                            cor_ipe          = st.text_input("Cor", value=ip["cor"], key="ip_edit_cor")
                            disponivel_ipe   = st.toggle("Disponível na loja", value=bool(ip["disponivel"]), key="ip_edit_disp")
                            bateria_ipe      = None
                            if disponivel_ipe:
                                bateria_ipe = st.number_input(
                                    "Bateria (%)", min_value=0, max_value=100,
                                    value=ip["bateria"] or 100, step=1, key="ip_edit_bat",
                                )
                            preco_ipe        = st.number_input(
                                "Preço à vista (R$)", min_value=0.0,
                                value=ip["preco_avista"], step=50.0,
                                format="%.2f", key="ip_edit_preco",
                            )
                            obs_ipe          = st.text_area("Observações", value=ip["observacoes"] or "", key="ip_edit_obs", height=80)

                            if st.button("💾 Salvar Alterações", key="btn_salvar_ip"):
                                atualizar_iphone(ip["id"], {
                                    "modelo":        modelo_ipe,
                                    "armazenamento": armazenamento_ipe,
                                    "cor":           cor_ipe,
                                    "bateria":       bateria_ipe,
                                    "disponivel":    int(disponivel_ipe),
                                    "preco_avista":  preco_ipe,
                                    "observacoes":   obs_ipe or None,
                                })
                                st.success("iPhone atualizado com sucesso!")
                                st.rerun()

                elif opcao_ip == "Excluir":
                    iphones_todos = buscar_iphones()
                    if not iphones_todos:
                        st.info("Nenhum iPhone cadastrado.")
                    else:
                        opcoes_ip = {
                            f"{a['modelo']} {a['armazenamento']} {a['cor']}": a["id"]
                            for a in iphones_todos
                        }
                        sel_ip = st.selectbox("Selecione o iPhone", list(opcoes_ip.keys()), key="ip_del_sel")
                        st.warning(f"Tem certeza que deseja excluir **{sel_ip}**?")
                        if st.button("🗑️ Confirmar Exclusão", key="btn_del_ip"):
                            excluir_iphone(opcoes_ip[sel_ip])
                            st.success("iPhone excluído com sucesso!")
                            st.rerun()

        # --------------------------------------------------
        # ANDROIDS
        # --------------------------------------------------
        with cat_tab2:
            col_lista, col_form = st.columns([3, 2])

            with col_lista:
                st.markdown("##### Androids disponíveis")
                androids = buscar_androids()
                exibir_androids(androids)

            with col_form:
                st.markdown("##### Gerenciar Android")

                opcao_and = st.radio(
                    "Ação", ["Cadastrar", "Editar", "Excluir"],
                    horizontal=True, key="radio_android",
                )

                if opcao_and == "Cadastrar":
                    marca_and  = st.text_input("Marca", key="and_marca")
                    modelo_and = st.text_input("Modelo", key="and_modelo")
                    ram_and    = st.text_input("RAM (ex: 6GB)", key="and_ram")
                    arm_and    = st.text_input("Armazenamento (ex: 128GB)", key="and_arm")
                    estado_and = st.selectbox(
                        "Estado", ["novo", "usado"],
                        format_func=lambda x: x.capitalize(),
                        key="and_estado",
                    )
                    preco_and  = st.number_input(
                        "Preço à vista (R$)", min_value=0.0,
                        step=50.0, format="%.2f", key="and_preco",
                    )
                    obs_and    = st.text_area("Observações", key="and_obs", height=80)

                    if st.button("💾 Cadastrar Android", key="btn_cad_and"):
                        if not marca_and or not modelo_and or not ram_and or not arm_and or preco_and <= 0:
                            st.warning("Preencha todos os campos obrigatórios.")
                        else:
                            inserir_android({
                                "id":            str(uuid.uuid4()),
                                "marca":         marca_and,
                                "modelo":        modelo_and,
                                "ram":           ram_and,
                                "armazenamento": arm_and,
                                "estado":        estado_and,
                                "preco_avista":  preco_and,
                                "observacoes":   obs_and or None,
                                "created_at":    datetime.now().isoformat(),
                            })
                            st.success("Android cadastrado com sucesso!")
                            st.rerun()

                elif opcao_and == "Editar":
                    androids_lista = buscar_androids()
                    if not androids_lista:
                        st.info("Nenhum Android cadastrado.")
                    else:
                        opcoes_and = {
                            f"{a['marca']} {a['modelo']} {a['ram']} {a['armazenamento']} ({a['estado']})": a["id"]
                            for a in androids_lista
                        }
                        sel_and = st.selectbox("Selecione o Android", list(opcoes_and.keys()), key="and_edit_sel")
                        and_ap  = buscar_android_por_id(opcoes_and[sel_and])

                        if and_ap:
                            marca_ande  = st.text_input("Marca", value=and_ap["marca"], key="and_edit_marca")
                            modelo_ande = st.text_input("Modelo", value=and_ap["modelo"], key="and_edit_modelo")
                            ram_ande    = st.text_input("RAM", value=and_ap["ram"], key="and_edit_ram")
                            arm_ande    = st.text_input("Armazenamento", value=and_ap["armazenamento"], key="and_edit_arm")
                            est_opcoes  = ["novo", "usado"]
                            estado_ande = st.selectbox(
                                "Estado", est_opcoes,
                                index=est_opcoes.index(and_ap["estado"]),
                                format_func=lambda x: x.capitalize(),
                                key="and_edit_estado",
                            )
                            preco_ande  = st.number_input(
                                "Preço à vista (R$)", min_value=0.0,
                                value=and_ap["preco_avista"], step=50.0,
                                format="%.2f", key="and_edit_preco",
                            )
                            obs_ande    = st.text_area("Observações", value=and_ap["observacoes"] or "", key="and_edit_obs", height=80)

                            if st.button("💾 Salvar Alterações", key="btn_salvar_and"):
                                atualizar_android(and_ap["id"], {
                                    "marca":         marca_ande,
                                    "modelo":        modelo_ande,
                                    "ram":           ram_ande,
                                    "armazenamento": arm_ande,
                                    "estado":        estado_ande,
                                    "preco_avista":  preco_ande,
                                    "observacoes":   obs_ande or None,
                                })
                                st.success("Android atualizado com sucesso!")
                                st.rerun()

                elif opcao_and == "Excluir":
                    androids_lista = buscar_androids()
                    if not androids_lista:
                        st.info("Nenhum Android cadastrado.")
                    else:
                        opcoes_and = {
                            f"{a['marca']} {a['modelo']} {a['ram']} {a['armazenamento']} ({a['estado']})": a["id"]
                            for a in androids_lista
                        }
                        sel_and = st.selectbox("Selecione o Android", list(opcoes_and.keys()), key="and_del_sel")
                        st.warning(f"Tem certeza que deseja excluir **{sel_and}**?")
                        if st.button("🗑️ Confirmar Exclusão", key="btn_del_and"):
                            excluir_android(opcoes_and[sel_and])
                            st.success("Android excluído com sucesso!")
                            st.rerun()

        # --------------------------------------------------
        # PERFUMES
        # --------------------------------------------------
        with cat_tab3:
            col_lista, col_form = st.columns([3, 2])

            with col_lista:
                st.markdown("##### Perfumes disponíveis")
                perfumes = buscar_perfumes()
                exibir_perfumes(perfumes)

            with col_form:
                st.markdown("##### Gerenciar perfume")

                opcao_perf = st.radio(
                    "Ação", ["Cadastrar", "Editar", "Excluir"],
                    horizontal=True, key="radio_perfume",
                )

                if opcao_perf == "Cadastrar":
                    marca_p = st.text_input("Marca", key="perf_marca")
                    nome_p  = st.text_input("Nome", key="perf_nome")
                    preco_p = st.number_input(
                        "Preço (R$)", min_value=0.0,
                        step=10.0, format="%.2f", key="perf_preco",
                    )
                    obs_p   = st.text_area("Observações", key="perf_obs", height=80)

                    if st.button("💾 Cadastrar Perfume", key="btn_cad_perf"):
                        if not marca_p or not nome_p or preco_p <= 0:
                            st.warning("Preencha marca, nome e preço.")
                        else:
                            inserir_perfume({
                                "id":         str(uuid.uuid4()),
                                "marca":      marca_p,
                                "nome":       nome_p,
                                "preco":      preco_p,
                                "observacoes": obs_p or None,
                                "created_at": datetime.now().isoformat(),
                            })
                            st.success("Perfume cadastrado com sucesso!")
                            st.rerun()

                elif opcao_perf == "Editar":
                    perfumes_lista = buscar_perfumes()
                    if not perfumes_lista:
                        st.info("Nenhum perfume cadastrado.")
                    else:
                        opcoes_perf = {f"{p['marca']} — {p['nome']}": p["id"] for p in perfumes_lista}
                        sel_perf    = st.selectbox("Selecione o perfume", list(opcoes_perf.keys()), key="perf_edit_sel")
                        perf        = buscar_perfume_por_id(opcoes_perf[sel_perf])

                        if perf:
                            marca_pe = st.text_input("Marca", value=perf["marca"], key="perf_edit_marca")
                            nome_pe  = st.text_input("Nome", value=perf["nome"], key="perf_edit_nome")
                            preco_pe = st.number_input(
                                "Preço (R$)", min_value=0.0, value=perf["preco"],
                                step=10.0, format="%.2f", key="perf_edit_preco",
                            )
                            obs_pe   = st.text_area("Observações", value=perf["observacoes"] or "", key="perf_edit_obs", height=80)

                            if st.button("💾 Salvar Alterações", key="btn_salvar_perf"):
                                atualizar_perfume(perf["id"], {
                                    "marca":       marca_pe,
                                    "nome":        nome_pe,
                                    "preco":       preco_pe,
                                    "observacoes": obs_pe or None,
                                })
                                st.success("Perfume atualizado com sucesso!")
                                st.rerun()

                elif opcao_perf == "Excluir":
                    perfumes_lista = buscar_perfumes()
                    if not perfumes_lista:
                        st.info("Nenhum perfume cadastrado.")
                    else:
                        opcoes_perf = {f"{p['marca']} — {p['nome']}": p["id"] for p in perfumes_lista}
                        sel_perf    = st.selectbox("Selecione o perfume", list(opcoes_perf.keys()), key="perf_del_sel")
                        st.warning(f"Tem certeza que deseja excluir **{sel_perf}**?")
                        if st.button("🗑️ Confirmar Exclusão", key="btn_del_perf"):
                            excluir_perfume(opcoes_perf[sel_perf])
                            st.success("Perfume excluído com sucesso!")
                            st.rerun()

        # --------------------------------------------------
        # PODS
        # --------------------------------------------------
        with cat_tab4:
            col_lista, col_form = st.columns([3, 2])

            with col_lista:
                st.markdown("##### PODs disponíveis")
                pods = buscar_pods()
                exibir_pods(pods)

            with col_form:
                st.markdown("##### Gerenciar POD")

                opcao_pod = st.radio(
                    "Ação", ["Cadastrar", "Editar", "Excluir"],
                    horizontal=True, key="radio_pod",
                )

                if opcao_pod == "Cadastrar":
                    marca_pod = st.text_input("Marca", key="pod_marca")
                    nome_pod  = st.text_input("Nome", key="pod_nome")
                    puffs_pod = st.number_input(
                        "Quantidade de Puffs", min_value=0,
                        step=500, key="pod_puffs",
                    )
                    preco_pod = st.number_input(
                        "Preço (R$)", min_value=0.0,
                        step=5.0, format="%.2f", key="pod_preco",
                    )
                    obs_pod   = st.text_area("Observações", key="pod_obs", height=80)

                    if st.button("💾 Cadastrar POD", key="btn_cad_pod"):
                        if not marca_pod or not nome_pod or not puffs_pod or preco_pod <= 0:
                            st.warning("Preencha marca, nome, quantidade de Puffs e preço.")
                        else:
                            inserir_pod({
                                "id":          str(uuid.uuid4()),
                                "marca":       marca_pod,
                                "nome":        nome_pod,
                                "puffs":       puffs_pod,
                                "preco":       preco_pod,
                                "observacoes": obs_pod or None,
                                "created_at":  datetime.now().isoformat(),
                            })
                            st.success("POD cadastrado com sucesso!")
                            st.rerun()

                elif opcao_pod == "Editar":
                    pods_lista = buscar_pods()
                    if not pods_lista:
                        st.info("Nenhum POD cadastrado.")
                    else:
                        opcoes_pod = {f"{p['marca']} — {p['nome']}": p["id"] for p in pods_lista}
                        sel_pod    = st.selectbox("Selecione o POD", list(opcoes_pod.keys()), key="pod_edit_sel")
                        pod        = buscar_pod_por_id(opcoes_pod[sel_pod])

                        if pod:
                            marca_pode = st.text_input("Marca", value=pod["marca"], key="pod_edit_marca")
                            nome_pode  = st.text_input("Nome", value=pod["nome"], key="pod_edit_nome")
                            puffs_pode = st.number_input(
                                "Puffs", min_value=0, value=pod["puffs"],
                                step=500, key="pod_edit_puffs",
                            )
                            preco_pode = st.number_input(
                                "Preço (R$)", min_value=0.0, value=pod["preco"],
                                step=5.0, format="%.2f", key="pod_edit_preco",
                            )
                            obs_pode   = st.text_area("Observações", value=pod["observacoes"] or "", key="pod_edit_obs", height=80)

                            if st.button("💾 Salvar Alterações", key="btn_salvar_pod"):
                                atualizar_pod(pod["id"], {
                                    "marca":       marca_pode,
                                    "nome":        nome_pode,
                                    "puffs":       puffs_pode,
                                    "preco":       preco_pode,
                                    "observacoes": obs_pode or None,
                                })
                                st.success("POD atualizado com sucesso!")
                                st.rerun()

                elif opcao_pod == "Excluir":
                    pods_lista = buscar_pods()
                    if not pods_lista:
                        st.info("Nenhum POD cadastrado.")
                    else:
                        opcoes_pod = {f"{p['marca']} — {p['nome']}": p["id"] for p in pods_lista}
                        sel_pod    = st.selectbox("Selecione o POD", list(opcoes_pod.keys()), key="pod_del_sel")
                        st.warning(f"Tem certeza que deseja excluir **{sel_pod}**?")
                        if st.button("🗑️ Confirmar Exclusão", key="btn_del_pod"):
                            excluir_pod(opcoes_pod[sel_pod])
                            st.success("POD excluído com sucesso!")
                            st.rerun()


    # ======================================================
    # TAB 2: SIMULADOR DE VENDAS
    # ======================================================
    with tab2:
        st.subheader("📱 Simulador de Vendas")

        col1, col2 = st.columns(2)

        with col1:
            valor_avista = st.number_input(
                "Valor à vista (R$)",
                min_value=0.0, value=0.0, step=50.0,
                format="%.2f", key="sim_valor_avista",
            )
            juros = st.number_input(
                "Juros (%)",
                min_value=0.0, value=20.0, step=1.0,
                format="%.1f", key="sim_juros",
            )

        with col2:
            entrada = st.number_input(
                "Entrada (R$)",
                min_value=0.0, value=0.0, step=50.0,
                format="%.2f", key="sim_entrada",
            )
            num_parcelas = st.number_input(
                "Quantidade de parcelas",
                min_value=1, max_value=48, value=10,
                step=1, key="sim_parcelas",
            )

        st.divider()

        if valor_avista > 0:
            resultado = calcular_parcelas(valor_avista, juros, entrada, num_parcelas)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Valor com Juros", f"R$ {resultado['valor_com_juros']:.2f}")
            with col2:
                st.metric("Valor Financiado", f"R$ {resultado['valor_financiado']:.2f}")
            with col3:
                st.metric(
                    "Valor da Parcela",
                    f"R$ {resultado['valor_parcela']:.2f}",
                    help=f"{num_parcelas}x de R$ {resultado['valor_parcela']:.2f}"
                )
            with col4:
                st.metric("Total Pago", f"R$ {resultado['total_pago']:.2f}")
        else:
            st.info("Informe o valor à vista para calcular.")

    # ======================================================
    # TAB 3: CALCULADORA DE JUROS
    # ======================================================
    with tab3:
        st.subheader("📅 Calculadora de Juros por Atraso")

        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data de vencimento",
                value=date.today(), format="DD/MM/YYYY",
                key="juros_inicio",
            )
        with col2:
            data_fim = st.date_input(
                "Data atual / negociação",
                value=date.today(), format="DD/MM/YYYY",
                key="juros_fim",
            )

        st.divider()

        if data_fim > data_inicio:
            resultado = calcular_juros_atraso(data_inicio, data_fim)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dias em atraso", resultado["dias"])
            with col2:
                st.metric("Taxa diária", f"R$ {resultado['taxa_diaria']:.2f}")
            with col3:
                st.metric("Total de Juros", f"R$ {resultado['total_juros']:.2f}")
        elif data_fim == data_inicio:
            st.info("Selecione um intervalo de datas para calcular os juros.")
        else:
            st.warning("A data final deve ser posterior à data de vencimento.")

    
