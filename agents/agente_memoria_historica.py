import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AMARU.AgenteMemoriaHistorica")

class AgenteMemoriaHistorica:
    """
    Agente Oráculo y Memoria Histórica del Enjambre AMARU-FEN.
    Centraliza el conocimiento de eventos pasados del Fenómeno El Niño (1982-1983, 1997-1998, 2017, 2023),
    permitiendo pronósticos por 'Años Análogos' (Analogue Forecasting) y consultas territoriales
    cruzadas para que todos los demás agentes tomen decisiones informadas en lugar de operar en silos.
    """

    # Perfiles térmicos y temporales de referencia de los FEN históricos documentados (Anomalía TSM Niño 1+2)
    CATALOGO_EVENTOS_HISTORICOS = {
        "1997-1998": {
            "nombre": "El Niño Extraordinario 1997-1998",
            "categoria": "EXTRAORDINARIO_GLOBAL",
            "pico_tsm_anomalia": 2.8,
            "mes_pico": 12,
            "duracion_meses": 14,
            "curva_mensual_tsm": {
                5: 1.5, 6: 1.9, 7: 2.2, 8: 2.4, 9: 2.6, 10: 2.7, 11: 2.7, 12: 2.8,
                1: 2.6, 2: 2.5, 3: 2.3, 4: 1.8
            },
            "caracteristicas_clave": (
                "Calentamiento sostenido desde invierno austral con pico extraordinario en verano. "
                "Caudal récord del Río Piura (>3,200 m3/s), anegamiento de Catacaos, activación simultánea "
                "de las quebradas San Ildefonso/San Carlos en Trujillo y 8 quebradas en Lurigancho-Chosica."
            ),
            "consecuencias_en_cascada": [
                "Desborde masivo de ríos costeros en Piura, Tumbes y Lambayeque entre enero y marzo.",
                "Colapso de defensas ribereñas y puentes troncales de la Panamericana Norte.",
                "Activación masiva de quebradas en Lima (Chosica) y La Libertad (Trujillo).",
                "Sequía severa simultánea en el Altiplano (Puno/Cusco) con pérdida agropecuaria."
            ],
            "leccion_estrategica": (
                "Pre-posicionamiento de puentes bailey, combustible y motobombas pesadas de 6'' a 8'' "
                "con 4 meses de anticipación (entre agosto y octubre)."
            )
        },
        "2017": {
            "nombre": "El Niño Costero 2017",
            "categoria": "COSTERO_SUBITO",
            "pico_tsm_anomalia": 2.1,
            "mes_pico": 3,
            "duracion_meses": 5,
            "curva_mensual_tsm": {
                12: 0.6, 1: 1.2, 2: 1.8, 3: 2.1, 4: 1.6, 5: 0.8, 6: 0.3,
                7: 0.2, 8: 0.2, 9: 0.3, 10: 0.3, 11: 0.4
            },
            "caracteristicas_clave": (
                "Calentamiento súbito localizado en la costa norte/centro del Perú sin señal previa en el Pacífico central. "
                "Lluvias convectivas violentas de corta duración y alta intensidad. 7 huaicos sucesivos en Trujillo."
            ),
            "consecuencias_en_cascada": [
                "Inundación relámpago en Piura, Chiclayo y Trujillo por saturación rápida de suelos.",
                "Corte de la Carretera Central durante más de dos semanas por aludes en Chosica.",
                "Aislamiento de distritos enteros en el Bajo Piura y colapso del alcantarillado."
            ],
            "leccion_estrategica": (
                "Monitoreo horario de estaciones de radar y alerta rápida ciudadana (OSINT y telefonía SOS) "
                "para evacuación táctica inmediata de quebradas."
            )
        },
        "1982-1983": {
            "nombre": "El Niño Catastrófico 1982-1983",
            "categoria": "EXTRAORDINARIO_HISTORICO",
            "pico_tsm_anomalia": 3.4,
            "mes_pico": 12,
            "duracion_meses": 16,
            "curva_mensual_tsm": {
                5: 1.8, 6: 2.2, 7: 2.6, 8: 2.8, 9: 3.0, 10: 3.1, 11: 3.2, 12: 3.4,
                1: 3.2, 2: 3.0, 3: 2.7, 4: 2.0
            },
            "caracteristicas_clave": (
                "Uno de los eventos más intensos del siglo XX. Precipitación acumulada récord en Piura "
                "(2,147 mm), desolación de campos agrícolas y destrucción de la infraestructura de transporte norte."
            ),
            "consecuencias_en_cascada": [
                "Aislamiento terrestre total del norte peruano durante semanas.",
                "Epidemias de malaria, cólera y enfermedades transmitidas por vectores.",
                "Hambre y crisis alimentaria severa en la sierra sur por sequía implacable."
            ],
            "leccion_estrategica": (
                "Fondos de contingencia MEF automáticos activados en etapa temprana y puentes aéreos FF.AA."
            )
        },
        "2023": {
            "nombre": "Ciclón Yaku y El Niño Costero 2023",
            "categoria": "HIBRIDO_CICLONICO",
            "pico_tsm_anomalia": 1.9,
            "mes_pico": 3,
            "duracion_meses": 6,
            "curva_mensual_tsm": {
                1: 0.5, 2: 1.1, 3: 1.9, 4: 1.7, 5: 1.4, 6: 1.0, 7: 0.9, 8: 0.8,
                9: 0.7, 10: 0.6, 11: 0.5, 12: 0.5
            },
            "caracteristicas_clave": (
                "Presencia anómala de un sistema de baja presión cuasi-ciclónico frente al mar peruano, "
                "arrastrando masiva humedad hacia cuencas de la vertiente occidental."
            ),
            "consecuencias_en_cascada": [
                "Lluvia histórica de 24h en Trujillo y Chiclayo con inundación total de centros urbanos.",
                "Río La Leche y Río Chancay con desbordes simultáneos.",
                "Activación masiva de quebradas en Lima este y norte (Chaclacayo, Chosica, Ancón)."
            ],
            "leccion_estrategica": (
                "Uso de tecnología de IA y geolocalización en tiempo real para despacho directo de brigadas."
            )
        }
    }

    def __init__(self):
        self.nombre = "Agente de Memoria Histórica y Años Análogos FEN"
        self._cargar_bases_conocimiento()

    def _cargar_bases_conocimiento(self):
        base_path = Path(__file__).parent.parent / "data"
        hist_path = base_path / "historico_fen_1998_2017.json"
        queb_path = base_path / "catalogo_quebradas_criticas.json"

        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                data_hist = json.load(f)
                self.metadata_historica = data_hist.get("metadata", {})
                self.distritos_criticos = data_hist.get("distritos_criticos", [])
                self.estaciones_igp = data_hist.get("estaciones_meteorologicas_igp_1998", [])
                self.memoria_congreso_1998 = data_hist.get("memoria_detallada_congreso_1998", {})
                self.memoria_coen_2017 = data_hist.get("memoria_oficial_coen_2017", {})
                self.memoria_ops_2017 = data_hist.get("memoria_sanitaria_ops_oms_piura_2017", {})
                self.informe_enfen_2026 = data_hist.get("informe_oficial_enfen_ano12_n15_agosto_2026", {})
                self.estudio_senamhi_1998 = data_hist.get("estudio_senamhi_fen_1997_1998_idesep", {})
                self.estudio_capel_molina_1998 = data_hist.get("investigacion_academica_capel_molina_1998", {})
                self.informe_cenepred_2026 = data_hist.get("informe_tecnico_senamhi_cenepred_69_2026_pisco", {})
                self.reporte_noaa_98 = data_hist.get("reporte_noaa_ncdc_98_02_winter_97_98", {})
                self.estudio_oannes = data_hist.get("estudio_comparativo_oannes_1972_1983_1998_2017", {})
                self.editorial_el_peruano = data_hist.get("editorial_el_peruano_cooperacion_fen_2026", {})
                self.estudio_unu_1998 = data_hist.get("estudio_onu_unu_zapata_broad_1997_1998", {})
        except Exception as e:
            logger.error(f"Error cargando historico_fen_1998_2017.json: {e}")
            self.metadata_historica = {}
            self.distritos_criticos = []
            self.estaciones_igp = []
            self.memoria_congreso_1998 = {}
            self.memoria_coen_2017 = {}
            self.memoria_ops_2017 = {}
            self.informe_enfen_2026 = {}
            self.estudio_senamhi_1998 = {}
            self.estudio_capel_molina_1998 = {}
            self.informe_cenepred_2026 = {}
            self.reporte_noaa_98 = {}
            self.estudio_oannes = {}
            self.editorial_el_peruano = {}
            self.estudio_unu_1998 = {}

        try:
            with open(queb_path, "r", encoding="utf-8") as f:
                self.quebradas = json.load(f)
        except Exception as e:
            logger.error(f"Error cargando catalogo_quebradas_criticas.json: {e}")
            self.quebradas = []

    def identificar_ano_analogo(self, anomalia_tsm: float, mes: int = 8) -> Dict[str, Any]:
        """
        Calcula la correlación y cercanía con eventos históricos documentados en base a la
        anomalía de Temperatura Superficial del Mar (°C en Región Niño 1+2) y el mes calendario.
        Devuelve el año análogo más representativo, el grado de similitud y las consecuencias esperadas.
        """
        mejor_evento = None
        menor_diferencia = 999.0
        puntuaciones = []

        for key, evento in self.CATALOGO_EVENTOS_HISTORICOS.items():
            curva = evento["curva_mensual_tsm"]
            tsm_historica_mes = curva.get(mes, evento["pico_tsm_anomalia"] * 0.7)
            diff = abs(anomalia_tsm - tsm_historica_mes)
            
            # Cálculo de similitud porcentual normalizado
            similitud = max(0.0, min(100.0, 100.0 - (diff / 2.0) * 100.0))
            
            puntuaciones.append({
                "evento_id": key,
                "nombre": evento["nombre"],
                "categoria": evento["categoria"],
                "tsm_historica_en_mes": tsm_historica_mes,
                "diferencia_grados": round(diff, 2),
                "porcentaje_similitud": round(similitud, 1)
            })

            if diff < menor_diferencia:
                menor_diferencia = diff
                mejor_evento = (key, evento)

        puntuaciones.sort(key=lambda x: x["porcentaje_similitud"], reverse=True)
        evento_seleccionado = mejor_evento[1] if mejor_evento else None
        id_seleccionado = mejor_evento[0] if mejor_evento else "Desconocido"

        # Análisis predictivo de evolución a 90 - 180 días
        es_extraordinario = anomalia_tsm >= 2.0
        horizonte_alerta = (
            "Fase Crítica Inminente: Se prevé aceleración del tren de ondas Kelvin cálidas y desborde en el verano siguiente."
            if es_extraordinario
            else "Fase de Seguimiento Activo: Posibilidad de evento moderado o costero localizado."
        )

        return {
            "agente": self.nombre,
            "consulta_actual": {
                "anomalia_tsm_evaluada": anomalia_tsm,
                "mes_calendario": mes
            },
            "ano_analogo_principal": {
                "id": id_seleccionado,
                "nombre": evento_seleccionado["nombre"] if evento_seleccionado else "N/A",
                "categoria": evento_seleccionado["categoria"] if evento_seleccionado else "N/A",
                "similitud_porcentaje": puntuaciones[0]["porcentaje_similitud"] if puntuaciones else 0.0,
                "caracteristicas_clave": evento_seleccionado["caracteristicas_clave"] if evento_seleccionado else "",
                "consecuencias_en_cascada_esperadas": evento_seleccionado["consecuencias_en_cascada"] if evento_seleccionado else [],
                "leccion_estrategica_recomendada": evento_seleccionado["leccion_estrategica"] if evento_seleccionado else ""
            },
            "ranking_similitud_completo": puntuaciones,
            "pronostico_evolucion_temporal": horizonte_alerta
        }

    def consultar_antecedentes_territoriales(
        self,
        distrito: str,
        departamento: str = "",
        lluvia_actual_mm: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Recupera el historial de desastres previos (1998, 2017) en un distrito específico,
        la infraestructura crítica que colapsó, el tiempo de anticipación necesario y
        las quebradas asociadas con su estado respecto a los umbrales de activación.
        """
        distrito_lower = distrito.lower()
        depto_lower = departamento.lower()

        coincidencias = [
            d for d in self.distritos_criticos
            if distrito_lower in d["distrito"].lower()
            or (depto_lower and depto_lower in d["departamento"].lower())
        ]

        # Quebradas ubicadas en la zona
        quebradas_zona = [
            q for q in self.quebradas
            if distrito_lower in q.get("distrito", "").lower()
            or distrito_lower in q.get("region", "").lower()
            or (depto_lower and depto_lower in q.get("region", "").lower())
        ]

        quebradas_superando = []
        if lluvia_actual_mm is not None:
            quebradas_superando = [
                q for q in quebradas_zona
                if lluvia_actual_mm >= q.get("umbral_acumulado_24h", 999.0)
            ]

        resumen_infraestructura = []
        poblacion_afectada_total = 0
        tiempos_anticipacion = []

        for c in coincidencias:
            resumen_infraestructura.extend(c.get("infraestructura_critica", []))
            poblacion_afectada_total += c.get("poblacion_vulnerable", 0)
            if "tiempo_anticipacion_horas" in c:
                tiempos_anticipacion.append(c["tiempo_anticipacion_horas"])

        tiempo_minimo_alerta = min(tiempos_anticipacion) if tiempos_anticipacion else 4

        return {
            "agente": self.nombre,
            "distrito_consultado": distrito,
            "departamento_consultado": departamento,
            "registros_historicos_encontrados": coincidencias,
            "total_poblacion_historicamente_expuesta": poblacion_afectada_total,
            "infraestructura_critica_reincidente": list(set(resumen_infraestructura)),
            "tiempo_anticipacion_minimo_requerido_horas": tiempo_minimo_alerta,
            "quebradas_en_la_zona": quebradas_zona,
            "quebradas_en_peligro_inminente": quebradas_superando,
            "alerta_reincidencia_severa": len(coincidencias) > 0 and (lluvia_actual_mm or 0) >= 35.0
        }

    def consultar_lecciones_cientificas_igp(self, estacion_o_region: str = "") -> Dict[str, Any]:
        """
        Consulta las lecciones científicas consolidadas en el compendio histórico del IGP 1997-1998,
        incluyendo anomalías pluviométricas de estaciones emblemáticas (Miraflores, Puerto Pizarro, Chosica).
        """
        term = estacion_o_region.lower()
        estaciones_filtradas = [
            e for e in self.estaciones_igp
            if not term or term in e["estacion"].lower()
        ]

        return {
            "agente": self.nombre,
            "referencia_oficial": self.metadata_historica.get("referencia_cientifica_igp", "Compendio IGP"),
            "fuente": self.metadata_historica.get("fuente", "INDECI / SENAMHI / SINPAD"),
            "archivo_evidencia": self.metadata_historica.get("evidencia_archivo_local", "data/igp_el_nino_1997_1998.pdf"),
            "estaciones_relevantes_1998": estaciones_filtradas,
            "conclusiones_cientificas_clave": [
                "En 1998, la estación Miraflores (Piura) alcanzó 1,802 mm (+850% sobre la media normal).",
                "En Chosica (Lima), bastaron 280 mm acumulados para activar 8 quebradas simultáneas.",
                "El pico de temperatura en la costa (Niño 1+2) precedió a las inundaciones terrestres en aproximadamente 60 días.",
                "Las defensas provisionales de tierra fallaron en el 100% de los puntos críticos de Trujillo y Piura."
            ]
        }

    def estructurar_memoria_historica_1998(
        self,
        filtro_etapa: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estructura y recupera la información técnica, los hechos y las acciones
        gubernamentales del Fenómeno El Niño 1997-1998 documentadas ante la Comisión
        Permanente del Congreso de la República (sesión del 26 de febrero de 1998).

        Parámetros:
            filtro_etapa: Opcional ('antes', 'durante', 'despues' o None).
                          Si se especifica, filtra las acciones gubernamentales a esa fase.

        Retorna un diccionario estructurado con:
            - metadatos_fuente
            - informacion_tecnica
            - hechos_y_territorio
            - acciones_gubernamentales (clasificadas en antes_prevencion, durante_emergencia, despues_reconstruccion)
        """
        data = self.memoria_congreso_1998
        if not data:
            return {
                "agente": self.nombre,
                "error": "Base de memoria del Congreso 1998 no disponible."
            }

        acciones = data.get("acciones_gubernamentales", {})
        if filtro_etapa:
            etapa_norm = filtro_etapa.lower().strip()
            if "antes" in etapa_norm or "prev" in etapa_norm:
                acciones_filtradas = {"antes_prevencion": acciones.get("antes_prevencion", {})}
            elif "durante" in etapa_norm or "emerg" in etapa_norm:
                acciones_filtradas = {"durante_emergencia": acciones.get("durante_emergencia", {})}
            elif "despues" in etapa_norm or "reconst" in etapa_norm or "post" in etapa_norm:
                acciones_filtradas = {"despues_reconstruccion": acciones.get("despues_reconstruccion", {})}
            else:
                acciones_filtradas = acciones
        else:
            acciones_filtradas = acciones

        return {
            "agente": self.nombre,
            "fuente_oficial": data.get("fuente"),
            "presidencia_congreso": data.get("presidencia_congreso"),
            "expositor_ejecutivo": data.get("expositor_ejecutivo"),
            "informacion_tecnica": data.get("informacion_tecnica", {}),
            "hechos_y_territorio": data.get("hechos_y_territorio", {}),
            "acciones_gubernamentales": acciones_filtradas
        }

    def consultar_historial_quebradas(self, filtro_region_o_distrito: str = "") -> List[Dict[str, Any]]:
        """
        Consulta el catálogo científico de quebradas críticas reincidentes,
        permitiendo filtrar por región, cuenca o distrito impactado.
        """
        if not filtro_region_o_distrito:
            return self.quebradas

        termino = filtro_region_o_distrito.lower().strip()
        coincidencias = []
        for q in self.quebradas:
            match = (
                termino in q.get("nombre", "").lower()
                or termino in q.get("region", "").lower()
                or termino in q.get("provincia", "").lower()
                or termino in q.get("distrito", "").lower()
                or termino in q.get("cuenca", "").lower()
                or any(termino in d.lower() for d in q.get("distritos_impactados", []))
            )
            if match:
                coincidencias.append(q)
        return coincidencias

    def evaluar_probabilidad_reincidencia_quebrada(self, nombre_o_id: str, lluvia_mm: float) -> Dict[str, Any]:
        """
        Calcula la Probabilidad Condicionada de Activación de Quebrada (PCAQ)
        cruzando la precipitación actual con la memoria histórica de desbordes (1983, 1998, 2017, 2023).
        """
        termino = nombre_o_id.lower().strip()
        quebrada = None
        for q in self.quebradas:
            if (
                termino == q.get("id_quebrada", "").lower()
                or termino == q.get("codigo_tactico_c2", "").lower()
                or termino in q.get("codigo_tactico_c2", "").lower()
                or q.get("codigo_tactico_c2", "").lower().startswith(termino)
                or termino in q.get("denominacion_amaru", "").lower()
                or termino in q.get("nombre", "").lower()
            ):
                quebrada = q
                break

        if not quebrada:
            return {
                "agente": self.nombre,
                "estado": "NO_ENCONTRADA",
                "mensaje": f"No se encontró la quebrada '{nombre_o_id}' en el catálogo georreferenciado."
            }

        umbral_24h = quebrada.get("umbral_acumulado_24h", 35.0)
        ratio_saturacion = min(1.0, lluvia_mm / max(1.0, umbral_24h))
        num_activaciones = len(quebrada.get("historial_activaciones", []))
        
        # Factor histórico: más activaciones registradas elevan la certeza de reincidencia
        factor_historico = min(1.0, num_activaciones / 4.0)
        
        # Probabilidad de Activación Condicionada (PCAQ) normalizada
        pcaq = round(0.60 * ratio_saturacion + 0.40 * factor_historico, 2)
        if lluvia_mm >= umbral_24h:
            pcaq = max(pcaq, 0.95)

        tc_horas = quebrada.get("tiempo_concentracion_horas", 1.5)
        impacto_rapido = tc_horas <= 1.2

        return {
            "agente": self.nombre,
            "id_quebrada": quebrada.get("id_quebrada"),
            "quebrada": quebrada.get("nombre"),
            "region": quebrada.get("region"),
            "distritos_en_cono": quebrada.get("distritos_impactados", []),
            "lluvia_observada_mm": lluvia_mm,
            "umbral_critico_mm": umbral_24h,
            "probabilidad_activacion_pcaq": pcaq,
            "nivel_alerta": "ROJO_CRITICO" if pcaq >= 0.85 else ("NARANJA_ALTO" if pcaq >= 0.65 else ("AMARILLO_MEDIO" if pcaq >= 0.40 else "VERDE_BAJO")),
            "tiempo_concentracion_horas": tc_horas,
            "alerta_impacto_rapido": impacto_rapido,
            "historial_activaciones": quebrada.get("historial_activaciones", []),
            "leccion_historica": quebrada.get("leccion_historica", ""),
            "fuente_estudio": quebrada.get("fuente_estudio", ""),
            "accion_tactica_inmediata": (
                f"ALERTA MÁXIMA: Quebrada {quebrada.get('nombre')} en umbral de saturación. "
                f"Tiempo estimado de llegada del huaico: {tc_horas} horas. "
                f"Evacuar cono de deyección ({quebrada.get('poblacion_en_cono_deyeccion', 0):,} hab.) "
                f"hacia zonas altas y alertar puntos de estrangulamiento: {', '.join(quebrada.get('puntos_estrangulamiento', [])[:2])}."
                if pcaq >= 0.80
                else f"Monitoreo continuo de cabecera de cuenca. Umbral al {int(ratio_saturacion*100)}%."
            )
        }

    def consultar_balance_oficial_coen_2017(self) -> Dict[str, Any]:
        """
        Retorna el balance y reporte oficial del Centro de Operaciones de Emergencia Nacional (COEN)
        e INDECI sobre el impacto de El Niño Costero 2017, incluyendo cifras de damnificados/afectados,
        regiones críticas, definiciones normativas y análisis de fallas ingenieriles en puentes y drenajes.
        """
        if not self.memoria_coen_2017:
            return {
                "agente": self.nombre,
                "error": "Memoria oficial del COEN 2017 no disponible en la base histórica."
            }

        return {
            "agente": self.nombre,
            **self.memoria_coen_2017
        }

    def analizar_lecciones_infraestructura_y_puentes(self, termino_busqueda: str = "") -> Dict[str, Any]:
        """
        Analiza las fallas estructurales históricas de puentes y defensas ribereñas (1998 y 2017),
        identificando mecanismos de colapso como socavación, acumulación de desmontes y falta de canales de coronación.
        """
        fallas = self.memoria_coen_2017.get("lecciones_ingenieriles_fallas_infraestructura", [])
        if termino_busqueda:
            t = termino_busqueda.lower().strip()
            fallas = [f for f in fallas if t in f.get("estructura", "").lower() or t in f.get("mecanismo_falla", "").lower()]

        return {
            "agente": self.nombre,
            "fuente_analisis": "Colegio de Ingenieros del Perú (CIP) / COEN 2017",
            "total_lecciones": len(fallas),
            "fallas_estructurales_identificadas": fallas,
            "conclusion_ingenieril": (
                "La mayoría de puentes caídos (Virú, Pérez de Cuéllar) no colapsaron por fuerza bruta del agua sino "
                "por socavación evitable, alteración del cauce por desmontes ilegales y omisión de canales de coronación."
            )
        }

    def analizar_patron_chosica_nino_costero(self) -> Dict[str, Any]:
        """
        Analiza la dinámica histórica de reactivación temprana de quebradas en Chosica y Santa Eulalia
        al inicio de El Niño Costero (América TV / SENAMHI Aviso de Activación de Quebradas).
        """
        caso_chosica = self.memoria_coen_2017.get("estudio_caso_chosica_nino_costero", {})
        if not caso_chosica:
            return {
                "agente": self.nombre,
                "error": "Estudio de caso Chosica no disponible."
            }

        return {
            "agente": self.nombre,
            **caso_chosica
        }

    def consultar_memoria_sanitaria_ops(self) -> Dict[str, Any]:
        """
        Retorna la memoria sanitaria y epidemiológica documentada por la Organización Panamericana de la Salud (OPS/OMS)
        sobre El Niño en Piura y costa norte (IRIS PAHO handle 10665.2/34889), cubriendo brotes de dengue, leptospirosis,
        afectación de hospitales y lecciones de respuesta asistencial.
        """
        if not self.memoria_ops_2017:
            return {
                "agente": self.nombre,
                "error": "Memoria sanitaria OPS/OMS no disponible en la base histórica."
            }

        return {
            "agente": self.nombre,
            **self.memoria_ops_2017
        }

    def evaluar_riesgo_epidemiologico_post_inundacion(self, region_o_distrito: str, anegamiento_dias: int) -> Dict[str, Any]:
        """
        Modela el riesgo epidemiológico en cascada derivado de inundaciones y aguas estancadas,
        siguiendo las lecciones aprendidas de la OPS/OMS 2017:
        - Leptospirosis: Pico en días 1 a 14 por contacto con agua/lodo contaminado con roedores.
        - Dengue / Arbovirosis: Detonación explosiva a partir del día 7 a 21 (ciclo biológico de Aedes aegypti).
        - Enfermedades Diarreicas Agudas (EDA): Inmediatas ante colapso de redes de agua y desagüe.
        """
        dias = max(0, anegamiento_dias)
        
        # Cálculo de niveles de riesgo
        riesgo_leptospirosis = "CRITICO" if dias >= 3 else ("ALTO" if dias >= 1 else "MEDIO")
        riesgo_dengue = "CRITICO" if dias >= 14 else ("ALTO" if dias >= 7 else "MEDIO")
        riesgo_eda = "CRITICO" if dias >= 2 else "ALTO"

        acciones_preventivas = [
            "Distribución inmediata de tabletas de cloro (Aquatabs) para desinfección de agua domiciliaria",
            "Profilaxis con doxiciclina a brigadas de rescate y personal expuesto a aguas de inundación",
            "Control larvario físico y químico (piriproxifeno) en todas las cuencas ciegas y charcos antes del día 7",
            "Instalación obligatoria de mosquiteros y repelentes en albergues y refugios temporales"
        ]

        if dias >= 7:
            acciones_preventivas.append("Iniciar nebulización espacial (fumigación intradomiciliaria en 3 ciclos de 3 días)")

        return {
            "agente": self.nombre,
            "region_o_distrito": region_o_distrito,
            "dias_anegamiento_evaluados": dias,
            "evaluacion_vectorial_sanitaria": {
                "dengue_arbovirosis": {
                    "nivel_riesgo": riesgo_dengue,
                    "patogeno": "Virus Dengue (Serotipos 1, 2, 3) / Aedes aegypti",
                    "ventana_critica_dias": "Día 7 a 30",
                    "leccion_historica_piura": "En 2017 se alcanzaron 48,000 casos y 43 fallecidos por no actuar antes del día 7."
                },
                "leptospirosis": {
                    "nivel_riesgo": riesgo_leptospirosis,
                    "patogeno": "Leptospira interrogans",
                    "ventana_critica_dias": "Día 1 a 14",
                    "leccion_historica_piura": "Alto riesgo en personas que caminan descalzas o sin botas en lodo y aguas residuales."
                },
                "infecciones_gastrointestinales_eda": {
                    "nivel_riesgo": riesgo_eda,
                    "ventana_critica_dias": "Inmediata (Día 1 en adelante)",
                    "factor": "Contaminación fecal por mezcla de aguas de lluvia con desagües colapsados."
                }
            },
            "acciones_tacticas_salud_amaru": acciones_preventivas,
            "fuente_protocolo": "Organización Panamericana de la Salud (OPS/OMS) - IRIS 10665.2/34889"
        }

    def consultar_informe_enfen_n15_agosto_2026(self) -> Dict[str, Any]:
        """
        Retorna el análisis estructurado del Informe Técnico Oficial ENFEN Año 12 Nº 15
        (26 de agosto de 2026), base científica vinculante del DU 010-2026 y DS 124-2026-PCM.
        """
        data_enfen = self.informe_enfen_2026
        return {
            "agente": self.nombre,
            "documento": data_enfen.get("identificador", "Informe Técnico ENFEN Año 12 Nº 15"),
            "fecha_emision": data_enfen.get("fecha_emision", "2026-08-26"),
            "estado_alerta": data_enfen.get("estado_sistema_alerta", "Alerta de El Niño Costero"),
            "archivo_local": data_enfen.get("archivo_local_pdf", "data/informe_tecnico_enfen_ano12_n15_2026.pdf"),
            "diagnostico_multisectorial": data_enfen.get("diagnostico_multisectorial", {}),
            "escenarios_hidrologicos_y_climaticos": data_enfen.get("escenarios_hidrologicos_y_climaticos", {}),
            "impactos_biologico_pesqueros": data_enfen.get("impactos_biologico_pesqueros_imarpe", {}),
            "impacto_politica_publica": data_enfen.get("impacto_juridico_politica_publica", {})
        }

    def consultar_estudio_senamhi_1997_1998(self) -> Dict[str, Any]:
        """
        Retorna los hallazgos científicos y lecciones operativas del estudio oficial de SENAMHI:
        'El evento El Niño - Oscilación Sur 1997-1998: su impacto en el departamento de Lambayeque' (IDESEP).
        """
        data = self.estudio_senamhi_1998
        return {
            "agente": self.nombre,
            "titulo": data.get("titulo", "El evento El Niño - Oscilación Sur 1997-1998: su impacto en el departamento de Lambayeque"),
            "autor": data.get("autor_institucional", "SENAMHI"),
            "archivo_local": data.get("archivo_local_pdf", "data/senamhi_el_evento_el_nino_1997_1998.pdf"),
            "total_paginas": data.get("total_paginas", 78),
            "conceptos_clave": data.get("conceptos_clave_refuerzo_amaru", {})
        }

    def consultar_estudio_capel_molina_1998(self) -> Dict[str, Any]:
        """
        Retorna los hallazgos científicos y datos cuantitativos del estudio de Capel Molina (1998):
        'EL NIÑO 1997-98 Y SU IMPACTO CLIMÁTICO GLOBAL' (Papeles de Geografía, Universidad de Murcia).
        """
        data = self.estudio_capel_molina_1998
        return {
            "agente": self.nombre,
            "titulo": data.get("titulo", "EL NIÑO 1997-98 Y SU IMPACTO CLIMÁTICO GLOBAL"),
            "autor": data.get("autor", "José Jaime Capel Molina"),
            "publicacion": data.get("publicacion", "Papeles de Geografía, Nº 27, 1998"),
            "archivo_local": data.get("archivo_local_pdf", "data/capel_molina_1998_el_nino_impacto_global.pdf"),
            "total_paginas": data.get("total_paginas", 26),
            "resumen": data.get("resumen_ejecutivo", ""),
            "evidencias_cuantitativas_peru": data.get("evidencias_cuantitativas_peru", {}),
            "teleconexiones_globales": data.get("teleconexiones_globales", {}),
            "lecciones_amaru": data.get("lecciones_para_amaru_fen", [])
        }

    def consultar_informe_senamhi_cenepred_69_2026(self) -> Dict[str, Any]:
        """
        Retorna los hallazgos del Informe Técnico Nº 69-2026/SENAMHI-DMA-SPC para CENEPRED:
        Mapas composite PISCO v2.2 (0.1º) de anomalías extremas ENOS vs Niño Costero (EFM).
        """
        data = self.informe_cenepred_2026
        return {
            "agente": self.nombre,
            "identificador": data.get("identificador", "Informe Técnico Nº 69-2026/SENAMHI-DMA-SPC"),
            "titulo": data.get("titulo", "Mapas de Anomalías Extremas de Precipitación"),
            "emisor": data.get("emisor", "SENAMHI Subdirección de Predicción Climática"),
            "solicitante": data.get("solicitante", "CENEPRED"),
            "fecha": data.get("fecha", "Junio de 2026"),
            "archivo_local": data.get("archivo_local_pdf", "data/cenepred_informe_tecnico_2026_0006823.pdf"),
            "total_paginas": data.get("total_paginas", 21),
            "grilla_pisco": data.get("fuente_datos_grillada", "PISCO v2.2 (0.1º ~ 10 km)"),
            "patrones_regionales": data.get("patrones_regionales_conclusiones", {}),
            "impacto_amaru_fen": data.get("impacto_amaru_fen", "")
        }

    def consultar_reporte_noaa_ncdc_98_02(self) -> Dict[str, Any]:
        """
        Retorna los hallazgos del Technical Report No. 98-02 de NOAA NCDC:
        'The El Nino Winter of '97 - '98' (Ross, Lott, McCown, Quinn).
        """
        data = self.reporte_noaa_98
        return {
            "agente": self.nombre,
            "identificador": data.get("identificador", "NOAA NCDC Technical Report No. 98-02"),
            "titulo": data.get("titulo", "The El Nino Winter of '97 - '98"),
            "autores": data.get("autores", "Ross, Lott, McCown, Quinn"),
            "entidad": data.get("entidad", "NOAA / NESDIS / NCDC"),
            "fecha": data.get("fecha", "Abril de 1998"),
            "archivo_local": data.get("archivo_local_pdf", "data/noaa_ncdc_technical_report_98_02_el_nino_winter_97_98.pdf"),
            "total_paginas": data.get("total_paginas", 28),
            "resumen": data.get("resumen", ""),
            "mecanismo_fisico_clave": data.get("mecanismo_fisico_clave", ""),
            "impacto_amaru_fen": data.get("impacto_amaru_fen", "")
        }

    def consultar_comparativa_oannes_fen(self) -> Dict[str, Any]:
        """
        Retorna la comparativa histórica y lecciones de Oannes / El Regional Piura
        sobre las diferencias hidromorfológicas entre 1972, 1982-83, 1997-98 y 2017.
        """
        data = self.estudio_oannes
        return {
            "agente": self.nombre,
            "identificador": data.get("identificador", "Oannes / El Regional Piura (2017)"),
            "titulo": data.get("titulo", "Fenómenos El Niño y las diferencias entre 1972, 1982-83 y 1997-98"),
            "enlace_web": data.get("enlace_web", "https://www.oannes.org.pe/noticias/peru-fenomenos-el-nino-y-las-diferencias-entre-1972-1982-83-y-1997-98/"),
            "autor": data.get("autor", "Andrés Vera Córdova"),
            "fecha": data.get("fecha_publicacion", "15 de marzo de 2017"),
            "comparativa_eventos": data.get("comparativa_fenomenos", {}),
            "lecciones_clave": data.get("lecciones_clave_amaru_fen", [])
        }

    def consultar_editorial_cooperacion_el_peruano(self) -> Dict[str, Any]:
        """
        Retorna los lineamientos del Editorial oficial de El Peruano (22-ago-2026):
        Diplomacia proactiva, 69% probabilidad récord NOAA, y despliegue del buque hospital USNS Comfort en Piura.
        """
        data = self.editorial_el_peruano
        return {
            "agente": self.nombre,
            "identificador": data.get("identificador", "Diario Oficial El Peruano - Editorial"),
            "titulo": data.get("titulo", "Cooperación ante El Niño"),
            "fecha": data.get("fecha", "22 de agosto de 2026"),
            "enlace_web": data.get("enlace_web", "https://elperuano.pe/noticia/303038-cooperacion-ante-el-nino"),
            "cifras_clave_noaa": data.get("cifras_clave_noaa", ""),
            "pilares_diplomacia_proactiva": data.get("pilares_diplomacia_proactiva", []),
            "impacto_amaru_fen": data.get("impacto_amaru_fen", "")
        }

    def consultar_estudio_onu_unu_1998(self) -> Dict[str, Any]:
        """
        Retorna los hallazgos del estudio de la Universidad de Naciones Unidas (UNU / WMO / UNEP):
        'Reducing the Impact of Environmental Emergencies: The Case of the 1997-98 El Niño - Peru' (Zapata y Broad).
        """
        data = self.estudio_unu_1998
        return {
            "agente": self.nombre,
            "identificador": data.get("identificador", "UNU / WMO / UNEP Country Study"),
            "titulo": data.get("titulo", "Reducing the Impact of Environmental Emergencies - Peru"),
            "autores": data.get("autores", "Antonio Zapata y Kenneth Broad"),
            "ano": data.get("ano", "2000"),
            "enlace_web": data.get("enlace_web", "https://collections.unu.edu/eserv/UNU:8398/Peru.pdf"),
            "enlace_archivo": data.get("enlace_archivo", "https://archive.unu.edu/env/govern/ElNIno/CountryReports/pdf/peru.pdf"),
            "conclusiones_clave": data.get("conclusiones_clave", [])
        }





