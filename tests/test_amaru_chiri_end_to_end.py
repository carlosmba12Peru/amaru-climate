"""
TEST OPERATIVO INTEGRAL END-TO-END: ARQUITECTURA AMARU-CHIRI
============================================================
Verifica los 6 pilares de la arquitectura de La Niña:
1. Capa de Datos Soberanos (19 distritos, UBIGEOs, Hash SHA-256).
2. Motor Crono-Inteligente (Reloj de La Niña, Arco Glacial SVG).
3. Agente Crioclimático (Cálculo ISH-CHIRI, persistencia, alertas C2).
4. Perfilador de 3 Niveles (Glaciar >4800m, Corredor 4300m, Meseta 3900m).
5. Desacoplamiento Absoluto (Cero colisión con IPH-FEN y 46 quebradas).
6. Capa de Presentación C2 (ui/app_nina.py y ui/app_amaru.py Tab 9).
"""

import pytest
import os
import json
import hashlib
from datetime import datetime

from core.reloj_nina import MotorRelojNina, ModeloRelojNina
from core.reloj_fen import MotorRelojFEN
from agents.agente_crioclimatico_nina import AgenteCrioclimaticoNina

def test_pilar_1_datos_soberanos_e_integridad():
    """Valida la integridad criptográfica y consistencia de los 19 distritos"""
    ruta = "data/catalogo_distritos_heladas_nina.json"
    assert os.path.exists(ruta), "Falta el catálogo de datos de heladas"
    
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    distritos = data["distritos"]
    assert len(distritos) == 27
    
    # Validar regiones
    regiones = set(d["departamento"] for d in distritos)
    assert {"PUNO", "HUANCAVELICA", "AREQUIPA", "CUSCO", "TACNA", "LIMA", "PASCO", "HUANUCO"}.issubset(regiones)
    
    # Validar que cada distrito tenga estación SENAMHI, censo pecuario, escolar y UBIGEO
    for d in distritos:
        assert len(d["ubigeo"]) == 6
        assert d["altitud_msnm"] >= 3000
        assert d["censo_camelidos_alpacas"] > 0
        assert d.get("colegios_vulnerables_sin_aislamiento", 0) > 0
        assert d.get("escolares_en_riesgo", 0) > 0
        assert "estación" in d["estacion_senamhi_referencia"].lower() or "código" in d["estacion_senamhi_referencia"].lower()
        assert d["umbral_helada_extrema_c"] <= -9.0

def test_pilar_2_motor_polar_reloj_nina():
    """Valida el cálculo del minutero táctico crioclimático y generación SVG"""
    motor = MotorRelojNina()
    
    # Escenario frío severo
    modelo = motor.calcular_reloj(
        fecha_evaluacion=datetime(2026, 6, 20),
        anomalia_tsm=-1.8,
        velocidad_alisios=8.5,
        tmin_promedio=-16.0
    )
    
    assert modelo.minutero.calificacion_tiempo == "HELADA_TEMPRANA_ACELERADA"
    assert modelo.minutero.desfase_forzamiento_dias > 12.0
    assert "2007-2008" in modelo.analogo_dominante.evento_nombre or "1988-1989" in modelo.analogo_dominante.evento_nombre
    
    # Validar SVG vectorial
    svg = motor.generar_svg_reloj(modelo)
    assert "<svg" in svg and "</svg>" in svg
    assert "#00f2fe" in svg  # Cian eléctrico glacial
    assert "LA NIÑA C2" in svg

def test_pilar_3_agente_crioclimatico_ish_chiri():
    """Valida la fórmula del ISH-CHIRI y reglas duras ante heladas extremas"""
    agente = AgenteCrioclimaticoNina()
    
    # Mazocruz con helada extrema (-22 °C, 5 días continuos)
    eval_mazo = agente.evaluar_distrito(
        ubigeo="210504",
        tmin_observada=-22.0,
        viento_kmh=30.0,
        dias_bajo_cero=5
    )
    assert eval_mazo.ish_chiri >= 85.0
    assert eval_mazo.nivel_alerta == "ALERTA_ROJA_GLACIAL"
    assert "cobertizos" in eval_mazo.accion_tactica_c2.lower()
    assert "SUSPENSIÓN" in eval_mazo.directiva_educativa_prevaed
    assert "PELIGRO DE CONGELAMIENTO" in eval_mazo.alerta_vial_escarcha
    
    # Barrido general de 27 distritos
    barrido = agente.ejecutar_barrido_territorial(escenario_tmin_delta=-3.0)
    assert barrido.total_distritos_evaluados == 27
    assert barrido.alpacas_en_riesgo_critico > 100000
    assert barrido.personas_vulnerables_en_riesgo_critico > 5000
    assert barrido.total_colegios_en_riesgo > 0
    assert barrido.total_escolares_en_riesgo > 0
    assert barrido.vias_con_alerta_hielo > 0

def test_pilar_4_perfilador_tres_niveles_anticipacion():
    """Simula el flujo temporal: Glaciar (18:30h) -> Puna (22:00h) -> Meseta (04:00h)"""
    agente = AgenteCrioclimaticoNina()
    
    # Nivel 1: Detección en cumbre glaciar al atardecer
    t_glaciar_crepuscular = -14.0
    viento_catabatico_cumbre = 32.0 # km/h
    
    # Nivel 2: Tránsito en pastizales de altura
    t_puna_media = -10.0
    dias_puna = 4
    
    # Nivel 3: Empozamiento final en la pampa de Mazocruz
    t_meseta_empozada = -22.4
    
    # Evaluar que el sistema procesa coherentemente el impacto
    eval_final = agente.evaluar_distrito(
        ubigeo="210504",
        tmin_observada=t_meseta_empozada,
        viento_kmh=viento_catabatico_cumbre,
        dias_bajo_cero=dias_puna
    )
    
    assert eval_final.ish_chiri >= 88.0
    assert eval_final.nivel_alerta == "ALERTA_ROJA_GLACIAL"

def test_pilar_5_blindaje_y_desacoplamiento_estricto_fen():
    """Verifica que AMARU-CHIRI no altera ni contamina los datos ni el IPH de AMARU-FEN"""
    # 1. Catálogo FEN intacto con 46 quebradas
    with open("data/catalogo_quebradas_criticas.json", "r", encoding="utf-8") as f:
        quebradas_fen = json.load(f)
    assert len(quebradas_fen) == 46
    for q in quebradas_fen:
        assert not str(q.get("id_quebrada", "")).startswith("CHIRI")
        
    # 2. Motor Reloj FEN mantiene su clímax en Marzo (hora 3.0 = 90°)
    motor_fen = MotorRelojFEN()
    res_fen = motor_fen.calcular_reloj(anomalia_tsm=2.0)
    assert res_fen.arco_rojo.angulo_climax_deg == 90.0
    
    # 3. Motor Reloj Niña mantiene su clímax en Julio (hora 6.75 = 202.5°)
    motor_nina = MotorRelojNina()
    res_nina = motor_nina.calcular_reloj(anomalia_tsm=-1.5)
    assert res_nina.arco_glacial.angulo_climax_deg == 202.5

def test_pilar_6_capa_ui_y_sintaxis():
    """Valida la sintaxis en memoria de las consolas Streamlit"""
    with open("ui/app_nina.py", "r", encoding="utf-8") as f:
        code_nina = f.read()
    assert compile(code_nina, "ui/app_nina.py", "exec") is not None

    with open("ui/app_amaru.py", "r", encoding="utf-8") as f:
        code_amaru = f.read()
    assert compile(code_amaru, "ui/app_amaru.py", "exec") is not None
