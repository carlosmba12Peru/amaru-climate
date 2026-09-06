"""
Pruebas Unitarias de Gobernanza y Aprendizaje por Refuerzo (Safe RL)
Módulo: Motor de Calibración Post-Mortem (Nivel 3) - AMARU-FEN
Normativa: R.J. Nº 112-2014-CENEPRED/J | Ley Nº 31814 (IA en el Perú)
"""

import pytest
import json
import hashlib
from core.motor_calibracion_post_mortem import (
    MotorCalibracionPostMortem,
    RegistroDecisionC2,
    ResultadoRealEvento,
    MatrizSaaty,
    OrdenCorteTemporadaFEN,
    ActaRatificacionComite
)
from core.orchestrator import AmaruOrchestrator


def test_consistencia_matriz_saaty_basal():
    """Verifica que la matriz basal canónica de AMARU-FEN cumpla con el estándar de Saaty (CR <= 0.10)."""
    motor = MotorCalibracionPostMortem()
    matriz = motor.matriz_activa

    assert matriz.es_consistente is True
    assert matriz.cr <= 0.10
    assert matriz.cr == pytest.approx(0.0113, abs=0.01)

    pesos = matriz.pesos
    # Suma de pesos normalizados debe ser 1.0 (aprox por redondeo a 4 decimales)
    assert sum(pesos.values()) == pytest.approx(1.0, abs=0.01)
    # Peligro debe ser el factor dominante
    assert pesos["w_P"] > pesos["w_V"] > pesos["w_E"] > pesos["w_C"]
    assert pesos["w_P"] == pytest.approx(0.467, abs=0.02)


def test_filtro_dura_lex_rechaza_inconsistencias():
    """Comprueba que una matriz contradictoria (A > B, B > C, C > A extremo) sea rechazada por CR > 0.10."""
    tabla_inconsistente = [
        [1.0,  9.0,  0.11, 5.0],
        [0.11, 1.0,  9.0,  0.2],
        [9.0,  0.11, 1.0,  8.0],
        [0.2,  5.0,  0.12, 1.0]
    ]
    matriz_invalida = MotorCalibracionPostMortem.construir_matriz_saaty(tabla_inconsistente)
    assert matriz_invalida.es_consistente is False
    assert matriz_invalida.cr > 0.10


def test_funcion_recompensa_asimetrica_rl():
    """Valida la función de recompensa con penalización crítica para Falsos Negativos."""
    # 1. Caso Ideal: 3 Evacuaciones a tiempo (+18h)
    r_exito = MotorCalibracionPostMortem.calcular_recompensa_rl(
        len_tp=3, len_fp=0, len_fn=0, len_tn=10, promedio_horas_anticipacion=18.0
    )
    assert r_exito > 400.0

    # 2. Caso con Falsa Alarma (costo económico leve)
    r_fa = MotorCalibracionPostMortem.calcular_recompensa_rl(
        len_tp=3, len_fp=2, len_fn=0, len_tn=10, promedio_horas_anticipacion=18.0
    )
    assert r_fa < r_exito
    assert (r_exito - r_fa) == pytest.approx(70.0)  # 2 * 35 = 70

    # 3. Caso Catastrófico con Falso Negativo (desborde sin alerta)
    r_fn = MotorCalibracionPostMortem.calcular_recompensa_rl(
        len_tp=2, len_fp=0, len_fn=1, len_tn=10, promedio_horas_anticipacion=18.0
    )
    # Debe recibir el impacto severo de beta = -600
    assert r_fn < 0.0


def test_evaluacion_desempeno_matriz_confusion():
    """Comprueba el cálculo de TP, FP, FN, TN y métricas estadísticas."""
    motor = MotorCalibracionPostMortem()

    decisiones = [
        # Catacaos: Alertó evacuación (TP)
        RegistroDecisionC2(
            id_alerta="ALT-001",
            ubigeo="200105",
            distrito="Catacaos",
            score_irce_emitido=0.92,
            nivel_alerta="CRITICO_ROJO",
            orden_evacuacion_emitida=True,
            tiempo_anticipacion_horas=24.0,
            factores_evaluados={"peligro": 0.95, "vulnerabilidad": 0.85, "exposicion": 0.80, "capacidad": 0.70}
        ),
        # Chosica: Alertó evacuación pero fue falsa alarma (FP)
        RegistroDecisionC2(
            id_alerta="ALT-002",
            ubigeo="150118",
            distrito="Lurigancho-Chosica",
            score_irce_emitido=0.88,
            nivel_alerta="CRITICO_ROJO",
            orden_evacuacion_emitida=True,
            tiempo_anticipacion_horas=12.0,
            factores_evaluados={"peligro": 0.85, "vulnerabilidad": 0.70, "exposicion": 0.65, "capacidad": 0.80}
        ),
        # Illimo: NO alertó y sí se desbordó (FN - Crítico)
        RegistroDecisionC2(
            id_alerta="ALT-003",
            ubigeo="140303",
            distrito="Illimo",
            score_irce_emitido=0.55,
            nivel_alerta="MEDIO_AMARILLO",
            orden_evacuacion_emitida=False,
            tiempo_anticipacion_horas=0.0,
            factores_evaluados={"peligro": 0.60, "vulnerabilidad": 0.50, "exposicion": 0.50, "capacidad": 0.90}
        ),
        # San Isidro: No alertó y no pasó nada (TN)
        RegistroDecisionC2(
            id_alerta="ALT-004",
            ubigeo="150131",
            distrito="San Isidro",
            score_irce_emitido=0.15,
            nivel_alerta="BAJO_VERDE",
            orden_evacuacion_emitida=False,
            tiempo_anticipacion_horas=0.0,
            factores_evaluados={"peligro": 0.10, "vulnerabilidad": 0.10, "exposicion": 0.10, "capacidad": 1.40}
        )
    ]

    reales = [
        ResultadoRealEvento(ubigeo="200105", distrito="Catacaos", ocurrio_desborde_o_huaico=True, tiempo_evacuacion_requerido_horas=14.0),
        ResultadoRealEvento(ubigeo="150118", distrito="Lurigancho-Chosica", ocurrio_desborde_o_huaico=False),
        ResultadoRealEvento(ubigeo="140303", distrito="Illimo", ocurrio_desborde_o_huaico=True, tiempo_evacuacion_requerido_horas=12.0),
        ResultadoRealEvento(ubigeo="150131", distrito="San Isidro", ocurrio_desborde_o_huaico=False)
    ]

    metricas = motor.evaluar_desempeno(decisiones, reales)

    assert metricas.total_distritos_evaluados == 4
    assert metricas.verdaderos_positivos == ["Catacaos"]
    assert metricas.falsos_positivos == ["Lurigancho-Chosica"]
    assert metricas.falsos_negativos == ["Illimo"]
    assert metricas.verdaderos_negativos == ["San Isidro"]
    assert metricas.precision == 0.50
    assert metricas.recall == 0.50
    assert metricas.f1_score == 0.50


def test_emision_dictamen_pericial_y_sellado_sha256():
    """Valida la generación del informe pericial, hash SHA-256 inmutable y firma del Oráculo C2."""
    motor = MotorCalibracionPostMortem()

    decisiones = [
        RegistroDecisionC2(
            id_alerta="ALT-CAT-01",
            ubigeo="200105",
            distrito="Catacaos",
            score_irce_emitido=0.90,
            nivel_alerta="CRITICO_ROJO",
            orden_evacuacion_emitida=True,
            tiempo_anticipacion_horas=20.0,
            factores_evaluados={"peligro": 0.90, "vulnerabilidad": 0.80, "exposicion": 0.70, "capacidad": 0.75}
        )
    ]
    reales = [
        ResultadoRealEvento(ubigeo="200105", distrito="Catacaos", ocurrio_desborde_o_huaico=True, tiempo_evacuacion_requerido_horas=14.0)
    ]

    informe = motor.emitir_informe_pericial("Simulación FEN 2026", decisiones, reales)

    assert "INF-PERICIAL-AMARU-POSTMORTEM" in informe.id_informe
    assert len(informe.hash_sha256_acta) == 64
    assert informe.sello_soberania_humana is True
    assert informe.matriz_saaty_optimizada.es_consistente is True

    # Verificar recibo criptográfico ECDSA
    recibo = informe.recibo_criptografico_c2
    assert recibo is not None
    assert recibo["algoritmo"] == "ECDSA-SECP256K1-SHA256"
    assert "firma_hex" in recibo

    # Exportar y verificar Markdown
    md = motor.exportar_acta_markdown(informe)
    assert "# DICTAMEN PERICIAL FORENSE" in md
    assert "Ley Nº 31814" in md
    assert informe.hash_sha256_acta in md


def test_integracion_orquestador_bucle_completo():
    """Valida el bucle end-to-end desde el orquestador: inferencia C2 -> recolección EDAN -> calibración pericial."""
    orchestrator = AmaruOrchestrator()

    # 1. El orquestador emite alertas para dos distritos en sesión operativa
    res_catacaos = orchestrator.calcular_irce_fen_distrital(
        distrito="Catacaos",
        lluvia_mm=80.0,
        anomalia_tsm=3.2,
        anegamiento_dias=5
    )
    res_lima = orchestrator.calcular_irce_fen_distrital(
        distrito="Lima",
        lluvia_mm=2.0,
        anomalia_tsm=0.4,
        anegamiento_dias=0
    )

    assert len(orchestrator.historial_decisiones_c2) >= 2

    # 2. Tras el evento, se reporta el Ground Truth oficial (EDAN)
    ground_truth = [
        ResultadoRealEvento(
            ubigeo="Catacaos",
            distrito="Catacaos",
            ocurrio_desborde_o_huaico=True,
            tiempo_evacuacion_requerido_horas=14.0,
            danos_totales_soles=5000000.0
        ),
        ResultadoRealEvento(
            ubigeo="Lima",
            distrito="Lima",
            ocurrio_desborde_o_huaico=False
        )
    ]

    # 3. Se ejecuta la evaluación post-mortem Nivel 3
    resultado_calibracion = orchestrator.ejecutar_evaluacion_post_mortem(
        resultados_reales=ground_truth,
        evento_nombre="Evaluación Oficial FEN Costero 2026"
    )

    assert "id_informe" in resultado_calibracion
    assert len(resultado_calibracion["hash_sha256"]) == 64
    assert resultado_calibracion["sello_soberania_humana_ley_31814"] is True
    assert resultado_calibracion["matriz_calibrada"]["es_consistente"] is True
    assert resultado_calibracion["matriz_calibrada"]["cr"] <= 0.10

    # 4. Verificar que el último informe quedó guardado en el estado del orquestador
    vigente = orchestrator.obtener_pesos_saaty_vigentes()
    assert "pesos" in vigente
    assert vigente["es_consistente"] is True
    assert orchestrator.obtener_ultimo_informe_pericial() is not None


def test_flujo_gobernanza_comite_hito1_corte_y_hito2_ratificacion():
    """Valida el protocolo de 2 fases: Orden de Corte del Comité -> Propuesta Pendiente -> Ratificación."""
    orchestrator = AmaruOrchestrator()
    pesos_basales = orchestrator.obtener_pesos_saaty_vigentes()["pesos"].copy()

    # Simular decisiones de sesión
    orchestrator.calcular_irce_fen_distrital("Catacaos", lluvia_mm=85.0, anomalia_tsm=3.5)
    orchestrator.calcular_irce_fen_distrital("Illimo", lluvia_mm=60.0, anomalia_tsm=3.0)

    # Ground truth de INDECI
    reales = [
        ResultadoRealEvento(ubigeo="Catacaos", distrito="Catacaos", ocurrio_desborde_o_huaico=True),
        ResultadoRealEvento(ubigeo="Illimo", distrito="Illimo", ocurrio_desborde_o_huaico=True)
    ]

    # HITO 1: El Comité emite la Orden de Corte de Temporada
    orden_corte = OrdenCorteTemporadaFEN(
        id_orden_corte="ORD-CORTE-FEN-2026-001",
        evento_evaluado="Temporada FEN 2026 - Costa Norte",
        comunicado_enfen_referencia="Comunicado Oficial ENFEN N° 14-2026 (Cese de Avenidas)",
        justificacion_corte="Retorno de TSM a rango neutro y declive sostenido de caudales en Chira y Piura."
    )

    res_corte = orchestrator.declarar_corte_temporada_fen(orden_corte, reales)

    assert res_corte["id_orden_corte"] == "ORD-CORTE-FEN-2026-001"
    assert res_corte["estado_gobernanza"] == "PROPUESTA_PENDIENTE_COMITE"
    assert "PROPUESTA_PENDIENTE_COMITE" in res_corte["acta_markdown"]

    # SOBERANÍA HUMANA: La matriz activa NO debe haber cambiado todavía
    assert orchestrator.obtener_pesos_saaty_vigentes()["pesos"] == pesos_basales

    # HITO 2: El Comité sesiona y aprueba formalmente la ratificación
    acta = ActaRatificacionComite(
        id_acta="ACTA-RATIF-COMITE-2026-001",
        id_informe_pericial=res_corte["id_informe"],
        decision_comite="APROBADO_Y_RATIFICADO",
        quorum_alcanzado=True,
        votos_a_favor=4,
        votos_en_contra=0,
        observaciones_tecnicas="Matriz aprobada unánimemente por coherencia hidrodinámica.",
        firmas_digitales_miembros=[
            {"rol": "Presidente", "nombre": "Director C2", "firma": "SIG-C2-001"},
            {"rol": "Hidrólogo", "nombre": "Especialista ANA", "firma": "SIG-ANA-002"}
        ]
    )

    res_ratif = orchestrator.ratificar_calibracion_comite(acta)

    assert res_ratif["decision_comite"] == "APROBADO_Y_RATIFICADO"
    assert res_ratif["estado_gobernanza"] == "APROBADO_Y_RATIFICADO"
    assert len(res_ratif["hash_sha256_acta"]) == 64

    # Ahora SÍ la matriz activa del orquestador se actualizó a la nueva versión ratificada
    pesos_ratificados = orchestrator.obtener_pesos_saaty_vigentes()["pesos"]
    assert pesos_ratificados["w_P"] >= pesos_basales["w_P"]  # Incrementó sensibilidad


def test_rechazo_soberano_comite_conserva_matriz_basal():
    """Comprueba que si el Comité rechaza la propuesta, la matriz activa permanezca inalterada."""
    orchestrator = AmaruOrchestrator()
    pesos_iniciales = orchestrator.obtener_pesos_saaty_vigentes()["pesos"].copy()

    orden = OrdenCorteTemporadaFEN(
        id_orden_corte="ORD-CORTE-2026-002",
        evento_evaluado="Prueba Evento Atípico",
        comunicado_enfen_referencia="ENFEN 15-2026",
        justificacion_corte="Fin de evento local atípico."
    )
    reales = [ResultadoRealEvento(ubigeo="Lima", distrito="Lima", ocurrio_desborde_o_huaico=False)]

    res_corte = orchestrator.declarar_corte_temporada_fen(orden, reales)

    # El Comité rechaza por considerar el evento atípico
    acta_rechazo = ActaRatificacionComite(
        id_acta="ACTA-RECHAZO-001",
        id_informe_pericial=res_corte["id_informe"],
        decision_comite="RECHAZADO_CONSERVAR_BASAL",
        votos_a_favor=1,
        votos_en_contra=3,
        observaciones_tecnicas="Evento considerado outlier estacional. No generalizable."
    )

    res_ratif = orchestrator.ratificar_calibracion_comite(acta_rechazo)
    assert res_ratif["estado_gobernanza"] == "RECHAZADO_CONSERVAR_BASAL"

    # La matriz activa sigue siendo idéntica a la basal
    assert orchestrator.obtener_pesos_saaty_vigentes()["pesos"] == pesos_iniciales

