"""
Pruebas Unitarias del Motor Científico de El Reloj del FEN
Sistema AMARU-FEN - Sala de Mando C2
"""

import pytest
from datetime import datetime
from core.reloj_fen import MotorRelojFEN, ModeloRelojFEN

def test_inicializacion_reloj_fen():
    motor = MotorRelojFEN()
    assert len(motor.meses) == 12
    # Comprobar que Diciembre está en las 12:00 (0.0 grados)
    mes_dic = next(m for m in motor.meses if m.hora == 12)
    assert mes_dic.nombre_corto == "DIC"
    assert mes_dic.angulo_grados == 0.0

    # Marzo en las 3:00 (90.0 grados)
    mes_mar = next(m for m in motor.meses if m.hora == 3)
    assert mes_mar.nombre_corto == "MAR"
    assert mes_mar.angulo_grados == 90.0

def test_calculo_arco_rojo_amenaza():
    motor = MotorRelojFEN()
    modelo = motor.calcular_reloj(anomalia_tsm=2.4, velocidad_alisios=4.0, iph_actual=82.0)
    
    arco = modelo.arco_rojo
    assert arco.hora_inicio == 12.0
    assert arco.hora_climax == 3.0
    assert arco.angulo_inicio_deg == 0.0
    assert arco.angulo_climax_deg == 90.0
    assert arco.color_climax_hex == "#7f0000"

def test_deteccion_analogo_fen_1997_1998():
    motor = MotorRelojFEN()
    # Condiciones extremas tipo 1997-1998: TSM > 2.0 y alisios colapsados
    modelo = motor.calcular_reloj(anomalia_tsm=2.3, velocidad_alisios=4.2, iph_actual=80.0)
    analogo = modelo.analogo_dominante
    assert "1997-1998" in analogo.evento_nombre
    assert analogo.porcentaje_similitud >= 85.0
    assert analogo.tipo_evento == "Canónico Extraordinario de Cuenca Completa"

def test_desfase_minutero_adelantado_temprano():
    motor = MotorRelojFEN()
    # Fecha 15 de Septiembre
    fecha = datetime(2026, 9, 15)
    
    # Caso 1: Forzamiento severo acelera la llegada del FEN
    mod_acelerado = motor.calcular_reloj(fecha_evaluacion=fecha, anomalia_tsm=2.5, velocidad_alisios=3.5, iph_actual=85.0)
    minutero = mod_acelerado.minutero
    assert minutero.desfase_forzamiento_dias > 0
    assert minutero.calificacion_tiempo == "IMPACTO_TEMPRANO_ACELERADO"
    assert minutero.angulo_tactico_final_deg > minutero.angulo_calendario_deg

def test_generacion_svg_reloj():
    motor = MotorRelojFEN()
    modelo = motor.calcular_reloj(anomalia_tsm=2.1, velocidad_alisios=4.5, iph_actual=75.0)
    svg = motor.generar_svg_reloj(modelo)
    
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "EL RELOJ DEL FEN" in svg
    assert "12:00 INICIO FEN" in svg
    assert "1997-1998" in svg
    assert "minutero-tactico" in svg

def test_diferenciacion_anos_2026_2027():
    motor = MotorRelojFEN()
    modelo = motor.calcular_reloj()
    svg = motor.generar_svg_reloj(modelo)

    # Verificar presencia de biseles y pistas perimétricas de años
    assert "track-ano-2026" in svg
    assert "track-ano-2027" in svg
    assert "AÑO 2026" in svg
    assert "AÑO 2027" in svg

    # Verificar cuadrantes de fondo bicolor ejecutivos
    assert "cuadrante-2026" in svg
    assert "cuadrante-2027" in svg

    # Verificar insignias y cartelas de transición de año (15°)
    assert "2026 ➔ 2027" in svg
    assert "FIN AÑO 2026" in svg
    assert "INICIO AÑO 2027" in svg
    assert "glow-gold" in svg

    # Verificar etiquetas de meses con su año respectivo y barra de leyenda
    assert "'26" in svg  # SET '26, OCT '26, NOV '26, DIC '26
    assert "'27" in svg  # ENE '27, FEB '27, MAR '27...
    assert "TRANSICIÓN CICLO 2026 ➔ 2027" in svg
    assert "leyenda-ejecutiva-anos" in svg
    assert "2027 ◄ | ► 2026" in svg

