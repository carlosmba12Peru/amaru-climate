import pytest

# Wrapper that imports **all** AMARU test modules (both FEN and CHIRI).
# Running this suite gives a full end‑to‑end regression check.

# FEN‑related tests
import test_blindaje_criptografico_iph_fen
import test_reloj_fen
import test_edge_resilience
import test_anticipatory_triggers
import test_motor_calibracion_post_mortem
import test_motor_chat_soberano
import test_amaru_strands_agent

# CHIRI‑related tests
import test_agente_crioclimatico_nina
import test_modulo_satelite_edan_cgr
import test_amaru_chiri_end_to_end
# Add any other CHIRI‑only modules here if needed.
