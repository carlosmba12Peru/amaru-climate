import pytest
from core.anticipatory_triggers import MotorGobernanzaAnticipatoria
from core.orchestrator import AmaruOrchestrator


def test_trigger_anticipatorio_emergencia():
    motor = MotorGobernanzaAnticipatoria()
    
    # Simular anomalía térmica alta en Niño 1+2 (+1.8 °C)
    res = motor.evaluar_triggers_climaticos(anomalia_tsm_nino12=1.8, mes_actual=8)
    
    assert res.nivel_advertencia == "ADVERTENCIA_TEMPRANA"
    assert res.trigger_presupuestal_activo is True
    assert len(res.preposicionamiento_norte) == 4
    
    piura = next(p for p in res.preposicionamiento_norte if p.region == "Piura")
    assert piura.motobombas_desplegadas > 20
    assert piura.estado == "EN_POSICION"
    
    # Verificar impacto dual en el sur
    assert res.alerta_dual_sur_sequias["trigger_activo"] is True
    assert "Puno" in res.alerta_dual_sur_sequias["regiones_afectadas"]

def test_trigger_anticipatorio_normal():
    motor = MotorGobernanzaAnticipatoria()
    res = motor.evaluar_triggers_climaticos(anomalia_tsm_nino12=0.4, mes_actual=4)
    assert res.nivel_advertencia == "NORMAL"
    assert res.trigger_presupuestal_activo is False

def test_calcular_irce_fen_distrital_orquestador():
    from core.orchestrator import AmaruOrchestrator
    orchestrator = AmaruOrchestrator()
    
    # 1. Catacaos con lluvia extrema (75 mm), mar a +3.5 °C y 6 días de anegamiento
    res_catacaos = orchestrator.calcular_irce_fen_distrital(
        distrito="Catacaos",
        lluvia_mm=75.0,
        anomalia_tsm=3.5,
        anegamiento_dias=6
    )
    assert res_catacaos["score_irce_fen"] >= 0.65
    assert res_catacaos["nivel_alerta"] in ["CRITICO_ROJO", "ALTO_NARANJA"]
    assert res_catacaos["respaldo_legal_ds_124"] is True
    assert res_catacaos["antecedentes_historicos"] is True
    
    # 2. Distrito con condiciones normales/bajas
    res_tranquilo = orchestrator.calcular_irce_fen_distrital(
        distrito="Lima",
        lluvia_mm=2.0,
        anomalia_tsm=0.3,
        anegamiento_dias=0
    )
    assert res_tranquilo["score_irce_fen"] < 0.40
    assert "VERDE" in res_tranquilo["semaforo"] or "AMARILLO" in res_tranquilo["semaforo"]

def test_consultar_satelite_imarpe_triada():
    orchestrator = AmaruOrchestrator()
    im = orchestrator.consultar_satelite_imarpe()
    
    assert "IMARPE" in im["entidad"]
    assert "satelite.imarpe.gob.pe" in im["portal_url"]
    
    triada = im["triada_biofisica_monitoreada"]
    assert "tsm_temperatura_superficial" in triada
    assert "clorofila_a_productividad" in triada
    assert "vientos_superficiales" in triada
    assert "Ekman" in triada["vientos_superficiales"]["indicador_fen"]
    assert "anchoveta" in triada["clorofila_a_productividad"]["indicador_fen"]


