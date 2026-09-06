from typing import Dict, Any, Optional, List
from agents.agente_senamhi import AgenteSenamhi
from agents.agente_georriesgo import AgenteGeorriesgo
from agents.agente_vigia_osint import AgenteVigiaOSINT
from agents.agente_voz_vapi import AgenteVozVapi
from agents.agente_despacho_edan import AgenteDespachoEDAN
from agents.agente_memoria_historica import AgenteMemoriaHistorica
from agents.agente_legal_normativo import AgenteLegalNormativo
from core.anticipatory_triggers import MotorGobernanzaAnticipatoria
from core.ingestor_oficial import IngestorOficialSenamhiEnfen
from core.edge_resilience import GestorResilienciaOffGrid, ModoConectividad
from core.alerta_defensa_civil import DespachadorDefensaCivilMunicipal
from core.consola_c2 import ConsolaTacticoC2
from core.motor_calibracion_post_mortem import (
    MotorCalibracionPostMortem,
    RegistroDecisionC2,
    ResultadoRealEvento,
    InformePericialPostMortem,
    OrdenCorteTemporadaFEN,
    ActaRatificacionComite
)
from agents.agente_crioclimatico_nina import AgenteCrioclimaticoNina
from core.reloj_nina import MotorRelojNina
from core.telegram_notifier import TelegramNotifier
from datetime import datetime, timezone

class AmaruOrchestrator:
    """
    Orquestador Central del Enjambre AMARU-FEN.
    Coordina el ciclo integral: Memoria Histórica y Años Análogos,
    Gobernanza Anticipatoria (Antes), Triaje Táctico (Durante),
    Marco Legal & Normativo y Despacho EDAN (Después).
    """
    def __init__(self):
        self.motor_anticipatorio = MotorGobernanzaAnticipatoria()
        self.agente_memoria = AgenteMemoriaHistorica()
        self.agente_legal = AgenteLegalNormativo()
        self.agente_senamhi = AgenteSenamhi()
        self.agente_georriesgo = AgenteGeorriesgo()
        self.agente_osint = AgenteVigiaOSINT()
        self.agente_voz = AgenteVozVapi()
        self.agente_despacho = AgenteDespachoEDAN()
        self.ingestor_oficial = IngestorOficialSenamhiEnfen()
        self.gestor_resiliencia = GestorResilienciaOffGrid()
        self.despachador_defensa_civil = DespachadorDefensaCivilMunicipal()
        self.consola_c2 = ConsolaTacticoC2()
        self.motor_post_mortem = MotorCalibracionPostMortem()
        # Subsistema Crioclimático AMARU-CHIRI (La Niña & Heladas Altoandinas)
        self.agente_crioclimatico = AgenteCrioclimaticoNina()
        self.motor_reloj_nina = MotorRelojNina()
        self.notificador_telegram = TelegramNotifier()
        self.historial_decisiones_c2: List[RegistroDecisionC2] = []
        self.ultimo_informe_pericial: Optional[InformePericialPostMortem] = None
        self.metadata_ultima_ingesta = {
            "fecha_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tipo": "INICIAL_LINEA_BASE",
            "fuentes_consultadas": ["SENAMHI", "ENFEN", "ANA"],
            "total_ubigeos_procesados": 893,
            "version_id": f"INGESTA-{int(datetime.now().timestamp())}"
        }



    def evaluar_gobernanza_anticipada(self, anomalia_tsm: float, mes: int = 8) -> Dict[str, Any]:
        """
        Evalúa triggers presupuestales y logísticos cruzando la anomalía climática
        con el año análogo histórico detectado por el Agente de Memoria.
        """
        eval_ant = self.motor_anticipatorio.evaluar_triggers_climaticos(anomalia_tsm, mes).model_dump()
        analisis_analogo = self.agente_memoria.identificar_ano_analogo(anomalia_tsm, mes)
        eval_ant["ano_analogo_historico"] = analisis_analogo
        return eval_ant

    def procesar_incidente_completo(
        self,
        region: str,
        distrito: str,
        lluvia_mm: float,
        alerta_senamhi: str,
        reporte_ciudadano_texto: str,
        tipo_canal: str = "VOZ_VAPI",
        atrapados: int = 0
    ) -> Dict[str, Any]:
        # 1. Consulta a la Memoria Histórica y Antecedentes Territoriales (1998 / 2017)
        eval_memoria = self.agente_memoria.consultar_antecedentes_territoriales(
            distrito=distrito,
            departamento=region,
            lluvia_actual_mm=lluvia_mm
        )

        # 2. Análisis Meteorológico en tiempo real
        eval_senamhi = self.agente_senamhi.procesar_aviso_meteorologico({
            "region": region,
            "nivel_alerta": alerta_senamhi,
            "lluvia_estimada_mm": lluvia_mm
        })
        
        # 3. Análisis de Georriesgo Territorial
        eval_geo = self.agente_georriesgo.evaluar_amenaza_territorial(distrito, lluvia_mm)
        
        # 4. Análisis de Reporte Ciudadano (OSINT / Voz)
        if tipo_canal == "VOZ_VAPI":
            eval_reporte = self.agente_voz.procesar_transcripcion_llamada(reporte_ciudadano_texto)
        else:
            eval_reporte = self.agente_osint.analizar_transmision_o_post(reporte_ciudadano_texto)
            
        # 5. Determinación de Severidad combinando sensores actuales y memoria de reincidencia
        alerta_reincidente = eval_memoria.get("alerta_reincidencia_severa", False)
        severidad = "CRITICA" if (lluvia_mm >= 60.0 or atrapados > 0 or alerta_reincidente) else "ALTA"
        
        # 6. Generación y Despacho Ficha EDAN
        necesidades_base = ["Botes de rescate", "Maquinaria pesada", "Kits de emergencia"]
        if eval_memoria.get("infraestructura_critica_reincidente"):
            necesidades_base.append(f"Protección prioritaria de: {', '.join(eval_memoria['infraestructura_critica_reincidente'][:2])}")

        ficha_edan = self.agente_despacho.generar_y_despachar_ficha(
            departamento=region,
            provincia=region,
            distrito=distrito,
            localidad=f"Sector {distrito} Centro",
            tipo_evento="Huayco e Inundación" if lluvia_mm > 40 else "Lluvia Extrema",
            severidad=severidad,
            origen=tipo_canal,
            atrapados=atrapados,
            necesidades=necesidades_base
        )
        
        # 6. Validación Legal y Estado de Emergencia (DS 124-2026-PCM / DU 010-2026)
        eval_legal = self.agente_legal.verificar_distrito_estado_emergencia(distrito, region)

        return {
            "status": "OPERATIVO_DESPACHADO",
            "ficha_edan": ficha_edan.model_dump(),
            "memoria_historica": eval_memoria,
            "diagnostico_senamhi": eval_senamhi,
            "analisis_georriesgo": eval_geo,
            "triaje_reporte": eval_reporte,
            "cobertura_legal_emergencia": eval_legal,
            "soberania_humana_ley_31814": self.agente_legal.obtener_sello_soberania_humana(),
            "requiere_autorizacion_humana": True
        }


    def consultar_ano_analogo(self, anomalia_tsm: float, mes: int = 8) -> Dict[str, Any]:
        return self.agente_memoria.identificar_ano_analogo(anomalia_tsm, mes)

    def consultar_historia_zona(self, distrito: str, region: str = "", lluvia_mm: Optional[float] = None) -> Dict[str, Any]:
        return self.agente_memoria.consultar_antecedentes_territoriales(distrito, region, lluvia_mm)

    def consultar_lecciones_igp(self, tema: str = "") -> Dict[str, Any]:
        return self.agente_memoria.consultar_lecciones_cientificas_igp(tema)

    def consultar_quebradas_reincidentes(self, filtro_region_o_distrito: str = ""):
        return self.agente_memoria.consultar_historial_quebradas(filtro_region_o_distrito)

    def evaluar_quebrada_especifica(self, nombre_o_id: str, lluvia_mm: float):
        return self.agente_memoria.evaluar_probabilidad_reincidencia_quebrada(nombre_o_id, lluvia_mm)

    def evaluar_probabilidad_dinamica_huaico(
        self,
        id_o_nombre: str,
        lluvia_cabecera_mm_h: float = 0.0,
        lluvia_acumulada_24h: float = 0.0,
        saturacion_api_72h: float = 0.0,
        irce_circundante: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calcula el IPH-FEN blindado criptográficamente cruzando cabecera andina, IRCE circundante y memoria histórica."""
        return self.agente_georriesgo.calcular_probabilidad_dinamica_huaico(
            id_o_nombre=id_o_nombre,
            lluvia_cabecera_mm_h=lluvia_cabecera_mm_h,
            lluvia_acumulada_24h=lluvia_acumulada_24h,
            saturacion_api_72h=saturacion_api_72h,
            irce_circundante=irce_circundante
        )

    def verificar_integridad_formula_iph(self) -> Dict[str, Any]:
        """Verifica la integridad criptográfica SHA-256 de los pesos y la lógica del IPH-FEN."""
        return self.agente_georriesgo.verificar_integridad_formula()

    def obtener_corredor_cabeceras_andinas(self) -> Dict[str, Any]:
        """Retorna la estructura y puntos de muestreo del Corredor de Cabeceras Andinas."""
        return self.agente_georriesgo.obtener_corredor_cabeceras()

    def consultar_telemetria_in_situ_igp(self, id_o_nombre: str, lluvia_cabecera_mm_h: float = 0.0) -> Dict[str, Any]:
        """Consulta la telemetría del sensor in situ del IGP (velocidad, altura, alarma sonora, ETA)."""
        from core.conector_igp_lahares import conector_igp_lahares
        return conector_igp_lahares.consultar_telemetria_in_situ(id_o_nombre, lluvia_cabecera_mm_h=lluvia_cabecera_mm_h)

    def consultar_balance_coen_2017(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_balance_oficial_coen_2017()

    def consultar_lecciones_puentes(self, termino: str = "") -> Dict[str, Any]:
        return self.agente_memoria.analizar_lecciones_infraestructura_y_puentes(termino)

    def consultar_patron_chosica(self) -> Dict[str, Any]:
        return self.agente_memoria.analizar_patron_chosica_nino_costero()

    def consultar_memoria_sanitaria_ops(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_memoria_sanitaria_ops()

    def evaluar_riesgo_epidemiologico(self, region_o_distrito: str, anegamiento_dias: int) -> Dict[str, Any]:
        return self.agente_memoria.evaluar_riesgo_epidemiologico_post_inundacion(region_o_distrito, anegamiento_dias)

    def consultar_informe_enfen_n15(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_informe_enfen_n15_agosto_2026()

    def consultar_estudio_senamhi_97_98(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_estudio_senamhi_1997_1998()

    def consultar_estudio_capel_molina_1998(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_estudio_capel_molina_1998()

    def consultar_informe_cenepred_2026(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_informe_senamhi_cenepred_69_2026()

    def consultar_reporte_noaa_98(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_reporte_noaa_ncdc_98_02()

    def consultar_comparativa_oannes(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_comparativa_oannes_fen()

    def consultar_satelite_goes19(self) -> Dict[str, Any]:
        return self.agente_senamhi.consultar_satelite_goes19()

    def consultar_editorial_cooperacion_el_peruano(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_editorial_cooperacion_el_peruano()

    def consultar_estudio_onu_unu(self) -> Dict[str, Any]:
        return self.agente_memoria.consultar_estudio_onu_unu_1998()

    def consultar_satelite_imarpe(self) -> Dict[str, Any]:
        return self.ingestor_oficial.consultar_satelite_imarpe_oceanografia()

    # --- MÉTODOS DEL AGENTE VIGÍA OSINT (MULTIMODAL Y TRI-TEMPORAL) ---




    def procesar_stream_tiktok(self, texto: str, autor: str = "anonimo", enlace: str = "", depto: str = "Piura", lluvia_senamhi: Optional[float] = None) -> Dict[str, Any]:
        return self.agente_osint.procesar_stream_tiktok(texto, autor, enlace, depto, lluvia_senamhi)

    def procesar_reporte_radial(self, transcripcion: str, emisora: str = "Radio Cutivalú", dial: str = "107.9 FM", provincia: str = "Piura", depto: str = "Piura") -> Dict[str, Any]:
        return self.agente_osint.procesar_audio_radial_comunitario(transcripcion, emisora, dial, provincia, depto)

    def procesar_noticia_prensa_ex_post(self, titular: str, cuerpo: str, diario: str = "El Tiempo de Piura", fecha: str = "2026-09-03", depto: str = "Piura") -> Dict[str, Any]:
        return self.agente_osint.procesar_noticia_prensa_ex_post(titular, cuerpo, diario, fecha, depto)

    def obtener_balance_osint_multicanal(self) -> Dict[str, Any]:
        return self.agente_osint.obtener_balance_multicanal_osint()

    def consultar_caso_rpp_piura(self) -> Dict[str, Any]:
        return self.agente_osint.consultar_caso_estudio_rpp_piura()

    # --- MÉTODOS DEL AGENTE LEGAL Y NORMATIVO FEN ---






    def consultar_normas_legales_fen(self) -> List[Dict[str, Any]]:
        return self.agente_legal.consultar_normas_vigentes()

    def verificar_estado_emergencia_distrito(self, distrito: str, departamento: str = "") -> Dict[str, Any]:
        return self.agente_legal.verificar_distrito_estado_emergencia(distrito, departamento)

    def consultar_mecanismo_oxi_du010(self) -> Dict[str, Any]:
        return self.agente_legal.consultar_mecanismo_obras_por_impuestos_du_010()

    def generar_sustento_legal_contratacion(self, entidad: str, distrito: str, tipo_intervencion: str) -> Dict[str, Any]:
        return self.agente_legal.generar_sustento_contratacion_directa(entidad, distrito, tipo_intervencion)

    def generar_resolucion_alcaldia(self, entidad: str, alcalde: str, distrito: str, intervencion: str, monto: float) -> str:
        return self.agente_legal.generar_resolucion_alcaldia_emergencia(entidad, alcalde, distrito, intervencion, monto)

    def obtener_estadisticas_distritos_emergencia(self) -> Dict[str, Any]:
        return self.agente_legal.obtener_estadisticas_distritos_emergencia()

    def calcular_irce_fen_distrital(
        self,
        distrito: str,
        lluvia_mm: float,
        anomalia_tsm: float = 2.5,
        anegamiento_dias: int = 0,
        caudal_fluvial_m3s: Optional[float] = None,
        umbral_desborde_m3s: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula el Índice de Riesgo Crítico y Evacuación ante El Niño (IRCE-FEN)
        para cualquier distrito de los 893 declarados en el Perú:
        IRCE-FEN = min(1.0, (Peligro * Vulnerabilidad) / Capacidad)
        Integra lluvia acumulada y caudal fluvial instantáneo (m³/s).
        """
        # 1. Peligro Hidrometeorológico (P)
        i_tsm = min(1.0, max(0.0, anomalia_tsm / 2.5))
        i_senamhi = 1.0 if lluvia_mm >= 50 else (0.7 if lluvia_mm >= 30 else (0.4 if lluvia_mm >= 15 else 0.1))
        i_lluvia = min(1.0, lluvia_mm / 50.0)
        p_peligro = (0.35 * i_tsm) + (0.35 * i_senamhi) + (0.30 * i_lluvia)

        # Acoplamiento Hidrométrico Fluvial (ANA / SENAMHI) si se dispone de estación
        if caudal_fluvial_m3s is not None and umbral_desborde_m3s is not None and umbral_desborde_m3s > 0:
            i_caudal = min(1.0, max(0.0, caudal_fluvial_m3s / umbral_desborde_m3s))
            p_peligro = max(p_peligro, i_caudal)

        # 2. Vulnerabilidad Basal (V)
        # Cruce con antecedentes de desastres 1998/2017
        hist_check = self.agente_memoria.consultar_antecedentes_territoriales(distrito)
        tiene_hist = len(hist_check.get("registros_historicos_encontrados", [])) > 0
        v_hist = 1.0 if tiene_hist else 0.4
        
        # Cruce con quebradas críticas
        queb_check = self.agente_georriesgo.evaluar_amenaza_territorial(distrito, lluvia_mm)
        v_fisica = 0.9 if queb_check.get("total_quebradas_activadas", 0) > 0 or queb_check.get("nivel_prioridad_coen") == "CRITICA" else 0.5
        v_demo = 0.75  # Línea base de exposición urbana en faja marginal
        v_vulnerabilidad = (0.40 * v_demo) + (0.35 * v_fisica) + (0.25 * v_hist)

        # 3. Capacidad de Respuesta y Mitigación (C)
        # Cobertura legal en los 893 distritos del DS 124-2026-PCM
        legal_check = self.agente_legal.verificar_distrito_estado_emergencia(distrito)
        c_legal = 1.0 if legal_check.get("declarado_estado_emergencia") else 0.5
        c_dias = max(0.2, 1.0 - (0.04 * anegamiento_dias))
        c_capacidad = 0.50 + (0.30 * c_legal) + (0.20 * c_dias)

        # 4. Cálculo de IRCE-FEN
        score_irce = round(min(1.0, (p_peligro * v_vulnerabilidad) / c_capacidad), 3)

        # 5. Clasificación y Disparadores Tácticos
        if score_irce >= 0.85:
            nivel = "CRITICO_ROJO"
            semaforo = "🔴 ROJO (Evacuación Crítica Inminente)"
            accion = "Emisión inmediata de orden SISMATE / Sirenas, evacuación táctica de fajas marginales y despacho de fichas EDAN a PNP/FF.AA."
        elif score_irce >= 0.65:
            nivel = "ALTO_NARANJA"
            semaforo = "🟠 NARANJA (Acción Táctica Inmediata)"
            accion = "Preposicionamiento físico de motobombas pesadas de 6'', apertura de albergues temporales y quimioprofilaxis OPS con doxiciclina."
        elif score_irce >= 0.35:
            nivel = "MEDIO_AMARILLO"
            semaforo = "🟡 AMARILLO (Alerta Preventiva)"
            accion = "Activación de trigger MEF (PP 0068), descolmatación preventiva de drenes y suscripción de convenios OxI (DU 010-2026)."
        else:
            nivel = "BAJO_VERDE"
            semaforo = "🟢 VERDE (Vigilancia Basal)"
            accion = "Monitoreo rutinario de estaciones meteorológicas SENAMHI y boyas oceánicas NOAA/IMARPE."

        # 6. Registro Inmutable de la Decisión en el Historial C2 (Nivel 3 Post-Mortem)
        try:
            reg_decision = RegistroDecisionC2(
                id_alerta=f"ALERTA-{distrito[:3].upper()}-{int(datetime.now().timestamp() * 1000) % 1_000_000}",
                ubigeo=distrito,
                distrito=distrito,
                score_irce_emitido=score_irce,
                nivel_alerta=nivel,
                orden_evacuacion_emitida=(score_irce >= 0.85 or nivel == "CRITICO_ROJO"),
                tiempo_anticipacion_horas=18.0 if score_irce >= 0.85 else 12.0,
                factores_evaluados={
                    "peligro": p_peligro,
                    "vulnerabilidad": v_vulnerabilidad,
                    "exposicion": v_demo,
                    "capacidad": c_capacidad
                }
            )
            self.historial_decisiones_c2.append(reg_decision)
        except Exception:
            pass

        return {
            "agente": "AMARU-FEN Orquestador",
            "distrito": distrito,
            "lluvia_evaluada_mm": lluvia_mm,
            "anomalia_tsm_nino_1_2": anomalia_tsm,
            "dias_anegamiento": anegamiento_dias,
            "score_irce_fen": score_irce,
            "nivel_alerta": nivel,
            "semaforo": semaforo,
            "accion_tactica_disparada": accion,
            "vectores_componentes": {
                "peligro_p": round(p_peligro, 3),
                "vulnerabilidad_v": round(v_vulnerabilidad, 3),
                "capacidad_c": round(c_capacidad, 3)
            },
            "respaldo_legal_ds_124": legal_check.get("declarado_estado_emergencia"),
            "antecedentes_historicos": tiene_hist,
            "caudal_evaluado_m3s": caudal_fluvial_m3s,
            "umbral_desborde_m3s": umbral_desborde_m3s,
            "soberania_humana_ley_31814": self.agente_legal.obtener_sello_soberania_humana(),
            "requiere_autorizacion_humana": True
        }

    # --- MÉTODOS DE AFORO HIDROMÉTRICO Y RESILIENCIA OFF-GRID ---

    def consultar_estaciones_aforo(self, filtro_cuenca: str = "") -> List[Dict[str, Any]]:
        """Retorna las estaciones de aforo hidrológico del ANA / SENAMHI."""
        return self.ingestor_oficial.consultar_estaciones_aforo_fluvial(filtro_cuenca)

    def evaluar_caudal_estacion(self, id_estacion: str, caudal_simulado_m3s: Optional[float] = None) -> Dict[str, Any]:
        """
        Evalúa el riesgo de desborde fluvial para una estación específica según su umbral en m³/s.
        """
        estaciones = self.consultar_estaciones_aforo()
        est = next((e for e in estaciones if e["id_estacion"] == id_estacion), None)
        if not est:
            return {"error": f"Estación '{id_estacion}' no encontrada"}

        q_actual = caudal_simulado_m3s if caudal_simulado_m3s is not None else est.get("caudal_simulado_actual_m3s", est["caudal_normal_m3s"])
        q_desborde = est["umbral_rojo_desborde_m3s"]
        ratio = round(q_actual / q_desborde, 2)

        if q_actual >= q_desborde:
            alerta = "ROJO_DESBORDE"
            semaforo = "🔴 DESBORDE FLUVIAL INMINENTE"
            accion = "Evacuación inmediata de fajas marginales urbanas y activación de defensas ribereñas."
        elif q_actual >= est["umbral_naranja_m3s"]:
            alerta = "NARANJA_CRITICO"
            semaforo = "🟠 ALERTA NARANJA (Caudal Crítico)"
            accion = "Cierre preventivo de puentes peatonales y apertura de compuertas de alivio."
        elif q_actual >= est["umbral_amarillo_m3s"]:
            alerta = "AMARILLO_ALTO"
            semaforo = "🟡 ALERTA AMARILLA (Incremento Súbito)"
            accion = "Vigilancia continua de riberas y prealerta a brigadas municipales."
        else:
            alerta = "VERDE_NORMAL"
            semaforo = "🟢 CAUDAL NORMAL"
            accion = "Flujo fluvial seguro dentro del cauce ordinario."

        return {
            "estacion": est["nombre"],
            "rio": est["rio"],
            "distrito": est["distrito"],
            "caudal_evaluado_m3s": q_actual,
            "umbral_desborde_m3s": q_desborde,
            "record_1998_m3s": est["record_historico_1998_m3s"],
            "ratio_desborde": ratio,
            "alerta": alerta,
            "semaforo": semaforo,
            "accion_recomendada": accion,
            "impacto_urbano": est["impacto_urbano"],
            "soberania_humana_ley_31814": self.agente_legal.obtener_sello_soberania_humana()
        }

    def obtener_estado_resiliencia_red(self) -> Dict[str, Any]:
        """Retorna el diagnóstico de conectividad y estado del Circuit Breaker."""
        return self.gestor_resiliencia.obtener_estado_red()

    def conmutar_modo_resiliencia(self, modo: str) -> str:
        """Conmuta manualmente entre ONLINE_CLOUD y OFFLINE_EDGE_OFFGRID."""
        return self.gestor_resiliencia.forzar_modo(modo)

    def consultar_marco_soberania_humana(self) -> Dict[str, Any]:
        """Retorna el marco normativo de Soberanía Humana (Ley Nº 31814 / UNESCO / OCDE / Sendai)."""
        return self.agente_legal.consultar_marco_soberania_humana_ia()

    # --- MÓDULO DE DESPACHO A DEFENSA CIVIL MUNICIPAL ---

    def consultar_contacto_defensa_civil(self, ubigeo: str) -> Optional[Dict[str, Any]]:
        """Retorna el contacto oficial de Defensa Civil y GRD para un UBIGEO específico."""
        return self.despachador_defensa_civil.buscar_contacto_por_ubigeo(ubigeo)

    def disparar_alerta_defensa_civil_municipal(
        self,
        ubigeo: str,
        datos_irce: Optional[Dict[str, Any]] = None,
        anomalia_tsm: float = 1.8,
        precipitacion_estimada_mm: float = 65.0,
        modo_simulacion: bool = True
    ) -> Dict[str, Any]:
        """
        Dispara la notificación formal por correo electrónico al Jefe de Defensa Civil
        del municipio correspondiente según el índice IRCE y la telemetría FEN.
        """
        if datos_irce is None:
            datos_irce = self.calcular_irce_fen_distrital(ubigeo=ubigeo)
        return self.despachador_defensa_civil.disparar_correo_alerta(
            ubigeo=ubigeo,
            datos_irce=datos_irce,
            anomalia_tsm=anomalia_tsm,
            precipitacion_estimada_mm=precipitacion_estimada_mm,
            modo_simulacion=modo_simulacion
        )

    def consultar_historial_despachos_defensa_civil(self) -> List[Dict[str, Any]]:
        """Retorna el registro histórico de alertas enviadas a municipalidades."""
        return self.despachador_defensa_civil.consultar_historial_despachos()

    def ejecutar_comando_consola(self, comando: str, usuario: str = "Operador Sala C2") -> Dict[str, Any]:
        """Ejecuta una directiva táctica en la terminal de la Sala C2."""
        return self.consola_c2.ejecutar_comando(comando, self, usuario)

    def calcular_indicadores_todos_ubigeos(
        self,
        lluvia_base_mm: float = 40.0,
        anomalia_tsm: float = 1.8,
        region_activa: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Calcula de forma dinámica el Índice IRCE-FEN y asigna el color cromático
        para cada uno de los 893 UBIGEOs del Perú según la telemetría actual.
        Permite actualizar el mapa nacional en tiempo real al mover los sliders.
        """
        import os
        import json

        path_ubigeos = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "geodatos_893_distritos_ubigeo.json")
        try:
            with open(path_ubigeos, "r", encoding="utf-8") as f:
                data = json.load(f)
                ubigeos = data.get("ubigeos", [])
        except Exception:
            return []

        # Departamentos con alta vulnerabilidad costera FEN
        macro_norte = ["PIURA", "TUMBES", "LAMBAYEQUE", "LA LIBERTAD"]
        dept_activa = region_activa.strip().upper() if region_activa else ""

        resultados = []
        for u in ubigeos:
            dep = u["departamento"]
            dist = u["distrito"]
            
            # Modulador territorial de precipitación
            mult_lluvia = 1.0
            if dept_activa and dep == dept_activa:
                mult_lluvia = 1.35
            elif dep in macro_norte:
                mult_lluvia = 1.20 if anomalia_tsm >= 1.5 else 0.90
            elif dep in ["LIMA", "ICA", "ANCASH"]:
                mult_lluvia = 1.05
            else:
                mult_lluvia = 0.70

            lluvia_efectiva = lluvia_base_mm * mult_lluvia

            # 1. Peligro (P)
            i_tsm = min(1.0, max(0.0, anomalia_tsm / 2.5))
            i_sen = 1.0 if lluvia_efectiva >= 50 else (0.7 if lluvia_efectiva >= 30 else (0.4 if lluvia_efectiva >= 15 else 0.1))
            i_lluvia = min(1.0, lluvia_efectiva / 55.0)
            p_peligro = (0.35 * i_tsm) + (0.35 * i_sen) + (0.30 * i_lluvia)

            # 2. Vulnerabilidad (V)
            # Premio/castigo a distritos históricos conocidos de inundación
            dist_norm = dist.replace(" ", "").upper()
            es_critico = dist_norm in ["CATACAOS", "CURAMORI", "PIURA", "CASTILLA", "TAMBOGRANDE", "ELPORVENIR", "HUANCHACO", "LURIGANCHO", "CHOSICA", "ILLIMO", "PACORA", "LATINGUIÑA"]
            v_hist = 0.95 if es_critico else 0.50
            v_expo = min(1.0, u["poblacion_estimada"] / 120000.0)
            v_vuln = (0.45 * v_hist) + (0.35 * v_expo) + 0.20

            # 3. Capacidad (C)
            c_cap = 0.85  # Declarado en DS 124-2026-PCM

            # 4. Cálculo del Score IRCE-FEN
            score = round(min(1.0, (p_peligro * v_vuln) / c_cap), 3)

            # 5. Asignación Cromática y de Semáforo
            if score >= 0.78:
                nivel = "CRITICO_ROJO"
                semaforo = "🔴 ROJO (Evacuación Crítica Inminente)"
                color = [230, 57, 70, 230]       # Rojo vibrante
                radio = 11000

            elif score >= 0.60:
                nivel = "ALTO_NARANJA"
                semaforo = "🟠 NARANJA (Alerta Táctica Inmediata)"
                color = [247, 127, 0, 210]       # Naranja
                radio = 8500
            elif score >= 0.35:
                nivel = "MEDIO_AMARILLO"
                semaforo = "🟡 AMARILLO (Vigilancia Preventiva)"
                color = [255, 209, 102, 190]     # Amarillo
                radio = 6500
            else:
                nivel = "BAJO_VERDE"
                semaforo = "🟢 VERDE (Monitoreo Basal)"
                color = [6, 214, 160, 160]       # Verde azulado
                radio = 4500

            resultados.append({
                "id": u["id"],
                "ubigeo": u["ubigeo"],
                "distrito": dist,
                "provincia": u["provincia"],
                "departamento": dep,
                "lat": u["latitud"],
                "lon": u["longitud"],
                "poblacion": u["poblacion_estimada"],
                "lluvia_estimada_mm": round(lluvia_efectiva, 1),
                "score_irce": score,
                "nivel_alerta": nivel,
                "semaforo": semaforo,
                "color": color,
                "radius": radio,
                "p_peligro": round(p_peligro, 2),
                "v_vuln": round(v_vuln, 2)
            })

        return resultados

    def procesar_alertas_telegram_cambio_rojo(
        self,
        distritos_fen: Optional[List[Dict[str, Any]]] = None,
        distritos_chiri: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Monitorea transiciones territoriales y despacha alertas a Telegram
        únicamente cuando un distrito transiciona a ALERTA ROJA (Crítico).
        Cada mensaje declara explícitamente que fue elaborado por IA (Ley N° 31814).
        """
        alertas_fen = []
        alertas_chiri = []
        if distritos_fen:
            alertas_fen = self.notificador_telegram.procesar_transiciones_fen(distritos_fen)
        if distritos_chiri:
            alertas_chiri = self.notificador_telegram.procesar_transiciones_chiri(distritos_chiri)

        return {
            "total_alertas_fen": len(alertas_fen),
            "total_alertas_chiri": len(alertas_chiri),
            "alertas_fen": alertas_fen,
            "alertas_chiri": alertas_chiri,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def calcular_indicadores_desde_ingestas_oficiales(
        self,
        sync_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula de forma automática el Índice IRCE-FEN y asigna el color cromático
        para cada uno de los 893 UBIGEOs del Perú cruzando directamente los datos
        de las INGESTAS OFICIALES AUTORIZADAS (SENAMHI, ENFEN, NOAA, ANA).
        Se ejecuta con cada actualización de las fuentes oficiales.
        """
        import os
        import json

        if sync_data is None:
            sync_data = self.ingestor_oficial.obtener_informe_tecnico_enfen()
            anomalia_tsm = float(sync_data.get("anomalia_tsm_nino_1_2", 1.8))
            avisos = self.ingestor_oficial.obtener_avisos_meteorologicos()

        else:
            anomalia_tsm = float(sync_data.get("anomalia_tsm_detectada", 1.8))
            avisos = sync_data.get("avisos_meteorologicos_activos", [])

        # Extraer departamentos bajo aviso oficial de SENAMHI
        dept_en_aviso_rojo = set()
        dept_en_aviso_naranja = set()
        dept_en_aviso_amarillo = set()

        for av in avisos:
            lvl = av.get("nivel_alerta", "").upper()
            titulo = av.get("titulo", "").upper()
            if "NORTE" in titulo or "PIURA" in titulo or "TUMBES" in titulo or "LAMBAYEQUE" in titulo:
                if lvl == "ROJO":
                    dept_en_aviso_rojo.update(["PIURA", "TUMBES", "LAMBAYEQUE", "LA LIBERTAD"])
                elif lvl == "NARANJA":
                    dept_en_aviso_naranja.update(["PIURA", "TUMBES", "LAMBAYEQUE", "LA LIBERTAD"])
            if "CENTRO" in titulo or "LIMA" in titulo:
                if lvl in ["ROJO", "NARANJA"]:
                    dept_en_aviso_naranja.update(["LIMA", "ANCASH", "ICA"])
            if "SUR" in titulo:
                dept_en_aviso_amarillo.update(["AREQUIPA", "MOQUEGUA", "TACNA"])

        # Por defecto según diagnóstico ENFEN vigente
        if not dept_en_aviso_rojo and not dept_en_aviso_naranja:
            if anomalia_tsm >= 1.5:
                dept_en_aviso_rojo.update(["PIURA", "TUMBES", "LAMBAYEQUE"])
                dept_en_aviso_naranja.update(["LA LIBERTAD", "LIMA", "ICA", "ANCASH"])

        # Verificar si hay ríos en desborde en las estaciones de aforo
        estaciones_aforo = self.consultar_estaciones_aforo()
        dept_aforo_desborde = set()
        for e in estaciones_aforo:
            q_act = e.get("caudal_simulado_actual_m3s", e.get("caudal_normal_m3s"))
            if q_act >= e.get("umbral_rojo_desborde_m3s", 999999):
                dept_aforo_desborde.add(e.get("departamento", "").upper())

        # Cargar los 893 UBIGEOs
        path_ubigeos = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "geodatos_893_distritos_ubigeo.json")
        try:
            with open(path_ubigeos, "r", encoding="utf-8") as f:
                data = json.load(f)
                ubigeos = data.get("ubigeos", [])
        except Exception:
            return []

        resultados = []
        for u in ubigeos:
            dep = u["departamento"].upper()
            dist = u["distrito"].upper()

            # Lluvia modulada por avisos autorizados SENAMHI
            if dep in dept_en_aviso_rojo or dep in dept_aforo_desborde:
                lluvia_efectiva = 75.0  # Lluvia torrencial asociada a aviso rojo
                senamhi_score = 1.0
            elif dep in dept_en_aviso_naranja:
                lluvia_efectiva = 45.0  # Lluvia moderada a fuerte
                senamhi_score = 0.7
            elif dep in dept_en_aviso_amarillo:
                lluvia_efectiva = 25.0
                senamhi_score = 0.4
            else:
                lluvia_efectiva = 10.0
                senamhi_score = 0.2

            # 1. Peligro (P)
            i_tsm = min(1.0, max(0.0, anomalia_tsm / 2.5))
            i_lluvia = min(1.0, lluvia_efectiva / 55.0)
            p_peligro = (0.35 * i_tsm) + (0.35 * senamhi_score) + (0.30 * i_lluvia)

            # 2. Vulnerabilidad (V)
            dist_norm = dist.replace(" ", "").upper()
            es_critico = dist_norm in ["CATACAOS", "CURAMORI", "PIURA", "CASTILLA", "TAMBOGRANDE", "ELPORVENIR", "HUANCHACO", "LURIGANCHO", "CHOSICA", "ILLIMO", "PACORA", "LATINGUIÑA"]
            v_hist = 0.95 if es_critico else 0.50
            v_expo = min(1.0, u["poblacion_estimada"] / 120000.0)
            v_vuln = (0.45 * v_hist) + (0.35 * v_expo) + 0.20

            # 3. Capacidad (C)
            c_cap = 0.85

            # 4. Cálculo del Score IRCE-FEN
            score = round(min(1.0, (p_peligro * v_vuln) / c_cap), 3)

            # 5. Asignación Cromática
            if score >= 0.75:
                nivel = "CRITICO_ROJO"
                semaforo = "🔴 ROJO (Evacuación Crítica Inminente)"
                color = [230, 57, 70, 230]
                radio = 11000
            elif score >= 0.60:
                nivel = "ALTO_NARANJA"
                semaforo = "🟠 NARANJA (Alerta Táctica Inmediata)"
                color = [247, 127, 0, 210]
                radio = 8500
            elif score >= 0.35:
                nivel = "MEDIO_AMARILLO"
                semaforo = "🟡 AMARILLO (Vigilancia Preventiva)"
                color = [255, 209, 102, 190]
                radio = 6500
            else:
                nivel = "BAJO_VERDE"
                semaforo = "🟢 VERDE (Monitoreo Basal)"
                color = [6, 214, 160, 160]
                radio = 4500

            resultados.append({
                "id": u["id"],
                "ubigeo": u["ubigeo"],
                "distrito": dist,
                "provincia": u["provincia"],
                "departamento": dep,
                "lat": u["latitud"],
                "lon": u["longitud"],
                "poblacion": u["poblacion_estimada"],
                "lluvia_estimada_mm": round(lluvia_efectiva, 1),
                "score_irce": score,
                "nivel_alerta": nivel,
                "semaforo": semaforo,
                "color": color,
                "radius": radio,
                "p_peligro": round(p_peligro, 2),
                "v_vuln": round(v_vuln, 2),
                "origen_ingesta": "INGESTAS_AUTORIZADAS_SENAMHI_ENFEN",
                "fecha_hora_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            })

        self.metadata_ultima_ingesta = {
            "fecha_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tipo": "TOTAL_MULTIFUENTE" if avisos else "PARCIAL_DIAGNOSTICO",
            "fuentes_consultadas": ["SENAMHI Avisos", "ENFEN Diagnóstico", "ANA Red de Aforo", "Open-Meteo"],
            "total_ubigeos_procesados": len(resultados),
            "version_id": f"INGESTA-{int(datetime.now().timestamp())}"
        }

        # Registrar snapshot en el historial para análisis comparativo delta
        try:
            from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
            gestor_historico_sincronizaciones.registrar_snapshot(
                ubigeos_data=resultados,
                fuente="Ingesta Oficial Autorizada (SENAMHI / ENFEN / ANA)",
                motivo=f"Actualización de telemetría ({self.metadata_ultima_ingesta['tipo']})"
            )
        except Exception as e:
            pass

        return resultados

    def obtener_metadata_ultima_ingesta(self) -> Dict[str, Any]:
        """Retorna la fecha, hora y tipo de la última actualización de ingestas autorizadas."""
        return self.metadata_ultima_ingesta

    def obtener_historico_sincronizaciones(self, periodo: str = "TODO") -> List[Dict[str, Any]]:
        """Retorna la serie temporal de sincronizaciones filtrada por período (1D, 5D, 7D, 1M, 1A, TODO)."""
        from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
        if not periodo or str(periodo).upper() == "TODO":
            return gestor_historico_sincronizaciones.obtener_todos_los_snapshots()
        return gestor_historico_sincronizaciones.filtrar_por_periodo(periodo)

    def obtener_comparativa_delta_sincronizaciones(self) -> Dict[str, Any]:
        """Retorna la variación de nodos (Rojos, Naranjas, Amarillos, Verdes) entre la última y penúltima sincronización."""
        from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
        return gestor_historico_sincronizaciones.obtener_comparativa_delta_ultima()

    def consultar_open_meteo(self, latitud: float, longitud: float, dias: int = 3) -> Dict[str, Any]:
        """Consulta el pronóstico climático de Open-Meteo para contraste internacional."""
        from core.conector_open_meteo import conector_open_meteo
        return conector_open_meteo.consultar_pronostico_distrital(latitud, longitud, dias)

    def sincronizar_fuentes_oficiales(self, incluir_internacionales: bool = True) -> Dict[str, Any]:
        """
        Sincroniza en tiempo real las fuentes oficiales nacionales (SENAMHI, ENFEN)
        e internacionales (NOAA CPC, IRI Columbia, El Niño Live), actualizando
        de inmediato los indicadores y colores de los 893 UBIGEOs.
        """
        from core.ingestor_oficial import IngestorOficialSenamhiEnfen
        ingestor = IngestorOficialSenamhiEnfen()
        sync_result = ingestor.sincronizar_todo(incluir_internacionales=incluir_internacionales)

        # Actualizar Agente Senamhi
        self.agente_senamhi.sincronizar_avisos_en_vivo(ingestor)

        # Evaluar gobernanza anticipada con la anomalía detectada del ENFEN
        anomalia_enfen = sync_result.get("anomalia_tsm_detectada", 1.8)
        eval_anticipatoria = self.evaluar_gobernanza_anticipada(anomalia_tsm=anomalia_enfen)

        sync_result["gobernanza_anticipada_enfen"] = eval_anticipatoria
        
        # ACTUALIZACIÓN AUTOMÁTICA DEL MAPA NACIONAL POR UBIGEO BASADO EN INGESTAS AUTORIZADAS (AMARU-FEN)
        sync_result["ubigeos_indicadores_actualizados"] = self.calcular_indicadores_desde_ingestas_oficiales(sync_result)

        # SINCRONIZACIÓN DUAL ACOPLADA: AMARU-CHIRI (Fase Fría / Heladas Altoandinas)
        try:
            # Detectar forzamiento térmico marino
            tsm_n34 = sync_result.get("enfen_diagnostico_oficial", {}).get("anomalia_tsm_nino_3_4", -1.2)
            if "fuentes_internacionales" in sync_result:
                noaa = sync_result["fuentes_internacionales"].get("noaa_cpc", {})
                tsm_noaa = noaa.get("anomalia_tsm_nino_3_4")
                if tsm_noaa is not None:
                    tsm_n34 = float(tsm_noaa)

            # Si hay calentamiento fuerte en costa (FEN), el Altiplano sufre subsidencia y helada radiativa (-2.5°C)
            # Si hay La Niña (TSM < 0), sufre advección polar y alisios fuertes
            delta_frio = -2.5 if anomalia_enfen >= 1.5 else -1.5
            alisios_calc = 8.2 if anomalia_enfen <= 0.0 else 7.4

            eval_chiri = self.agente_crioclimatico.ejecutar_barrido_territorial(
                escenario_tmin_delta=delta_frio,
                anomalia_tsm_pacifico=float(tsm_n34) if isinstance(tsm_n34, (int, float)) else -1.4,
                alisios_velocidad=alisios_calc
            )
            sync_result["amaru_chiri"] = eval_chiri.model_dump()
            
            # Generar actualización directa del Reloj de La Niña
            tsm_chiri_val = float(tsm_n34) if isinstance(tsm_n34, (int, float)) else -1.4
            tmin_prom = sum(e.tmin_observada_c for e in eval_chiri.evaluaciones) / len(eval_chiri.evaluaciones) if eval_chiri.evaluaciones else -10.0
            reloj_modelo = self.motor_reloj_nina.calcular_reloj(
                fecha_evaluacion=datetime.now(),
                anomalia_tsm=tsm_chiri_val,
                velocidad_alisios=alisios_calc,
                tmin_promedio=tmin_prom
            )
            sync_result["amaru_chiri_reloj"] = {
                "hora_tactica": reloj_modelo.minutero.hora_tactica_final,
                "desfase_dias": reloj_modelo.minutero.desfase_forzamiento_dias,
                "calificacion": reloj_modelo.minutero.calificacion_tiempo,
                "analogo_dominante": reloj_modelo.analogo_dominante.evento_nombre,
                "similitud": reloj_modelo.analogo_dominante.porcentaje_similitud,
                "svg": self.motor_reloj_nina.generar_svg_reloj(reloj_modelo)
            }
            sync_result["amaru_chiri_sincronizado"] = True
        except Exception as e:
            sync_result["amaru_chiri_sincronizado"] = False
            sync_result["amaru_chiri_error"] = str(e)

        # PROCESAMIENTO AUTOMÁTICO DE ALERTAS TELEGRAM (LEY Nº 31814)
        try:
            distritos_fen_actualizados = sync_result.get("ubigeos_indicadores_actualizados", [])
            distritos_chiri_actualizados = []
            if "amaru_chiri" in sync_result and "evaluaciones" in sync_result["amaru_chiri"]:
                distritos_chiri_actualizados = sync_result["amaru_chiri"]["evaluaciones"]

            alertas_tg = self.procesar_alertas_telegram_cambio_rojo(
                distritos_fen=distritos_fen_actualizados,
                distritos_chiri=distritos_chiri_actualizados
            )
            sync_result["alertas_telegram_despachadas"] = alertas_tg
        except Exception as e_tg:
            sync_result["alertas_telegram_error"] = str(e_tg)

        return sync_result

    def actualizar_reloj_nina(
        self,
        anomalia_tsm: Optional[float] = None,
        fecha_evaluacion: Optional[datetime] = None,
        velocidad_alisios: Optional[float] = None,
        tmin_promedio: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula y actualiza el estado dinámico del Reloj de La Niña (AMARU-CHIRI)
        conectándolo con la telemetría más reciente o parámetros personalizados.
        """
        if anomalia_tsm is None:
            diag = self.ingestor_oficial.consultar_diagnostico_climatico_enfen()
            anomalia_tsm = float(diag.get("anomalia_tsm_nino_3_4", -1.4))
        if velocidad_alisios is None:
            velocidad_alisios = 8.2 if anomalia_tsm <= -0.5 else 6.5
        if tmin_promedio is None:
            tmin_promedio = -12.5 if anomalia_tsm <= -1.2 else -6.0

        modelo = self.motor_reloj_nina.calcular_reloj(
            fecha_evaluacion=fecha_evaluacion or datetime.now(),
            anomalia_tsm=anomalia_tsm,
            velocidad_alisios=velocidad_alisios,
            tmin_promedio=tmin_promedio
        )
        svg = self.motor_reloj_nina.generar_svg_reloj(modelo)
        return {
            "modelo": modelo.model_dump(),
            "svg": svg,
            "hora_tactica": modelo.minutero.hora_tactica_final,
            "desfase_dias": modelo.minutero.desfase_forzamiento_dias,
            "calificacion": modelo.minutero.calificacion_tiempo,
            "analogo_dominante": modelo.analogo_dominante.evento_nombre,
            "similitud": modelo.analogo_dominante.porcentaje_similitud,
            "anomalia_tsm": anomalia_tsm,
            "velocidad_alisios": velocidad_alisios,
            "tmin_promedio": tmin_promedio
        }

    def consultar_contacto_defensa_civil(self, ubigeo: str) -> Optional[Dict[str, Any]]:
        """Consulta el directorio institucional de Defensa Civil Municipal por código UBIGEO."""
        from core.alerta_defensa_civil import DespachadorDefensaCivilMunicipal
        despachador = DespachadorDefensaCivilMunicipal()
        return despachador.buscar_contacto_por_ubigeo(ubigeo)

    def consultar_historial_despachos_defensa_civil(self) -> List[Dict[str, Any]]:
        """Retorna el historial auditado de despachos con protección de datos personales."""
        from core.alerta_defensa_civil import DespachadorDefensaCivilMunicipal
        despachador = DespachadorDefensaCivilMunicipal()
        return despachador.consultar_historial_despachos()

    def disparar_alerta_defensa_civil_municipal(
        self,
        ubigeo: str,
        datos_irce: Optional[Dict[str, Any]] = None,
        anomalia_tsm: float = 1.8,
        precipitacion_estimada_mm: float = 65.0,
        modo_simulacion: bool = True,
        firma_humana: Optional[Dict[str, Any]] = None,
        autorizacion_humana: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Emite la alerta formal (correo detallado y mensaje corto Telegram) al responsable de Defensa Civil.
        Aplica estricta compuerta de soberanía humana (Ley N° 31814) y anonimización de datos (Ley N° 29733).
        """
        from core.alerta_defensa_civil import DespachadorDefensaCivilMunicipal
        despachador = DespachadorDefensaCivilMunicipal()
        
        # Resolver datos IRCE si no fueron proporcionados
        if not datos_irce:
            contacto = despachador.buscar_contacto_por_ubigeo(ubigeo)
            nom_dist = contacto.get("distrito", "DISTRITO") if contacto else "DISTRITO"
            dep = contacto.get("departamento", "DEPARTAMENTO") if contacto else "DEPARTAMENTO"
            prov = contacto.get("provincia", "PROVINCIA") if contacto else "PROVINCIA"
            
            score_irce = 0.85
            nivel = "CRITICO_ROJO"
            semaforo = "🔴 ROJO (Evacuación Inminente)"
            poblacion = 68400
            
            datos_irce = {
                "ubigeo": ubigeo,
                "distrito": nom_dist,
                "provincia": prov,
                "departamento": dep,
                "score_irce": score_irce,
                "nivel_alerta": nivel,
                "semaforo": semaforo,
                "poblacion": poblacion
            }

        firma_efectiva = firma_humana or autorizacion_humana

        return despachador.disparar_correo_alerta(
            ubigeo=ubigeo,
            datos_irce=datos_irce,
            anomalia_tsm=anomalia_tsm,
            precipitacion_estimada_mm=precipitacion_estimada_mm,
            modo_simulacion=modo_simulacion,
            firma_humana=firma_efectiva
        )

    def consultar_marco_soberania_humana(self) -> Dict[str, Any]:
        """Retorna las directivas vinculantes de Soberanía Humana (Ley N° 31814 y DS 085-2024-PCM)."""
        if hasattr(self, "agente_legal") and hasattr(self.agente_legal, "consultar_marco_soberania_humana_ia"):
            return self.agente_legal.consultar_marco_soberania_humana_ia()
        from agents.agente_legal_normativo import AgenteLegalNormativo
        return AgenteLegalNormativo().consultar_marco_soberania_humana_ia()


    def ejecutar_comando_consola(self, comando: str, usuario: str = "Operador Sala C2") -> Dict[str, Any]:
        """Ejecuta una directiva de mando táctico en la Sala de Situación C2."""
        from core.consola_c2 import ConsolaTacticoC2
        consola = ConsolaTacticoC2()
        return consola.ejecutar_comando(linea_comando=comando, orchestrator=self, usuario_autorizador=usuario)

    def registrar_snapshot_sincronizacion(
        self,
        ubigeos_data: List[Dict[str, Any]],
        fuente: str = "Ingesta Oficial Autorizada (SENAMHI / ENFEN)",
        motivo: str = "Sincronización periódica C2"
    ) -> Dict[str, Any]:
        """Registra un snapshot de los 893 UBIGEOS y calcula las variaciones delta."""
        from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
        return gestor_historico_sincronizaciones.registrar_snapshot(ubigeos_data, fuente=fuente, motivo=motivo)

    def obtener_comparativa_delta_sincronizaciones(self) -> Dict[str, Any]:
        """Retorna la comparativa delta de semáforo entre la última sincronización y la previa."""
        from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
        return gestor_historico_sincronizaciones.obtener_comparativa_delta_ultima()

    def obtener_historico_sincronizaciones(self, periodo: str = "TODO") -> List[Dict[str, Any]]:
        """Retorna la serie temporal de sincronizaciones filtrada por período (1D, 5D, 7D, 1M, 1A, TODO)."""
        from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
        if not periodo or periodo.upper() == "TODO":
            return gestor_historico_sincronizaciones.obtener_todos_los_snapshots()
        return gestor_historico_sincronizaciones.filtrar_por_periodo(periodo)

    def consultar_open_meteo(
        self,
        latitud: float,
        longitud: float,
        dias: int = 3
    ) -> Dict[str, Any]:
        """Consulta el pronóstico pluviométrico en tiempo real vía Open-Meteo para una coordenada."""
        from core.conector_open_meteo import conector_open_meteo
        return conector_open_meteo.consultar_pronostico_distrital(latitud=latitud, longitud=longitud, dias_pronostico=dias)

    # --- BUCLE DE MEJORA CONTINUA TRANSPARENTE: NIVEL 3 POST-MORTEM RL ---

    def ejecutar_evaluacion_post_mortem(
        self,
        resultados_reales: List[ResultadoRealEvento],
        evento_nombre: str = "Temporada FEN 2026",
        decisiones_custom: Optional[List[RegistroDecisionC2]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el Bucle de Mejora Continua Transparente (Nivel 3 Safe RL / Saaty AHP).
        Contrasta las decisiones operativas C2 contra el Ground Truth oficial (EDAN INDECI/ANA),
        optimiza los coeficientes de Saaty manteniendo CR <= 0.10 y emite el dictamen pericial con SHA-256.
        """
        decs = decisiones_custom or self.historial_decisiones_c2
        informe = self.motor_post_mortem.emitir_informe_pericial(
            evento_nombre=evento_nombre,
            decisiones=decs,
            resultados_reales=resultados_reales
        )
        self.ultimo_informe_pericial = informe
        acta_md = self.motor_post_mortem.exportar_acta_markdown(informe)
        return {
            "id_informe": informe.id_informe,
            "hash_sha256": informe.hash_sha256_acta,
            "metricas": informe.metricas_rendimiento.model_dump(),
            "matriz_calibrada": informe.matriz_saaty_optimizada.model_dump(),
            "variacion_pesos": informe.variacion_ponderados,
            "acta_markdown": acta_md,
            "recibo_criptografico": informe.recibo_criptografico_c2,
            "sello_soberania_humana_ley_31814": informe.sello_soberania_humana
        }

    def declarar_corte_temporada_fen(
        self,
        orden_corte: OrdenCorteTemporadaFEN,
        resultados_reales: List[ResultadoRealEvento],
        decisiones_custom: Optional[List[RegistroDecisionC2]] = None
    ) -> Dict[str, Any]:
        """
        HITO 1 DE GOBERNANZA (Ley Nº 31814):
        El Comité Técnico Científico emite la Orden de Corte de Temporada FEN.
        El orquestador congela las decisiones C2, ejecuta la auditoría post-mortem
        y genera el informe pericial en estado 'PROPUESTA_PENDIENTE_COMITE'
        (sin modificar la matriz activa hasta la ratificación formal).
        """
        decs = decisiones_custom or self.historial_decisiones_c2
        informe = self.motor_post_mortem.emitir_informe_pericial(
            evento_nombre=orden_corte.evento_evaluado,
            decisiones=decs,
            resultados_reales=resultados_reales,
            orden_corte=orden_corte,
            auto_ratificar=False  # Requiere sesión y acta de ratificación
        )
        self.ultimo_informe_pericial = informe
        acta_md = self.motor_post_mortem.exportar_acta_markdown(informe)
        return {
            "id_orden_corte": orden_corte.id_orden_corte,
            "id_informe": informe.id_informe,
            "estado_gobernanza": informe.estado_gobernanza,
            "hash_sha256": informe.hash_sha256_acta,
            "metricas": informe.metricas_rendimiento.model_dump(),
            "matriz_propuesta": informe.matriz_saaty_optimizada.model_dump(),
            "variacion_pesos": informe.variacion_ponderados,
            "acta_markdown": acta_md,
            "sello_soberania_humana_ley_31814": True
        }

    def ratificar_calibracion_comite(
        self,
        acta: ActaRatificacionComite
    ) -> Dict[str, Any]:
        """
        HITO 2 DE GOBERNANZA (Ley Nº 31814):
        El Comité Técnico Científico sesiona, evalúa el dictamen y firma la ratificación.
        Solo tras este acto humano soberano la nueva matriz Saaty AHP entra en vigor.
        """
        if not self.ultimo_informe_pericial:
            raise RuntimeError("No existe informe pericial pendiente de ratificación.")

        informe_ratificado = self.motor_post_mortem.ratificar_calibracion_comite(
            informe=self.ultimo_informe_pericial,
            acta=acta
        )
        self.ultimo_informe_pericial = informe_ratificado
        acta_md = self.motor_post_mortem.exportar_acta_markdown(informe_ratificado)

        return {
            "id_acta": acta.id_acta,
            "id_informe": informe_ratificado.id_informe,
            "estado_gobernanza": informe_ratificado.estado_gobernanza,
            "decision_comite": acta.decision_comite,
            "pesos_activos_vigentes": self.motor_post_mortem.matriz_activa.pesos,
            "cr_activo": self.motor_post_mortem.matriz_activa.cr,
            "acta_markdown": acta_md,
            "hash_sha256_acta": acta.hash_sha256_acta,
            "sello_soberania_humana_ley_31814": True
        }

    def obtener_pesos_saaty_vigentes(self) -> Dict[str, Any]:
        """Retorna los pesos Saaty AHP vigentes y el Ratio de Consistencia (CR)."""
        mat = self.motor_post_mortem.matriz_activa
        return {
            "pesos": mat.pesos,
            "cr": mat.cr,
            "lambda_max": mat.lambda_max,
            "ci": mat.ci,
            "es_consistente": mat.es_consistente
        }

    def obtener_ultimo_informe_pericial(self) -> Optional[Dict[str, Any]]:
        """Retorna el último informe pericial post-mortem generado."""
        if not self.ultimo_informe_pericial:
            return None
        return self.ultimo_informe_pericial.model_dump()





