import os
import json
import uuid
import hashlib
import streamlit as st
from datetime import datetime, timedelta

# ==============================
# PATHS & CONFIG
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_DIR = os.path.join(BASE_DIR, "runtime")
LOCK_FILE = os.path.join(RUNTIME_DIR, "bestcell.lock")

LOCK_TIMEOUT_MINUTES = 60

os.makedirs(RUNTIME_DIR, exist_ok=True)

# ==============================
# SESSION INIT
# ==============================

def init_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "login_time" not in st.session_state:
        st.session_state.login_time = None

    if "lock_acquired" not in st.session_state:
        st.session_state.lock_acquired = False

# ==============================
# AUTH HELPERS
# ==============================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def check_credentials(username: str, password: str) -> bool:
    env_user = os.getenv("BESTCELL_USER", "admin")
    env_password_hash = os.getenv(
        "BESTCELL_PASSWORD_HASH",
        hash_password("admin123")  # fallback DEV
    )

    return (
        username == env_user
        and hash_password(password) == env_password_hash
    )

# ==============================
# LOCK CONTROL
# ==============================

def read_lock():
    if not os.path.exists(LOCK_FILE):
        return None

    try:
        with open(LOCK_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None

def is_lock_expired(created_at: str) -> bool:
    lock_time = datetime.fromisoformat(created_at)
    return datetime.utcnow() - lock_time > timedelta(minutes=LOCK_TIMEOUT_MINUTES)

def write_lock():
    lock_data = {
        "session_id": st.session_state.session_id,
        "created_at": datetime.utcnow().isoformat()
    }
    with open(LOCK_FILE, "w") as f:
        json.dump(lock_data, f)

def release_lock(force=False):
    if not os.path.exists(LOCK_FILE):
        return

    if force:
        os.remove(LOCK_FILE)
        return

    existing_lock = read_lock()
    if existing_lock and existing_lock.get("session_id") == st.session_state.session_id:
        os.remove(LOCK_FILE)

def acquire_lock() -> bool:
    existing_lock = read_lock()

    if existing_lock is None:
        write_lock()
        return True

    if existing_lock.get("session_id") == st.session_state.session_id:
        return True

    if is_lock_expired(existing_lock.get("created_at")):
        release_lock(force=True)
        write_lock()
        return True

    return False

# ==============================
# UI — LOGIN / LOGOUT
# ==============================

def render_login():
    st.title("🔐 Acesso restrito")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if check_credentials(username, password):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.login_time = datetime.utcnow()

            if acquire_lock():
                st.session_state.authenticated = True
                st.session_state.lock_acquired = True
                st.rerun()
            else:
                st.error("⚠️ O sistema já está em uso por outro acesso.")
        else:
            st.error("Usuário ou senha inválidos")

def logout():
    release_lock()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
    