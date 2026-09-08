"""
Pruebas de Conexión y Actualización Dinámica de Datos para El Reloj de La Niña (AMARU-CHIRI)
Sistema AMARU - Mando y Control C2
"""

import pytest
from datetime import datetime
from core.orchestrator import AmaruOrchestrator
from core.reloj_nina import MotorRelojNina

def test_actualizacion_reloj_nina_con_datos_dinamicos():
    """
    Verifica que el Reloj de La Niña responde y actualiza sus parámetros tácticos
    al recibir nuevas telemetrías climáticas (TSM, Alisios, Tmin).
    """
    orchestrator = AmaruOrchestrator()
    fecha_base = datetime(2026, 6, 10)
    
    # 1. Escenario de Forzamiento Frío Extremo (La Niña Severa)
    resultado_frio = orchestrator.actualizar_reloj_nina(
        anomalia_tsm=-1.8,
        fecha_evaluacion=fecha_base,
        velocidad_alisios=8.8,
        tmin_promedio=-14.5
    )
    
    assert resultado_frio["anomalia_tsm"] == -1.8
    assert resultado_frio["desfase_dias"] > 10.0
    assert resultado_frio["calificacion"] == "HELADA_TEMPRANA_ACELERADA"
    assert "2007-2008" in resultado_frio["analogo_dominante"] or "1988-1989" in resultado_frio["analogo_dominante"]
    assert resultado_frio["similitud"] >= 80.0
    
    # Verificar SVG actualizado
    svg_frio = resultado_frio["svg"]
    assert "-1.8°C" in svg_frio
    assert "-14.5°C" in svg_frio
    assert "Ventana de Oro (Abril)" in svg_frio
    assert "#facc15" in svg_frio  # Amarillo táctico de la ventana de oro
    assert 'fill="#000000"' in svg_frio  # Letras negras sobre el arco glacial

    # 2. Escenario Neutro / Benigno
    resultado_benigno = orchestrator.actualizar_reloj_nina(
        anomalia_tsm=-0.1,
        fecha_evaluacion=fecha_base,
        velocidad_alisios=5.0,
        tmin_promedio=-2.0
    )
    
    assert resultado_benigno["anomalia_tsm"] == -0.1
    assert resultado_benigno["desfase_dias"] < 5.0
    assert resultado_benigno["calificacion"] in {"RITMO_ESTACIONAL_ESTANDAR", "INVIERNO_TARDIO_BENIGNO"}
    assert "-0.1°C" in resultado_benigno["svg"]

def test_sincronizacion_global_dual_fen_y_chiri_con_reloj():
    """
    Garantiza que la sincronización oficial acoplada actualiza tanto
    los indicadores de AMARU-FEN como el Reloj Crioclimático de AMARU-CHIRI.
    """
    orchestrator = AmaruOrchestrator()
    
    # Ejecutar sincronización oficial
    res_sync = orchestrator.sincronizar_fuentes_oficiales(incluir_internacionales=False)
    
    # Verificaciones AMARU-FEN
    assert "ubigeos_indicadores_actualizados" in res_sync
    assert len(res_sync["ubigeos_indicadores_actualizados"]) > 0
    
    # Verificaciones AMARU-CHIRI
    assert res_sync["amaru_chiri_sincronizado"] is True
    assert "amaru_chiri" in res_sync
    assert "amaru_chiri_reloj" in res_sync
    
    reloj_data = res_sync["amaru_chiri_reloj"]
    assert "hora_tactica" in reloj_data
    assert "desfase_dias" in reloj_data
    assert "calificacion" in reloj_data
    assert "analogo_dominante" in reloj_data
    assert "svg" in reloj_data
    assert "<svg" in reloj_data["svg"]
    assert "LA NIÑA C2" in reloj_data["svg"]

def test_preservacion_ventana_de_oro_amarillo_y_letras_negras():
    """
    Comprueba que el sector de Abril 'Ventana de Oro' mantiene su formato
    en amarillo táctico y las letras del arco glacial en negro #000000.
    """
    motor = MotorRelojNina()
    
    for tsm_test in [-0.5, -1.2, -1.9, -2.4]:
        modelo = motor.calcular_reloj(
            fecha_evaluacion=datetime(2026, 4, 15),
            anomalia_tsm=tsm_test,
            velocidad_alisios=7.5,
            tmin_promedio=-8.0
        )
        svg = motor.generar_svg_reloj(modelo)
        
        # Sector amarillo
        assert 'fill="#facc15"' in svg
        assert 'stroke="#fef08a"' in svg
        assert "trackOroAbril" in svg
        assert "Ventana de Oro (Abril)" in svg
        assert "ABR★" in svg
        
        # Letras negras en los textos del arco glacial
        assert 'fill="#000000"' in svg
        assert "VENTANA DE HELADAS SEVERAS (AMARU-CHIRI)" in svg
