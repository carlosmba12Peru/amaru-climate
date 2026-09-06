import pytest
from agents.agente_vigia_osint import AgenteVigiaOSINT

def test_tiktok_emergencia_confirmada():
    agente = AgenteVigiaOSINT()
    texto = "En vivo desde Catacaos, el río Piura se está desbordando, estamos atrapados en el techo del colegio, ayuda por favor!"
    
    # Pluviómetro SENAMHI registra 65 mm (lluvia extrema confirmada)
    res = agente.procesar_stream_tiktok(
        texto_transmision=texto,
        autor="@vecino_catacaos",
        departamento_sospecha="Piura",
        lluvia_actual_senamhi_mm=65.0
    )
    
    assert res["es_emergencia"] is True
    assert res["nivel_severidad"] == "CRITICA"
    assert "Catacaos" in res["ubicacion_detectada"]
    assert res["filtro_consistencia_hidrologica"]["es_sospechoso_reciclado"] is False
    assert res["filtro_consistencia_hidrologica"]["confianza_veracidad"] == "ALTA_CONFIRMADA"

def test_tiktok_filtro_video_reciclado_fake_news():
    agente = AgenteVigiaOSINT()
    # Video alarmista afirmando que Chosica está siendo arrasada, pero en tiempo seco (0 mm)
    texto = "URGENTE HUAICO GIGANTESCO EN CHOSICA EL AGUA SE LLEVA TODO COMPARTAN!"
    
    res = agente.procesar_stream_tiktok(
        texto_transmision=texto,
        autor="@noticias_virales_peru",
        departamento_sospecha="Lima",
        lluvia_actual_senamhi_mm=0.0
    )
    
    assert res["es_emergencia"] is True
    assert res["filtro_consistencia_hidrologica"]["es_sospechoso_reciclado"] is True
    assert "MEDIA_BAJA" in res["filtro_consistencia_hidrologica"]["confianza_veracidad"]
    assert "Verificar" in res["accion_recomendada"]

def test_radio_comunitaria_rural_cutivalu():
    agente = AgenteVigiaOSINT()
    llamada = "Buenos días Radio Cutivalú, les hablo desde el caserío Pedregal Chico en Cura Mori. La quebrada se llevó el camino, estamos incomunicados y sin agua potable ni comida para los niños."
    
    res = agente.procesar_audio_radial_comunitario(
        transcripcion_cabina=llamada,
        emisora="Radio Cutivalú",
        dial="107.9 FM",
        provincia="Piura",
        departamento="Piura"
    )
    
    assert "Pedregal Chico" in res["caserio_identificado"]
    assert any("Agua potable" in n for n in res["necesidades_humanitarias_urgentes"])
    assert any("Raciones de alimentos" in n for n in res["necesidades_humanitarias_urgentes"])
    assert any("aislamiento" in n for n in res["necesidades_humanitarias_urgentes"])
    assert res["nivel_prioridad_coen"] == "ALTA"

def test_prensa_regional_consolidacion_ex_post():
    agente = AgenteVigiaOSINT()
    titular = "Desborde en el Bajo Piura deja 3,500 damnificados y colapso de defensas"
    cuerpo = "Según el balance confirmado del COER, las lluvias del fin de semana dejaron 1,200 viviendas destruidas y más de 4,500 hectáreas de cultivo de arroz bajo el agua. Además, 2 puentes colapsados mantienen aislados varios sectores."
    
    res = agente.procesar_noticia_prensa_ex_post(
        titular=titular,
        cuerpo=cuerpo,
        diario="El Tiempo de Piura",
        fecha_edicion="2026-09-04",
        departamento="Piura"
    )
    
    edan = res["metricas_consolidadas_edan"]
    assert edan["poblacion_damnificada_confirmada"] == 3500
    assert edan["viviendas_destruidas_censo"] == 1200
    assert edan["hectareas_cultivo_perdidas"] == 4500
    assert edan["puentes_destruidos"] == 2
    assert "EDAN" in res["utilidad_operativa"]

def test_balance_multicanal():
    agente = AgenteVigiaOSINT()
    agente.procesar_stream_tiktok("Alerta en Tumbes, río Zarumilla desbordado")
    agente.procesar_audio_radial_comunitario("Llamada a Radio Yaraví por badén en Arequipa")
    agente.procesar_noticia_prensa_ex_post("Reporte diario", "Balance con 500 damnificados")
    
    bal = agente.obtener_balance_multicanal_osint()
    assert bal["total_reportes_tiktok_en_vivo"] == 1
    assert bal["total_despachos_radiales_comunitarios"] == 1
    assert bal["total_noticias_prensa_ex_post"] == 1
    assert len(bal["emisoras_asociadas"]) >= 6

def test_tiktok_canal_oficial_catacaos_central_emergencias():
    agente = AgenteVigiaOSINT()
    texto = "COMUNICADO URGENTE: Desborde inminente del río Piura. Central de Emergencias activa: 907622154."
    
    res = agente.procesar_stream_tiktok(
        texto_transmision=texto,
        autor="@municatacaos",
        departamento_sospecha="Piura",
        lluvia_actual_senamhi_mm=10.0
    )
    
    assert res["es_canal_oficial_municipal"] is True
    assert res["datos_municipales_grd"]["central_emergencias_grd"] == "907622154"
    assert res["datos_municipales_grd"]["ubigeo"] == "200105"
    assert "95%" in res["filtro_consistencia_hidrologica"]["confianza_veracidad"]
    assert "907622154" in res["accion_recomendada"]

def test_caso_estudio_rpp_piura():
    agente = AgenteVigiaOSINT()
    caso = agente.consultar_caso_estudio_rpp_piura()
    
    assert "RPP" in caso["fuente"]
    assert "Luis Neyra" in caso["vocero"]
    assert "trabas burocráticas" in caso["titular"].lower()
    assert "rpp.pe/audio" in caso["stream_live"]
    assert len(caso["respuesta_resolutiva_amaru"]) == 3

