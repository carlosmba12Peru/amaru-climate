"""
Pruebas Unitarias Automatizadas para el Adaptador AWS Strands Agents SDK
Track: Good Neighbor Agents - AMARU-FEN
"""

import pytest
from agents.amaru_strands_agent import (
    crear_agente_amaru_good_neighbor,
    monitorear_hidrometria_senamhi,
    evaluar_georriesgo_quebradas,
    consultar_memoria_historica_desastres,
    auditar_marco_legal_decretos,
    rastrear_reportes_ciudadanos_osint,
    despachar_ficha_oficial_edan,
    contencion_voz_y_alerta_vapi,
    anclar_socorro_climatico_web3,
    evaluar_resiliencia_comunitaria_distrito,
    evaluar_crioclima_heladas_nina,
    consultar_reloj_tactico_nina,
    HERRAMIENTAS_AMARU
)


def test_amaru_strands_agent_instantiation():
    """Verifica que el agente Strands se inicialice con sus 11 herramientas empaquetadas (Dual FEN + CHIRI)."""
    agente = crear_agente_amaru_good_neighbor()
    assert agente is not None
    assert len(HERRAMIENTAS_AMARU) == 11
    assert "Good Neighbor" in agente.system_prompt

    # Ejecutar simulación de llamada al agente
    res = agente("Monitorear situación del río Piura en Catacaos")
    assert res["status"] == "COMPLETED"
    assert "AmaruGoodNeighborAgent" in res["agent"]


def test_tool_monitorear_hidrometria():
    """Verifica la herramienta de aforo hidrométrico SENAMHI."""
    res_normal = monitorear_hidrometria_senamhi("Piura", 25.0)
    assert res_normal["nivel_alerta_senamhi"] == "AMARILLO"

    res_extrema = monitorear_hidrometria_senamhi("Piura", 85.0)
    assert res_extrema["nivel_alerta_senamhi"] == "ROJO"


def test_tool_evaluar_georriesgo():
    """Verifica la evaluación geográfica y activación de quebradas críticas."""
    res = evaluar_georriesgo_quebradas("Catacaos", 55.0)
    assert "distritos_historicos_amenazados" in res
    assert "nivel_prioridad_coen" in res


def test_tool_memoria_historica():
    """Verifica la recuperación de antecedentes históricos de inundaciones."""
    res = consultar_memoria_historica_desastres("Catacaos")
    assert res["distrito"] == "Catacaos"
    assert "antecedentes_historicos" in res
    assert "lecciones_de_resiliencia" in res


def test_tool_auditar_marco_legal():
    """Verifica la auditoría del D.S. N° 124-2026-PCM y sustento de contratación directa."""
    res = auditar_marco_legal_decretos("Catacaos", "ROJO")
    assert res["distrito"] == "Catacaos"
    assert res["verificacion_ds_124"]["declarado_estado_emergencia"] is True
    assert "amparo_legal_principal" in res["sustento_contratacion_directa"]


def test_tool_osint_ciudadano():
    """Verifica el filtrado de reportes sociales comunitarios."""
    res = rastrear_reportes_ciudadanos_osint("Catacaos")
    assert "analisis_vigia" in res
    assert res["alerta_inminente"] is True


def test_tool_despachar_edan():
    """Verifica la generación formal de Ficha EDAN comunitaria."""
    res = despachar_ficha_oficial_edan(
        departamento="Piura",
        provincia="Piura",
        distrito="Catacaos",
        localidad="Pedregal Grande",
        familias_afectadas=80
    )
    assert "EDAN-FEN-" in res["id_ficha"]
    assert res["estado"] == "DESPACHADO"
    assert "COEN-INDECI" in res["entidades_notificadas"]


def test_tool_contencion_vapi():
    """Verifica el triaje telefónico por voz de personas vulnerables."""
    res = contencion_voz_y_alerta_vapi("El agua subió rápido, mis dos niños y mi abuelita están arriba")
    assert res["poblacion_vulnerable_detectada"]["ninos_presentes"] is True
    assert res["poblacion_vulnerable_detectada"]["ancianos_presentes"] is True
    assert res["prioridad_atencion"] == "URGENCIA_MAXIMA"


def test_tool_anclar_web3():
    """Verifica el oráculo climático y firma secp256k1 para socorro paramétrico."""
    # Umbral seguro (< 1900 m3/s)
    res_seguro = anclar_socorro_climatico_web3(1500.0, "Catacaos")
    assert res_seguro["disparo_parametrico_habilitado"] is False

    # Desborde catastrófico (>= 1900 m3/s)
    res_critico = anclar_socorro_climatico_web3(2140.0, "Catacaos")
    assert res_critico["disparo_parametrico_habilitado"] is True
    assert res_critico["atestado_firmado"]["signature_hex"] is not None


def test_tool_evaluar_resiliencia_comunitaria_distrito():
    """Verifica el protocolo holístico de protección comunitaria Buen Vecino."""
    res = evaluar_resiliencia_comunitaria_distrito(
        distrito="Catacaos",
        lluvia_mm=80.0,
        caudal_m3s=2100.0
    )
    assert res["semaforo_comunitario"] == "ROJO"
    assert res["peligro_desborde"] is True
    assert len(res["acciones_inmediatas_buen_vecino"]) >= 3


def test_tool_evaluar_crioclima_heladas_nina():
    """Verifica la herramienta de evaluación crioclimática altoandina AMARU-CHIRI."""
    res = evaluar_crioclima_heladas_nina(departamento="Puno", tmin_c=-22.0)
    assert res["departamento"] == "Puno"
    assert res["temperatura_ingresada_c"] == -22.0
    assert "PMHF" in res["marco_legal"]
    assert len(res["distritos_altoandinos_criticos"]) > 0


def test_tool_consultar_reloj_tactico_nina():
    """Verifica la herramienta de cronómetro polar táctico y Ventana de Oro en Abril."""
    res = consultar_reloj_tactico_nina(anomalia_tsm=-1.5)
    assert res["anomalia_tsm"] == -1.5
    assert "ABRIL" in res["ventana_de_oro"]
    assert res["desfase_dias"] > 0
    assert "1988-1989" in res["analogo_historico"] or "2007-2008" in res["analogo_historico"]

