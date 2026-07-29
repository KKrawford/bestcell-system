import streamlit as st

from diagnostico.database import (
    init_db,
    inserir_diagnostico,
    buscar_diagnosticos,
    buscar_diagnostico_por_id,
    buscar_modelo_por_codigo,
    cadastrar_modelo_aparelho,
    excluir_diagnostico,
)

from diagnostico.utils import (
    verificar_dispositivo_adb,
    coletar_identificacao_aparelho_adb,
    montar_nome_aparelho,
    executar_diagnostico_software,
    executar_diagnostico_hardware,
)

from diagnostico.view import (
    render_adb_status,
    render_card_diagnostico,
    render_historico_tabela,
    fmt_tipo,
    fmt_data_iso,
)


def app():
    init_db()

    st.title("🔬 Diagnóstico de Aparelhos")
    st.caption("Análise via ADB para segurança, software, hardware e placa.")

    tab_software, tab_hardware, tab_historico = st.tabs([
        "🛡️ Software",
        "🔬 Hardware",
        "📚 Histórico",
    ])

    # ======================================================
    # ABA SOFTWARE
    # ======================================================
    with tab_software:
        st.subheader("Diagnóstico de Software / Segurança")
        st.write(
            "Use esta análise para verificar apps de terceiros, permissões críticas, "
            "apps suspeitos e possíveis ameaças instaladas no aparelho."
        )

        with st.expander("Status da conexão ADB", expanded=True):
            if st.button("Verificar aparelho conectado", key="btn_check_adb_software"):
                status = verificar_dispositivo_adb()
                render_adb_status(status)
            else:
                st.caption("Conecte o celular via USB, ative a depuração USB e clique para verificar.")

        st.markdown("---")

        with st.form("form_diagnostico_software"):
            cliente = st.text_input("Cliente")
            aparelho = st.text_input("Aparelho / Modelo")
            observacao = st.text_area("Observações iniciais", height=90)

            executar = st.form_submit_button(
                "Executar diagnóstico de software",
                width="stretch",
                type="primary"
            )

        diagnostico_software = None

        if executar:
            conexao = verificar_dispositivo_adb()

            if not conexao["ok"]:
                render_adb_status(conexao)

            else:
                with st.spinner("Identificando o aparelho conectado..."):
                    identificacao = coletar_identificacao_aparelho_adb()

                modelo_tecnico = identificacao.get("modelo_tecnico", "").strip()

                if (
                    not modelo_tecnico
                    or modelo_tecnico == "Não identificado"
                ):
                    st.error(
                        "O Android não informou um modelo técnico válido. "
                        "O diagnóstico não foi iniciado."
                    )

                else:
                    modelo_cadastrado = buscar_modelo_por_codigo(
                        modelo_tecnico
                    )

                    if modelo_cadastrado:
                        modelo_comercial = modelo_cadastrado[
                            "modelo_comercial"
                        ]

                        nome_aparelho = montar_nome_aparelho(
                            identificacao,
                            modelo_comercial
                        )

                        identificacao["modelo_comercial"] = modelo_comercial
                        identificacao["nome_exibicao"] = nome_aparelho

                        with st.spinner(
                            "Executando diagnóstico de software via ADB..."
                        ):
                            diagnostico_software = executar_diagnostico_software(
                                cliente=cliente,
                                aparelho=nome_aparelho,
                                identificacao_adb=identificacao
                            )

                    else:
                        st.session_state["modelo_pendente_software"] = {
                            "cliente": cliente,
                            "observacao": observacao,
                            "aparelho_informado": aparelho,
                            "identificacao": identificacao,
                        }

        modelo_pendente = st.session_state.get(
            "modelo_pendente_software"
        )

        if modelo_pendente:
            identificacao = modelo_pendente["identificacao"]

            st.warning(
                "Este modelo ainda não possui um nome comercial "
                "cadastrado. Informe-o uma única vez para continuar."
            )

            with st.container(border=True):
                st.markdown("### Modelo identificado pelo ADB")

                col1, col2 = st.columns(2)

                with col1:
                    st.caption("Fabricante")
                    st.write(identificacao.get("fabricante"))

                with col2:
                    st.caption("Modelo técnico / Variante")
                    st.write(identificacao.get("modelo_tecnico"))

                st.caption("Código interno do dispositivo")
                st.write(
                    identificacao.get("dispositivo")
                    or "Não informado pelo Android"
                )

            sugestao = (
                modelo_pendente.get("aparelho_informado")
                or identificacao.get("nome_comercial_adb")
                or ""
            )

            with st.form("form_cadastro_modelo_software"):
                modelo_comercial = st.text_input(
                    "Nome comercial do aparelho",
                    value=sugestao,
                    placeholder="Ex.: Galaxy S24 FE"
                )

                confirmar_modelo = st.form_submit_button(
                    "Cadastrar modelo e continuar diagnóstico",
                    type="primary",
                    width="stretch"
                )

            if confirmar_modelo:
                if not modelo_comercial.strip():
                    st.error("Informe o nome comercial do aparelho.")

                else:
                    try:
                        cadastrar_modelo_aparelho(
                            fabricante=identificacao.get("fabricante"),
                            modelo_tecnico=identificacao.get(
                                "modelo_tecnico"
                            ),
                            modelo_comercial=modelo_comercial
                        )

                        nome_aparelho = montar_nome_aparelho(
                            identificacao,
                            modelo_comercial
                        )

                        identificacao["modelo_comercial"] = (
                            modelo_comercial.strip()
                        )
                        identificacao["nome_exibicao"] = nome_aparelho

                        with st.spinner(
                            "Modelo cadastrado. Executando diagnóstico..."
                        ):
                            diagnostico_software = (
                                executar_diagnostico_software(
                                    cliente=modelo_pendente["cliente"],
                                    aparelho=nome_aparelho,
                                    identificacao_adb=identificacao
                                )
                            )

                        observacao_pendente = modelo_pendente[
                            "observacao"
                        ].strip()

                        if observacao_pendente:
                            diagnostico_software["resultado_json"][
                                "observacao_inicial"
                            ] = observacao_pendente

                        del st.session_state[
                            "modelo_pendente_software"
                        ]

                    except Exception as erro:
                        st.error(
                            f"Não foi possível cadastrar o modelo: {erro}"
                        )

        if diagnostico_software:
            if observacao.strip():
                diagnostico_software["resultado_json"][
                    "observacao_inicial"
                ] = observacao.strip()

            if diagnostico_software["status"] == "concluido":
                inserir_diagnostico(diagnostico_software)

                st.success(
                    "Diagnóstico finalizado e salvo no histórico."
                )

            else:
                st.error(
                    "Não foi possível executar o diagnóstico de software."
                )
                st.caption(
                    "O diagnóstico não foi salvo porque a coleta "
                    "não foi concluída."
                )

            render_card_diagnostico(
                diagnostico_software,
                key_prefix=(
                    f"software_exec_{diagnostico_software['id']}"
                )
            )

    # ======================================================
    # ABA HARDWARE
    # ======================================================
    with tab_hardware:
        st.subheader("Diagnóstico de Hardware / Placa")
        st.write(
            "Use esta análise para coletar dados de bateria, sensores, temperatura, "
            "logs de crash, reinícios e possíveis falhas de componentes."
        )

        with st.expander("Status da conexão ADB", expanded=True):
            if st.button("Verificar aparelho conectado", key="btn_check_adb_hardware"):
                status = verificar_dispositivo_adb()
                render_adb_status(status)
            else:
                st.caption("Conecte o celular via USB, ative a depuração USB e clique para verificar.")

        st.markdown("---")

        with st.form("form_diagnostico_hardware"):
            cliente = st.text_input("Cliente")
            aparelho = st.text_input("Aparelho / Modelo")
            observacao = st.text_area("Observações iniciais", height=90)

            executar = st.form_submit_button(
                "Executar diagnóstico de hardware",
                width="stretch",
                type="primary"
            )

        diagnostico_hardware = None

        if executar:
            conexao = verificar_dispositivo_adb()

            if not conexao["ok"]:
                render_adb_status(conexao)

            else:
                with st.spinner("Identificando o aparelho conectado..."):
                    identificacao = coletar_identificacao_aparelho_adb()

                modelo_tecnico = identificacao.get(
                    "modelo_tecnico",
                    ""
                ).strip()

                if (
                    not modelo_tecnico
                    or modelo_tecnico == "Não identificado"
                ):
                    st.error(
                        "O Android não informou um modelo técnico válido. "
                        "O diagnóstico não foi iniciado."
                    )

                else:
                    modelo_cadastrado = buscar_modelo_por_codigo(
                        modelo_tecnico
                    )

                    if modelo_cadastrado:
                        modelo_comercial = modelo_cadastrado[
                            "modelo_comercial"
                        ]

                        nome_aparelho = montar_nome_aparelho(
                            identificacao,
                            modelo_comercial
                        )

                        identificacao["modelo_comercial"] = modelo_comercial
                        identificacao["nome_exibicao"] = nome_aparelho

                        with st.spinner(
                            "Executando diagnóstico de hardware via ADB..."
                        ):
                            diagnostico_hardware = (
                                executar_diagnostico_hardware(
                                    cliente=cliente,
                                    aparelho=nome_aparelho,
                                    identificacao_adb=identificacao
                                )
                            )

                    else:
                        st.session_state["modelo_pendente_hardware"] = {
                            "cliente": cliente,
                            "observacao": observacao,
                            "aparelho_informado": aparelho,
                            "identificacao": identificacao,
                        }

        modelo_pendente = st.session_state.get(
            "modelo_pendente_hardware"
        )

        if modelo_pendente:
            identificacao = modelo_pendente["identificacao"]

            st.warning(
                "Este modelo ainda não possui um nome comercial "
                "cadastrado. Informe-o uma única vez para continuar."
            )

            with st.container(border=True):
                st.markdown("### Modelo identificado pelo ADB")

                col1, col2 = st.columns(2)

                with col1:
                    st.caption("Fabricante")
                    st.write(identificacao.get("fabricante"))

                with col2:
                    st.caption("Modelo técnico / Variante")
                    st.write(identificacao.get("modelo_tecnico"))

                st.caption("Código interno do dispositivo")
                st.write(
                    identificacao.get("dispositivo")
                    or "Não informado pelo Android"
                )

            sugestao = (
                modelo_pendente.get("aparelho_informado")
                or identificacao.get("nome_comercial_adb")
                or ""
            )

            with st.form("form_cadastro_modelo_hardware"):
                modelo_comercial = st.text_input(
                    "Nome comercial do aparelho",
                    value=sugestao,
                    placeholder="Ex.: Galaxy S24 FE"
                )

                confirmar_modelo = st.form_submit_button(
                    "Cadastrar modelo e continuar diagnóstico",
                    type="primary",
                    width="stretch"
                )

            if confirmar_modelo:
                if not modelo_comercial.strip():
                    st.error("Informe o nome comercial do aparelho.")

                else:
                    try:
                        cadastrar_modelo_aparelho(
                            fabricante=identificacao.get("fabricante"),
                            modelo_tecnico=identificacao.get(
                                "modelo_tecnico"
                            ),
                            modelo_comercial=modelo_comercial
                        )

                        nome_aparelho = montar_nome_aparelho(
                            identificacao,
                            modelo_comercial
                        )

                        identificacao["modelo_comercial"] = (
                            modelo_comercial.strip()
                        )
                        identificacao["nome_exibicao"] = nome_aparelho

                        with st.spinner(
                            "Modelo cadastrado. Executando diagnóstico..."
                        ):
                            diagnostico_hardware = (
                                executar_diagnostico_hardware(
                                    cliente=modelo_pendente["cliente"],
                                    aparelho=nome_aparelho,
                                    identificacao_adb=identificacao
                                )
                            )

                        observacao_pendente = modelo_pendente[
                            "observacao"
                        ].strip()

                        if observacao_pendente:
                            diagnostico_hardware["resultado_json"][
                                "observacao_inicial"
                            ] = observacao_pendente

                        del st.session_state[
                            "modelo_pendente_hardware"
                        ]

                    except Exception as erro:
                        st.error(
                            f"Não foi possível cadastrar o modelo: {erro}"
                        )

        if diagnostico_hardware:
            if observacao.strip():
                diagnostico_hardware["resultado_json"][
                    "observacao_inicial"
                ] = observacao.strip()

            if diagnostico_hardware["status"] == "concluido":
                inserir_diagnostico(diagnostico_hardware)

                st.success(
                    "Diagnóstico finalizado e salvo no histórico."
                )

            else:
                st.error(
                    "Não foi possível executar o diagnóstico de hardware."
                )
                st.caption(
                    "O diagnóstico não foi salvo porque a coleta "
                    "não foi concluída."
                )

            render_card_diagnostico(
                diagnostico_hardware,
                key_prefix=(
                    f"hardware_exec_{diagnostico_hardware['id']}"
                )
            )

    # ======================================================
    # ABA HISTÓRICO
    # ======================================================
    with tab_historico:
        st.subheader("Histórico de Diagnósticos")

        diagnosticos = buscar_diagnosticos()

        render_historico_tabela(diagnosticos)

        if diagnosticos:
            st.markdown("---")

            opcoes = {
                f"{item['cliente']} • {item['aparelho']} • {item['tipo']} • {item['created_at'][:19]}": item["id"]
                for item in diagnosticos
            }

            diagnosticos_por_id = {
                item["id"]: item
                for item in diagnosticos
            }

            def formatar_opcao_historico(item_id):
                item = diagnosticos_por_id[item_id]

                cliente = (item.get("cliente") or "").strip()
                aparelho = (
                    item.get("aparelho")
                    or "Aparelho não identificado"
                )

                cliente_ausente = cliente.lower() in {
                    "",
                    "não informado",
                    "nao informado",
                }

                referencia = (
                    aparelho
                    if cliente_ausente
                    else f"{cliente} • {aparelho}"
                )

                return (
                    f"{referencia} • "
                    f"{fmt_tipo(item.get('tipo'))} • "
                    f"{fmt_data_iso(item.get('created_at'))}"
                )

            diagnostico_id = st.selectbox(
                "Selecionar diagnóstico para visualizar",
                options=list(diagnosticos_por_id),
                format_func=formatar_opcao_historico,
            )