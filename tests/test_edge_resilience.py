import pytest
from core.orchestrator import AmaruOrchestrator
from core.edge_resilience import GestorResilienciaOffGrid, ModoConectividad

def test_gestor_resiliencia_circuit_breaker():
    gestor = GestorResilienciaOffGrid()
    
    # 1. Modo por defecto
    estado = gestor.obtener_estado_red()
    assert estado["modo_operativo"] in [ModoConectividad.ONLINE_CLOUD, ModoConectividad.OFFLINE_EDGE]
    assert estado["buffer_local_activo"] is True
    
    # 2. Conmutación manual a modo offline (simulando caída de fibra óptica)
    nuevo_modo = gestor.forzar_modo(ModoConectividad.OFFLINE_EDGE)
    assert nuevo_modo == ModoConectividad.OFFLINE_EDGE
    assert gestor.obtener_estado_red()["es_offline"] is True
    
    # 3. Registro de evento en buffer local inmutable
    res_buffer = gestor.registrar_evento_en_buffer({
        "tipo": "FICHA_EDAN_EMERGENCIA",
        "distrito": "Catacaos",
        "damnificados": 150
    })
    assert res_buffer["status"] == "ENCOLADO_LOCAL"
    assert "OFFGRID-" in res_buffer["id"]
    
    # Verificar lectura del buffer
    eventos = gestor.leer_eventos_buffer()
    assert len(eventos) >= 1
    
    # 4. Inferencia local resiliente
    inferencia = gestor.ejecutar_inferencia_local("Generar plan táctico de evacuación")
    assert inferencia["estado"] in ["EXITO_LOCAL", "EXITO_FALLBACK_EXPERTO"]
    
    # 5. Sincronización post-restablecimiento
    sync = gestor.sincronizar_buffer_con_nube()
    assert sync["status"] == "SINCRONIZACION_EXITOSA"
    assert sync["total_sincronizados"] >= 1
    
    # Restaurar modo online
    gestor.forzar_modo(ModoConectividad.ONLINE_CLOUD)

def test_orquestador_delegacion_resiliencia():
    orchestrator = AmaruOrchestrator()
    estado = orchestrator.obtener_estado_resiliencia_red()
    assert "modo_operativo" in estado
    
    modo = orchestrator.conmutar_modo_resiliencia(ModoConectividad.OFFLINE_EDGE)
    assert modo == ModoConectividad.OFFLINE_EDGE
    
    # Restaurar
    orchestrator.conmutar_modo_resiliencia(ModoConectividad.ONLINE_CLOUD)
