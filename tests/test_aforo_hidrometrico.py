import pytest
from core.orchestrator import AmaruOrchestrator

def test_catalogo_estaciones_aforo_fluvial():
    orchestrator = AmaruOrchestrator()
    estaciones = orchestrator.consultar_estaciones_aforo()
    
    assert len(estaciones) >= 7
    ids = [e["id_estacion"] for e in estaciones]
    assert "EST-PIU-01" in ids  # Puente Sánchez Cerro
    assert "EST-PIU-02" in ids  # Puente Independencia
    assert "EST-CHI-01" in ids  # Puente Sullana
    assert "EST-ICA-01" in ids  # Bocatoma Socorro

def test_evaluacion_caudal_estacion_alerta():
    orchestrator = AmaruOrchestrator()
    
    # 1. Caudal normal en Puente Sánchez Cerro (150 m³/s)
    eval_normal = orchestrator.evaluar_caudal_estacion("EST-PIU-01", caudal_simulado_m3s=300.0)
    assert eval_normal["alerta"] == "VERDE_NORMAL"
    assert eval_normal["ratio_desborde"] < 0.50
    
    # 2. Caudal de desborde crítico en Catacaos / Puente Independencia (2300 m³/s)
    eval_desborde = orchestrator.evaluar_caudal_estacion("EST-PIU-02", caudal_simulado_m3s=2300.0)
    assert eval_desborde["alerta"] == "ROJO_DESBORDE"
    assert eval_desborde["ratio_desborde"] >= 1.0
    assert "DESBORDE FLUVIAL INMINENTE" in eval_desborde["semaforo"]
    assert "Ley Nº 31814" in eval_desborde["soberania_humana_ley_31814"]

def test_acoplamiento_caudal_en_irce_fen():
    orchestrator = AmaruOrchestrator()
    
    # Distrito con lluvia moderada (20 mm) pero caudal fluvial a tope (2,200 m³/s con desborde en 2,000 m³/s)
    irce_desborde = orchestrator.calcular_irce_fen_distrital(
        distrito="Catacaos",
        lluvia_mm=20.0,
        anomalia_tsm=2.0,
        anegamiento_dias=2,
        caudal_fluvial_m3s=2200.0,
        umbral_desborde_m3s=2000.0
    )
    
    # El vector Peligro debe tomar el máximo del caudal (1.0) elevando el score
    assert irce_desborde["vectores_componentes"]["peligro_p"] >= 0.90
    assert irce_desborde["score_irce_fen"] >= 0.70
    assert irce_desborde["caudal_evaluado_m3s"] == 2200.0
