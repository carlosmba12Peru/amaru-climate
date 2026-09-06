import pytest
from datetime import datetime
from core.reloj_nina import MotorRelojNina, ModeloRelojNina
from core.reloj_fen import MotorRelojFEN, ModeloRelojFEN

def test_inicializacion_motor_nina():
    motor = MotorRelojNina()
    assert len(motor.meses) == 12
    
    # Verificar fijación canónica del dial polar
    mes_dic = next(m for m in motor.meses if m.hora == 12)
    assert mes_dic.angulo_grados == 0.0
    assert mes_dic.nombre_corto == "DIC"
    
    mes_jun = next(m for m in motor.meses if m.hora == 6)
    assert mes_jun.angulo_grados == 180.0
    assert mes_jun.nombre_corto == "JUN"
    assert "Solsticio de Invierno" in mes_jun.estacion
    
    mes_jul = next(m for m in motor.meses if m.hora == 7)
    assert mes_jul.angulo_grados == 210.0
    assert "Clímax" in mes_jul.estacion

def test_calculo_reloj_nina_condicion_fria_extrema():
    motor = MotorRelojNina()
    fecha_eval = datetime(2026, 5, 20) # 20 de Mayo
    
    modelo = motor.calcular_reloj(
        fecha_evaluacion=fecha_eval,
        anomalia_tsm=-1.6,
        velocidad_alisios=8.2,
        tmin_promedio=-14.0
    )
    
    assert isinstance(modelo, ModeloRelojNina)
    assert modelo.anomalia_tsm_pacifico == -1.6
    
    # Verificación del forzamiento
    minutero = modelo.minutero
    assert minutero.desfase_forzamiento_dias > 10.0
    assert minutero.calificacion_tiempo == "HELADA_TEMPRANA_ACELERADA"
    
    # Verificación del análogo histórico dominante
    analogo = modelo.analogo_dominante
    assert "2007-2008" in analogo.evento_nombre or "1988-1989" in analogo.evento_nombre
    assert analogo.porcentaje_similitud >= 80.0
    assert "Mazocruz" in analogo.indicadores_clave.get("Récord Tmin Mazocruz", "") or analogo.porcentaje_similitud > 85.0

def test_calculo_reloj_nina_condicion_benigna():
    motor = MotorRelojNina()
    fecha_eval = datetime(2026, 6, 1)
    
    modelo = motor.calcular_reloj(
        fecha_evaluacion=fecha_eval,
        anomalia_tsm=-0.1,  # Apenas frío, casi neutro
        velocidad_alisios=5.0,  # Alisios débiles
        tmin_promedio=-2.0   # Helada leve
    )
    
    minutero = modelo.minutero
    assert minutero.desfase_forzamiento_dias < 5.0
    assert minutero.calificacion_tiempo in {"RITMO_ESTACIONAL_ESTANDAR", "INVIERNO_TARDIO_BENIGNO"}

def test_generacion_svg_reloj_nina():
    motor = MotorRelojNina()
    modelo = motor.calcular_reloj(
        fecha_evaluacion=datetime(2026, 6, 15),
        anomalia_tsm=-1.2,
        velocidad_alisios=7.5,
        tmin_promedio=-12.0
    )
    
    svg = motor.generar_svg_reloj(modelo)
    
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "LA NIÑA C2" in svg
    assert "#00f2fe" in svg  # Color cian eléctrico glacial
    assert "textPath" in svg
    assert "trackGlacialMed" in svg
    assert modelo.analogo_dominante.evento_nombre in svg

def test_desacoplamiento_estricto_reloj_fen_vs_reloj_nina():
    """Garantiza que ambos motores conviven sin interferir ni contaminar sus modelos"""
    motor_fen = MotorRelojFEN()
    motor_nina = MotorRelojNina()
    
    # 1. El FEN usa forzamiento cálido (+1.8 °C) y busca pico en Marzo (hora 3.0 / 90°)
    res_fen = motor_fen.calcular_reloj(anomalia_tsm=1.8)
    assert res_fen.arco_rojo.hora_climax == 3.0
    assert res_fen.arco_rojo.angulo_climax_deg == 90.0
    assert "1997-1998" in res_fen.analogo_dominante.evento_nombre
    
    # 2. La Niña usa forzamiento frío (-1.5 °C) y busca pico en Julio (hora 6.75 / ~202.5°)
    res_nina = motor_nina.calcular_reloj(anomalia_tsm=-1.5)
    assert res_nina.arco_glacial.angulo_climax_deg == 202.5
    assert "2007-2008" in res_nina.analogo_dominante.evento_nombre
    
    # 3. Comprobar que los arcos de amenaza no se solapan en sus picos
    assert res_fen.arco_rojo.angulo_climax_deg != res_nina.arco_glacial.angulo_climax_deg
