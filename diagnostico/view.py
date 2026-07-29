import json
from pathlib import Path

import pandas as pd
import streamlit as st


# ======================================================
# FORMATADORES
# ======================================================

def fmt_tipo(tipo: str):
    if tipo == "software":
        return "Software / Segurança"

    if tipo == "hardware":
        return "Hardware / Placa"

    return tipo or "-"


def fmt_status(status: str):
    if status == "concluido":
        return "Concluído"

    if status == "erro":
        return "Erro"

    return status or "-"


def fmt_data_iso(valor: str):
    if not valor:
        return "-"

    try:
        return valor[:19].replace("T", " ")
    except Exception:
        return valor


# ======================================================
# COMPONENTES VISUAIS
# ======================================================

def render_adb_status(status: dict):
    if status.get("ok"):
        st.success(status.get("mensagem", "ADB conectado."))
    else:
        st.warning(status.get("mensagem", "ADB não conectado."))

        detalhe = status.get("detalhe")

        if detalhe:
            st.caption(detalhe)

    devices = status.get("devices", [])

    if devices:
        st.dataframe(
            pd.DataFrame(devices),
            width="stretch",
            hide_index=True
        )


def render_resultado_software(resultado: dict):
    st.subheader("Resultado da análise de software")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Ameaças críticas", len(resultado.get("criticos", [])))

    with col2:
        st.metric("Apps suspeitos", len(resultado.get("suspeitos", [])))

    with col3:
        st.metric("Apps analisados", resultado.get("pacotes_total", 0))

    st.info(resultado.get("resumo", "Sem resumo disponível."))

    criticos = resultado.get("criticos", [])
    suspeitos = resultado.get("suspeitos", [])
    seguros = resultado.get("seguros", [])
    permissoes = resultado.get("permissoes_detectadas", [])

    st.markdown("### Ameaças críticas")

    if criticos:
        for app in criticos:
            with st.expander(f"🚨 {app.get('nome')} — {app.get('pacote')}", expanded=True):
                st.write(f"**Explicação:** {app.get('explicacao')}")
                st.write(f"**Risco:** {app.get('risco')}")
                st.warning("Recomendação: confirmar com o cliente e remover o aplicativo se ele não reconhecer.")
    else:
        st.success("Nenhuma ameaça crítica conhecida foi identificada.")

    st.markdown("### Apps suspeitos")

    if suspeitos:
        for app in suspeitos:
            with st.expander(f"⚠️ {app.get('pacote')}", expanded=True):
                st.write(f"**Classificação:** {app.get('nome')}")
                st.write(f"**Explicação:** {app.get('explicacao')}")
                st.write(f"**Risco:** {app.get('risco')}")
    else:
        st.success("Nenhum app suspeito foi identificado por palavra-chave.")

    st.markdown("### Permissões críticas encontradas no laudo")

    if permissoes:
        st.warning("Essas permissões apareceram na coleta do aparelho. Nem sempre indicam vírus, mas merecem atenção.")
        st.dataframe(
            pd.DataFrame(permissoes, columns=["Permissão"]),
            width="stretch",
            hide_index=True
        )
    else:
        st.success("Nenhuma permissão crítica foi destacada na análise inicial.")

    with st.expander("Ver apps comuns / conferência manual", expanded=False):
        if seguros:
            st.dataframe(
                pd.DataFrame(seguros),
                width="stretch",
                hide_index=True
            )
        else:
            st.write("Nenhum app comum listado.")


def render_resultado_hardware(resultado: dict):
    st.subheader("Resultado da análise de hardware")

    dados_bateria = resultado.get("dados_bateria", {})
    achados = resultado.get("achados", [])
    status_geral = resultado.get("status_geral")
    ocorrencias_total = resultado.get("ocorrencias_total", 0)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Situações identificadas", len(achados))

    with col2:
        st.metric("Ocorrências nos logs", ocorrencias_total)

    with col3:
        st.metric("Leituras da bateria", len(dados_bateria))

    resumo = resultado.get("resumo", "Sem resumo disponível.")

    if status_geral == "requer_atencao":
        st.warning(resumo)

    elif status_geral == "observacao":
        st.info(resumo)

    elif status_geral == "sem_indicios":
        st.success(resumo)

    else:
        st.info(resumo)

    st.markdown("### Energia e bateria")

    if dados_bateria:
        df_bateria = pd.DataFrame(
            list(dados_bateria.items()),
            columns=["Item", "Leitura"]
        )

        st.dataframe(
            df_bateria,
            width="stretch",
            hide_index=True,
            column_config={
                "Item": st.column_config.TextColumn(
                    width="medium"
                ),
                "Leitura": st.column_config.TextColumn(
                    width="large"
                ),
            }
        )

        st.caption(
            "As leituras representam o estado do aparelho no momento "
            "da coleta. Valores isolados devem ser confirmados em teste."
        )

    else:
        st.warning(
            "O Android não retornou dados suficientes da bateria."
        )

    st.markdown("### Interpretação dos achados")

    if achados:
        icones = {
            "Crítica": "🚨",
            "Alta": "⚠️",
            "Moderada": "ℹ️",
        }

        for indice, achado in enumerate(achados, start=1):
            gravidade = achado.get("gravidade", "Moderada")
            icone = icones.get(gravidade, "ℹ️")

            titulo = (
                f"{icone} {achado.get('titulo')} · "
                f"{achado.get('componente')}"
            )

            with st.expander(
                titulo,
                expanded=gravidade in {"Crítica", "Alta"}
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Gravidade:** {gravidade}"
                    )

                with col2:
                    st.write(
                        "**Ocorrências encontradas:** "
                        f"{achado.get('quantidade', 0)}"
                    )

                st.write(
                    f"**O que significa:** "
                    f"{achado.get('significado')}"
                )

                st.write(
                    f"**Possíveis causas:** "
                    f"{achado.get('possiveis_causas')}"
                )

                st.write(
                    f"**Como verificar:** "
                    f"{achado.get('recomendacao')}"
                )

                evidencias = achado.get("evidencias", [])

                if evidencias:
                    with st.expander(
                        "Ver evidências técnicas",
                        expanded=False
                    ):
                        st.code(
                            "\n\n".join(evidencias),
                            language=None
                        )

    else:
        st.success(
            "Nenhuma situação com evidência suficiente foi "
            "identificada."
        )

    # Compatibilidade com laudos criados pelo analisador anterior.
    if (
        not achados
        and (
            resultado.get("alertas")
            or resultado.get("erros_componentes")
        )
    ):
        st.warning(
            "Este laudo foi processado por uma versão anterior do "
            "analisador e pode conter falsos positivos. Execute um "
            "novo diagnóstico para obter a interpretação atualizada."
        )


def render_laudo_download(laudo_path: str, key_prefix: str = "laudo"):
    if not laudo_path:
        return

    path = Path(laudo_path)

    if not path.exists():
        st.warning("O caminho do laudo foi salvo, mas o arquivo não foi encontrado no disco.")
        st.caption(laudo_path)
        return

    conteudo = path.read_text(encoding="utf-8", errors="replace")

    st.download_button(
        "Baixar laudo bruto (.txt)",
        data=conteudo,
        file_name=path.name,
        mime="text/plain",
        width="stretch",
        key=f"{key_prefix}_download_laudo"
    )

    with st.expander("Ver laudo bruto", expanded=False):
        st.text_area(
            "Conteúdo bruto coletado via ADB",
            value=conteudo,
            height=400,
            disabled=True,
            key=f"{key_prefix}_texto_laudo"
        )

def render_identificacao_aparelho(item: dict):
    resultado = item.get("resultado_json") or {}
    identificacao = resultado.get("identificacao_adb") or {}

    nome_exibicao = (
        identificacao.get("nome_exibicao")
        or item.get("aparelho")
        or "Aparelho não identificado"
    )

    st.markdown("### Aparelho identificado")

    with st.container(border=True):
        st.markdown(f"## {nome_exibicao}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.caption("Fabricante")
            st.write(
                identificacao.get("fabricante")
                or "Não identificado"
            )

        with col2:
            st.caption("Modelo técnico / Variante")
            st.write(
                identificacao.get("modelo_tecnico")
                or "Não identificado"
            )

        with col3:
            st.caption("Código do dispositivo")
            st.write(
                identificacao.get("dispositivo")
                or "Não informado pelo Android"
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.caption("Android")
            versao = identificacao.get("versao_android") or "-"
            sdk = identificacao.get("nivel_sdk") or "-"

            st.write(f"{versao} · SDK {sdk}")

        with col5:
            st.caption("Produto")
            st.write(
                identificacao.get("nome_produto")
                or "Não informado pelo Android"
            )

        with col6:
            st.caption("Placa / Hardware")

            placa = identificacao.get("placa") or "-"
            hardware = identificacao.get("hardware") or "-"

            st.write(f"{placa} · {hardware}")

        build = identificacao.get("build")

        if build:
            st.caption(f"Build do sistema: {build}")


def render_card_diagnostico(item: dict, key_prefix: str | None = None):
    base_key = key_prefix or f"diagnostico_{item.get('id', 'sem_id')}"
    status = item.get("status")

    cliente = (item.get("cliente") or "").strip()
    cliente_informado = cliente.lower() not in {
        "",
        "não informado",
        "nao informado",
    }

    st.markdown(f"## {fmt_tipo(item.get('tipo'))}")

    render_identificacao_aparelho(item)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption("Cliente")
        st.write(cliente if cliente_informado else "Não informado")

    with col2:
        st.caption("Data do diagnóstico")
        st.write(fmt_data_iso(item.get("created_at")))

    with col3:
        st.caption("Status")

        if status == "concluido":
            st.success(fmt_status(status))
        else:
            st.error(fmt_status(status))

    st.write(item.get("resumo") or "Sem resumo.")

    if item.get("erro"):
        st.warning(item.get("erro"))

    resultado = item.get("resultado_json") or {}

    if item.get("tipo") == "software" and status == "concluido":
        render_resultado_software(resultado)

    elif item.get("tipo") == "hardware" and status == "concluido":
        render_resultado_hardware(resultado)

    elif resultado:
        with st.expander("Detalhes técnicos", expanded=False):
            st.json(resultado)

    render_laudo_download(item.get("laudo_path"), key_prefix=base_key)


def render_historico_tabela(diagnosticos: list[dict]):
    if not diagnosticos:
        st.info("Nenhum diagnóstico salvo até o momento.")
        return

    dados = []

    for item in diagnosticos:
        alertas = item.get("alertas_total", 0)
        status = item.get("status")

        if status == "erro":
            resultado = "Erro na coleta"
        elif alertas:
            resultado = f"{alertas} situação(ões)"
        else:
            resultado = "Sem alertas"

        dados.append({
            "Tipo": fmt_tipo(item.get("tipo")),
            "Cliente": item.get("cliente"),
            "Aparelho": item.get("aparelho"),
            "Resultado": resultado,
            "Data": fmt_data_iso(item.get("created_at")),
        })

    st.dataframe(
        pd.DataFrame(dados),
        width="stretch",
        hide_index=True,
        column_config={
            "Tipo": st.column_config.TextColumn(
                "Diagnóstico",
                width="medium"
            ),
            "Cliente": st.column_config.TextColumn(
                width="medium"
            ),
            "Aparelho": st.column_config.TextColumn(
                width="large"
            ),
            "Resultado": st.column_config.TextColumn(
                width="medium"
            ),
            "Data": st.column_config.TextColumn(
                width="medium"
            ),
        }
    )