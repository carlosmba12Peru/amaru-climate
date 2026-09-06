import pytest
from core.orchestrator import AmaruOrchestrator

def test_full_swarm_lifecycle():
    orchestrator = AmaruOrchestrator()
    
    resultado = orchestrator.procesar_incidente_completo(
        region="La Libertad",
        distrito="El Porvenir",
        lluvia_mm=75.0,
        alerta_senamhi="ROJO",
        reporte_ciudadano_texto="El huaico de la quebrada San Ildefonso se desbordo, auxilio estamos atrapados!",
        tipo_canal="VOZ_VAPI",
        atrapados=4
    )
    
    assert resultado["status"] == "OPERATIVO_DESPACHADO"
    assert "ficha_edan" in resultado
    ficha = resultado["ficha_edan"]
    assert ficha["nivel_severidad"] == "CRITICA"
    assert "COEN-INDECI" in ficha["entidades_notificadas"]
    assert "EJERCITO_DEL_PERU" in ficha["entidades_notificadas"]
    assert len(resultado["analisis_georriesgo"]["quebradas_superando_umbral"]) > 0
    assert "memoria_historica" in resultado
    mem = resultado["memoria_historica"]
    assert mem["distrito_consultado"] == "El Porvenir"
    assert len(mem["registros_historicos_encontrados"]) > 0
    assert mem["alerta_reincidencia_severa"] is True
