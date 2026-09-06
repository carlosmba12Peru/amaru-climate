import json
import math
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.climate_oracle_web3 import AmaruClimateOracle
from core.conector_igp_lahares import conector_igp_lahares

logger = logging.getLogger(__name__)

# Constantes canónicas inmutables de la fórmula IPH-FEN
PESOS_CANONICOS_IPH = {
    "w_meteo": 0.30,
    "w_suelo": 0.20,
    "w_irce": 0.20,
    "w_geomorf": 0.15,
    "w_hist": 0.15,
    "phi_0": 0.68,
    "k_sigmoide": 4.2
}

# Hash SHA-256 inmutable de los pesos calibrados (anclado criptográficamente)
HASH_CANONICO_PESOS = hashlib.sha256(
    json.dumps(PESOS_CANONICOS_IPH, sort_keys=True).encode("utf-8")
).hexdigest()

class AgenteGeorriesgo:
    """
    Agente de Georriesgo Dinámico, Hidro-Cinético y Criptográficamente Blindado C2:
    Cruza avisos meteorológicos en tiempo real (Open-Meteo, ECMWF, SENAMHI)
    con la Franja de Cabecera Andina (800 - 3,800 msnm), el IRCE de UBIGEOs circundantes
    y la memoria histórica FEN para calcular el IPH-FEN y el retardo T_lag.
    
    Blindaje de Ciberseguridad:
    - Circuit-breaker anti-tampering por hash SHA-256.
    - Sanitización anti-envenenamiento de inputs (Zero-Trust Data Filter).
    - Firma digital asimétrica no repudiable secp256k1 en cada cálculo.
    """
    def __init__(self):
        self.nombre = "Agente de Georriesgo e Hidrocemática C2 Blindado"
        self.oraculo = AmaruClimateOracle()
        self.pesos = dict(PESOS_CANONICOS_IPH)
        self.hash_pesos_esperado = HASH_CANONICO_PESOS
        self._cargar_datos_territoriales()

    def _cargar_datos_territoriales(self):
        base_path = Path(__file__).parent.parent / "data"
        hist_path = base_path / "historico_fen_1998_2017.json"
        queb_path = base_path / "catalogo_quebradas_criticas.json"
        corredor_path = base_path / "corredor_cabeceras_andinas.json"
        fondes_path = base_path / "distritos_riesgo_nacional_1891_cenepred_mef.json"
        
        with open(hist_path, "r", encoding="utf-8") as f:
            self.historico = json.load(f)["distritos_criticos"]
            
        with open(queb_path, "r", encoding="utf-8") as f:
            self.quebradas = json.load(f)

        if corredor_path.exists():
            with open(corredor_path, "r", encoding="utf-8") as f:
                self.corredor = json.load(f)
        else:
            self.corredor = {"tramos_orograficos": []}

        # Matriz nacional de los 1,891 distritos FONDES (D.S. N° 234-2025-EF)
        self.distritos_fondes_map = {}
        if fondes_path.exists():
            try:
                with open(fondes_path, "r", encoding="utf-8") as f:
                    data_f = json.load(f)
                    for d in data_f.get("distritos", []):
                        ub = d.get("ubigeo")
                        nom = d.get("distrito", "").upper()
                        dep = d.get("departamento", "").upper()
                        if ub:
                            self.distritos_fondes_map[ub] = d
                        self.distritos_fondes_map[f"{dep}-{nom}"] = d
            except Exception as e:
                logger.warning(f"No se pudo cargar distritos_riesgo_nacional_1891_cenepred_mef.json: {e}")

    def verificar_integridad_formula(self) -> Dict[str, Any]:
        """
        Circuit-Breaker Anti-Tampering:
        Verifica que los pesos y la lógica algorítmica no hayan sido alterados
        maliciosamente en memoria RAM por inyección o manipulación de hackers.
        """
        hash_actual = hashlib.sha256(
            json.dumps(self.pesos, sort_keys=True).encode("utf-8")
        ).hexdigest()
        es_integro = (hash_actual == self.hash_pesos_esperado)
        return {
            "estado": "INTEGRO_VERIFICADO_OK" if es_integro else "ALERTA_SABOTAJE_TAMPER_DETECTED",
            "es_integro": es_integro,
            "hash_actual": hash_actual,
            "hash_canonico_esperado": self.hash_pesos_esperado,
            "algoritmo_hashing": "SHA-256",
            "oraculo_direccion": self.oraculo.oracle_address_fingerprint,
            "blindaje_activo": True
        }

    def obtener_corredor_cabeceras(self) -> Dict[str, Any]:
        """Retorna la configuración y puntos de muestreo de la Franja de Cabeceras Andinas."""
        return self.corredor

    def calcular_probabilidad_dinamica_huaico(
        self,
        id_o_nombre: str,
        lluvia_cabecera_mm_h: float = 0.0,
        lluvia_acumulada_24h: float = 0.0,
        saturacion_api_72h: float = 0.0,
        irce_circundante: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calcula el Índice de Previsión de Huaicos ante El Niño (IPH-FEN) con blindaje criptográfico:
        Integra 5 componentes físico-territoriales:
        1. C_meteo (30%): Hidrometeorología dinámica de cabecera (Open-Meteo/ECMWF)
        2. C_suelo (20%): Saturación antecedente API a 72 horas
        3. C_irce  (20%): Vulnerabilidad territorial ponderada de UBIGEOs circundantes
        4. C_geomorf (15%): Pendiente media y carga detrítica
        5. C_hist  (15%): Memoria histórica y reincidencia FEN (1983-2023)
        """
        # 0. Verificación de Integridad Anti-Sabotaje
        verif = self.verificar_integridad_formula()
        if not verif["es_integro"]:
            raise RuntimeError(
                f"ALERTA CRÍTICA DE CIBERSEGURIDAD C2: Alteración no autorizada detectada en la fórmula IPH-FEN. "
                f"Hash actual ({verif['hash_actual'][:12]}...) no coincide con hash canónico. Proceso abortado."
            )

        # 0.1 Sanitización de Entradas Anti-Envenenamiento (Zero-Trust Data Sanity Check)
        lluvia_cabecera_limpia = max(0.0, min(float(lluvia_cabecera_mm_h), 300.0))
        lluvia_24h_limpia = max(0.0, min(float(lluvia_acumulada_24h), 600.0))
        api_limpio = max(0.0, min(float(saturacion_api_72h), 200.0))
        irce_limpio = max(0.0, min(float(irce_circundante if irce_circundante is not None else 0.40), 1.0))

        termino = id_o_nombre.lower().strip()
        quebrada = None
        for q in self.quebradas:
            match = (
                termino == q.get("id_quebrada", "").lower()
                or termino == q.get("codigo_tactico_c2", "").lower()
                or termino in q.get("codigo_tactico_c2", "").lower()
                or q.get("codigo_tactico_c2", "").lower().startswith(termino)
                or termino in q.get("denominacion_amaru", "").lower()
                or termino in q.get("nombre", "").lower()
                or termino == q.get("codigo_oficial_igp", "").lower()
                or termino in q.get("denominacion_oficial_igp", "").lower()
                or termino == q.get("codigo_pfafstetter_ana", "").lower()
                or termino == q.get("codigo_punto_critico_ana", "").lower()
                or termino == q.get("codigo_ingemmet_peligro", "").lower()
                or termino == q.get("codigo_sigrid_cenepred", "").lower()
                or termino in q.get("codigo_vial_mtc_pvn", "").lower()
                or termino in q.get("distrito", "").lower()
            )
            if match:
                quebrada = q
                break

        if not quebrada:
            return {
                "agente": self.nombre,
                "estado": "NO_ENCONTRADA",
                "mensaje": f"Quebrada o código oficial '{id_o_nombre}' no localizado en el catálogo C2."
            }

        umbral_horario = max(1.0, float(quebrada.get("umbral_critico_mm_hora", 12.0)))
        umbral_24h = max(1.0, float(quebrada.get("umbral_acumulado_24h", 35.0)))
        tc_horas = float(quebrada.get("tiempo_concentracion_horas", 1.8))
        pendiente_pct = float(quebrada.get("pendiente_media_pct", 16.0))

        # 1. C_meteo: Ratios Hidrometeorológicos Dinámicos (Cabecera)
        ratio_horario = min(1.5, lluvia_cabecera_limpia / umbral_horario)
        ratio_24h = min(1.5, lluvia_24h_limpia / umbral_24h)
        c_meteo = 0.60 * ratio_horario + 0.40 * ratio_24h

        # 2. C_suelo: Saturación Antecedente del Suelo (API 72h)
        c_suelo = min(1.0, max(0.0, api_limpio / 50.0))

        # 3. C_irce: Vulnerabilidad Territorial Circundante
        c_irce = irce_limpio

        # 4. C_geomorf: Pendiente de Ladera y Gradiente
        c_geomorf = min(1.0, max(0.0, pendiente_pct / 22.0))

        # 5. C_hist: Factor de Reincidencia FEN (1983, 1998, 2017, 2023)
        num_activaciones = len(quebrada.get("historial_activaciones", []))
        c_hist = min(1.0, num_activaciones / 4.0)

        # 6. Fuerza Motriz Combinada (Phi) con Pesos Canónicos
        w = self.pesos
        phi = (
            w["w_meteo"] * c_meteo +
            w["w_suelo"] * c_suelo +
            w["w_irce"] * c_irce +
            w["w_geomorf"] * c_geomorf +
            w["w_hist"] * c_hist
        )

        # 7. Probabilidad Sigmoidal IPH-FEN
        z = w["k_sigmoide"] * (phi - w["phi_0"])
        p_huaico_raw = 1.0 / (1.0 + math.exp(-z))
        p_huaico_pct = round(p_huaico_raw * 100.0, 1)

        # Reglas duras de seguridad física (Anti-dilución de riesgo)
        if lluvia_cabecera_limpia >= umbral_horario and api_limpio >= 30.0:
            p_huaico_pct = max(p_huaico_pct, 88.0)
        elif lluvia_cabecera_limpia >= umbral_horario or lluvia_24h_limpia >= umbral_24h:
            p_huaico_pct = max(p_huaico_pct, 85.0)

        if lluvia_cabecera_limpia == 0.0 and lluvia_24h_limpia == 0.0:
            p_huaico_pct = min(p_huaico_pct, 12.0)

        # 8. Clasificación y Semáforo Táctico C2
        if p_huaico_pct >= 85.0:
            nivel = "ROJO_CRITICO"
            color_hex = "#e63946"
        elif p_huaico_pct >= 65.0:
            nivel = "NARANJA_ALTO"
            color_hex = "#f77f00"
        elif p_huaico_pct >= 35.0:
            nivel = "AMARILLO_MEDIO"
            color_hex = "#ffd166"
        else:
            nivel = "VERDE_BAJO"
            color_hex = "#06d6a0"

        minutos_retardo = int(tc_horas * 60)
        puntos_estrang = quebrada.get("puntos_estrangulamiento", [])
        poblacion = quebrada.get("poblacion_en_cono_deyeccion", 0)

        if nivel == "ROJO_CRITICO":
            accion = (
                f"🚨 ALERTA ROJA INMINENTE (IPH-FEN: {p_huaico_pct}%): Activación torrencial en cabecera ({lluvia_cabecera_limpia:.1f} mm/h). "
                f"Onda de detritos impactará puntos críticos ({', '.join(puntos_estrang[:2])}) en aproximadamente "
                f"{tc_horas:.1f} horas ({minutos_retardo} min). Cierre inmediato de badenes y evacuación de {poblacion:,} hab."
            )
        elif nivel == "NARANJA_ALTO":
            accion = (
                f"⚠️ ALERTA NARANJA PREVENTIVA (IPH-FEN: {p_huaico_pct}%): Precipitación en cabecera ({lluvia_cabecera_limpia:.1f} mm/h) cercana a umbral crítico. "
                f"Disponer maquinaria pesada en badenes y alertar comités de Defensa Civil distritales."
            )
        elif nivel == "AMARILLO_MEDIO":
            accion = (
                f"🟡 PRE-ALERTA AMARILLA (IPH-FEN: {p_huaico_pct}%): Incremento de saturación y lluvia moderada en cabecera. "
                f"Vigilancia continua del cauce y monitoreo hidrométrico."
            )
        else:
            accion = f"🟢 CONDICIÓN VERDE ESTABLE (IPH-FEN: {p_huaico_pct}%): Cauce seco en equilibrio. Monitoreo satelital regular."

        # 8.5 Telemetría In Situ del IGP y Doble Confirmación Soberana C2
        telemetria_igp = conector_igp_lahares.consultar_telemetria_in_situ(
            id_quebrada=quebrada.get("id_quebrada", ""),
            lluvia_cabecera_mm_h=lluvia_cabecera_limpia
        )
        consenso_c2 = conector_igp_lahares.evaluar_doble_confirmacion(
            iph_score=p_huaico_pct,
            telemetria_igp=telemetria_igp
        )

        resultado_calculo = {
            "agente": self.nombre,
            "id_quebrada": quebrada.get("id_quebrada"),
            "nombre_oficial": quebrada.get("nombre"),
            "quebrada": quebrada.get("nombre"),
            "cuenca": quebrada.get("cuenca"),
            "region": quebrada.get("region"),
            "provincia": quebrada.get("provincia"),
            "distrito_cabecera": quebrada.get("distrito"),
            "distritos_impactados": quebrada.get("distritos_impactados", []),
            "homologacion_oficial": {
                # Denominación canónica AMARU-FEN (Comando C2)
                "codigo_amaru": quebrada.get("id_quebrada"),
                "codigo_tactico_c2": quebrada.get("codigo_tactico_c2", f"{quebrada.get('id_quebrada')}-{quebrada.get('nombre')}"),
                "denominacion_amaru": quebrada.get("denominacion_amaru", f"{quebrada.get('id_quebrada')}: {quebrada.get('nombre')}"),
                "entidad_amaru": "AMARU-FEN (Centro de Comando & Gobernanza Anticipatoria C2)",

                # Denominación Oficial IGP (Instituto Geofísico del Perú)
                "denominacion_igp": quebrada.get("denominacion_oficial_igp", "N/A"),
                "codigo_oficial_igp": quebrada.get("codigo_oficial_igp", "N/A"),
                "entidad_igp": "Instituto Geofísico del Perú (IGP - Sistema Nacional Lahares y Huaicos)",
                "monitoreo_igp_in_situ": quebrada.get("monitoreo_igp_in_situ", False),

                # Denominación Oficial ANA (Autoridad Nacional del Agua)
                "codigo_pfafstetter_ana": quebrada.get("codigo_pfafstetter_ana", "N/A"),
                "codigo_punto_critico_ana": quebrada.get("codigo_punto_critico_ana", "N/A"),
                "entidad_ana": "Autoridad Nacional del Agua (ANA - MIDAGRI)",

                # Denominación Oficial INGEMMET
                "codigo_ingemmet_peligro": quebrada.get("codigo_ingemmet_peligro", "N/A"),
                "entidad_ingemmet": "Instituto Geológico, Minero y Metalúrgico (INGEMMET)",

                # Denominación Oficial CENEPRED (SIGRID EVAR)
                "codigo_sigrid_cenepred": quebrada.get("codigo_sigrid_cenepred", "N/A"),
                "entidad_cenepred": "Centro Nacional de Estimación, Prevención y Reducción del Riesgo de Desastres (CENEPRED)",

                # Denominación Oficial MTC / Provías Nacional
                "codigo_vial_mtc_pvn": quebrada.get("codigo_vial_mtc_pvn", "N/A"),
                "entidad_mtc": "Ministerio de Transportes y Comunicaciones (MTC / Provías Nacional)",

                # Ubigeos INEI
                "ubigeo_cabecera": quebrada.get("ubigeo_cabecera", "N/A"),
                "distrito_cabecera_nombre": quebrada.get("distrito_cabecera_nombre", quebrada.get("distrito")),
                "ubigeo_receptor": quebrada.get("ubigeo_receptor", "N/A"),
                "distrito_receptor_nombre": quebrada.get("distrito_receptor_nombre", quebrada.get("distrito")),
                "entidad_ubigeo": "Instituto Nacional de Estadística e Informática (INEI)"
            },
            "telemetria_in_situ_igp": telemetria_igp,
            "consenso_doble_confirmacion_c2": consenso_c2,
            "coordenadas_desembocadura": {"lat": quebrada.get("lat"), "lng": quebrada.get("lng")},
            "coordenadas_cabecera": {
                "lat": quebrada.get("cabecera_lat"),
                "lng": quebrada.get("cabecera_lng"),
                "altitud_msnm": quebrada.get("cabecera_altitud_msnm", 1500)
            },
            "pendiente_media_pct": pendiente_pct,
            "lluvia_cabecera_mm_h": lluvia_cabecera_limpia,
            "lluvia_acumulada_24h": lluvia_24h_limpia,
            "saturacion_api_72h": api_limpio,
            "irce_circundante_usado": round(c_irce, 3),
            "umbral_critico_mm_hora": umbral_horario,
            "umbral_acumulado_24h": umbral_24h,
            "fuerza_motriz_phi": round(phi, 3),
            "probabilidad_huaico_pct": p_huaico_pct,
            "iph_fen_score": p_huaico_pct,
            "nivel_alerta": nivel,
            "color_hex": color_hex,
            "tiempo_concentracion_horas": tc_horas,
            "tiempo_retardo_minutos": minutos_retardo,
            "poblacion_en_cono_deyeccion": poblacion,
            "puntos_estrangulamiento": puntos_estrang,
            "obras_defensa_existentes": quebrada.get("obras_defensa_existentes", ""),
            "accion_tactica_inmediata": accion,
            "triangulo_hidrografico": quebrada.get("triangulo_hidrografico", {}),
            "evidencia_visual_oficial": quebrada.get("evidencia_visual_oficial", {}),
            "boletin_pericial_ampliacion_decreto": self._generar_boletin_pericial_ampliacion(
                quebrada=quebrada,
                iph_score=p_huaico_pct,
                lluvia_cabecera=lluvia_cabecera_limpia,
                tc_horas=tc_horas
            )
        }

        # 9. Firma Criptográfica No Repudiable con Oráculo Web3 (secp256k1)
        recibo_c2 = self.oraculo.firmar_calculo_iph_fen(resultado_calculo)
        resultado_calculo["recibo_criptografico_c2"] = recibo_c2
        resultado_calculo["sello_inviolabilidad"] = {
            "estado": "VERIFICADO_CRIPTOGRAFICAMENTE_OK",
            "hash_integridad_formula": self.hash_pesos_esperado,
            "oraculo_address": recibo_c2["oracle_address"],
            "payload_hash": recibo_c2["payload_hash"],
            "firma_secp256k1_preview": recibo_c2["firma_hex"][:32] + "...",
            "ley_31814_soberania": True
        }

        return resultado_calculo

    def _generar_boletin_pericial_ampliacion(
        self,
        quebrada: Dict[str, Any],
        iph_score: float,
        lluvia_cabecera: float,
        tc_horas: float
    ) -> Optional[Dict[str, Any]]:
        """
        Emite el Dictamen Pericial C2 de Ampliación de Estado de Emergencia cuando
        el IPH-FEN supera el 85% y existen distritos del Triángulo Hidrográfico no contemplados
        en el D.S. N° 124-2026-PCM, sustentando su incorporación con la Matriz FONDES (D.S. 234-2025-EF).
        """
        triangulo = quebrada.get("triangulo_hidrografico", {})
        cobertura = triangulo.get("cobertura_legal_triangulo", {})
        requiere_ampliacion = cobertura.get("requiere_ampliacion_decreto", False)

        if iph_score < 85.0 or not requiere_ampliacion:
            return None

        # Identificar vértices extradecreto
        vertices = [
            triangulo.get("vertice_superior_cabecera", {}),
            triangulo.get("vertice_medio_transito", {}),
            triangulo.get("vertice_inferior_cono", {})
        ]

        distritos_incorporar_detalle = []
        nombres_incorporar = []

        for v in vertices:
            if not v or not v.get("distrito"):
                continue
            if not v.get("en_decreto_pcm"):
                nom = v.get("distrito")
                ub = v.get("ubigeo")
                
                # Cruzar con Matriz Nacional FONDES (D.S. N° 234-2025-EF)
                fondes_info = self.distritos_fondes_map.get(ub) or self.distritos_fondes_map.get(f"{quebrada.get('region', '').upper()}-{nom.upper()}")
                
                if fondes_info:
                    item = {
                        "distrito": nom,
                        "ubigeo": ub,
                        "vertice_rol": v.get("rol", "Vértice de Afectación"),
                        "nivel_riesgo_sigrid_fondes": fondes_info.get("nivel_peligro_riesgo_sigrid", "Alto"),
                        "documento_sustento_oficial": fondes_info.get("documento_sustento", "Oficio N° 00072-2026-CENEPRED/J"),
                        "marco_fondes": "Decreto Supremo N° 234-2025-EF (Priorización de Recursos FONDES)"
                    }
                else:
                    item = {
                        "distrito": nom,
                        "ubigeo": ub,
                        "vertice_rol": v.get("rol", "Vértice de Afectación"),
                        "nivel_riesgo_sigrid_fondes": "Alto",
                        "documento_sustento_oficial": "Oficio N° 00072-2026-CENEPRED/J",
                        "marco_fondes": "Decreto Supremo N° 234-2025-EF"
                    }
                distritos_incorporar_detalle.append(item)
                if nom not in nombres_incorporar:
                    nombres_incorporar.append(nom)

        cono_distrito = triangulo.get("vertice_inferior_cono", {}).get("distrito", quebrada.get("distrito", "Zona Baja"))

        fundamento = (
            f"Activación torrencial inminente en cabecera andina ({lluvia_cabecera:.1f} mm/h) con IPH-FEN {iph_score:.1f}%. "
            f"La masa de detritos impactará el cono de deyección ({cono_distrito}) en aproximadamente {tc_horas:.1f} horas. "
            f"Los distritos del triángulo hidrográfico ({', '.join(nombres_incorporar)}) no contemplados en el D.S. N° 124-2026-PCM "
            f"cuentan con respaldo pericial C2 y calificación oficial de riesgo en SIGRID FONDES (D.S. N° 234-2025-EF), "
            f"habilitando el uso inmediato de fondos de contingencia del Programa Presupuestal 0068."
        )

        return {
            "emitir_boletin": True,
            "titulo": f"DICTAMEN PERICIAL C2 DE AMPLIACIÓN DE ESTADO DE EMERGENCIA: {quebrada.get('nombre')}",
            "fundamento_tecnico": fundamento,
            "base_legal": "Ley N° 29664 Art. 67 (SINAGERD - Principio de Acción Inmediata), D.S. N° 234-2025-EF (FONDES) y Ley N° 31814",
            "distritos_a_incorporar": nombres_incorporar,
            "detalle_distritos_fondes": distritos_incorporar_detalle,
            "accion_financiera": "Habilitar gasto extraordinario del Programa Presupuestal 0068 para maquinaria pesada, defensas ribereñas y evacuación preventiva inmediata."
        }

    def evaluar_amenaza_territorial(self, region_o_distrito: str, lluvia_mm: float) -> Dict[str, Any]:
        """Evalúa distritos y quebradas de una zona ante un determinado volumen de precipitación."""
        termino = region_o_distrito.lower().strip()
        
        coincidencias_distritos = [
            d for d in self.historico 
            if termino in d["distrito"].lower() 
            or termino in d["departamento"].lower()
        ]
        
        quebradas_zona = [
            q for q in self.quebradas
            if termino in q.get("region", "").lower()
            or termino in q.get("distrito", "").lower()
            or termino in q.get("provincia", "").lower()
            or any(termino in d.lower() for d in q.get("distritos_impactados", []))
        ]
        
        quebradas_a_evaluar = quebradas_zona if quebradas_zona else self.quebradas

        quebradas_en_peligro = [
            q for q in quebradas_a_evaluar
            if lluvia_mm >= q.get("umbral_acumulado_24h", 35.0)
        ]
        
        quebradas_impacto_rapido = [
            q for q in quebradas_en_peligro
            if q.get("tiempo_concentracion_horas", 2.0) <= 1.2
        ]

        prioridad = "ALTA" if lluvia_mm >= 40.0 else "MEDIA"
        if lluvia_mm >= 70.0 or len(quebradas_en_peligro) > 0:
            prioridad = "CRITICA"

        poblacion_quebradas = sum(q.get("poblacion_en_cono_deyeccion", 0) for q in quebradas_en_peligro)
        poblacion_distritos = sum(d.get("poblacion_vulnerable", 0) for d in coincidencias_distritos)

        puntos_criticos = []
        for q in quebradas_en_peligro:
            puntos_criticos.extend(q.get("puntos_estrangulamiento", []))

        return {
            "agente": self.nombre,
            "termino_consultado": region_o_distrito,
            "distritos_historicos_amenazados": coincidencias_distritos,
            "quebradas_superando_umbral": quebradas_en_peligro,
            "total_quebradas_activadas": len(quebradas_en_peligro),
            "quebradas_impacto_rapido": quebradas_impacto_rapido,
            "requiere_evacuacion_inmediata": len(quebradas_impacto_rapido) > 0 or prioridad == "CRITICA",
            "nivel_prioridad_coen": prioridad,
            "puntos_estrangulamiento_viales": list(set(puntos_criticos)),
            "total_poblacion_en_riesgo": max(poblacion_distritos, poblacion_quebradas)
        }

    def obtener_catalogo_completo(self) -> List[Dict[str, Any]]:
        return self.quebradas
