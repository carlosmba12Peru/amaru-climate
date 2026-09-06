import pytest
from agents.agente_memoria_historica import AgenteMemoriaHistorica
from agents.agente_georriesgo import AgenteGeorriesgo
from core.orchestrator import AmaruOrchestrator

def test_catalogo_quebradas_enriquecido():
    agente_mem = AgenteMemoriaHistorica()
    quebradas = agente_mem.consultar_historial_quebradas()
    assert len(quebradas) >= 10
    
    # Verificar presencia de zonas de los estudios
    nombres = [q["nombre"] for q in quebradas]
    assert any("San Ildefonso" in n for n in nombres)
    assert any("El León" in n for n in nombres)
    assert any("Cuculí" in n for n in nombres)
    assert any("Payhua" in n for n in nombres)
    assert any("Quirio" in n for n in nombres)
    assert any("Huaycoloro" in n for n in nombres)
    assert any("Canto Grande" in n for n in nombres)
    assert any("Cansas" in n for n in nombres)

def test_filtro_quebradas_por_zona():
    agente_mem = AgenteMemoriaHistorica()
    
    # Trujillo
    q_trujillo = agente_mem.consultar_historial_quebradas("Trujillo")
    assert len(q_trujillo) >= 2
    assert all("La Libertad" in q["region"] or "Trujillo" in q["provincia"] for q in q_trujillo)
    
    # Santa Eulalia
    q_eulalia = agente_mem.consultar_historial_quebradas("Santa Eulalia")
    assert len(q_eulalia) >= 3
    
    # San Juan de Lurigancho
    q_sjl = agente_mem.consultar_historial_quebradas("San Juan de Lurigancho")
    assert len(q_sjl) >= 3

def test_evaluar_probabilidad_reincidencia():
    agente_mem = AgenteMemoriaHistorica()
    
    # San Ildefonso con 50 mm de lluvia (supera umbral 40 mm)
    eval_san_ildefonso = agente_mem.evaluar_probabilidad_reincidencia_quebrada("San Ildefonso", lluvia_mm=50.0)
    assert eval_san_ildefonso["probabilidad_activacion_pcaq"] >= 0.90
    assert eval_san_ildefonso["nivel_alerta"] == "ROJO_CRITICO"
    assert eval_san_ildefonso["tiempo_concentracion_horas"] == 2.5
    assert not eval_san_ildefonso["alerta_impacto_rapido"]
    
    # Cuculí (Santa Eulalia) con 25 mm (supera umbral 22 mm, tiempo de concentración 0.8h)
    eval_cuculi = agente_mem.evaluar_probabilidad_reincidencia_quebrada("Cuculí", lluvia_mm=25.0)
    assert eval_cuculi["probabilidad_activacion_pcaq"] >= 0.90
    assert eval_cuculi["alerta_impacto_rapido"] is True
    assert eval_cuculi["tiempo_concentracion_horas"] <= 1.0

def test_agente_georriesgo_amenaza_territorial_ampliada():
    georriesgo = AgenteGeorriesgo()
    
    # Evaluar amenaza en Santa Eulalia con lluvia 30 mm
    res = georriesgo.evaluar_amenaza_territorial("Santa Eulalia", lluvia_mm=30.0)
    assert res["total_quebradas_activadas"] >= 2
    assert res["requiere_evacuacion_inmediata"] is True
    assert len(res["puntos_estrangulamiento_viales"]) > 0

def test_orquestador_consultas_quebradas():
    orchestrator = AmaruOrchestrator()
    q_lista = orchestrator.consultar_quebradas_reincidentes("Chosica")
    assert len(q_lista) >= 1
    
    diag = orchestrator.evaluar_quebrada_especifica("Huaycoloro", lluvia_mm=35.0)
    assert diag["probabilidad_activacion_pcaq"] >= 0.85
    assert "Campoy" in diag["quebrada"] or "Huaycoloro" in diag["quebrada"]

def test_calcular_indicadores_todos_ubigeos_dinamico():
    orchestrator = AmaruOrchestrator()
    
    # 1. Escenario de Lluvia Severa FEN (+2.2 °C TSM, 70 mm lluvia)
    ubigeos_severo = orchestrator.calcular_indicadores_todos_ubigeos(lluvia_base_mm=70.0, anomalia_tsm=2.2, region_activa="PIURA")
    assert len(ubigeos_severo) == 893
    
    # Verificar Catacaos o Piura en condición crítica roja
    catacaos = next((u for u in ubigeos_severo if u["distrito"] == "CATACAOS"), None)
    assert catacaos is not None
    assert catacaos["ubigeo"].startswith("20")  # Piura
    assert catacaos["score_irce"] >= 0.75
    assert catacaos["nivel_alerta"] == "CRITICO_ROJO"

    assert catacaos["color"][0] > 200  # Canal Rojo predominante
    assert -18.5 <= catacaos["lat"] <= 0.0
    assert -81.5 <= catacaos["lon"] <= -68.0
    
    # 2. Escenario de Clima Seco / Basal (0 mm lluvia, -0.5 °C TSM)
    ubigeos_seco = orchestrator.calcular_indicadores_todos_ubigeos(lluvia_base_mm=0.0, anomalia_tsm=-0.5)
    catacaos_seco = next((u for u in ubigeos_seco if u["distrito"] == "CATACAOS"), None)
    assert catacaos_seco is not None
    assert catacaos_seco["score_irce"] < catacaos["score_irce"]
    assert catacaos_seco["nivel_alerta"] in ["BAJO_VERDE", "MEDIO_AMARILLO"]
    # El color debió cambiar en respuesta al recálculo del índice
    assert catacaos_seco["color"] != catacaos["color"]

def test_calcular_indicadores_desde_ingestas_oficiales():
    orchestrator = AmaruOrchestrator()
    
    # 1. Simulación de payload de ingesta autorizada (Aviso Rojo en Norte y TSM +2.0 °C)
    mock_sync = {
        "anomalia_tsm_detectada": 2.0,
        "nivel_alerta_maximo_vigente": "ROJO",
        "avisos_meteorologicos_activos": [
            {
                "numero_aviso": "Aviso 230",
                "titulo": "Precipitaciones extremas en la Costa y Sierra Norte (Piura, Tumbes)",
                "nivel_alerta": "ROJO"
            }
        ]
    }
    
    ubigeos_ingestados = orchestrator.calcular_indicadores_desde_ingestas_oficiales(mock_sync)
    assert len(ubigeos_ingestados) == 893
    
    # Los distritos del norte bajo aviso rojo deben estar en alerta crítica y rojos
    catacaos = next((u for u in ubigeos_ingestados if u["distrito"] == "CATACAOS"), None)
    assert catacaos is not None
    assert catacaos["score_irce"] >= 0.75
    assert catacaos["nivel_alerta"] == "CRITICO_ROJO"
    assert catacaos["color"][0] > 200
    assert catacaos["origen_ingesta"] == "INGESTAS_AUTORIZADAS_SENAMHI_ENFEN"


def test_corredor_cabeceras_andinas_estructura():
    georriesgo = AgenteGeorriesgo()
    corredor = georriesgo.obtener_corredor_cabeceras()
    assert "tramos_orograficos" in corredor
    assert len(corredor["tramos_orograficos"]) >= 6
    
    # Verificar presencia de tramos clave
    tramos_nom = [t["id_tramo"] for t in corredor["tramos_orograficos"]]
    assert "TRAMO-LAMBAYEQUE-CHANCAY-ZANA" in tramos_nom
    assert "TRAMO-PIURA-ALTO-PIURA" in tramos_nom
    assert "TRAMO-TUMBES-CASITAS" in tramos_nom
    assert "TRAMO-ANCASH-SANTA-CASCAJAL" in tramos_nom


def test_calcular_probabilidad_dinamica_huaico_juana_rios_severo():
    georriesgo = AgenteGeorriesgo()
    # Simular tormenta torrencial en cabecera de Chongoyape: 18 mm/h, 45 mm acumulado en 24h
    res = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-LAM-01",  # Quebrada Juana Ríos
        lluvia_cabecera_mm_h=18.0,
        lluvia_acumulada_24h=45.0,
        saturacion_api_72h=40.0
    )
    assert res["id_quebrada"] == "Q-LAM-01"
    assert "Juana Ríos" in res["quebrada"]
    assert res["probabilidad_huaico_pct"] >= 88.0
    assert res["nivel_alerta"] == "ROJO_CRITICO"
    assert res["tiempo_concentracion_horas"] == 1.8
    assert res["tiempo_retardo_minutos"] == 108
    assert "Badén Juana Ríos" in res["puntos_estrangulamiento"]
    assert res["poblacion_en_cono_deyeccion"] >= 18000
    assert "Badén" in res["accion_tactica_inmediata"] or "Cierre" in res["accion_tactica_inmediata"]


def test_calcular_probabilidad_dinamica_huaico_condicion_seca():
    georriesgo = AgenteGeorriesgo()
    res = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Quebrada Juana Ríos",
        lluvia_cabecera_mm_h=0.0,
        lluvia_acumulada_24h=0.0,
        saturacion_api_72h=0.0
    )
    assert res["probabilidad_huaico_pct"] <= 15.0
    assert res["nivel_alerta"] == "VERDE_BAJO"
    assert "CONDICIÓN VERDE" in res["accion_tactica_inmediata"]


def test_calcular_probabilidad_dinamica_sol_sol_y_cascajal():
    georriesgo = AgenteGeorriesgo()
    
    # Sol Sol (Chulucanas) con 14 mm/h
    res_sol = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Quebrada Sol Sol y Pacchas",
        lluvia_cabecera_mm_h=14.0,
        lluvia_acumulada_24h=38.0,
        saturacion_api_72h=30.0
    )
    assert res_sol["probabilidad_huaico_pct"] >= 85.0
    assert res_sol["nivel_alerta"] == "ROJO_CRITICO"
    assert res_sol["tiempo_concentracion_horas"] == 1.5
    
    # Cascajal (Chimbote) con 12 mm/h
    res_cas = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Quebrada Cascajal",
        lluvia_cabecera_mm_h=12.0,
        lluvia_acumulada_24h=32.0,
        saturacion_api_72h=25.0
    )
    assert res_cas["probabilidad_huaico_pct"] >= 85.0
    assert res_cas["tiempo_concentracion_horas"] == 2.0


def test_orquestador_evaluar_probabilidad_dinamica_huaico():
    orchestrator = AmaruOrchestrator()
    corredor = orchestrator.obtener_corredor_cabeceras_andinas()
    assert len(corredor["tramos_orograficos"]) >= 6
    
    diag = orchestrator.evaluar_probabilidad_dinamica_huaico(
        id_o_nombre="Q-TUM-01",  # Panales y Bocapán
        lluvia_cabecera_mm_h=16.0,
        lluvia_acumulada_24h=42.0,
        saturacion_api_72h=35.0
    )
    assert diag["probabilidad_huaico_pct"] >= 85.0
    assert diag["tiempo_concentracion_horas"] == 2.5
    assert "Casitas" in diag["distrito_cabecera"] or "Casitas" in diag["distritos_impactados"]


def test_homologacion_oficial_registros_estado():
    georriesgo = AgenteGeorriesgo()
    catalogo = georriesgo.obtener_catalogo_completo()
    assert len(catalogo) >= 33
    
    # 1. Búsqueda por código Pfafstetter ANA
    res_ana = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="ANA-PF-137564",
        lluvia_cabecera_mm_h=15.0,
        lluvia_acumulada_24h=38.0
    )
    assert res_ana["id_quebrada"] in ["Q-LAM-01", "Q-LAM-02"]
    assert "Juana Ríos" in res_ana["quebrada"] or "Yaipón" in res_ana["quebrada"]
    assert "homologacion_oficial" in res_ana
    assert res_ana["homologacion_oficial"]["codigo_pfafstetter_ana"] == "ANA-PF-137564"

    # 2. Búsqueda por código documental CENEPRED SIGRID
    res_sigrid = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="SIGRID-DOC-4542",
        lluvia_cabecera_mm_h=14.0,
        lluvia_acumulada_24h=37.0
    )
    assert "Oyotún" in res_sigrid["quebrada"] or "Cerro al Umbral" in res_sigrid["quebrada"] or "Algarrobal" in res_sigrid["quebrada"]
    assert res_sigrid["homologacion_oficial"]["codigo_sigrid_cenepred"] == "SIGRID-DOC-4542"

    # 3. Búsqueda por código vial MTC Provías
    res_mtc = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="PE-06A km 68+200",
        lluvia_cabecera_mm_h=16.0,
        lluvia_acumulada_24h=40.0
    )
    assert res_mtc["id_quebrada"] == "Q-LAM-01"
    assert "Chongoyape" in res_mtc["homologacion_oficial"]["distrito_receptor_nombre"]

def test_filtrado_historico_sincronizaciones_por_periodos():
    orchestrator = AmaruOrchestrator()
    
    # 1 Día (últimas 24h)
    snaps_1d = orchestrator.obtener_historico_sincronizaciones(periodo="1_DIA")
    assert len(snaps_1d) >= 1
    
    # 5 Días
    snaps_5d = orchestrator.obtener_historico_sincronizaciones(periodo="5_DIAS")
    assert len(snaps_5d) >= len(snaps_1d)
    
    # 7 Días (1 semana)
    snaps_7d = orchestrator.obtener_historico_sincronizaciones(periodo="7_DIAS")
    assert len(snaps_7d) >= len(snaps_5d)
    
    # 1 Mes (30 días)
    snaps_1m = orchestrator.obtener_historico_sincronizaciones(periodo="1_MES")
    assert len(snaps_1m) >= len(snaps_7d)
    
    # 1 Año (365 días) y Todo
    snaps_1a = orchestrator.obtener_historico_sincronizaciones(periodo="1_ANO")
    snaps_todo = orchestrator.obtener_historico_sincronizaciones(periodo="TODO")
    assert len(snaps_1a) >= len(snaps_1m)
    assert len(snaps_todo) >= len(snaps_1a)
    
    # Comprobar que los campos de semáforo existen
    ultimo = snaps_1d[-1]
    for key in ["timestamp", "rojos", "naranjas", "amarillos", "verdes"]:
        assert key in ultimo


def test_denominacion_canonica_amaru_fen_y_entidades_oficiales():
    """Valida que todas las quebradas mantengan el código canónico AMARU-FEN (Q-XXX-NN)
    y declaren explícitamente su denominación y la entidad pública que las denomina."""
    import re
    georriesgo = AgenteGeorriesgo()
    catalogo = georriesgo.obtener_catalogo_completo()
    assert len(catalogo) == 46

    patron_amaru = re.compile(r"^Q-[A-Z]{3}-\d{2}$")

    for q in catalogo:
        # 1. Código canónico y Denominación Identificable AMARU-FEN
        id_amaru = q["id_quebrada"]
        assert patron_amaru.match(id_amaru), f"Código {id_amaru} no cumple el patrón canónico Q-XXX-NN"
        assert q["denominacion_amaru"] == f"{id_amaru}: {q['nombre']}"
        assert q["codigo_tactico_c2"].startswith(id_amaru)
        assert "AMARU" in q["entidad_amaru"]

        # 2. Denominación y Entidad IGP
        assert "denominacion_oficial_igp" in q
        assert "codigo_oficial_igp" in q
        assert "entidad_igp" in q
        assert "IGP" in q["entidad_igp"] or "Instituto Geofísico" in q["entidad_igp"]

        # 3. Denominación y Entidad ANA
        assert "codigo_pfafstetter_ana" in q
        assert q["codigo_pfafstetter_ana"].startswith("ANA-PF-")

        # 4. Denominación y Entidad INGEMMET
        assert "codigo_ingemmet_peligro" in q
        assert q["codigo_ingemmet_peligro"].startswith("PEL-ING-")

        # 5. Denominación y Entidad CENEPRED
        assert "codigo_sigrid_cenepred" in q
        assert q["codigo_sigrid_cenepred"].startswith("SIGRID-DOC-")

        # 6. Denominación y Entidad MTC / Provías
        assert "codigo_vial_mtc_pvn" in q

        # 7. Denominación y Entidad INEI (Ubigeo)
        assert len(q["ubigeo_cabecera"]) == 6
        assert len(q["ubigeo_receptor"]) == 6


def test_red_igp_lahares_huaicos_busqueda_y_doble_confirmacion():
    """Valida la resolución de búsqueda por código o denominación del IGP (grd.igp.gob.pe/lahares-huaicos)
    y el protocolo de Doble Confirmación Soberana C2."""
    georriesgo = AgenteGeorriesgo()

    # 1. Búsqueda por denominación oficial IGP: Quebrada Limón (Canchaque - Piura)
    res_limon = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Quebrada Limón",
        lluvia_cabecera_mm_h=18.0,
        lluvia_acumulada_24h=45.0,
        saturacion_api_72h=40.0
    )
    assert res_limon["id_quebrada"] == "Q-PIU-06"
    assert res_limon["homologacion_oficial"]["codigo_amaru"] == "Q-PIU-06"
    assert res_limon["homologacion_oficial"]["denominacion_igp"] == "Quebrada Limón"
    assert res_limon["homologacion_oficial"]["codigo_oficial_igp"] == "IGP-HUAICO-PIU-LIMON-01"
    assert res_limon["homologacion_oficial"]["monitoreo_igp_in_situ"] is True
    
    # Validar telemetría in situ y consenso
    assert res_limon["telemetria_in_situ_igp"]["monitoreada_por_igp"] is True
    assert res_limon["telemetria_in_situ_igp"]["es_flujo_activo"] is True
    assert res_limon["telemetria_in_situ_igp"]["velocidad_flujo_ms"] > 0.0
    assert res_limon["telemetria_in_situ_igp"]["altura_flujo_m"] > 0.0
    assert res_limon["telemetria_in_situ_igp"]["alarma_sonora_activa"] is True
    assert len(res_limon["telemetria_in_situ_igp"]["puntos_criticos_eta"]) > 0
    assert "DOBLE_CONFIRMACION_CRITICA_SOBERANA" in res_limon["consenso_doble_confirmacion_c2"]["nivel_consenso"]
    assert res_limon["consenso_doble_confirmacion_c2"]["doble_confirmacion_activa"] is True

    # 2. Búsqueda por código oficial IGP: Río Seco Chosica
    res_rioseco = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="IGP-HUAICO-LIM-RIOSECO-01",
        lluvia_cabecera_mm_h=15.0,
        lluvia_acumulada_24h=35.0
    )
    assert res_rioseco["id_quebrada"] == "Q-LIM-09"
    assert res_rioseco["homologacion_oficial"]["codigo_amaru"] == "Q-LIM-09"
    assert "Chosica" in res_rioseco["distrito_cabecera"]
    assert res_rioseco["consenso_doble_confirmacion_c2"]["doble_confirmacion_activa"] is True

    # 3. Búsqueda por código oficial IGP: San Lázaro Misti Arequipa
    res_sl = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="IGP-LAHAR-ARE-SANLAZARO-02",
        lluvia_cabecera_mm_h=14.0,
        lluvia_acumulada_24h=30.0
    )
    assert res_sl["id_quebrada"] == "Q-ARE-01"
    assert res_sl["region"] == "Arequipa"
    assert res_sl["homologacion_oficial"]["codigo_amaru"] == "Q-ARE-01"

    # 4. Condición seca en Quebrada Limón -> Consenso en equilibrio
    res_limon_seco = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-PIU-06",
        lluvia_cabecera_mm_h=0.0,
        lluvia_acumulada_24h=0.0
    )
    assert "VIGILANCIA EN REPOSO" in res_limon_seco["consenso_doble_confirmacion_c2"]["nivel_consenso"]
    assert res_limon_seco["consenso_doble_confirmacion_c2"]["doble_confirmacion_activa"] is False

    # 5. Resolución y fácil identificación de Q-ARE-03 con código, número y nombre
    res_are03 = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-ARE-03: Quebradas Huarangal, Pastores y El Pato (Lahar Misti)",
        lluvia_cabecera_mm_h=12.0,
        lluvia_acumulada_24h=25.0
    )
    assert res_are03["id_quebrada"] == "Q-ARE-03"
    assert "Huarangal" in res_are03["quebrada"]
    assert res_are03["homologacion_oficial"]["codigo_amaru"] == "Q-ARE-03"
    assert "Q-ARE-03" in res_are03["homologacion_oficial"]["denominacion_amaru"]
    assert "Huarangal" in res_are03["homologacion_oficial"]["denominacion_amaru"]
    assert res_are03["homologacion_oficial"]["codigo_tactico_c2"].startswith("Q-ARE-03-")

    # Búsqueda por slug táctico C2
    res_are03_slug = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-ARE-03-HUARANGAL",
        lluvia_cabecera_mm_h=5.0
    )
    assert res_are03_slug["id_quebrada"] == "Q-ARE-03"


def test_quebradas_canete_e_ica_integradas():
    """Valida la integración de las quebradas de Cañete (Q-LIM-10 a Q-LIM-16) e Ica (Q-ICA-02)."""
    georriesgo = AgenteGeorriesgo()

    # 1. Quebrada Parca (Chilca - Cañete)
    res_parca = georriesgo.calcular_probabilidad_dinamica_huaico("Q-LIM-10")
    assert res_parca["id_quebrada"] == "Q-LIM-10"
    assert "Parca" in res_parca["quebrada"]
    assert "Chilca" in res_parca["distrito_cabecera"]
    assert "PE-1S" in res_parca["homologacion_oficial"]["codigo_vial_mtc_pvn"]

    # 2. Quebrada Las Viñas (Santa Cruz de Flores - Cañete / SIGRID Doc 5784)
    res_vinas = georriesgo.calcular_probabilidad_dinamica_huaico("SIGRID-DOC-5784")
    assert res_vinas["id_quebrada"] == "Q-LIM-12"
    assert "Flores" in res_vinas["distrito_cabecera"]
    assert res_vinas["homologacion_oficial"]["codigo_sigrid_cenepred"] == "SIGRID-DOC-5784"

    # 3. Quebrada Calango (SIGRID Doc 5776)
    res_calango = georriesgo.calcular_probabilidad_dinamica_huaico("SIGRID-DOC-5776")
    assert res_calango["id_quebrada"] == "Q-LIM-13"
    assert "Calango" in res_calango["quebrada"]

    # 4. Quebrada Río Grande (Asia - Cañete / SIGRID Doc 5799)
    res_asia = georriesgo.calcular_probabilidad_dinamica_huaico("SIGRID-DOC-5799")
    assert res_asia["id_quebrada"] == "Q-LIM-14"
    assert "Asia" in res_asia["homologacion_oficial"]["distrito_receptor_nombre"]

    # 5. Quebradas Zúñiga (SIGRID Doc 5629)
    res_zuniga = georriesgo.calcular_probabilidad_dinamica_huaico("SIGRID-DOC-5629")
    assert res_zuniga["id_quebrada"] == "Q-LIM-16"

    # 6. Quebrada Pampas de Chincha (Alto Larán / Lámina Oficial ANA N° 11)
    res_chincha = georriesgo.calcular_probabilidad_dinamica_huaico("Q-ICA-02")
    assert res_chincha["id_quebrada"] == "Q-ICA-02"
    assert "Chincha" in res_chincha["quebrada"]
    assert res_chincha["poblacion_en_cono_deyeccion"] == 140


def test_triangulo_hidrografico_y_boletin_extradecreto():
    """Valida la estructura del Triángulo Hidrográfico y la emisión del Dictamen Pericial C2 para distritos extradecreto."""
    georriesgo = AgenteGeorriesgo()

    # Evaluar Quebrada Las Viñas con tormenta severa (18 mm/h)
    res = georriesgo.calcular_probabilidad_dinamica_huaico(
        id_o_nombre="Q-LIM-12",
        lluvia_cabecera_mm_h=18.0,
        lluvia_acumulada_24h=40.0,
        saturacion_api_72h=35.0
    )
    assert "triangulo_hidrografico" in res
    tri = res["triangulo_hidrografico"]

    # Verificar 3 vértices: Margen Superior, Tránsito, Tierras Abajo
    assert "vertice_superior_cabecera" in tri
    assert "vertice_medio_transito" in tri
    assert "vertice_inferior_cono" in tri
    assert tri["tiempo_arribo_cono_minutos"] > 0
    assert tri["propagar_alerta_triangulo"] is True

    # Verificar emisión del Boletín Pericial C2 de Ampliación de Decreto
    assert res["probabilidad_huaico_pct"] >= 85.0
    boletin = res["boletin_pericial_ampliacion_decreto"]
    assert boletin is not None
    assert boletin["emitir_boletin"] is True
    assert "DICTAMEN PERICIAL C2" in boletin["titulo"]
    assert "Ley N° 29664" in boletin["base_legal"]
    assert "0068" in boletin["accion_financiera"] or "068" in boletin["accion_financiera"]


def test_evidencia_visual_oficial_y_descargo_amaru():
    """Valida que AMARU-FEN declare explícitamente la fuente oficial de fotos y cartografía (CENEPRED/ANA)
    y mantenga el descargo legal de que AMARU-FEN no toma fotos."""
    georriesgo = AgenteGeorriesgo()

    # Quebrada Pampas de Chincha con Lámina Oficial ANA N° 11
    res = georriesgo.calcular_probabilidad_dinamica_huaico("Q-ICA-02")
    assert "evidencia_visual_oficial" in res
    evid = res["evidencia_visual_oficial"]
    assert evid["tiene_evidencia_visual"] is True
    assert "ANA" in evid["entidad_fuente"] or "Autoridad Nacional del Agua" in evid["entidad_fuente"]
    assert "AMARU-FEN no toma fotos" in evid["atribucion_obligatoria"]
    assert evid["datos_censales_lamina"]["total_habitantes"] == 140
    assert evid["datos_censales_lamina"]["viviendas_riesgo"] == 20


