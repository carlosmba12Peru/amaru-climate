import pytest
from agents.agente_legal_normativo import AgenteLegalNormativo
from core.orchestrator import AmaruOrchestrator

def test_agente_legal_inicializacion_y_catalogo():
    agente = AgenteLegalNormativo()
    normas = agente.consultar_normas_vigentes()
    
    assert len(normas) >= 3
    ids = [n["id_norma"] for n in normas]
    assert "DS-124-2026-PCM" in ids
    assert "DU-010-2026" in ids
    assert "LEY-30225-ART-27" in ids

def test_verificar_distritos_893_ds_124():
    agente = AgenteLegalNormativo()
    
    # 1. Catacaos (Piura)
    res_catacaos = agente.verificar_distrito_estado_emergencia("Catacaos")
    assert res_catacaos["declarado_estado_emergencia"] is True
    assert any("CATACAOS" in d["distrito"] for d in res_catacaos["detalle_distritos"])
    assert "AUTORIZADO" in res_catacaos["habilitacion_operativa"]
    
    # 2. El Porvenir (La Libertad)
    res_porvenir = agente.verificar_distrito_estado_emergencia("El Porvenir", departamento="La Libertad")
    assert res_porvenir["declarado_estado_emergencia"] is True
    
    # 3. Chala (Arequipa)
    res_chala = agente.verificar_distrito_estado_emergencia("Chala")
    assert res_chala["declarado_estado_emergencia"] is True

    # 4. Distrito inexistente
    res_falso = agente.verificar_distrito_estado_emergencia("DistritoFicticioXYZ")
    assert res_falso["declarado_estado_emergencia"] is False
    assert "NO DECLARADO" in res_falso["habilitacion_operativa"]

def test_mecanismo_obras_por_impuestos_du_010():
    agente = AgenteLegalNormativo()
    res_oxi = agente.consultar_mecanismo_obras_por_impuestos_du_010()
    
    assert "010-2026" in res_oxi["norma"]
    assert "ENFEN" in res_oxi["sustento_enfen"]
    assert len(res_oxi["sectores_habilitados"]) >= 2
    assert any("MIDAGRI" in s for s in res_oxi["sectores_habilitados"])
    assert len(res_oxi["pasos_para_alcalde_o_gobernador"]) == 4

def test_generar_sustento_contratacion_directa():
    agente = AgenteLegalNormativo()
    sustento = agente.generar_sustento_contratacion_directa(
        entidad="Municipalidad Distrital de Catacaos",
        distrito="Catacaos",
        tipo_intervencion="Alquiler de 5 retroexcavadoras para encauzamiento del Río Piura"
    )
    
    assert "Artículo 27" in sustento["amparo_legal_principal"]
    assert "Emergencia" in sustento["causal"]
    assert "10 días hábiles" in sustento["plazo_regularizacion_normativo"]
    assert "PROCEDENTE" in sustento["dictamen_juridico_amaru"]
    assert "sin responsabilidad administrativa" in sustento["dictamen_juridico_amaru"]

def test_estadisticas_distritos_emergencia():
    agente = AgenteLegalNormativo()
    stats = agente.obtener_estadisticas_distritos_emergencia()
    
    assert stats["total_distritos_declarados"] == 893
    assert stats["total_departamentos"] >= 20
    assert len(stats["top_departamentos"]) > 0

def test_orquestador_integracion_legal():
    orchestrator = AmaruOrchestrator()
    
    # 1. Métodos delegados del orquestador
    check = orchestrator.verificar_estado_emergencia_distrito("Castilla", "Piura")
    assert check["declarado_estado_emergencia"] is True
    
    du010 = orchestrator.consultar_mecanismo_oxi_du010()
    assert "010-2026" in du010["norma"]
    
    # 2. Cobertura legal en el flujo de incidente
    incidente = orchestrator.procesar_incidente_completo(
        region="Piura",
        distrito="Catacaos",
        lluvia_mm=65.0,
        alerta_senamhi="ROJO",
        reporte_ciudadano_texto="El agua se está desbordando en el Dique Pedregal",
        tipo_canal="VOZ_VAPI",
        atrapados=2
    )
    
    assert "cobertura_legal_emergencia" in incidente
    assert incidente["cobertura_legal_emergencia"]["declarado_estado_emergencia"] is True

def test_generar_resolucion_alcaldia():
    orchestrator = AmaruOrchestrator()
    resolucion = orchestrator.generar_resolucion_alcaldia(
        entidad="Municipalidad Distrital de Catacaos",
        alcalde="Econ. Johnny Cruz Flores",
        distrito="Catacaos",
        intervencion="Alquiler de 5 excavadoras sobre oruga",
        monto=285000.0
    )
    
    assert "RESOLUCIÓN DE ALCALDÍA" in resolucion
    assert "Johnny Cruz Flores" in resolucion
    assert "Catacaos" in resolucion
    assert "DS Nº 124-2026-PCM" in resolucion or "124-2026-PCM" in resolucion
    assert "285,000.00" in resolucion
    assert "SE RESUELVE" in resolucion

def test_soberania_humana_ley_31814():
    orchestrator = AmaruOrchestrator()
    sob = orchestrator.consultar_marco_soberania_humana()
    
    assert "SOBERANÍA HUMANA" in sob["principio_rector"]
    assert "Ley Nº 31814" in sob["marco_normativo_nacional"]["ley"]
    assert "Supervisión Humana Obligatoria" in sob["marco_normativo_nacional"]["principios_clave_peru"][0]
    assert "UNESCO" in sob["marco_normativo_internacional"]["unesco"]
    assert "Sendai" in sob["marco_normativo_internacional"]["onu_sendai"]
    
    # Validar que el flujo táctico requiera autorización humana obligatoria
    irce = orchestrator.calcular_irce_fen_distrital(distrito="Catacaos", lluvia_mm=60.0, anomalia_tsm=2.0, anegamiento_dias=3)
    assert irce["requiere_autorizacion_humana"] is True
    assert "Ley Nº 31814" in irce["soberania_humana_ley_31814"]
    
    incidente = orchestrator.procesar_incidente_completo("Piura", "Catacaos", 50.0, "ROJO", "inundacion", "VOZ_VAPI", 0)
    assert incidente["requiere_autorizacion_humana"] is True
    assert "Ley Nº 31814" in incidente["soberania_humana_ley_31814"]

def test_matriz_nacional_fondes_1891():
    agente = AgenteLegalNormativo()
    assert len(agente.distritos_fondes_1891) == 1891
    resumen = agente.obtener_resumen_nacional_fondes()
    assert resumen["total_distritos"] == 1891
    distrib = resumen["distribucion_riesgo"]
    assert distrib["Muy Alto"] == 240
    assert distrib["Alto"] == 798
    
    # Validar consulta de Molinopampa (Oficio 0537-2026-ANA-J)
    res_moli = agente.consultar_distrito_riesgo_fondes("010114")
    assert res_moli["total_coincidencias"] == 1
    moli = res_moli["coincidencias"][0]
    assert moli["distrito"] == "MOLINOPAMPA"
    assert moli["nivel_peligro_riesgo_sigrid"] == "Muy Alto"
    assert "ANA-J" in moli["documento_sustento"]
    assert moli["priorizacion_fondes"] is True
    
    # Validar consulta de Calango (Cañete, Lima)
    res_cal = agente.consultar_distrito_riesgo_fondes("CALANGO", "LIMA")
    assert res_cal["total_coincidencias"] >= 1
    cal = res_cal["coincidencias"][0]
    assert cal["ubigeo"] == "150503"
    assert cal["nivel_peligro_riesgo_sigrid"] == "Alto"
    assert "00072-2026-CENEPRED/J" in cal["documento_sustento"]



