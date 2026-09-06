import pytest
from core.ingestor_oficial import IngestorOficialSenamhiEnfen
from agents.agente_senamhi import AgenteSenamhi
from core.orchestrator import AmaruOrchestrator

def test_ingestor_inicializacion():
    ingestor = IngestorOficialSenamhiEnfen()
    assert ingestor.URL_AVISOS_SENAMHI == "https://www.senamhi.gob.pe/?p=aviso-meteorologico"
    assert ingestor.URL_PRONOSTICO_SENAMHI == "https://www.senamhi.gob.pe/?p=pronostico-climatico"

def test_ingestor_obtener_avisos():
    ingestor = IngestorOficialSenamhiEnfen()
    avisos = ingestor.obtener_avisos_meteorologicos()
    assert len(avisos) > 0
    primer_aviso = avisos[0]
    assert "titulo" in primer_aviso
    assert "nivel_alerta" in primer_aviso
    assert primer_aviso["nivel_alerta"] in ["ROJO", "NARANJA", "AMARILLO"]
    assert "url_detalle" in primer_aviso

def test_ingestor_obtener_pronostico():
    ingestor = IngestorOficialSenamhiEnfen()
    prono = ingestor.obtener_pronostico_climatico()
    assert "fuente" in prono
    assert "Precipitación" in prono["variables_monitoreadas"]
    assert prono["escenario_precipitacion_costa_norte"] is not None

def test_ingestor_obtener_informe_enfen():
    ingestor = IngestorOficialSenamhiEnfen()
    enfen = ingestor.obtener_informe_tecnico_enfen()
    assert "alerta_oficial" in enfen
    assert "anomalia_tsm_nino_1_2" in enfen
    assert enfen["anomalia_tsm_nino_1_2"] > 0
    assert "probabilidades_verano" in enfen

def test_ingestor_sincronizar_todo():
    ingestor = IngestorOficialSenamhiEnfen()
    res = ingestor.sincronizar_todo()
    assert res["estado_sincronizacion"] == "EXITOSA"
    assert res["nivel_alerta_maximo_vigente"] in ["ROJO", "NARANJA", "AMARILLO"]
    assert len(res["avisos_meteorologicos_activos"]) > 0
    assert "enfen_diagnostico_oficial" in res

def test_agente_senamhi_sincronizacion():
    agente = AgenteSenamhi()
    res = agente.sincronizar_avisos_en_vivo()
    assert res["estado"] == "SINCRONIZADO"
    assert res["total_avisos_vigentes"] > 0
    assert agente.nivel_alerta_actual in ["ROJO", "NARANJA", "AMARILLO"]

def test_orchestrator_sincronizar_fuentes_oficiales():
    orchestrator = AmaruOrchestrator()
    res = orchestrator.sincronizar_fuentes_oficiales(incluir_internacionales=True)
    assert res["estado_sincronizacion"] == "EXITOSA"
    assert "gobernanza_anticipada_enfen" in res
    assert "fuentes_internacionales" in res
    assert "matriz_consenso_dual" in res
    
    gov = res["gobernanza_anticipada_enfen"]
    assert "nivel_advertencia" in gov
    assert "ano_analogo_historico" in gov

def test_conector_internacional_noaa_indices():
    from core.ingestor_oficial import ConectorInternacionalENSO
    conector = ConectorInternacionalENSO()
    noaa = conector.obtener_indices_noaa_cpc()
    assert "anomalia_tsm_nino_1_2" in noaa
    assert "anomalia_tsm_nino_3_4" in noaa
    assert noaa["anomalia_tsm_nino_1_2"] > 0
    assert noaa["alerta_automatica"] in ["EXTRAORDINARIO", "FUERTE", "MODERADO", "DEBIL", "NEUTRO"]

def test_conector_internacional_iri_y_live():
    from core.ingestor_oficial import ConectorInternacionalENSO
    conector = ConectorInternacionalENSO()
    iri = conector.obtener_consenso_iri()
    live = conector.obtener_telemetria_elnino_live()
    
    assert "probabilidades_consenso" in iri
    assert "el_nino" in iri["probabilidades_consenso"]
    assert "elninolive.com" in live["url_mapa"]

def test_matriz_consenso_dual():
    from core.ingestor_oficial import ConectorInternacionalENSO
    conector = ConectorInternacionalENSO()
    
    enfen_mock = {"anomalia_tsm_nino_1_2": 2.4, "alerta_oficial": "ALERTA DE EL NIÑO COSTERO"}
    noaa_mock = {"anomalia_tsm_nino_1_2": 2.6, "anomalia_tsm_nino_3_4": 1.7, "status_alerta_oficial": "El Niño Advisory"}
    iri_mock = {"probabilidades_consenso": {"el_nino": 70.0}}
    
    consenso = conector.calcular_matriz_consenso(enfen_mock, noaa_mock, iri_mock)
    assert consenso["grado_convergencia"] == "ALTA_CONVERGENCIA"
    assert consenso["diferencia_tsm_grados"] == 0.2
    assert "CONSENSO CRÍTICO GLOBAL" in consenso["consenso_enjambre_amaru"]

def test_fuentes_copernicus_c3s_y_noaa_ersstv5():
    from core.ingestor_oficial import ConectorInternacionalENSO
    conector = ConectorInternacionalENSO()
    
    # 1. Test Copernicus C3S
    c3s = conector.obtener_datos_copernicus_c3s()
    assert "Copernicus C3S" in c3s["fuente"]
    assert len(c3s["modelos_activos"]) >= 5
    assert c3s["probabilidad_precipitacion_costa_norte"] > 50.0

    # 2. Test NOAA ERSSTv5
    ersst = conector.obtener_datos_noaa_ersstv5()
    assert "ERSST v5" in ersst["fuente"]
    assert ersst["anomalia_ersstv5_nino12"] > 1.5
    assert "FUERTE" in ersst["categoria_oni_global"]

    # 3. Test Sincronización Internacional Completa (5 fuentes)
    sync_int = conector.sincronizar_internacional()
    assert "copernicus_c3s" in sync_int
    assert "noaa_ersstv5" in sync_int
    assert "noaa_cpc" in sync_int
    assert "iri_columbia" in sync_int
    assert "el_nino_live" in sync_int

def test_grilla_departamental_open_meteo_coherencia_mochumi():
    """
    Verifica que la telemetría Open-Meteo de Mapa 3 desacople los UBIGEOs del score IRCE
    y mantenga 100% de coherencia con la tarjeta lateral (Mochumí 0.0 mm / Verde / Soleado).
    """
    from core.conector_open_meteo import conector_open_meteo
    grilla = conector_open_meteo.consultar_grilla_departamental_peru(dias_pronostico=3)
    assert len(grilla) >= 25
    assert "MOCHUMI_ESPECIAL" in grilla
    assert "LAMBAYEQUE" in grilla

    moch = grilla["MOCHUMI_ESPECIAL"]
    assert moch["alerta_pluviometrica"] == "VERDE"
    assert any(c in moch["condicion_texto"] for c in ["Despejado", "Soleado", "Nublado", "Parcialmente"])
    assert moch["dias"][0]["lluvia_mm"] == 0.0
    assert moch["temp_actual_c"] > 20.0

def test_portal_oficial_fen_senamhi():
    ingestor = IngestorOficialSenamhiEnfen()
    assert ingestor.URL_PORTAL_FEN == "https://www.senamhi.gob.pe/?p=fenomeno-el-nino"

    portal = ingestor.obtener_portal_fen_senamhi()
    assert portal["estado"] in ["ACTIVO", "EN_LINEA_VERIFICADO"]
    assert "https://www.senamhi.gob.pe/?p=fenomeno-el-nino" in portal["url_portal"]
    assert "comunicado_oficial_reciente" in portal
    assert "indices_oficiales" in portal
    assert "icen_igp" in portal["indices_oficiales"]
    assert "roni_noaa" in portal["indices_oficiales"]

    # Test Agente SENAMHI
    agente = AgenteSenamhi()
    res_agente = agente.consultar_portal_fen_oficial()
    assert "url_portal" in res_agente




