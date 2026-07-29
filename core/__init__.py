"""
Core do sistema Bestcell.

Centraliza utilidades globais compartilhadas entre os módulos,
como gerenciamento de session_state e constantes do sistema.
"""

from .state_manager import StateManager
from .state_keys import *

__all__ = [
    "StateManager"
]