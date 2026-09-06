import pytest
from agents.agente_memoria_historica import AgenteMemoriaHistorica
from core.orchestrator import AmaruOrchestrator

def test_inicializacion_memoria_historica():
    agente = AgenteMemoriaHistorica()
    assert agente.nombre == "Agente de Memoria Histórica y Años Análogos FEN"
    assert len(agente.distritos_criticos) > 0
    assert len(agente.quebradas) > 0
    assert len(agente.estaciones_igp) > 0

def test_identificar_ano_analogo_extraordinario_1997_1998():
    agente = AgenteMemoriaHistorica()
    # Anomalía TSM +2.4 en agosto (mes 8) corresponde estrechamente al 1997-1998
    resultado = agente.identificar_ano_analogo(anomalia_tsm=2.4, mes=8)
    
    assert "ano_analogo_principal" in resultado
    analogo = resultado["ano_analogo_principal"]
    assert analogo["id"] == "1997-1998"
    assert analogo["categoria"] == "EXTRAORDINARIO_GLOBAL"
    assert analogo["similitud_porcentaje"] >= 95.0
    assert len(analogo["consecuencias_en_cascada_esperadas"]) > 0

def test_identificar_ano_analogo_costero_2017():
    agente = AgenteMemoriaHistorica()
    # Anomalía +2.1 en marzo (mes 3) es la firma del Niño Costero 2017
    resultado = agente.identificar_ano_analogo(anomalia_tsm=2.1, mes=3)
    
    analogo = resultado["ano_analogo_principal"]
    assert analogo["id"] == "2017"
    assert analogo["categoria"] == "COSTERO_SUBITO"
    assert analogo["similitud_porcentaje"] >= 95.0

def test_consultar_antecedentes_territoriales():
    agente = AgenteMemoriaHistorica()
    # Consulta para Catacaos (Bajo Piura) con lluvia que supera el umbral
    res = agente.consultar_antecedentes_territoriales(
        distrito="Catacaos",
        departamento="Piura",
        lluvia_actual_mm=85.0
    )
    
    assert res["distrito_consultado"] == "Catacaos"
    assert len(res["registros_historicos_encontrados"]) > 0
    assert res["total_poblacion_historicamente_expuesta"] > 0
    assert "Dique Pedregal" in res["infraestructura_critica_reincidente"]
    assert res["alerta_reincidencia_severa"] is True
    assert len(res["quebradas_en_peligro_inminente"]) > 0

def test_consultar_lecciones_cientificas_igp():
    agente = AgenteMemoriaHistorica()
    res = agente.consultar_lecciones_cientificas_igp("Miraflores")
    assert "Miraflores (Piura)" in res["estaciones_relevantes_1998"][0]["estacion"]
    assert len(res["conclusiones_cientificas_clave"]) > 0

def test_orchestrator_gobernanza_anticipada_con_memoria():
    orchestrator = AmaruOrchestrator()
    resultado = orchestrator.evaluar_gobernanza_anticipada(anomalia_tsm=2.4, mes=8)
    
    assert "ano_analogo_historico" in resultado
    analogo = resultado["ano_analogo_historico"]["ano_analogo_principal"]
    assert analogo["id"] == "1997-1998"
    assert resultado["trigger_presupuestal_activo"] is True

def test_estructurar_memoria_historica_1998_completa():
    agente = AgenteMemoriaHistorica()
    memoria = agente.estructurar_memoria_historica_1998()
    
    # 1. Metadatos de la sesión parlamentaria
    assert "Comisión Permanente" in memoria["fuente_oficial"]
    assert "Carlos Torres y Torres Lara" in memoria["presidencia_congreso"]
    assert "Alberto Pandolfi Arbulú" in memoria["expositor_ejecutivo"]
    
    # 2. Información técnica y pronósticos
    tecnica = memoria["informacion_tecnica"]
    assert "vientos alisios" in tecnica["definicion_mecanismo"]
    assert "pronosticos_cientificos" in tecnica
    
    # 3. Hechos y territorios
    hechos = memoria["hechos_y_territorio"]
    regiones = [r["region"] for r in hechos["regiones_criticas"]]
    assert "Tumbes" in regiones
    assert "Piura" in regiones
    assert "Ica" in regiones
    assert hechos["balance_cuantitativo_danos"]["transporte_vial"]["carreteras_asfaltadas_destruidas_km"] == 400
    
    # 4. Acciones gubernamentales clasificadas en Antes, Durante y Después
    acciones = memoria["acciones_gubernamentales"]
    assert "antes_prevencion" in acciones
    assert "durante_emergencia" in acciones
    assert "despues_reconstruccion" in acciones
    assert acciones["antes_prevencion"]["costo_invertido_dolares"] == 150000000
    assert len(acciones["durante_emergencia"]["mando_y_normatividad"]) > 0
    assert len(acciones["despues_reconstruccion"]["financiamiento_externo_concertado"]) > 0

def test_estructurar_memoria_historica_1998_filtros():
    agente = AgenteMemoriaHistorica()
    
    # Filtro Antes
    memoria_antes = agente.estructurar_memoria_historica_1998(filtro_etapa="antes")
    assert "antes_prevencion" in memoria_antes["acciones_gubernamentales"]
    assert "durante_emergencia" not in memoria_antes["acciones_gubernamentales"]
    
    # Filtro Durante
    memoria_durante = agente.estructurar_memoria_historica_1998(filtro_etapa="durante")
    assert "durante_emergencia" in memoria_durante["acciones_gubernamentales"]
    assert "antes_prevencion" not in memoria_durante["acciones_gubernamentales"]
    
    # Filtro Después
    memoria_despues = agente.estructurar_memoria_historica_1998(filtro_etapa="despues")
    assert "despues_reconstruccion" in memoria_despues["acciones_gubernamentales"]
    assert "durante_emergencia" not in memoria_despues["acciones_gubernamentales"]

def test_consultar_balance_oficial_coen_2017():
    agente = AgenteMemoriaHistorica()
    coen = agente.consultar_balance_oficial_coen_2017()
    
    assert "cifras_nacionales_consolidadas" in coen
    cifras = coen["cifras_nacionales_consolidadas"]
    assert cifras["fallecidos"] == 75
    assert cifras["damnificados"] == 100169
    assert cifras["afectados"] == 627048
    assert cifras["viviendas_colapsadas"] == 10600
    
    regiones = [r["region"] for r in coen["regiones_mayor_impacto"]]
    assert "Lambayeque" in regiones
    assert "Piura" in regiones
    assert "Lima" in regiones
    
    # Validar definiciones INDECI y fallas ingenieriles
    assert "afectado" in coen["definiciones_normativas_indeci"]
    assert "damnificado" in coen["definiciones_normativas_indeci"]
    assert len(coen["lecciones_ingenieriles_fallas_infraestructura"]) >= 2
    estructuras = [f["estructura"] for f in coen["lecciones_ingenieriles_fallas_infraestructura"]]
    assert any("Pérez de Cuéllar" in e for e in estructuras)
    assert any("Virú" in e for e in estructuras)

def test_analizar_lecciones_puentes_y_patron_chosica():
    agente = AgenteMemoriaHistorica()
    
    # Análisis de puentes
    lecciones_puentes = agente.analizar_lecciones_infraestructura_y_puentes("Pérez de Cuéllar")
    assert lecciones_puentes["total_lecciones"] == 1
    assert "desmonte" in lecciones_puentes["fallas_estructurales_identificadas"][0]["mecanismo_falla"].lower()
    
    # Análisis patrón Chosica
    patron_chosica = agente.analizar_patron_chosica_nino_costero()
    assert "Chosica" in patron_chosica["titulo"]
    assert "Quirio" in patron_chosica["quebradas_reincidentes_chosica"]
    assert "Carossio" in patron_chosica["quebradas_reincidentes_chosica"]
    assert "mallas_dinamicas" in patron_chosica["infraestructura_mitigacion"]

def test_consultar_memoria_sanitaria_ops_y_evaluar_riesgo_epidemiologico():
    agente = AgenteMemoriaHistorica()
    
    # 1. Consulta de memoria sanitaria OPS/OMS
    ops = agente.consultar_memoria_sanitaria_ops()
    assert "impacto_epidemiologico_regional" in ops
    assert ops["impacto_epidemiologico_regional"]["dengue"]["casos_totales_registrados"] == 48000
    assert "Cayetano Heredia" in ops["danos_en_red_asistencial_salud"]["hospitales_inundados"][0]
    assert len(ops["lecciones_aprendidas_salud_publica_amaru"]) >= 4
    
    # 2. Evaluación de riesgo epidemiológico post-inundación (día 10)
    eval_epi = agente.evaluar_riesgo_epidemiologico_post_inundacion(region_o_distrito="Piura - Catacaos", anegamiento_dias=10)
    assert eval_epi["region_o_distrito"] == "Piura - Catacaos"
    assert eval_epi["dias_anegamiento_evaluados"] == 10
    
    riesgos = eval_epi["evaluacion_vectorial_sanitaria"]
    assert riesgos["dengue_arbovirosis"]["nivel_riesgo"] in ["ALTO", "CRITICO"]
    assert riesgos["leptospirosis"]["nivel_riesgo"] == "CRITICO"
    assert any("doxiciclina" in acc.lower() for acc in eval_epi["acciones_tacticas_salud_amaru"])

def test_consultar_informe_enfen_n15_agosto_2026():
    agente = AgenteMemoriaHistorica()
    enfen = agente.consultar_informe_enfen_n15_agosto_2026()
    
    assert "Informe Técnico ENFEN" in enfen["documento"]
    assert enfen["fecha_emision"] == "2026-08-26"
    assert enfen["estado_alerta"] == "Alerta de El Niño Costero"
    
    # Diagnóstico térmico Niño 1+2
    n12 = enfen["diagnostico_multisectorial"]["region_nino_1_2"]
    assert "+3.56 °C" in n12["anomalia_mensual_julio_2026"]
    assert "Extraordinaria" in n12["pronostico_magnitud_primavera_verano"]["setiembre_2026_a_enero_2027"]
    
    # Impactos pesqueros IMARPE
    pesq = enfen["impactos_biologico_pesqueros"]
    assert "anchoveta" in pesq
    assert "61%" in pesq["anchoveta"]
    assert any("Mobula" in esp for esp in pesq["especies_atípicas_cálidas"])
    
    # Vínculo con políticas públicas
    assert "010-2026" in enfen["impacto_politica_publica"]["vinculacion_normativa"]
    assert "124-2026-PCM" in enfen["impacto_politica_publica"]["vinculacion_normativa"]

def test_consultar_estudio_senamhi_1997_1998():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_estudio_senamhi_1997_1998()
    
    assert "Lambayeque" in doc["titulo"]
    assert "SENAMHI" in doc["autor"]
    assert doc["total_paginas"] == 78

    
    # Validar conceptos clave físicos y operativos
    c = doc["conceptos_clave"]
    assert "teoria_carga_energetica_oceanica" in c
    assert "mecanismo_brisa_monzon_costero" in c
    assert "3,000 %" in c["anomalias_pluviales_extremas_lambayeque"]["porcentaje_sobre_la_normal"]
    assert "marco legal" in c["mandato_institucional_de_marco_legal_agil"]["conclusion_senamhi_pagina_74"]

def test_consultar_estudio_capel_molina_1998():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_estudio_capel_molina_1998()
    
    assert "Capel Molina" in doc["autor"]
    assert doc["total_paginas"] == 26
    
    evid = doc["evidencias_cuantitativas_peru"]
    # 1. Caudal récord Río Piura
    assert "4,424" in evid["caudal_record_rio_piura"]["caudal_pico"]
    assert "Bolognesi" in evid["caudal_record_rio_piura"]["colapso_puentes"]
    
    # 2. Desastre Ica y cauce estrangulado
    assert "660" in evid["catastrofe_urbana_rio_ica"]["caudal_desborde"]
    assert "250" in evid["catastrofe_urbana_rio_ica"]["capacidad_cauce_estrangulado"]
    
    # 3. Desastre criosférico Machu Picchu
    assert "Salcantay" in evid["desastre_criosferico_machu_picchu"]["descripcion"]
    assert "deshielo" in evid["desastre_criosferico_machu_picchu"]["causa_fisica_clave"]

def test_consultar_informe_senamhi_cenepred_69_2026():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_informe_senamhi_cenepred_69_2026()
    
    assert "69-2026" in doc["identificador"]
    assert "CENEPRED" in doc["solicitante"]
    assert "PISCO v2.2" in doc["grilla_pisco"]
    assert doc["total_paginas"] == 21
    
    patrones = doc["patrones_regionales"]
    assert "250%" in patrones["costa_norte_y_vertiente_occidental"]
    assert "-75%" in patrones["sierra_sur_altiplano"]

def test_consultar_reporte_noaa_ncdc_98_02():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_reporte_noaa_ncdc_98_02()
    
    assert "98-02" in doc["identificador"]
    assert "NOAA" in doc["entidad"]
    assert "Jet Stream" in doc["mecanismo_fisico_clave"]
    assert doc["total_paginas"] == 28

def test_consultar_comparativa_oannes_fen():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_comparativa_oannes_fen()
    
    assert "Oannes" in doc["identificador"]
    assert "Andrés Vera Córdova" in doc["autor"]
    
    eventos = doc["comparativa_eventos"]
    assert "1972" in eventos["evento_1972"]["naturaleza"] or "muros de contención" in eventos["evento_1972"]["naturaleza"]
    assert "Canon Petrolero" in eventos["mega_nino_1982_1983"]["respuestas_historicas"]
    assert "4,000" in eventos["mega_nino_1997_1998"]["impacto_hidrologico"]
    assert "cuencas ciegas" in eventos["nino_costero_2017"]["falla_estructural"]
    assert len(doc["lecciones_clave"]) >= 3

def test_consultar_editorial_cooperacion_el_peruano():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_editorial_cooperacion_el_peruano()
    
    assert "El Peruano" in doc["identificador"]
    assert "69%" in doc["cifras_clave_noaa"]
    assert any("USNS Comfort" in p for p in doc["pilares_diplomacia_proactiva"])

def test_consultar_estudio_onu_unu():
    agente = AgenteMemoriaHistorica()
    doc = agente.consultar_estudio_onu_unu_1998()
    
    assert "UNU" in doc["identificador"]
    assert "Zapata" in doc["autores"]
    assert len(doc["conclusiones_clave"]) >= 2

def test_consultar_satelite_goes19():
    from agents.agente_senamhi import AgenteSenamhi
    senamhi = AgenteSenamhi()
    sat = senamhi.consultar_satelite_goes19()
    
    assert "GOES-19" in sat["satelite"]
    assert "75.2° W" in sat["posicion_orbital"]
    assert "Canal_13_Infrarrojo_Limpio_10_3um" in sat["instrumentos_clave"]["ABI_Advanced_Baseline_Imager"]
    assert "GLM_Geostationary_Lightning_Mapper" in sat["instrumentos_clave"]











