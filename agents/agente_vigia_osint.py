import re
from typing import Dict, List, Any, Optional

class AgenteVigiaOSINT:
    """
    Agente Vigía OSINT Multimodal y Tri-Temporal para Emergencias FEN.
    Organizado en tres niveles temporales complementarios:
    - Tier 1: Tiempo Real Instantáneo (0 - 20 min) -> TikTok Lives, Videos cortos, X y Telegram.
    - Tier 2: Tiempo Real Rural-Comunitario (20 min - 3 horas) -> Radios provinciales (Radio Cutivalú, Yaraví, Marañón).
    - Tier 3: Consolidación & Auditoría Ex-Post (12 - 48 horas) -> Prensa escrita y diarios regionales (El Tiempo, La Industria, El Comercio).
    """

    PALABRAS_CRITICAS_TIKTOK = [
        "huaico", "huayco", "desborde", "se cayo el puente", "se cayó el puente",
        "estamos atrapados", "ayuda por favor", "el agua se lleva", "rio desbordado",
        "río desbordado", "socavamiento", "en el techo", "suban al segundo piso",
        "pedregal grande", "se rompio el dique", "se rompió el dique", "rio la leche",
        "río la leche", "quebrada san ildefonso", "quebrada el leon", "rio piura", "río piura"
    ]

    EMISORAS_RURALES_CONOCIDAS = {
        "Radio Cutivalú": {"frecuencia": "107.9 FM / 630 AM", "sede": "Piura", "cuencas": ["Bajo Piura", "Chira", "Huancabamba"]},
        "Radio Yaraví": {"frecuencia": "106.3 FM / 930 AM", "sede": "Arequipa", "cuencas": ["Río Chili", "Ocoña", "Camaná"]},
        "Radio Marañón": {"frecuencia": "96.1 FM", "sede": "Jaén - Cajamarca", "cuencas": ["Alto Marañón", "Chinchipe", "Utcubamba"]},
        "Radio Onda Azul": {"frecuencia": "640 AM / 95.7 FM", "sede": "Puno", "cuencas": ["Cuenca del Titicaca", "Ramis", "Ilave"]},
        "Radio Stereo Huarochirí": {"frecuencia": "90.5 FM", "sede": "Matucana / Chosica", "cuencas": ["Río Rímac", "Santa Eulalia"]},
        "Radio Exitosa Corresponsalía": {"frecuencia": "Red Descentralizada", "sede": "Multirregional", "cuencas": ["Costa Norte y Centro"]},
        "RPP Noticias Radio en Vivo": {
            "frecuencia": "89.7 FM / 730 AM",
            "sede": "Nacional / Piura",
            "cuencas": ["Nacional", "Bajo Piura", "Chira"],
            "stream_url": "https://rpp.pe/audio",
            "podcast_adn_piura": "https://rpp.pe/audio/podcast/entrevistas-adn/gobernador-regional-de-piura-sostiene-que-trabas-burocraticas-demoran-descolmatacion-del-rio-piura-ante-el-fenomeno-de-el-nino-23519"
        },
        "RPP Corresponsalía Regional": {"frecuencia": "Rotafono Regional", "sede": "Multirregional", "cuencas": ["Nacional"]}
    }

    DIARIOS_REGIONALES_CONOCIDOS = [
        "El Tiempo de Piura", "La Industria de Trujillo", "La Industria de Chiclayo",
        "Diario Correo", "El Comercio", "La República", "Agencia Andina"
    ]

    TIKTOK_MUNICIPALES_OFICIALES = {
        "@municatacaos": {
            "municipalidad": "Municipalidad Distrital de Catacaos",
            "ubigeo": "200105",
            "departamento": "Piura",
            "provincia": "Piura",
            "central_emergencias_grd": "907622154",
            "unidad": "Gestión de Riesgo y Desastre (GRD) - INDECI Catacaos",
            "nivel_confianza": 0.95,
            "es_fuente_oficial": True
        },
        "@munipiura": {
            "municipalidad": "Municipalidad Provincial de Piura",
            "ubigeo": "200101",
            "departamento": "Piura",
            "provincia": "Piura",
            "central_emergencias_grd": "073-305555",
            "unidad": "Oficina Provincial de Defensa Civil",
            "nivel_confianza": 0.90,
            "es_fuente_oficial": True
        },
        "@munichosica": {
            "municipalidad": "Municipalidad Distrital de Lurigancho - Chosica",
            "ubigeo": "150118",
            "departamento": "Lima",
            "provincia": "Lima",
            "central_emergencias_grd": "01-3603078",
            "unidad": "Subgerencia de GRD Chosica",
            "nivel_confianza": 0.90,
            "es_fuente_oficial": True
        },
        "@munielporvenir": {
            "municipalidad": "Municipalidad Distrital de El Porvenir",
            "ubigeo": "130103",
            "departamento": "La Libertad",
            "provincia": "Trujillo",
            "central_emergencias_grd": "044-401122",
            "unidad": "Defensa Civil y GRD El Porvenir",
            "nivel_confianza": 0.90,
            "es_fuente_oficial": True
        }
    }

    def __init__(self):
        self.nombre = "Agente Vigía OSINT Multimodal (TikTok, Radios & Prensa)"
        self.historial_reportes_tiktok: List[Dict[str, Any]] = []
        self.historial_reportes_radiales: List[Dict[str, Any]] = []
        self.historial_noticias_prensa: List[Dict[str, Any]] = []

    def analizar_transmision_o_post(self, texto_post: str, plataforma: str = "TikTok Live", autor: str = "anonimo") -> Dict[str, Any]:
        """Método de compatibilidad con interfaz previa."""
        return self.procesar_stream_tiktok(texto_transmision=texto_post, autor=autor, enlace=f"https://{plataforma.lower().replace(' ', '')}.com/post")

    # =========================================================================
    # TIER 1: TIEMPO REAL INSTANTÁNEO (TIKTOK LIVES / VIDEOS CORTOS / X)
    # =========================================================================


    def procesar_stream_tiktok(
        self,
        texto_transmision: str,
        autor: str = "usuario_anonimo",
        enlace: str = "https://tiktok.com/@live/stream_alerta",
        departamento_sospecha: str = "Piura",
        lluvia_actual_senamhi_mm: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analiza streams en vivo y clips virales de TikTok/X.
        Aplica filtro de consistencia hidrometeorológica cruzada con SENAMHI
        para identificar posibles videos reciclados o fake news de años anteriores.
        """
        texto_lower = texto_transmision.lower()
        coincidencias = [p for p in self.PALABRAS_CRITICAS_TIKTOK if p in texto_lower]
        
        es_alerta_inundacion = len(coincidencias) > 0
        nivel_severidad = "MEDIA"
        if any(k in texto_lower for k in ["atrapados", "se lleva", "techo", "auxilio", "se cayó el puente", "se cayo el puente"]):
            nivel_severidad = "CRITICA"
        elif es_alerta_inundacion:
            nivel_severidad = "ALTA"

        # Extracción de topónimos locales
        ubicacion = self._extraer_ubicacion(texto_transmision, departamento_sospecha)

        # Filtro Anti-Videos Reciclados y Fake News:
        # Si el usuario afirma que hay un desborde colosal pero SENAMHI registra 0 mm y tiempo seco
        es_sospechoso_reciclado = False
        motivo_sospecha = ""
        if lluvia_actual_senamhi_mm is not None:
            if lluvia_actual_senamhi_mm < 5.0 and nivel_severidad in ["CRITICA", "ALTA"]:
                # Podría ser onda de avenida que baja de la sierra alta, pero requiere verificación
                es_sospechoso_reciclado = True
                motivo_sospecha = f"Pluviómetro SENAMHI registra apenas {lluvia_actual_senamhi_mm} mm en la zona. Requiere verificar si es avenida de cuenca alta o video reciclado (2017/2023)."

        # Detección de Canal Oficial Municipal
        autor_norm = autor.strip().lower()
        if not autor_norm.startswith("@"):
            autor_norm = f"@{autor_norm}"
        
        info_oficial_muni = self.TIKTOK_MUNICIPALES_OFICIALES.get(autor_norm)
        es_cuenta_oficial = info_oficial_muni is not None

        # Si es canal oficial del municipio, se eleva la confianza y se ajustan los datos
        if es_cuenta_oficial:
            ubicacion = f"{info_oficial_muni['municipalidad']} ({info_oficial_muni['departamento']})"
            confianza = "ALTA_OFICIAL_INSTITUCIONAL (95%)"
            accion_despacho = (
                f"COMUNICADO OFICIAL MUNICIPAL. Contactar inmediatamente a la Central de Emergencias GRD "
                f"al número {info_oficial_muni['central_emergencias_grd']} para coordinar apoyo provincial y evacuación."
            )
        else:
            confianza = "MEDIA_BAJA (Verificar Terreno)" if es_sospechoso_reciclado else "ALTA_CONFIRMADA"
            accion_despacho = (
                "Verificar con serenazgo/PNP antes de emitir alarma masiva." 
                if es_sospechoso_reciclado else 
                "Despacho preventivo inmediato de brigada de rescate y monitoreo satelital."
            )

        reporte = {
            "tier": "Tier 1: Tiempo Real Instantáneo (0-20 min)",
            "plataforma": "TikTok Oficial / Live Municipal" if es_cuenta_oficial else "TikTok Live / Clip Viral",
            "autor": autor,
            "es_canal_oficial_municipal": es_cuenta_oficial,
            "datos_municipales_grd": info_oficial_muni,
            "enlace": enlace,
            "texto_extraido": texto_transmision,
            "es_emergencia": es_alerta_inundacion,
            "palabras_clave_detectadas": coincidencias,
            "nivel_severidad": nivel_severidad,
            "ubicacion_detectada": ubicacion,
            "filtro_consistencia_hidrologica": {
                "lluvia_senamhi_asociada_mm": lluvia_actual_senamhi_mm,
                "es_sospechoso_reciclado": False if es_cuenta_oficial else es_sospechoso_reciclado,
                "motivo_auditoria": "FUENTE OFICIAL VERIFICADA DE GOBIERNO LOCAL" if es_cuenta_oficial else motivo_sospecha,
                "confianza_veracidad": confianza
            },
            "accion_recomendada": accion_despacho
        }
        self.historial_reportes_tiktok.append(reporte)
        return reporte

    # =========================================================================
    # TIER 2: TIEMPO REAL RURAL-COMUNITARIO (RADIODIFUSIÓN PROVINCIAL)
    # =========================================================================

    def procesar_audio_radial_comunitario(
        self,
        transcripcion_cabina: str,
        emisora: str = "Radio Cutivalú",
        dial: str = "107.9 FM",
        provincia: str = "Piura",
        departamento: str = "Piura"
    ) -> Dict[str, Any]:
        """
        Procesa transcripciones de transmisiones radiales y llamadas de oyentes
        desde caseríos rurales, valles agrícolas y quebradas sin cobertura de internet.
        """
        texto_lower = transcripcion_cabina.lower()
        
        # Extracción de caserío o anexo específico
        patron_caserio = re.search(r'(caser[ií]o|anexo|sector|centro poblado|comunidad|poblado de)\s+([A-ZÁÉÍÓÚa-z\s]{3,25})', transcripcion_cabina, re.I)
        caserio_detectado = patron_caserio.group(0).strip() if patron_caserio else "Caserío rural no especificado"

        # Necesidades humanitarias identificadas en la llamada radial
        necesidades = []
        if any(k in texto_lower for k in ["agua", "sed", "sin agua potable", "tubo roto"]):
            necesidades.append("Agua potable y pastillas potabilizadoras")
        if any(k in texto_lower for k in ["comida", "alimentos", "viveres", "víveres", "hambre", "olla comun"]):
            necesidades.append("Raciones de alimentos fríos y ollas comunes")
        if any(k in texto_lower for k in ["incomunicados", "aislados", "se cayó el puente", "camino cortado", "no se puede pasar"]):
            necesidades.append("Puente aéreo / Lanchas Zodiac por aislamiento")
        if any(k in texto_lower for k in ["carpa", "calamina", "sin techo", "mojados", "se cayó la casa"]):
            necesidades.append("Kits de abrigo, calaminas y carpas de refugio")
        if any(k in texto_lower for k in ["heridos", "enfermos", "fiebre", "dengue", "posta cerrada"]):
            necesidades.append("Brigada médica de emergencia y sueros")

        if not necesidades:
            necesidades.append("Monitoreo continuo de caudal fluvial y soporte logístico")

        reporte = {
            "tier": "Tier 2: Rápido-Comunitario (20 min - 3 horas)",
            "medio": f"{emisora} ({dial})",
            "provincia": provincia,
            "departamento": departamento,
            "transcripcion": transcripcion_cabina,
            "caserio_identificado": caserio_detectado,
            "necesidades_humanitarias_urgentes": necesidades,
            "canal_comunicacion": "Llamada de poblador en cabina radial comunitaria",
            "nivel_prioridad_coen": "ALTA" if len(necesidades) >= 2 else "MEDIA",
            "accion_humanitaria_disparada": f"Preposicionamiento de ayuda humanitaria hacia {caserio_detectado} ({provincia})."
        }
        self.historial_reportes_radiales.append(reporte)
        return reporte

    def consultar_caso_estudio_rpp_piura(self) -> Dict[str, Any]:
        """
        Retorna el análisis de la denuncia en RPP del Gobernador de Piura sobre trabas burocráticas
        en la descolmatación del río Piura y la articulación de solución con el Agente Legal FEN.
        """
        return {
            "agente": self.nombre,
            "fuente": "RPP Noticias - Entrevistas ADN",
            "enlace_web": "https://rpp.pe/audio/podcast/entrevistas-adn/gobernador-regional-de-piura-sostiene-que-trabas-burocraticas-demoran-descolmatacion-del-rio-piura-ante-el-fenomeno-de-el-nino-23519",
            "stream_live": "https://rpp.pe/audio",
            "titular": "Gobernador regional de Piura sostiene que trabas burocráticas demoran descolmatación del río Piura ante el Fenómeno de El Niño",
            "vocero": "Luis Neyra León (Gobernador Regional de Piura y Presidente ANGR)",
            "demanda_clave": "Demora de decretos de urgencia y trabas burocráticas impiden ingresar maquinaria al río antes de las lluvias.",
            "respuesta_resolutiva_amaru": [
                "1. Agente Legal aplica Contratación Directa inmediata (Art. 27 Ley 30225) amparada en los 893 distritos del DS 124-2026-PCM.",
                "2. DU 010-2026 activa Obras por Impuestos para financiamiento de maquinaria sin requerir liquidez fiscal previa.",
                "3. Gobernanza Anticipatoria CAF/PUCP ejecuta fondos de contingencia (PP 0068) meses antes de la llegada de las crecidas fluviales."
            ]
        }

    # =========================================================================
    # TIER 3: CONSOLIDACIÓN & AUDITORÍA EX-POST (PRENSA Y DIARIOS REGIONALES)
    # =========================================================================

    def procesar_noticia_prensa_ex_post(
        self,
        titular: str,
        cuerpo: str,
        diario: str = "El Tiempo de Piura",
        fecha_edicion: str = "2026-09-03",
        departamento: str = "Piura"
    ) -> Dict[str, Any]:
        """
        Extrae métricas cuantitativas consolidadas de diarios regionales y prensa digital (12-48h después).
        Sirve para el cierre formal y actualización oficial de la Ficha EDAN en el SINPAD / INDECI.
        """
        texto_completo = f"{titular} {cuerpo}"
        
        # Extracción de métricas numéricas con expresiones regulares
        match_damnificados = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)\s+(?:damnificados|personas damnificadas|familias damnificadas)', texto_completo, re.I)
        match_viviendas = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)\s+(?:viviendas destruidas|casas colapsadas|viviendas colapsadas)', texto_completo, re.I)
        match_hectareas = re.search(r'([0-9]{1,3}(?:,[0-9]{3})*|[0-9]+)\s+(?:hect[aá]reas|has|hectareas agr[ií]colas)', texto_completo, re.I)
        match_puentes = re.search(r'([0-9]+)\s+(?:puentes destruidos|puentes colapsados|puentes ca[ií]dos)', texto_completo, re.I)

        damnificados_num = int(match_damnificados.group(1).replace(",", "")) if match_damnificados else 0
        viviendas_num = int(match_viviendas.group(1).replace(",", "")) if match_viviendas else 0
        has_num = int(match_hectareas.group(1).replace(",", "")) if match_hectareas else 0
        puentes_num = int(match_puentes.group(1)) if match_puentes else (1 if "puente colapsó" in texto_completo.lower() or "puente se cayó" in texto_completo.lower() else 0)

        payload_edan = {
            "poblacion_damnificada_confirmada": damnificados_num,
            "viviendas_destruidas_censo": viviendas_num,
            "hectareas_cultivo_perdidas": has_num,
            "puentes_destruidos": puentes_num
        }

        reporte = {
            "tier": "Tier 3: Consolidación & Auditoría Ex-Post (12-48 horas)",
            "fuente_periodistica": diario,
            "fecha_edicion": fecha_edicion,
            "departamento": departamento,
            "titular": titular,
            "metricas_consolidadas_edan": payload_edan,
            "utilidad_operativa": "Cierre formal y auditoría de la Ficha EDAN / SINPAD para transferencia de fondos de reconstrucción (FONDEN / MEF).",
            "validez_estadistica": "ALTA (Cifras censadas con verificación de corresponsales en terreno)"
        }
        self.historial_noticias_prensa.append(reporte)
        return reporte

    # =========================================================================
    # CONSOLIDACIÓN MULTICANAL
    # =========================================================================

    def obtener_balance_multicanal_osint(self) -> Dict[str, Any]:
        """
        Retorna el estado sintético de los 3 niveles de vigilancia ciudadana y medios.
        """
        return {
            "agente": self.nombre,
            "total_reportes_tiktok_en_vivo": len(self.historial_reportes_tiktok),
            "total_despachos_radiales_comunitarios": len(self.historial_reportes_radiales),
            "total_noticias_prensa_ex_post": len(self.historial_noticias_prensa),
            "emisoras_asociadas": list(self.EMISORAS_RURALES_CONOCIDAS.keys()),
            "diarios_regionales_asociados": self.DIARIOS_REGIONALES_CONOCIDOS,
            "ultimos_reportes_tier1": self.historial_reportes_tiktok[-3:] if self.historial_reportes_tiktok else [],
            "ultimos_reportes_tier2": self.historial_reportes_radiales[-3:] if self.historial_reportes_radiales else [],
            "ultimos_reportes_tier3": self.historial_noticias_prensa[-3:] if self.historial_noticias_prensa else []
        }

    def _extraer_ubicacion(self, texto: str, depto_default: str) -> str:
        # 1. Búsqueda de distritos y cuencas conocidas directamente en el texto
        distritos_comunes = [
            "Catacaos", "Castilla", "Chosica", "Chaclacayo", "Lurigancho", "Cura Mori",
            "Tambogrande", "Íllimo", "Jayanca", "Túcume", "Pacora", "Sullana", "Talara",
            "Paita", "Trujillo", "El Porvenir", "Huanchaco", "Ica", "La Tinguiña",
            "Santa Eulalia", "Punta Hermosa", "Huarmey", "Carabayllo", "San Juan de Lurigancho"
        ]
        for d in distritos_comunes:
            if d.lower() in texto.lower():
                return f"{d} ({depto_default})"

        # 2. Búsqueda de topónimos con conectores comunes (desde, en, quebrada, río)
        match_desde = re.search(r'(?:desde|cerca a|hacia|zona de|sector|quebrada|r[ií]o|en)\s+([A-ZÁÉÍÓÚ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóúñ]+)*)', texto)
        if match_desde:
            lugar = match_desde.group(1).strip()
            if lugar.lower() not in ["vivo", "directo", "el", "la", "los", "las"]:
                return f"{lugar} ({depto_default})"

        return f"Sector no determinado ({depto_default})"

