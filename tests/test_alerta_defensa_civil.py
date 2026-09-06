"""
Pruebas unitarias para el Despachador de Alertas a Defensa Civil Municipal
"""
import pytest
from core.alerta_defensa_civil import DespachadorDefensaCivilMunicipal
from core.orchestrator import AmaruOrchestrator

def test_cargar_directorio_contactos():
    despachador = DespachadorDefensaCivilMunicipal()
    assert len(despachador.contactos) >= 4
    
    # Verificar datos exactos de Pueblo Nuevo - Chincha extraídos de su portal oficial
    chincha = despachador.buscar_contacto_por_ubigeo("110206")
    assert chincha is not None
    assert chincha["distrito"] == "PUEBLO NUEVO"
    assert chincha["provincia"] == "CHINCHA"
    assert chincha["departamento"] == "ICA"
    assert "Espinoza Lujan" in chincha["responsable"]["nombre_completo"]
    assert "174-2023-MDPN/GM" in chincha["responsable"]["acto_resolutivo_designacion"]
    assert chincha["canales_comunicacion"]["correo_institucional_principal"] == "defensacivil@munipnuevochincha.gob.pe"
    assert "056-265459" in chincha["canales_comunicacion"]["telefonos_emergencia"]

def test_generar_dossier_correo_chincha():
    orchestrator = AmaruOrchestrator()
    datos_chincha = {
        "ubigeo": "110206",
        "distrito": "PUEBLO NUEVO",
        "provincia": "CHINCHA",
        "departamento": "ICA",
        "score_irce": 0.825,
        "nivel_alerta": "CRITICO_ROJO",
        "semaforo": "🔴 ROJO (Evacuación Crítica Inminente)",
        "poblacion": 68400
    }
    
    dossier = orchestrator.disparar_alerta_defensa_civil_municipal(
        ubigeo="110206",
        datos_irce=datos_chincha,
        anomalia_tsm=2.1,
        precipitacion_estimada_mm=70.0,
        modo_simulacion=True
    )
    
    assert dossier["destinatario_correo"] == "defensacivil@munipnuevochincha.gob.pe"
    assert "Whasinton Juan Espinoza" in dossier["destinatario_nombre"]
    assert "110206" in dossier["asunto"]
    assert "CRITICO_ROJO" in dossier["asunto"]
    assert "31814" in dossier["cuerpo_texto"]
    assert "Ficha EDAN" in dossier["cuerpo_texto"]
    assert "SINPAD" in dossier["cuerpo_texto"]

    assert dossier["registro_auditoria"]["estado_envio"] == "ENTREGADO_SIMULADO"

def test_historial_despachos_auditoria():
    orchestrator = AmaruOrchestrator()
    historial = orchestrator.consultar_historial_despachos_defensa_civil()
    assert isinstance(historial, list)
    assert len(historial) >= 1
