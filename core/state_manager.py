import streamlit as st


class StateManager:
    """
    Gerenciador global de session_state.

    Permite acessar o state com namespaces
    evitando conflito entre módulos.
    """

    @staticmethod
    def _build_key(module: str, key: str) -> str:
        return f"{module}.{key}"

    @staticmethod
    def get(module: str, key: str, default=None):
        full_key = StateManager._build_key(module, key)
        return st.session_state.get(full_key, default)

    @staticmethod
    def set(module: str, key: str, value):
        full_key = StateManager._build_key(module, key)
        st.session_state[full_key] = value

    @staticmethod
    def init(module: str, key: str, default=None):
        """
        Inicializa chave caso não exista
        """
        full_key = StateManager._build_key(module, key)

        if full_key not in st.session_state:
            st.session_state[full_key] = default

    @staticmethod
    def delete(module: str, key: str):
        full_key = StateManager._build_key(module, key)

        if full_key in st.session_state:
            del st.session_state[full_key]

    @staticmethod
    def clear_module(module: str):
        """
        Remove todas as chaves de um módulo
        """
        keys_to_delete = [
            k for k in st.session_state.keys()
            if k.startswith(f"{module}.")
        ]

        for k in keys_to_delete:
            del st.session_state[k]