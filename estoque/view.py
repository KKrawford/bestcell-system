import streamlit as st
import pandas as pd

def exibir_pecas(pecas):
    if not pecas:
        st.info("Nenhuma peça cadastrada.")
        return
    
    dados = []
    for peca in pecas:
        dados.append({
            "Descrição": peca["descricao"],
            "Modelo": peca["modelo"] or "-",
            "Quantidade": peca["quantidade"],
            "Observações": peca["observacoes"] or "-"
        })
    
    df = pd.DataFrame(dados)
    st.dataframe(df, width='stretch')

def exibir_capas(capas):
    if not capas:
        st.info("Nenhuma capa cadastrada.")
        return
    
    dados = []
    for capa in capas:
        dados.append({
            "Modelo": capa["modelo"],
            "Cor": capa["cor"],
            "Quantidade": capa["quantidade"]
        })
    
    df = pd.DataFrame(dados)
    st.dataframe(df, width='stretch')

def exibir_capas_dashboard(capas_sem_estoque, cores_por_modelo):
    if not capas_sem_estoque:
        st.success("✅ Todas as capas têm estoque disponível")
        return

    st.warning(f"⚠️ {len(capas_sem_estoque)} capas sem estoque")

    dados = []
    for capa in capas_sem_estoque:
        modelo = capa['modelo']
        cor = capa['cor']
        outras_cores = cores_por_modelo.get(modelo)
        
        dados.append({
            "Modelo": modelo,
            "Cor zerada": cor,
            "Outras cores disponíveis": outras_cores if outras_cores else "Nenhuma"
        })

    df = pd.DataFrame(dados)
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            "Modelo": st.column_config.TextColumn("Modelo", width="medium"),
            "Cor zerada": st.column_config.TextColumn("Cor zerada", width="small"),
            "Outras cores disponíveis": st.column_config.TextColumn("Outras cores disponíveis", width="large"),
        }
    )

def exibir_peliculas(peliculas):
    if not peliculas:
        st.info("Nenhuma película cadastrada.")
        return
    
    dados = []
    for pelicula in peliculas:
        compatibilidade = ", ".join(pelicula["compatibilidade"]) if pelicula["compatibilidade"] else "-"
        dados.append({
            "Modelo": pelicula["modelo"],
            "Quantidade": pelicula["quantidade"],
            "Compatível com": compatibilidade
        })
    
    df = pd.DataFrame(dados)
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            "Modelo": st.column_config.TextColumn("Modelo", width="medium"),
            "Quantidade": st.column_config.NumberColumn("Qtd", width="small"),
            "Compatível com": st.column_config.TextColumn("Compatível com", width="large"),
        }
    )

def exibir_busca(resultados):
    if not resultados:
        st.info("Nenhum produto encontrado.")
        return
    
    dados = []
    for resultado in resultados:
        if resultado['tipo'] == 'peca':
            dados.append({
                "Tipo": "Peça",
                "Descrição": resultado['descricao'],
                "Modelo": resultado['modelo'] or "-",
                "Quantidade": resultado['quantidade'],
                "Informação": resultado['informacao_adicional'] or "-"
            })
        elif resultado['tipo'] == 'capa':
            dados.append({
                "Tipo": "Capa",
                "Descrição": resultado['descricao'],
                "Modelo": resultado['modelo'],
                "Quantidade": resultado['quantidade'],
                "Informação": resultado['cor']
            })
        elif resultado['tipo'] == 'pelicula':
            compatibilidade = ", ".join(resultado['compatibilidade']) if resultado['compatibilidade'] else "-"
            dados.append({
                "Tipo": "Película",
                "Descrição": resultado['descricao'],
                "Modelo": resultado['modelo'],
                "Quantidade": resultado['quantidade'],
                "Informação": compatibilidade
            })
    
    df = pd.DataFrame(dados)
    st.dataframe(df, width='stretch')
