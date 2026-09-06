"""
Pruebas de Ciberseguridad y Blindaje Criptográfico del IPH-FEN
Sistema AMARU-FEN - Sala de Mando C2
Verifica: Anti-Tampering (SHA-256), Firma Digital Asimétrica (ECDSA secp256k1),
Filtro Zero-Trust Anti-Envenenamiento y Circuit-Breaker de Sabotaje.
"""
import pytest
from agents.agente_georriesgo import AgenteGeorriesgo
from core.climate_oracle_web3 import AmaruClimateOracle
from core.orchestrator import AmaruOrchestrator

def test_integridad_formula_sha256_valida():
    georriesgo = AgenteGeorriesgo()
    verif = georriesgo.verificar_integridad_formula()
    assert verif["es_integro"] is True
    assert verif["estado"] == "INTEGRO_VERIFICADO_OK"
    assert len(verif["hash_actual"]) == 64
    assert verif["hash_actual"] == verif["hash_canonico_esperado"]
    assert verif["blindaje_activo"] is True

def test_deteccion_sabotaje_tamper_detected():
    georriesgo = AgenteGeorriesgo()
    
    # Simular ataque de hacker: modifica el peso de la lluvia en memoria RAM
    georriesgo.pesos["w_meteo"] = 0.05
    
    verif = georriesgo.verificar_integridad_formula()
    assert verif["es_integro"] is False
    assert verif["estado"] == "ALERTA_SABOTAJE_TAMPER_DETECTED"
    
    # El cálculo debe abortar de inmediato por seguridad nacional
    with pytest.raises(RuntimeError) as exc_info:
        georriesgo.calcular_probabilidad_dinamica_huaico(
            id_o_nombre="Q-LAM-01",
            lluvia_cabecera_mm_h=20.0
        )
    assert "ALERTA CRÍTICA DE CIBERSEGURIDAD C2" in str(exc_info.value)
    
    # Restaurar peso legítimo
    georriesgo.pesos["w_meteo"] = 0.30
    assert georriesgo.verificar_integridad_formula()["es_integro"] is True

def test_firma_secp256k1_recibo_c2():
    georriesgo = AgenteGeorriesgo()
    res = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-LAM-01",
        lluvia_cabecera_mm_h=18.0,
        lluvia_acumulada_24h=42.0,
        saturacion_api_72h=35.0,
        irce_circundante=0.42
    )
    
    assert "recibo_criptografico_c2" in res
    recibo = res["recibo_criptografico_c2"]
    assert recibo["algoritmo"] == "ECDSA-SECP256K1-SHA256"
    assert len(recibo["payload_hash"]) == 64
    assert len(recibo["firma_hex"]) > 64
    assert "BEGIN PUBLIC KEY" in recibo["public_key_pem"]
    assert recibo["sello_soberania_humana_ley_31814"] is True
    
    # Verificar matemáticamente con la clave pública del oráculo
    es_valido, msg = AmaruClimateOracle.verificar_calculo_iph_fen(recibo)
    assert es_valido is True
    assert "verificada" in msg.lower() or "auténtico" in msg.lower()

def test_deteccion_recibo_adulterado_por_hacker():
    georriesgo = AgenteGeorriesgo()
    res = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-LAM-01",
        lluvia_cabecera_mm_h=18.0
    )
    recibo = res["recibo_criptografico_c2"]
    
    # Simular hacker adulterando el score en el payload firmado
    recibo["payload_firmado"]["iph_fen_score"] = 10.0  # Intentan bajar Alerta Roja a Verde
    
    es_valido, msg = AmaruClimateOracle.verificar_calculo_iph_fen(recibo)
    assert es_valido is False
    assert "Sabotaje" in msg or "inválida" in msg.lower()

def test_filtro_anti_envenenamiento_inputs():
    georriesgo = AgenteGeorriesgo()
    # Inyectar datos extremos fuera de los límites físicos (ataque de desbordamiento)
    res = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-LAM-01",
        lluvia_cabecera_mm_h=99999.0,   # Disparate físico
        lluvia_acumulada_24h=-500.0,    # Imposible físico
        saturacion_api_72h=8888.0,
        irce_circundante=15.0           # Fuera de [0, 1]
    )
    # Deben haberse sanitizado dentro de los rangos válidos
    assert res["lluvia_cabecera_mm_h"] <= 300.0
    assert res["lluvia_acumulada_24h"] >= 0.0
    assert res["saturacion_api_72h"] <= 200.0
    assert 0.0 <= res["irce_circundante_usado"] <= 1.0

def test_orquestador_verificacion_integridad():
    orchestrator = AmaruOrchestrator()
    verif = orchestrator.verificar_integridad_formula_iph()
    assert verif["es_integro"] is True
    assert verif["estado"] == "INTEGRO_VERIFICADO_OK"

def test_consola_c2_comando_fuentes_y_auditoria():
    orchestrator = AmaruOrchestrator()
    
    # Probar comando 'fuentes'
    res_fuentes = orchestrator.ejecutar_comando_consola("fuentes")
    assert res_fuentes["tipo"] == "OK"
    assert "SENAMHI" in res_fuentes["salida_texto"]
    assert "ENFEN" in res_fuentes["salida_texto"]
    assert "ANA" in res_fuentes["salida_texto"]
    assert "INGEMMET" in res_fuentes["salida_texto"]
    assert "CENEPRED" in res_fuentes["salida_texto"]
    assert "MTC" in res_fuentes["salida_texto"]
    assert "https://" in res_fuentes["salida_texto"]
    assert "VALIDADA" in res_fuentes["salida_texto"]

    # Probar comando 'auditoria'
    res_audit = orchestrator.ejecutar_comando_consola("auditoria")
    assert res_audit["tipo"] == "OK"
    assert "HASH CANÓNICO FÓRMULA" in res_audit["salida_texto"]
    assert "b8c2c1c73f324fcad0bfa51bbfa2efbb0a38f323719ce3f95ecb50f75e3c79c8" in res_audit["salida_texto"]
    assert "ECDSA secp256k1" in res_audit["salida_texto"]
    assert "Ley N° 31814" in res_audit["salida_texto"]

