import os
import json
import pytest
from core.telegram_notifier import TelegramNotifier

@pytest.fixture
def temp_notifier(tmp_path):
    ruta_estado = str(tmp_path / "estado_test.json")
    ruta_historico = str(tmp_path / "historico_test.json")
    notifier = TelegramNotifier(
        token=None,
        chat_id=None,
        ruta_estado=ruta_estado,
        ruta_historico=ruta_historico
    )
    return notifier

def test_declaracion_explicita_ia_en_mensaje_fen(temp_notifier):
    distrito_muestra = {
        "ubigeo": "200114",
        "distrito": "TAMBO GRANDE",
        "provincia": "PIURA",
        "departamento": "PIURA",
        "score_irce": 0.825,
        "lluvia_estimada_mm": 65.0,
        "poblacion_estimada": 24847,
        "nivel_alerta": "CRITICO_ROJO"
    }
    
    mensaje = temp_notifier.construir_mensaje_fen(distrito_muestra)
    
    # Verificación de requisitos legales y explícitos de IA
    assert "ELABORADO POR INTELIGENCIA ARTIFICIAL" in mensaje
    assert "Ley Nº 31814" in mensaje
    assert "UBIGEO 200114" in mensaje
    assert "TAMBO GRANDE" in mensaje
    assert "ALERTA ROJA DE EVACUACIÓN CRÍTICA" in mensaje
    assert "CLÁUSULA DE SOBERANÍA HUMANA" in mensaje

def test_declaracion_explicita_ia_en_mensaje_chiri(temp_notifier):
    distrito_muestra = {
        "ubigeo": "210504",
        "distrito": "SANTA ROSA / MAZOCRUZ",
        "departamento": "PUNO",
        "ish_chiri": 91.5,
        "tmin_observada_c": -24.5,
        "sensacion_termica_viento_c": -30.2,
        "alpacas_expuestas": 120000,
        "colegios_vulnerables": 18,
        "directiva_escolar_prevaed": "SUSPENSIÓN DE CLASES PRESENCIALES (PREVAED PP-0068)",
        "alerta_seguridad_vial": "Peligro de hielo negro en Carretera PE-38 Ilave - Mazocruz",
        "nivel_alerta": "ALERTA_ROJA_GLACIAL"
    }
    
    mensaje = temp_notifier.construir_mensaje_chiri(distrito_muestra)
    
    assert "ELABORADO POR INTELIGENCIA ARTIFICIAL" in mensaje
    assert "Ley Nº 31814" in mensaje
    assert "UBIGEO 210504" in mensaje
    assert "MAZOCRUZ" in mensaje
    assert "ALERTA ROJA GLACIAL" in mensaje
    assert "SUSPENSIÓN DE CLASES PRESENCIALES" in mensaje

def test_deteccion_transicion_estado_a_rojo_sin_spam(temp_notifier):
    # Ciclo 1: Tambogrande está en NARANJA
    distritos_t1 = [
        {"ubigeo": "200114", "distrito": "TAMBO GRANDE", "nivel_alerta": "ALTO_NARANJA"}
    ]
    alertas_t1 = temp_notifier.procesar_transiciones_fen(distritos_t1)
    assert len(alertas_t1) == 0  # No era rojo, no dispara

    # Ciclo 2: Tambogrande sube a ROJO (¡Transición detectada!)
    distritos_t2 = [
        {"ubigeo": "200114", "distrito": "TAMBO GRANDE", "nivel_alerta": "CRITICO_ROJO"}
    ]
    alertas_t2 = temp_notifier.procesar_transiciones_fen(distritos_t2)
    assert len(alertas_t2) == 1
    assert alertas_t2[0]["ubigeo"] == "200114"
    assert "ELABORADO POR INTELIGENCIA ARTIFICIAL" in alertas_t2[0]["mensaje_texto"]

    # Ciclo 3: Tambogrande SIGUE en ROJO en la siguiente evaluación (NO DEBE REPETIR ALERTA SPAM)
    distritos_t3 = [
        {"ubigeo": "200114", "distrito": "TAMBO GRANDE", "nivel_alerta": "CRITICO_ROJO"}
    ]
    alertas_t3 = temp_notifier.procesar_transiciones_fen(distritos_t3)
    assert len(alertas_t3) == 0  # Cero spam repetitivo

def test_registro_historico_auditoria(temp_notifier):
    distritos = [
        {"ubigeo": "200105", "distrito": "CATACAOS", "nivel_alerta": "CRITICO_ROJO"}
    ]
    alertas = temp_notifier.procesar_transiciones_fen(distritos)
    assert len(alertas) == 1
    
    assert os.path.exists(temp_notifier.ruta_historico)
    with open(temp_notifier.ruta_historico, "r", encoding="utf-8") as f:
        historico = json.load(f)
    assert len(historico) == 1
    assert historico[0]["metadata_envio"]["elaborado_por_ia"] is True
