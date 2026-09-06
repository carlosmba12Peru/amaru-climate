import pytest
import os
from agents.agente_crioclimatico_nina import (
    AgenteCrioclimaticoNina,
    EvaluacionDistritoChiri,
    ResumenEvaluacionChiri
)

def test_inicializacion_agente_crioclimatico():
    agente = AgenteCrioclimaticoNina()
    assert len(agente.distritos_catalogo) == 27
    depts = set(d["departamento"] for d in agente.distritos_catalogo)
    assert {"PUNO", "HUANCAVELICA", "AREQUIPA", "CUSCO", "TACNA", "LIMA", "PASCO", "HUANUCO"}.issubset(depts)

def test_calculo_ish_chiri_extremo_mazocruz():
    agente = AgenteCrioclimaticoNina()
    
    # Evaluar Mazocruz (UBIGEO 210504) con frío extremo (-22.0 °C, 5 días continuos, viento 28 km/h)
    eval_mazocruz = agente.evaluar_distrito(
        ubigeo="210504",
        tmin_observada=-22.0,
        viento_kmh=28.0,
        dias_bajo_cero=5
    )
    
    assert isinstance(eval_mazocruz, EvaluacionDistritoChiri)
    assert eval_mazocruz.distrito == "SANTA ROSA"
    assert "Mazocruz" in eval_mazocruz.nombre_comun
    assert eval_mazocruz.ish_chiri >= 85.0
    assert eval_mazocruz.nivel_alerta == "ALERTA_ROJA_GLACIAL"
    assert "cobertizos" in eval_mazocruz.accion_tactica_c2.lower()
    assert eval_mazocruz.censo_alpacas == 68500
    # Validación de directivas PREVAED y alerta vial
    assert eval_mazocruz.colegios_vulnerables > 0
    assert eval_mazocruz.escolares_en_riesgo > 0
    assert "SUSPENSIÓN" in eval_mazocruz.directiva_educativa_prevaed
    assert "PELIGRO DE CONGELAMIENTO" in eval_mazocruz.alerta_vial_escarcha

def test_calculo_ish_chiri_condicion_moderada():
    agente = AgenteCrioclimaticoNina()
    
    # Evaluar Lircay (UBIGEO 090301, 3278 msnm) con helada leve (-1.0 °C, 1 día)
    eval_lircay = agente.evaluar_distrito(
        ubigeo="090301",
        tmin_observada=-1.0,
        viento_kmh=10.0,
        dias_bajo_cero=1
    )
    
    assert eval_lircay.ish_chiri < 55.0
    assert eval_lircay.nivel_alerta in {"ALERTA_AMARILLA_PREVENTIVA", "CONDICION_VERDE_NORMAL"}

def test_barrido_territorial_distritos():
    agente = AgenteCrioclimaticoNina()
    
    # Escenario severo con enfriamiento adicional de -3.0 °C sobre umbrales
    resumen = agente.ejecutar_barrido_territorial(
        escenario_tmin_delta=-3.0,
        anomalia_tsm_pacifico=-1.5,
        alisios_velocidad=8.0
    )
    
    assert isinstance(resumen, ResumenEvaluacionChiri)
    assert resumen.total_distritos_evaluados == 27
    assert resumen.distritos_alerta_roja > 0
    assert resumen.alpacas_en_riesgo_critico > 0
    assert resumen.personas_vulnerables_en_riesgo_critico > 0
    assert resumen.total_colegios_en_riesgo > 0
    assert resumen.total_escolares_en_riesgo > 0
    assert resumen.vias_con_alerta_hielo > 0
    
    # Comprobar que el distrito más severo encabeza la lista
    assert len(resumen.evaluaciones) == 27
    assert resumen.evaluaciones[0].ish_chiri == resumen.ish_chiri_maximo
    
    # Comprobar integración con el Reloj de La Niña
    assert "arco_glacial" in resumen.estado_reloj_macro
    assert "analogo_dominante" in resumen.estado_reloj_macro
    assert resumen.estado_reloj_macro["anomalia_tsm_pacifico"] == -1.5

def test_distincion_conceptual_ish_vs_iph():
    """Verifica que el agente usa exclusivamente 'ish_chiri' y no contamina el IPH de huaicos"""
    agente = AgenteCrioclimaticoNina()
    eval_imata = agente.evaluar_distrito(ubigeo="040514", tmin_observada=-15.0)
    
    # El atributo debe ser ish_chiri
    assert hasattr(eval_imata, "ish_chiri")
    assert not hasattr(eval_imata, "iph_fen")
