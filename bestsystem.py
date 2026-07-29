import streamlit as st
from pathlib import Path

# Controle de estado global
from core.state_manager import StateManager
from core.state_keys import AppState

# Módulos do sistema
from vendas import app as vendas_app
from ordem_servico import app as os_app
from estoque import app as estoque_app
from catalogo import app as catalogo_app

from vendas.database import init_db as init_vendas_db
from ordem_servico.database import init_db as init_os_db
from estoque.database import init_db as init_estoque_db
from catalogo.database import init_db as init_catalogo_db

from vendas.view import fmt_today_label

# ======================================================
# INICIALIZAÇÃO DAS BASES DE DADOS
# ======================================================

@st.cache_resource
def initialize_databases():
    """Inicializa todas as bases de dados do sistema"""
    init_vendas_db()
    init_os_db()
    init_estoque_db()
    init_catalogo_db()

initialize_databases()

# ======================================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================================

st.set_page_config(
    page_title="BestCell System",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# PATHS E ASSETS
# ======================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

# ======================================================
# HEADER PRINCIPAL
# ======================================================

header_container = st.container()

with header_container:
    col_logo, col_date = st.columns([3, 1])

    with col_logo:
        st.image(BASE_DIR / "assets" / "bestcell.png", width='stretch')

    with col_date:
        # O segredo está em usar HTML com CSS flexbox para empurrar o texto para baixo
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; justify-content: flex-end; height: 250px;">
                <p style="margin-bottom: 0px;">{fmt_today_label()}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

# ======================================================
# SIDEBAR COM NAVEGAÇÃO MANUAL (FUNCIONAL)
# ======================================================

with st.sidebar:
    # Logo do sistema
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width="stretch")
    
    st.title("Sistema BestCell")
    st.markdown("---")
    
    # Determinar página atual
    current_page = st.query_params.get("page", "vendas")
    
    # Botão de Vendas
    if st.button(
        "📱 Vendas", 
        width='stretch',
        type="primary" if current_page == "vendas" else "secondary",
        help="Módulo de vendas e gestão comercial"
    ):
        st.query_params.page = "vendas"
        st.rerun()
    
    # Botão de Ordem de Serviço
    if st.button(
        "🔧 Ordem de Serviço",
        width='stretch', 
        type="primary" if current_page == "ordem_servico" else "secondary",
        help="Módulo de gestão de ordens de serviço"
    ):
        st.query_params.page = "ordem_servico"
        st.rerun()

    # Botão de Estoque
    if st.button(
        "📦 Estoque", 
        width='stretch',
        type="primary" if current_page == "estoque" else "secondary",
        help="Módulo de gestão de estoque"
    ):
        st.query_params.page = "estoque"
        st.rerun()

    if st.button(
        "🏷️ Catálogo",
        width='stretch',
        type="primary" if current_page == "catalogo" else "secondary",
        help="Simulador de vendas, calculadora de juros e catálogo"
    ):
        st.query_params.page = "catalogo"
        st.rerun()
    
    # Footer da sidebar
    st.markdown("---")
    st.caption("Sistema interno v2.0.0")
    st.caption(f"Streamlit {st.__version__}")

# ======================================================
# ROTEAMENTO SIMPLES
# ======================================================

page = st.query_params.get("page", "vendas")

if page == "vendas":
    vendas_app()
elif page == "ordem_servico":
    os_app()

elif page == "estoque":
    estoque_app()

elif page == "catalogo":
    catalogo_app()


