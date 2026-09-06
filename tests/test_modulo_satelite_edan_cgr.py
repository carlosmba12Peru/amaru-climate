"""
Pruebas Unitarias del Módulo Satélite Externo de Pre-Carga EDAN y Gobernanza de Comité CGR
Sistema AMARU-FEN - Marco Legal Ley Nº 31814 & Ley Nº 27785 (Memoria CGR Cap. 5)
"""

import pytest
from core.modulo_satelite_edan_cgr import ModuloSateliteEDANCGR

def test_inicializacion_y_criterios_cgr():
    satelite = ModuloSateliteEDANCGR(ubigeo="150119", distrito="Lurigancho-Chosica")
    assert len(satelite.criterios_cgr) == 8
    assert len(satelite.miembros_comite) == 3
    
    # Verificar que existen los criterios basados en Memoria Cap. 5
    codigos = [c.codigo for c in satelite.criterios_cgr]
    assert "CGR-01" in codigos  # Salubridad BAH (Achoma-Caylloma)
    assert "CGR-02" in codigos  # Custodia techada / Roedores (Castrovirreyna / Nasca)
    assert "CGR-03" in codigos  # Metrados consistentes (Sullana / Paita / Huarmey)
    assert "CGR-04" in codigos  # Depuración RENIEC

def test_ingesta_desacoplada_dossier_amaru():
    satelite = ModuloSateliteEDANCGR(ubigeo="150119", distrito="Lurigancho-Chosica")
    dossier_mock = {
        "id_alerta": "DOSSIER-C2-2026-CHOSICA-ALTA",
        "hash_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "departamento": "LIMA",
        "provincia": "LIMA",
        "distrito": "Lurigancho-Chosica",
        "quebrada_o_cuenca": "Quebrada Carossio",
        "coordenadas": {"lat": -11.938, "lng": -76.698},
        "tipo_evento": "Flujo de Detritos (Huaico)",
        "nivel_alerta": "ROJO",
        "familias_en_riesgo": 300,
        "sedimento_estimado_m3": 5400.0
    }
    staging = satelite.ingerir_dossier_amaru(dossier_mock)
    assert staging.id_dossier_origen == "DOSSIER-C2-2026-CHOSICA-ALTA"
    assert staging.familias_estimadas_afectadas == 300
    assert staging.viviendas_colapsadas_est == 36
    assert staging.volumen_descolmatacion_m3 == 5400.0
    assert staging.horas_retroexcavadora_est == 120.0  # 5400 / 45
    assert staging.actividad_presupuestal == "5005611 / PP 0068 (Emergencia y Reducción del Riesgo)"

def test_bloqueo_de_carga_sin_aprobacion_unanime():
    satelite = ModuloSateliteEDANCGR(ubigeo="150119", distrito="Lurigancho-Chosica")
    satelite.ingerir_dossier_amaru({"familias_en_riesgo": 100})
    
    # Uno de los miembros vota OBSERVADO
    satelite.emitir_voto_miembro("JEFE_OCI_LEGAL", "OBSERVADO", "Falta sustento de rendimiento de retroexcavadora.")
    
    acta = satelite.consolidar_sesion_comite()
    assert acta.todos_aprobaron is False
    assert acta.estado_despacho_sinpad == "BLOQUEADO_POR_COMITE"
    
    # Intento de despacho forzado debe ser denegado
    exito, msg, payload = satelite.despachar_a_sinpad()
    assert exito is False
    assert "ACCESO DENEGADO AL SINPAD" in msg
    assert payload is None

def test_bloqueo_por_criterio_cgr_fallido():
    satelite = ModuloSateliteEDANCGR(ubigeo="150119", distrito="Lurigancho-Chosica")
    satelite.ingerir_dossier_amaru({"familias_en_riesgo": 100})
    
    # Simulamos hallazgo de alimentos vencidos en almacén (Caso Achoma)
    satelite.criterios_cgr[0].estado = "OBSERVADO"
    satelite.criterios_cgr[0].hallazgo = "Se detectaron 40 sacos de avena vencidos en abril 2026."
    
    acta = satelite.consolidar_sesion_comite()
    assert acta.cumple_cgr_100 is False
    assert acta.estado_despacho_sinpad == "BLOQUEADO_POR_COMITE"
    
    exito, msg, payload = satelite.despachar_a_sinpad()
    assert exito is False
    assert "ACCESO DENEGADO AL SINPAD" in msg

def test_despacho_exitoso_con_comite_y_cgr_conforme():
    satelite = ModuloSateliteEDANCGR(ubigeo="150119", distrito="Lurigancho-Chosica")
    satelite.ingerir_dossier_amaru({"familias_en_riesgo": 150, "sedimento_estimado_m3": 3000.0})
    
    # Los 3 miembros firman APROBADO
    satelite.emitir_voto_miembro("EVALUADOR_GRD", "APROBADO", "Terreno verificado conforme.")
    satelite.emitir_voto_miembro("JEFE_OCI_LEGAL", "APROBADO", "Auditoría preventiva conforme con Memoria Cap. 5.")
    satelite.emitir_voto_miembro("ALCALDE_GERENTE", "APROBADO", "Autorización colegiada emitida según Ley 31814.")
    
    acta = satelite.consolidar_sesion_comite()
    assert acta.todos_aprobaron is True
    assert acta.cumple_cgr_100 is True
    assert acta.estado_despacho_sinpad == "AUTORIZADO"
    assert acta.hash_acta_sha256 is not None
    
    # Despacho final a SINPAD
    exito, msg, payload = satelite.despachar_a_sinpad()
    assert exito is True
    assert "TRANSMISIÓN EXITOSA" in msg
    assert payload["protocolo"] == "INDECI-SINPAD-EDAN-v2.0-SOBERANO"
    assert len(payload["firmantes_comite"]) == 3
    assert payload["acta_aprobacion_cgr_hash"] == acta.hash_acta_sha256
