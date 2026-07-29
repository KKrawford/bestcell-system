import streamlit as st
import uuid
from datetime import datetime

from .database import (
    init_db,
    # Peças
    inserir_peca, buscar_pecas, buscar_peca_por_id, atualizar_peca, excluir_peca,
    # Capas
    inserir_capa, buscar_capas, buscar_capa_por_id, atualizar_capa, excluir_capa,
    # Películas
    inserir_pelicula, buscar_peliculas, buscar_pelicula_por_id, atualizar_pelicula, excluir_pelicula,
    inserir_compatibilidade, buscar_compatibilidades_por_modelo, buscar_todas_compatibilidades, excluir_compatibilidade,
    atualizar_compatibilidade_peliculas, atualizar_todas_compatibilidades_peliculas,
    # Busca
    buscar_estoque,
    # Funções para dashboard
    contar_produtos_por_tipo, somar_quantidade_total,
    obter_capas_sem_estoque, obter_peliculas_com_estoque_baixo
)
from .utils import sugerir_compatibilidade, obter_modelos_principais,filtrar_valores_validos, calcular_quantidade_total_pelicula
from .view import exibir_pecas, exibir_capas, exibir_capas_dashboard, exibir_peliculas, exibir_busca

def app():
    st.header("📦 Gestão de Estoque")
    
    # Inicializar banco de dados
    init_db()
    
    # Abas principais
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Peças", "Capas", "Películas", "Busca"])
    
    # ======================================================
    # TAB 1: DASHBOARD
    # ======================================================
    with tab1:
        st.subheader("📊 Dashboard de Estoque")
        
        # Obter métricas
        contagem_produtos = contar_produtos_por_tipo()
        quantidade_total = somar_quantidade_total()
        
        # Exibir cards com métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Itens", quantidade_total["geral"])
        
        with col2:
            st.metric("Peças Cadastradas", contagem_produtos["pecas"])
            st.metric("Em Estoque", quantidade_total["pecas"])
        
        with col3:
            st.metric("Capas Cadastradas", contagem_produtos["capas"])
            st.metric("Em Estoque", quantidade_total["capas"])
        
        with col4:
            st.metric("Películas Cadastradas", contagem_produtos["peliculas"])
            st.metric("Em Estoque", quantidade_total["peliculas"])
        
        st.divider()
        
        # Seção informativa - Capas
        st.subheader("🧥 Capas — Cores sem estoque")
        
        capas_sem_estoque, cores_por_modelo = obter_capas_sem_estoque()
        exibir_capas_dashboard(capas_sem_estoque, cores_por_modelo)
        
        st.divider()
        
        # Seção informativa - Películas
        st.subheader("📋 Películas — Estoque baixo")
        
        estoque_minimo = st.slider("Estoque mínimo", 1, 20, 5, key="estoque_minimo")
        
        peliculas_estoque_baixo = obter_peliculas_com_estoque_baixo(estoque_minimo)
        todas_peliculas = buscar_peliculas()

        peliculas_alerta = [
            p for p in peliculas_estoque_baixo
            if calcular_quantidade_total_pelicula(p, todas_peliculas) < estoque_minimo
        ]

        if peliculas_alerta:
            st.info(f"📋 {len(peliculas_alerta)} películas com estoque abaixo de {estoque_minimo} unidades")
            exibir_peliculas(peliculas_alerta)
        else:
            st.success(f"✅ Todas as películas estão com estoque acima de {estoque_minimo} unidades")
    
    # ======================================================
    # TAB 2: PEÇAS
    # ======================================================
    with tab2:
        st.subheader("Peças em Estoque")
        
        # Buscar peças primeiro
        pecas = buscar_pecas()
        
        # Expander para cadastro
        with st.expander("➕ Adicionar Nova Peça", expanded=False):
            with st.form("peca_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                descricao = col1.text_input("Descrição da peça*")
                modelo = col2.text_input("Modelo do aparelho")
                quantidade = col1.number_input("Quantidade", min_value=0, step=1, value=0)
                observacoes = col2.text_area("Observações")
                
                if st.form_submit_button("Adicionar Peça"):
                    if not descricao:
                        st.error("Descrição é obrigatória")
                    else:
                        peca = {
                            "id": str(uuid.uuid4()),
                            "descricao": descricao,
                            "modelo": modelo,
                            "quantidade": quantidade,
                            "observacoes": observacoes,
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        inserir_peca(peca)
                        st.success("Peça adicionada com sucesso!")
                        st.rerun()
        
        # Expander para edição
        with st.expander("✏️ Editar/Excluir Peça", expanded=False):
            if not pecas:
                st.info("Nenhuma peça cadastrada para editar")
            else:
                # Busca para seleção
                opcoes_pecas = {f"{peca['descricao']} | {peca['modelo'] or 'Sem modelo'}": peca['id'] for peca in pecas}
                peca_selecionada = st.selectbox("Selecionar peça para editar", list(opcoes_pecas.keys()))
                peca_id = opcoes_pecas[peca_selecionada]
                
                # Carregar dados da peça selecionada
                peca = buscar_peca_por_id(peca_id)
                
                if peca:
                    with st.form("editar_peca_form"):
                        col1, col2 = st.columns(2)
                        
                        nova_descricao = col1.text_input("Descrição", value=peca['descricao'])
                        novo_modelo = col2.text_input("Modelo", value=peca['modelo'] or "")
                        nova_quantidade = col1.number_input("Quantidade", min_value=0, step=1, value=peca['quantidade'])
                        novas_observacoes = col2.text_area("Observações", value=peca['observacoes'] or "")
                        
                        col3, col4 = st.columns(2)
                        if col3.form_submit_button("💾 Salvar Alterações"):
                            atualizar_peca(peca_id, nova_descricao, novo_modelo, nova_quantidade, novas_observacoes)
                            st.success("Peça atualizada com sucesso!")
                            st.rerun()
                            
                        if col4.form_submit_button("🗑️ Excluir Peça"):
                            excluir_peca(peca_id)
                            st.success("Peça excluída com sucesso!")
                            st.rerun()
        
        # Filtro local para peças
        st.subheader("Filtrar Peças")
        filtro_pecas = st.text_input("🔍 Filtrar peças por descrição, modelo ou observações")
        
        # Aplicar filtro
        if filtro_pecas:
            pecas_filtradas = [
                peca for peca in pecas 
                if (filtro_pecas.lower() in peca['descricao'].lower() or 
                    (peca['modelo'] and filtro_pecas.lower() in peca['modelo'].lower()) or
                    (peca['observacoes'] and filtro_pecas.lower() in peca['observacoes'].lower()))
            ]
            exibir_pecas(pecas_filtradas)
            st.info(f"Mostrando {len(pecas_filtradas)} de {len(pecas)} peças")
        else:
            # Lista de peças sem filtro
            exibir_pecas(pecas)
    
    # ======================================================
    # TAB 3: CAPAS
    # ======================================================
    with tab3:
        st.subheader("Capas em Estoque")
        
        # Buscar capas primeiro
        capas = buscar_capas()
        
        # Expander para cadastro
        with st.expander("➕ Adicionar Nova Capa", expanded=False):
            with st.form("capa_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                modelo = col1.text_input("Modelo do aparelho*")
                cor = col2.text_input("Cor*")
                quantidade = col1.number_input("Quantidade", min_value=0, step=1, value=0)
                
                if st.form_submit_button("Adicionar Capa"):
                    if not modelo or not cor:
                        st.error("Modelo e cor são obrigatórios")
                    else:
                        capa = {
                            "id": str(uuid.uuid4()),
                            "modelo": modelo,
                            "cor": cor,
                            "quantidade": quantidade,
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        inserir_capa(capa)
                        st.success("Capa adicionada com sucesso!")
                        st.rerun()
        
        # Expander para edição
        with st.expander("✏️ Editar/Excluir Capa", expanded=False):
            if not capas:
                st.info("Nenhuma capa cadastrada para editar")
            else:
                # Busca para seleção
                opcoes_capas = {f"{capa['modelo']} | {capa['cor']}": capa['id'] for capa in capas}
                capa_selecionada = st.selectbox("Selecionar capa para editar", list(opcoes_capas.keys()))
                capa_id = opcoes_capas[capa_selecionada]
                
                # Carregar dados da capa selecionada
                capa = buscar_capa_por_id(capa_id)
                
                if capa:
                    with st.form("editar_capa_form"):
                        col1, col2 = st.columns(2)
                        
                        novo_modelo = col1.text_input("Modelo", value=capa['modelo'])
                        nova_cor = col2.text_input("Cor", value=capa['cor'])
                        nova_quantidade = col1.number_input("Quantidade", min_value=0, step=1, value=capa['quantidade'])
                        
                        col3, col4 = st.columns(2)
                        if col3.form_submit_button("💾 Salvar Alterações"):
                            atualizar_capa(capa_id, novo_modelo, nova_cor, nova_quantidade)
                            st.success("Capa atualizada com sucesso!")
                            st.rerun()
                            
                        if col4.form_submit_button("🗑️ Excluir Capa"):
                            excluir_capa(capa_id)
                            st.success("Capa excluída com sucesso!")
                            st.rerun()
        
        # Filtro local para capas
        st.subheader("Filtrar Capas")
        filtro_capas = st.text_input("🔍 Filtrar capas por modelo ou cor")
        
        # Aplicar filtro
        if filtro_capas:
            capas_filtradas = [
                capa for capa in capas 
                if (filtro_capas.lower() in capa['modelo'].lower() or 
                    filtro_capas.lower() in capa['cor'].lower())
            ]
            exibir_capas(capas_filtradas)
            st.info(f"Mostrando {len(capas_filtradas)} de {len(capas)} capas")
        else:
            # Lista de capas sem filtro
            exibir_capas(capas)
    
    # ======================================================
    # TAB 4: PELÍCULAS
    # ======================================================
    with tab4:
        st.subheader("Películas em Estoque")
        
        # Buscar películas primeiro
        peliculas = buscar_peliculas()
        
        # Expander para cadastro
        with st.expander("➕ Adicionar Nova Película", expanded=False):
            with st.form("pelicula_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                modelo = col1.text_input("Modelo principal*")
                quantidade = col1.number_input("Quantidade", min_value=0, step=1, value=0)
                
                # Buscar sugestões do banco de dados
                if modelo:                    
                    sugestoes = sugerir_compatibilidade(modelo)
                    
                    # Buscar todos os modelos disponíveis
                    todos_modelos = obter_modelos_principais()
                    
                    # Filtrar as sugestões para incluir apenas modelos que estão na lista de opções
                    sugestoes_validas = filtrar_valores_validos(todos_modelos, sugestoes)
                    
                    modelos_compatíveis = st.multiselect(
                        "Modelos compatíveis",
                        options=todos_modelos,
                        default=sugestoes_validas,
                        help="Selecione os modelos compatíveis com esta película"
                    )
                
                if st.form_submit_button("Adicionar Película"):
                    if not modelo:
                        st.error("Modelo é obrigatório")
                    else:
                        # Buscar compatibilidades para este modelo
                        compatibilidades = sugerir_compatibilidade(modelo)
                        
                        pelicula = {
                            "id": str(uuid.uuid4()),
                            "modelo": modelo,
                            "quantidade": quantidade,
                            "compatibilidade": modelos_compatíveis,
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                        inserir_pelicula(pelicula)
                        st.success("Película adicionada com sucesso!")
                        st.rerun()
        
        # Expander para edição
        with st.expander("✏️ Editar/Excluir Película", expanded=False):
            if not peliculas:
                st.info("Nenhuma película cadastrada para editar")
            else:
                # Busca para seleção
                opcoes_peliculas = {f"{pelicula['modelo']}": pelicula['id'] for pelicula in peliculas}
                pelicula_selecionada = st.selectbox("Selecionar película para editar", list(opcoes_peliculas.keys()))
                pelicula_id = opcoes_peliculas[pelicula_selecionada]
                
                # Carregar dados da película selecionada
                pelicula = buscar_pelicula_por_id(pelicula_id)
                
                if pelicula:
                    with st.form("editar_pelicula_form"):
                        col1, col2 = st.columns(2)
                        
                        novo_modelo = col1.text_input("Modelo", value=pelicula['modelo'])
                        nova_quantidade = col1.number_input("Quantidade", min_value=0, step=1, value=pelicula['quantidade'])
                        
                        # Na edição de películas:
                        if novo_modelo:
                            # Buscar sugestões do banco de dados
                            sugestoes = sugerir_compatibilidade(novo_modelo)
                            
                            # Buscar todos os modelos disponíveis
                            todos_modelos = obter_modelos_principais()

                            # Obter compatibilidades atuais da película
                            compatibilidades_atuais = pelicula.get('compatibilidade', [])
                            
                            # Combinar sugestões e compatibilidades atuais, filtrando valores válidos
                            valores_padrao = list(set(sugestoes + compatibilidades_atuais))
                            valores_validos = filtrar_valores_validos(todos_modelos, valores_padrao)                                                
                            
                            modelos_compatíveis = st.multiselect(
                                "Modelos compatíveis",
                                options=todos_modelos,
                                default=valores_validos,
                                help="Selecione os modelos compatíveis com esta película"
                            )
                        
                        col3, col4 = st.columns(2)
                        if col3.form_submit_button("💾 Salvar Alterações"):
                            atualizar_pelicula(pelicula_id, novo_modelo, nova_quantidade, modelos_compatíveis)
                            st.success("Película atualizada com sucesso!")
                            st.rerun()
                            
                        if col4.form_submit_button("🗑️ Excluir Película"):
                            excluir_pelicula(pelicula_id)
                            st.success("Película excluída com sucesso!")
                            st.rerun()

        # Gerenciamento de Compatibilidades
        with st.expander("🔧 Gerenciar Compatibilidades", expanded=False):
            st.subheader("Adicionar Nova Compatibilidade")
            
            with st.form("compatibilidade_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                modelo_principal = col1.text_input("Modelo Principal*")
                modelo_compativel = col2.text_input("Modelo Compatível*")
                
                if st.form_submit_button("Adicionar Compatibilidade"):
                    if not modelo_principal or not modelo_compativel:
                        st.error("Preencha ambos os campos")
                    else:
                        compatibilidade = {
                            "id": str(uuid.uuid4()),
                            "modelo_principal": modelo_principal.strip(),
                            "modelo_compativel": modelo_compativel.strip(),
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        if inserir_compatibilidade(compatibilidade):
                            atualizar_compatibilidade_peliculas(modelo_principal.strip())
                            st.success("Compatibilidade adicionada com sucesso!")
                            st.rerun()
                        else:
                            st.warning("Esta compatibilidade já existe")
            
            st.subheader("Compatibilidades Cadastradas")
            
            # Buscar todas as compatibilidades
            compatibilidades = buscar_todas_compatibilidades()
            
            if not compatibilidades:
                st.info("Nenhuma compatibilidade cadastrada.")
            else:
                # Filtro para compatibilidades
                filtro_compat = st.text_input("🔍 Filtrar compatibilidades")
                
                # Aplicar filtro
                if filtro_compat:
                    compatibilidades_filtradas = [
                        comp for comp in compatibilidades 
                        if (filtro_compat.lower() in comp['modelo_principal'].lower() or 
                            filtro_compat.lower() in comp['modelo_compativel'].lower())
                    ]
                else:
                    compatibilidades_filtradas = compatibilidades
                
                # Exibir compatibilidades
                for comp in compatibilidades_filtradas:
                    col1, col2, col3 = st.columns([3, 3, 1])
                    col1.write(f"**{comp['modelo_principal']}**")
                    col2.write(f"→ {comp['modelo_compativel']}")
                    
                    # Botão de exclusão
                    if col3.button("🗑️", key=f"del_comp_{comp['id']}"):
                        excluir_compatibilidade(comp['id'])
                        atualizar_compatibilidade_peliculas(comp['modelo_principal'])
                        st.success("Compatibilidade removida!")
                        st.rerun()
                
                st.info(f"Mostrando {len(compatibilidades_filtradas)} de {len(compatibilidades)} compatibilidades")
                # Sincronização manual de compatibilidades para películas:
                st.divider()
                st.subheader("Sincronização")

                if st.button("🔄 Sincronizar Todas as Películas"):
                    atualizar_todas_compatibilidades_peliculas()
                    st.success("Todas as películas foram sincronizadas com as compatibilidades!")
                    st.rerun()
          
        
        # Filtro local para películas
        st.subheader("Filtrar Películas")
        filtro_peliculas = st.text_input("🔍 Filtrar películas por modelo ou compatibilidade")
        
        # Aplicar filtro
        if filtro_peliculas:
            peliculas_filtradas = [
                pelicula for pelicula in peliculas 
                if (filtro_peliculas.lower() in pelicula['modelo'].lower() or 
                    any(filtro_peliculas.lower() in compat.lower() for compat in pelicula.get('compatibilidade', [])))
            ]
            exibir_peliculas(peliculas_filtradas)
            st.info(f"Mostrando {len(peliculas_filtradas)} de {len(peliculas)} películas")
        else:
            # Lista de películas sem filtro
            exibir_peliculas(peliculas)
    
    # ======================================================
    # TAB 5: BUSCA
    # ======================================================
    with tab5:
        st.subheader("Busca no Estoque")
        
        termo_busca = st.text_input("🔍 Digite o termo de busca")
        
        if termo_busca:
            resultados = buscar_estoque(termo_busca)
            exibir_busca(resultados)
            st.info(f"Encontrados {len(resultados)} resultados")
        else:
            st.info("Digite um termo para buscar em todo o estoque.")

        # Busca de películas compatíveis por modelo
        st.subheader("🔍 Encontrar Películas Compatíveis")

        modelo_consulta = st.text_input("Digite o modelo do aparelho para encontrar películas compatíveis")

        if modelo_consulta:
            # Buscar películas que são compatíveis com este modelo
            peliculas_compatíveis = []
            
            for pelicula in buscar_peliculas():
                # Verificar se o modelo consultado é compatível com esta película
                if (modelo_consulta.lower() == pelicula['modelo'].lower() or 
                    modelo_consulta.lower() in [m.lower() for m in pelicula.get('compatibilidade', [])]):
                    peliculas_compatíveis.append(pelicula)
            
            if peliculas_compatíveis:
                st.success(f"Encontradas {len(peliculas_compatíveis)} películas compatíveis com {modelo_consulta}")
                exibir_peliculas(peliculas_compatíveis)
            else:
                st.warning(f"Nenhuma película compatível encontrada para {modelo_consulta}")
