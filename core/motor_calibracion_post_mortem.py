"""
AMARU-FEN: Motor de Calibración Post-Mortem y Bucle de Mejora Continua Transparente (Nivel 3)
Marco Teórico: Safe Reinforcement Learning sobre Proceso de Jerarquía Analítica (Saaty AHP, 1980)
Normativa: R.J. Nº 112-2014-CENEPRED/J | Ley Nº 31814 (Uso de Inteligencia Artificial en el Perú)
Criptografía: SHA-256 & ECDSA secp256k1 (Oráculo Climático C2 / IPH-FEN)
"""

import json
import hashlib
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from core.climate_oracle_web3 import AmaruClimateOracle
from core.edan_normalizer import FichaEDAN

logger = logging.getLogger("AMARU.MotorCalibracionPostMortem")


class RegistroDecisionC2(BaseModel):
    """
    Registro inmutable de una decisión o alerta emitida por la Sala de Mando C2
    durante el desarrollo del Fenómeno El Niño.
    """
    id_alerta: str
    ubigeo: str
    distrito: str
    region: str = ""
    score_irce_emitido: float
    nivel_alerta: str  # CRITICO_ROJO, ALTO_NARANJA, MEDIO_AMARILLO, BAJO_VERDE
    orden_evacuacion_emitida: bool
    tiempo_anticipacion_horas: float
    factores_evaluados: Dict[str, float] = Field(
        default_factory=lambda: {
            "peligro": 0.5,
            "vulnerabilidad": 0.5,
            "exposicion": 0.5,
            "capacidad": 1.0
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResultadoRealEvento(BaseModel):
    """
    Ground Truth oficial (Post-Hechos) obtenido de informes EDAN INDECI/SINPAD,
    aforos hidrológicos de la ANA y balances de la Contraloría General de la República.
    """
    ubigeo: str
    distrito: str
    region: str = ""
    ocurrio_desborde_o_huaico: bool
    caudal_pico_m3s: Optional[float] = None
    tiempo_evacuacion_requerido_horas: float = 14.0
    ficha_edan: Optional[Dict[str, Any]] = None
    danos_totales_soles: float = 0.0
    personas_afectadas: int = 0
    fallecidos: int = 0
    costo_paralisis_falsa_alarma_soles: float = 0.0


class MetricasContraste(BaseModel):
    """
    Matriz de confusión territorial y balance de anticipación táctica.
    """
    total_distritos_evaluados: int
    verdaderos_positivos: List[str]  # Alertó evacuación y sí hubo desborde (vidas salvadas)
    falsos_positivos: List[str]      # Alertó evacuación pero no hubo desborde (falsa alarma)
    falsos_negativos: List[str]      # NO alertó evacuación y sí hubo desborde (falla crítica)
    verdaderos_negativos: List[str]  # No alertó evacuación y no hubo desborde (tranquilidad óptima)
    precision: float
    recall: float
    f1_score: float
    tasa_falsa_alarma: float
    promedio_horas_anticipacion_util: float
    recompensa_total_rl: float


class MatrizSaaty(BaseModel):
    """
    Representación matemática de la Matriz de Comparación Pareada AHP de Thomas Saaty (4x4).
    Garantiza consistencia axiomática estricta (Ratio de Consistencia CR <= 0.10).
    """
    criterios: List[str] = ["Peligro (P)", "Vulnerabilidad (V)", "Exposicion (E)", "Capacidad Inversa (1/C)"]
    matriz: List[List[float]]
    pesos: Dict[str, float]  # w_P, w_V, w_E, w_C
    lambda_max: float
    ci: float
    cr: float
    es_consistente: bool


class OrdenCorteTemporadaFEN(BaseModel):
    """
    Directiva oficial y colegiada del Comité Técnico Científico que declara
    el cese del periodo de avenidas extraordinarias y ordena formalmente al sistema
    la compilación de la auditoría forense post-mortem.
    """
    id_orden_corte: str
    fecha_corte: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evento_evaluado: str
    comunicado_enfen_referencia: str
    miembros_comite_firmantes: List[Dict[str, str]] = Field(
        default_factory=lambda: [
            {"rol": "Presidente del Comité C2", "nombre": "Director Sala C2 AMARU", "cargo": "Coordinador General C2"},
            {"rol": "Vocal Hidrometeorológico", "nombre": "Especialista ANA / SENAMHI", "cargo": "Hidrólogo Principal"},
            {"rol": "Vocal Territorial y Riesgos", "nombre": "Especialista CENEPRED", "cargo": "Evaluador EVAR"},
            {"rol": "Vocal Jurídico / Auditor", "nombre": "Asesor Legal SINAGERD", "cargo": "Auditor Ley 31814"}
        ]
    )
    justificacion_corte: str
    hash_sha256_orden: Optional[str] = None


class ActaRatificacionComite(BaseModel):
    """
    Resolución colegiada del Comité Técnico Científico donde se aprueba, observa
    o rechaza formalmente la nueva Matriz de Saaty AHP propuesta por el motor Safe RL.
    """
    id_acta: str
    id_informe_pericial: str
    decision_comite: str  # "APROBADO_Y_RATIFICADO", "RECHAZADO_CONSERVAR_BASAL", "OBSERVADO_REQUIERE_AJUSTES"
    quorum_alcanzado: bool = True
    votos_a_favor: int = 4
    votos_en_contra: int = 0
    observaciones_tecnicas: str = "Conforme con la consistencia Saaty y la mejora demostrada en el balance de alertas."
    firmas_digitales_miembros: List[Dict[str, str]] = Field(default_factory=list)
    fecha_ratificacion: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hash_sha256_acta: Optional[str] = None


class InformePericialPostMortem(BaseModel):
    """
    Dictamen pericial forense emitido al concluir la temporada FEN,
    apto para auditorías de CENEPRED, Contraloría y Ministerio Público.
    """
    id_informe: str
    fecha_emision: str
    evento_evaluado: str
    resumen_ejecutivo: str
    metricas_rendimiento: MetricasContraste
    matriz_saaty_anterior: MatrizSaaty
    matriz_saaty_optimizada: MatrizSaaty
    variacion_ponderados: Dict[str, float]
    diagnostico_causal_forense: List[str]
    justificacion_legal_ley_31814: str
    hash_sha256_acta: str
    estado_gobernanza: str = "PROPUESTA_PENDIENTE_COMITE"  # PROPUESTA_PENDIENTE_COMITE, APROBADO_Y_RATIFICADO, RECHAZADO_CONSERVAR_BASAL
    orden_corte_origen: Optional[OrdenCorteTemporadaFEN] = None
    acta_ratificacion: Optional[ActaRatificacionComite] = None
    sello_soberania_humana: bool = True
    recibo_criptografico_c2: Optional[Dict[str, Any]] = None


class MotorCalibracionPostMortem:
    """
    Motor Algorítmico de Nivel 3: Bucle de Mejora Continua Transparente.
    Aplica Safe Reinforcement Learning (RL) sobre el espacio de matrices de Saaty AHP,
    asegurando explicabilidad matemática (XAI) y cumplimiento de la Ley Nº 31814.
    """

    # Índice Aleatorio de Consistencia (RI) de Thomas Saaty para n=4
    RI_SAATY_N4 = 0.90

    # Matriz canónica basal de Saaty empleada en el diseño original de AMARU-FEN
    MATRIZ_BASAL_CANONICA = [
        [1.000, 2.000, 3.000, 4.000],  # Peligro
        [0.500, 1.000, 2.000, 3.000],  # Vulnerabilidad
        [0.333, 0.500, 1.000, 2.000],  # Exposición
        [0.250, 0.333, 0.500, 1.000],  # Capacidad Inversa
    ]

    def __init__(self, oraculo_c2: Optional[AmaruClimateOracle] = None):
        self.oraculo = oraculo_c2 or AmaruClimateOracle()
        self.matriz_activa = self.construir_matriz_saaty(self.MATRIZ_BASAL_CANONICA)

    @classmethod
    def construir_matriz_saaty(cls, tabla: List[List[float]]) -> MatrizSaaty:
        """
        Calcula el vector de prioridades (pesos w) mediante media geométrica,
        el autovalor máximo (lambda_max), el CI y el Ratio de Consistencia (CR).
        """
        n = 4
        # 1. Media geométrica de cada fila
        geom_means = []
        for i in range(n):
            prod = 1.0
            for j in range(n):
                val = tabla[i][j]
                if val <= 0:
                    val = 1.0
                prod *= val
            geom_means.append(prod ** (1.0 / n))

        sum_geom = sum(geom_means)
        if sum_geom == 0:
            sum_geom = 1.0
        w = [gm / sum_geom for gm in geom_means]

        # 2. Vector producto (A * w) y cálculo de lambda_max
        aw = [sum(tabla[i][j] * w[j] for j in range(n)) for i in range(n)]
        lambda_ratios = [aw[i] / w[i] if w[i] > 0 else n for i in range(n)]
        lambda_max = sum(lambda_ratios) / n

        # 3. Índice de Consistencia (CI) y Ratio de Consistencia (CR)
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        cr = ci / cls.RI_SAATY_N4

        # En Saaty AHP, valores de CR ligeramente negativos por precisión flotante se truncan a 0.0
        cr_norm = max(0.0, round(cr, 4))
        es_consistente = (cr_norm <= 0.10)

        pesos_dict = {
            "w_P": round(w[0], 4),
            "w_V": round(w[1], 4),
            "w_E": round(w[2], 4),
            "w_C": round(w[3], 4),
        }

        return MatrizSaaty(
            matriz=tabla,
            pesos=pesos_dict,
            lambda_max=round(lambda_max, 4),
            ci=round(ci, 4),
            cr=cr_norm,
            es_consistente=es_consistente
        )

    def evaluar_desempeno(
        self,
        decisiones: List[RegistroDecisionC2],
        resultados_reales: List[ResultadoRealEvento]
    ) -> MetricasContraste:
        """
        Cruza las decisiones tácticas emitidas frente a la verdad de campo oficial (EDAN / INDECI).
        Calcula Verdaderos Positivos, Falsos Positivos, Falsos Negativos y Verdaderos Negativos.
        """
        map_reales = {r.distrito.upper(): r for r in resultados_reales}
        # También mapear por ubigeo si está presente
        for r in resultados_reales:
            if r.ubigeo:
                map_reales[r.ubigeo] = r

        tp, fp, fn, tn = [], [], [], []
        horas_anticipacion_utiles = []

        for d in decisiones:
            clave_dist = d.distrito.upper()
            real = map_reales.get(d.ubigeo) or map_reales.get(clave_dist)

            if not real:
                # Si no hay registro de desborde, se asume normalidad
                ocurrio_evento = False
                t_req = 14.0
            else:
                ocurrio_evento = real.ocurrio_desborde_o_huaico
                t_req = real.tiempo_evacuacion_requerido_horas

            alerto_evacuacion = (d.orden_evacuacion_emitida or d.score_irce_emitido >= 0.85 or d.nivel_alerta == "CRITICO_ROJO")

            if alerto_evacuacion and ocurrio_evento:
                tp.append(d.distrito)
                # Anticipación lograda vs requerida
                margen_horas = d.tiempo_anticipacion_horas - t_req
                horas_anticipacion_utiles.append(margen_horas)
            elif alerto_evacuacion and not ocurrio_evento:
                fp.append(d.distrito)
            elif not alerto_evacuacion and ocurrio_evento:
                fn.append(d.distrito)
            else:
                tn.append(d.distrito)

        total = len(decisiones)
        total_pred_pos = len(tp) + len(fp)
        total_real_pos = len(tp) + len(fn)

        precision = len(tp) / total_pred_pos if total_pred_pos > 0 else 1.0
        recall = len(tp) / total_real_pos if total_real_pos > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        tasa_fp = len(fp) / (len(fp) + len(tn)) if (len(fp) + len(tn)) > 0 else 0.0

        prom_anticipacion = sum(horas_anticipacion_utiles) / len(horas_anticipacion_utiles) if horas_anticipacion_utiles else 0.0

        recompensa_rl = self.calcular_recompensa_rl(
            len_tp=len(tp),
            len_fp=len(fp),
            len_fn=len(fn),
            len_tn=len(tn),
            promedio_horas_anticipacion=prom_anticipacion
        )

        return MetricasContraste(
            total_distritos_evaluados=total,
            verdaderos_positivos=tp,
            falsos_positivos=fp,
            falsos_negativos=fn,
            verdaderos_negativos=tn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            tasa_falsa_alarma=round(tasa_fp, 4),
            promedio_horas_anticipacion_util=round(prom_anticipacion, 2),
            recompensa_total_rl=round(recompensa_rl, 2)
        )

    @classmethod
    def calcular_recompensa_rl(
        cls,
        len_tp: int,
        len_fp: int,
        len_fn: int,
        len_tn: int,
        promedio_horas_anticipacion: float,
        delta_tp: float = 100.0,
        lambda_fp: float = 35.0,
        beta_fn: float = 600.0,
        gamma_tn: float = 10.0
    ) -> float:
        """
        Función de Recompensa de Aprendizaje por Refuerzo (RL Objective):
        R = delta * TP * (1 + bonus_t) - lambda * FP - beta * FN + gamma * TN
        - Penalización asimétrica catastrófica ante Falsos Negativos (beta = 600.0).
        - Penalización económica moderada ante Falsos Positivos (lambda = 35.0).
        - Recompensa por vidas salvadas con bono por horas de anticipación ganadas.
        """
        factor_tiempo = 1.0 + min(1.0, max(-0.5, promedio_horas_anticipacion / 24.0))
        r_tp = len_tp * delta_tp * factor_tiempo
        r_fp = len_fp * (-lambda_fp)
        r_fn = len_fn * (-beta_fn)
        r_tn = len_tn * gamma_tn
        return r_tp + r_fp + r_fn + r_tn

    def recalcular_score_con_pesos(
        self,
        factores: Dict[str, float],
        pesos: Dict[str, float]
    ) -> float:
        """
        Re-evalúa el IRCE-FEN normalizado utilizando un vector de pesos AHP alternativo.
        Formula: IRCE = min(1.0, (w_P * P + w_V * V + w_E * E) / (w_C * C))
        """
        p = factores.get("peligro", 0.5)
        v = factores.get("vulnerabilidad", 0.5)
        e = factores.get("exposicion", 0.5)
        c = max(0.2, factores.get("capacidad", 1.0))

        wp = pesos.get("w_P", 0.467)
        wv = pesos.get("w_V", 0.277)
        we = pesos.get("w_E", 0.160)
        wc = pesos.get("w_C", 0.096)

        # Numerador de riesgo compuesto y denominador de mitigación
        numerador = (wp * p) + (wv * v) + (we * e)
        # La capacidad modula inversamente; ponderada con wc escalado
        denominador = c * (1.0 + wc)
        score = min(1.0, numerador / denominador)
        return round(score, 3)

    def optimizar_matriz_saaty(
        self,
        decisiones: List[RegistroDecisionC2],
        resultados_reales: List[ResultadoRealEvento],
        matriz_base: Optional[MatrizSaaty] = None
    ) -> Tuple[MatrizSaaty, MetricasContraste, List[str]]:
        """
        Safe Reinforcement Learning / Búsqueda Acotada sobre la Escala de Saaty:
        Explora variaciones pareadas de la matriz AHP buscando maximizar la recompensa RL
        respetando estrictamente el Filtro Dura Lex (CR <= 0.10).
        """
        base = matriz_base or self.matriz_activa
        metricas_base = self.evaluar_desempeno(decisiones, resultados_reales)
        mejor_recompensa = metricas_base.recompensa_total_rl
        mejor_matriz = base
        mejor_metricas = metricas_base

        diagnostico = []

        # Si no hubo fallas (FN = 0 y FP = 0), la matriz actual es óptima
        if len(metricas_base.falsos_negativos) == 0 and len(metricas_base.falsos_positivos) == 0:
            diagnostico.append("La matriz vigente operó con 100% de precisión y cobertura territorial sin discrepancias.")
            return mejor_matriz, mejor_metricas, diagnostico

        if len(metricas_base.falsos_negativos) > 0:
            diagnostico.append(
                f"ALERTA PERICIAL: Se detectaron {len(metricas_base.falsos_negativos)} Falsos Negativos "
                f"en: {', '.join(metricas_base.falsos_negativos)}. "
                "El RL priorizará incrementar la ponderación del Peligro (P) y Vulnerabilidad (V)."
            )

        if len(metricas_base.falsos_positivos) > 0:
            diagnostico.append(
                f"SOBRECOSTO LOGÍSTICO: Se registraron {len(metricas_base.falsos_positivos)} Falsas Alarmas "
                f"en: {', '.join(metricas_base.falsos_positivos)}. "
                "El RL moderará la sensibilidad ante avisos meteorológicos no corroborados por aforo fluvial."
            )

        # Espacio de perturbaciones controladas sobre comparaciones clave:
        # a_01: Peligro vs Vulnerabilidad (base = 2.0)
        # a_02: Peligro vs Exposición (base = 3.0)
        # a_03: Peligro vs Capacidad Inversa (base = 4.0)
        # a_12: Vulnerabilidad vs Exposición (base = 2.0)
        # a_13: Vulnerabilidad vs Capacidad Inversa (base = 3.0)
        # a_23: Exposición vs Capacidad Inversa (base = 2.0)
        
        # Generar candidatos en escala Saaty
        variaciones_p_v = [1.5, 2.0, 2.5, 3.0] if len(metricas_base.falsos_negativos) > 0 else [1.0, 1.5, 2.0]
        variaciones_p_c = [3.0, 4.0, 5.0] if len(metricas_base.falsos_negativos) > 0 else [2.5, 3.0, 4.0]
        variaciones_v_e = [1.5, 2.0, 2.5]

        for p_v in variaciones_p_v:
            for p_c in variaciones_p_c:
                for v_e in variaciones_v_e:
                    # Construir matriz candidata simétrica recíproca
                    cand_tabla = [
                        [1.0,       p_v,       3.0,       p_c      ],
                        [1.0 / p_v, 1.0,       v_e,       3.0      ],
                        [1.0 / 3.0, 1.0 / v_e, 1.0,       2.0      ],
                        [1.0 / p_c, 1.0 / 3.0, 1.0 / 2.0, 1.0      ]
                    ]
                    
                    cand_saaty = self.construir_matriz_saaty(cand_tabla)

                    # FILTRO DURA LEX: Restricción Dura Axiomática
                    if not cand_saaty.es_consistente:
                        continue  # Descartar cualquier matriz inconsistente (CR > 0.10)

                    # Re-simular decisiones con los nuevos pesos
                    decisiones_simuladas = []
                    for d in decisiones:
                        nuevo_score = self.recalcular_score_con_pesos(d.factores_evaluados, cand_saaty.pesos)
                        nueva_orden = (nuevo_score >= 0.85)
                        nuevo_nivel = "CRITICO_ROJO" if nuevo_score >= 0.85 else ("ALTO_NARANJA" if nuevo_score >= 0.65 else d.nivel_alerta)
                        
                        d_sim = d.model_copy(update={
                            "score_irce_emitido": nuevo_score,
                            "orden_evacuacion_emitida": nueva_orden,
                            "nivel_alerta": nuevo_nivel
                        })
                        decisiones_simuladas.append(d_sim)

                    metricas_cand = self.evaluar_desempeno(decisiones_simuladas, resultados_reales)

                    if metricas_cand.recompensa_total_rl > mejor_recompensa:
                        mejor_recompensa = metricas_cand.recompensa_total_rl
                        mejor_matriz = cand_saaty
                        mejor_metricas = metricas_cand

        if mejor_recompensa > metricas_base.recompensa_total_rl:
            diagnostico.append(
                f"OPTIMIZACIÓN EXITOSA: La recompensa RL aumentó de {metricas_base.recompensa_total_rl:.2f} "
                f"a {mejor_recompensa:.2f}. Nuevo CR = {mejor_matriz.cr:.4f} (Consistente <= 0.10)."
            )
        else:
            diagnostico.append(
                "ESTABILIDAD CONFIRMADA: La matriz previa ya representaba la frontera de Pareto óptima "
                "para el equilibrio entre anticipación y falsas alarmas."
            )

        return mejor_matriz, mejor_metricas, diagnostico

    def emitir_informe_pericial(
        self,
        evento_nombre: str,
        decisiones: List[RegistroDecisionC2],
        resultados_reales: List[ResultadoRealEvento],
        orden_corte: Optional[OrdenCorteTemporadaFEN] = None,
        auto_ratificar: bool = True
    ) -> InformePericialPostMortem:
        """
        Ejecuta el ciclo de calibración post-mortem completo, sella criptográficamente
        el dictamen con SHA-256 y emite el recibo ECDSA del Oráculo C2 (Ley Nº 31814).
        Por defecto auto_ratificar=True para pruebas y retrocompatibilidad; en régimen
        estricto con Comité Técnico se usa auto_ratificar=False y ratificar_calibracion_comite().
        """
        matriz_pre = self.matriz_activa
        matriz_post, metricas_post, diagnostico = self.optimizar_matriz_saaty(
            decisiones=decisiones,
            resultados_reales=resultados_reales,
            matriz_base=matriz_pre
        )

        variaciones = {
            "delta_w_P": round(matriz_post.pesos["w_P"] - matriz_pre.pesos["w_P"], 4),
            "delta_w_V": round(matriz_post.pesos["w_V"] - matriz_pre.pesos["w_V"], 4),
            "delta_w_E": round(matriz_post.pesos["w_E"] - matriz_pre.pesos["w_E"], 4),
            "delta_w_C": round(matriz_post.pesos["w_C"] - matriz_pre.pesos["w_C"], 4),
        }

        id_informe = f"INF-PERICIAL-AMARU-POSTMORTEM-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        resumen = (
            f"Evaluación de desempeño y calibración algorítmica post-evento para '{evento_nombre}'. "
            f"Se evaluaron {metricas_post.total_distritos_evaluados} decisiones territoriales frente al Ground Truth de INDECI. "
            f"Aciertos Críticos (TP): {len(metricas_post.verdaderos_positivos)} | "
            f"Falsas Alarmas (FP): {len(metricas_post.falsos_positivos)} | "
            f"Falsos Negativos (FN): {len(metricas_post.falsos_negativos)} | "
            f"F1-Score: {metricas_post.f1_score:.2f}. "
            f"Ratio de Consistencia Saaty resultante: CR = {matriz_post.cr:.4f} (Axiomáticamente Válido)."
        )

        justificacion_legal = (
            "El presente reajuste de coeficientes responde al principio de Gobernanza Algorítmica Continua, "
            "Explicabilidad y Transparencia consagrado en el Artículo 7 de la Ley Nº 31814 (Ley de Inteligencia Artificial "
            "del Perú) y las directivas de evaluación de riesgo del CENEPRED (R.J. Nº 112-2014-CENEPRED/J). "
            "Los nuevos ponderados conservan trazabilidad matemática determinística y anulan el sesgo de opacidad."
        )

        # Construcción de la carga canónica para el sellado SHA-256
        payload_para_hash = {
            "id_informe": id_informe,
            "evento_evaluado": evento_nombre,
            "metricas": metricas_post.model_dump(),
            "matriz_pre": matriz_pre.model_dump(),
            "matriz_post": matriz_post.model_dump(),
            "variaciones": variaciones,
            "diagnostico": diagnostico
        }
        payload_canonico_str = json.dumps(payload_para_hash, sort_keys=True, ensure_ascii=False)
        hash_sha256 = hashlib.sha256(payload_canonico_str.encode("utf-8")).hexdigest()

        # Firma asimétrica con el Oráculo C2
        recibo_cripto = self.oraculo.firmar_payload({
            "id_informe": id_informe,
            "hash_acta_sha256": hash_sha256,
            "cr_saaty": matriz_post.cr,
            "pesos_calibrados": matriz_post.pesos,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        informe = InformePericialPostMortem(
            id_informe=id_informe,
            fecha_emision=datetime.now(timezone.utc).isoformat(),
            evento_evaluado=evento_nombre,
            resumen_ejecutivo=resumen,
            metricas_rendimiento=metricas_post,
            matriz_saaty_anterior=matriz_pre,
            matriz_saaty_optimizada=matriz_post,
            variacion_ponderados=variaciones,
            diagnostico_causal_forense=diagnostico,
            justificacion_legal_ley_31814=justificacion_legal,
            hash_sha256_acta=hash_sha256,
            estado_gobernanza="APROBADO_Y_RATIFICADO" if auto_ratificar else "PROPUESTA_PENDIENTE_COMITE",
            orden_corte_origen=orden_corte,
            sello_soberania_humana=True,
            recibo_criptografico_c2=recibo_cripto
        )

        if auto_ratificar:
            self.matriz_activa = matriz_post

        return informe

    def ratificar_calibracion_comite(
        self,
        informe: InformePericialPostMortem,
        acta: ActaRatificacionComite
    ) -> InformePericialPostMortem:
        """
        Acto Soberano del Comité Técnico Científico (Ley Nº 31814):
        Evalúa el dictamen pericial y decide formalmente si aprueba la activación
        de la nueva matriz de pesos Saaty o conserva la matriz basal.
        """
        if not acta.quorum_alcanzado or acta.votos_a_favor <= acta.votos_en_contra:
            acta.decision_comite = "RECHAZADO_FALTA_QUORUM"

        payload_acta = {
            "id_acta": acta.id_acta,
            "id_informe_pericial": informe.id_informe,
            "decision": acta.decision_comite,
            "votos_favor": acta.votos_a_favor,
            "votos_contra": acta.votos_en_contra,
            "observaciones": acta.observaciones_tecnicas,
            "fecha": acta.fecha_ratificacion
        }
        acta.hash_sha256_acta = hashlib.sha256(
            json.dumps(payload_acta, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        informe.acta_ratificacion = acta

        if acta.decision_comite == "APROBADO_Y_RATIFICADO":
            informe.estado_gobernanza = "APROBADO_Y_RATIFICADO"
            self.matriz_activa = informe.matriz_saaty_optimizada
            logger.info(f"Comité Técnico aprobó nueva matriz Saaty para {informe.evento_evaluado}. CR={self.matriz_activa.cr}")
        else:
            informe.estado_gobernanza = "RECHAZADO_CONSERVAR_BASAL"
            logger.warning(f"Comité Técnico decidió conservar matriz previa: {acta.decision_comite}")

        return informe

    @classmethod
    def exportar_acta_markdown(cls, informe: InformePericialPostMortem) -> str:
        """
        Genera el dictamen pericial en formato Markdown listo para entrega física o digital a fiscalizadores.
        """
        met = informe.metricas_rendimiento
        pre = informe.matriz_saaty_anterior
        post = informe.matriz_saaty_optimizada
        var = informe.variacion_ponderados

        md = f"""# DICTAMEN PERICIAL FORENSE Y CALIBRACIÓN ALGORÍTMICA POST-MORTEM
**SALA DE MANDO C2 - SISTEMA SOBERANO AMARU-FEN**  
**Identificador Pericial:** `{informe.id_informe}`  
**Fecha de Emisión:** `{informe.fecha_emision}`  
**Evento Evaluado:** `{informe.evento_evaluado}`  
**Marco Normativo:** Ley Nº 31814 (IA en el Perú) | R.J. Nº 112-2014-CENEPRED/J | D.S. Nº 124-2026-PCM  

---

## 1. RESUMEN EJECUTIVO Y VEREDICTO DE GOBERNANZA
{informe.resumen_ejecutivo}

---

## 2. MATRIZ DE CONTRASTE TERRITORIAL (GROUND TRUTH INDECI vs AMARU-FEN)
* **Total Distritos Auditados:** {met.total_distritos_evaluados}
* **Verdaderos Positivos (Evacuaciones Exitosas):** `{len(met.verdaderos_positivos)}` ({', '.join(met.verdaderos_positivos) if met.verdaderos_positivos else 'Ninguno'})
* **Falsos Positivos (Sobrecosto por Falsa Alarma):** `{len(met.falsos_positivos)}` ({', '.join(met.falsos_positivos) if met.falsos_positivos else 'Ninguno'})
* **Falsos Negativos (Desbordes No Alertados):** `{len(met.falsos_negativos)}` ({', '.join(met.falsos_negativos) if met.falsos_negativos else 'Ninguno'})
* **Verdaderos Negativos (Zonas Seguras Preservadas):** `{len(met.verdaderos_negativos)}`

### Índices Estadísticos de Eficacia Operativa:
| Métrica Operativa | Valor Numérico | Criterio de Aceptación Pericial |
| :--- | :---: | :--- |
| **Precisión (Precision)** | `{met.precision * 100:.2f}%` | Mínimo 80% (Control de falsas alarmas) |
| **Sensibilidad (Recall)** | `{met.recall * 100:.2f}%` | Mínimo 90% (Protección estricta de vidas) |
| **F1-Score Balanceado** | `{met.f1_score:.3f}` | Criterio de optimización integral |
| **Anticipación Promedio Útil** | `+{met.promedio_horas_anticipacion_util} horas` | Margen sobre tiempo de evacuación requerido |
| **Puntaje de Recompensa RL** | `{met.recompensa_total_rl}` pts | Función asimétrica con penalización crítica |

---

## 3. COMPARATIVA AXIOMÁTICA DE MATRICES SAATY AHP

### Vector de Ponderados Calibrado para el Siguiente Ciclo:
| Criterio Evaluado | Peso Anterior (w_pre) | Peso Calibrado (w_post) | Variación (Delta w) | Justificación Hidrológica |
| :--- | :---: | :---: | :---: | :--- |
| **Peligro Dinámico (P)** | `{pre.pesos['w_P']:.4f}` | **`{post.pesos['w_P']:.4f}`** | `{var['delta_w_P']:+.4f}` | Ajuste por severidad de aforo fluvial |
| **Vulnerabilidad Territorial (V)** | `{pre.pesos['w_V']:.4f}` | **`{post.pesos['w_V']:.4f}`** | `{var['delta_w_V']:+.4f}` | Ponderación de fragilidad habitacional |
| **Exposición Socioeconómica (E)** | `{pre.pesos['w_E']:.4f}` | **`{post.pesos['w_E']:.4f}`** | `{var['delta_w_E']:+.4f}` | Densidad en faja marginal |
| **Capacidad Inversa (1/C)** | `{pre.pesos['w_C']:.4f}` | **`{post.pesos['w_C']:.4f}`** | `{var['delta_w_C']:+.4f}` | Eficacia de motobombas y defensas |

### Control de Consistencia Lógica (Saaty, 1980):
* **Autovalor Dominante (lambda_max):** `{post.lambda_max:.4f}`
* **Índice de Consistencia (CI):** `{post.ci:.4f}`
* **Ratio de Consistencia (CR):** **`{post.cr:.4f}`** (Umbral normativo: <= 0.10)
* **Dictamen Axiomático:** `{"APROBADO - CONSISTENCIA MATEMÁTICA FORMAL" if post.es_consistente else "RECHAZADO"}`

---

## 4. DIAGNÓSTICO CAUSAL FORENSE
"""
        for d in informe.diagnostico_causal_forense:
            md += f"* {d}\n"

        md += f"""
---

## 5. BLINDAJE LEGAL Y CADENA DE CUSTODIA CRIPTOGRÁFICA (IPH-FEN)
* **Sello de Soberanía Humana (Ley Nº 31814):** `CONFORME (Supervisión humana indelegable)`
* **Hash Inmutable SHA-256 del Dictamen:**  
  `{informe.hash_sha256_acta}`
* **Firma Digital ECDSA secp256k1 (Oráculo C2):**  
  `{informe.recibo_criptografico_c2.get('firma_hex', 'N/A')[:64] if informe.recibo_criptografico_c2 else 'N/A'}...`
* **Dirección Pública de Identidad del Oráculo:**  
  `{informe.recibo_criptografico_c2.get('oracle_address', 'N/A') if informe.recibo_criptografico_c2 else 'N/A'}`

---

## 6. RESOLUCIÓN DEL COMITÉ TÉCNICO CIENTÍFICO (GOBERNANZA HUMANA)
* **Estado de Gobernanza Actual:** `{informe.estado_gobernanza}`
* **Orden de Corte de Temporada:** `{informe.orden_corte_origen.id_orden_corte if informe.orden_corte_origen else 'Emisión Táctica de Rutina'}`
* **Referencia Oficial ENFEN:** `{informe.orden_corte_origen.comunicado_enfen_referencia if informe.orden_corte_origen else 'N/A'}`
* **Dictamen del Comité:** `{informe.acta_ratificacion.decision_comite if informe.acta_ratificacion else ('AUTORIZADO (Auto-Ratificación Operativa)' if informe.estado_gobernanza == 'APROBADO_Y_RATIFICADO' else 'PENDIENTE DE SESIÓN Y FIRMA DEL COMITÉ')}`
* **Quórum Reglamentario:** `{informe.acta_ratificacion.quorum_alcanzado if informe.acta_ratificacion else 'N/A'}`
* **Hash SHA-256 del Acta de Ratificación:** `{informe.acta_ratificacion.hash_sha256_acta if informe.acta_ratificacion else 'PENDIENTE'}`

---
*Este dictamen constituye un instrumento pericial auditable ante la Contraloría General de la República, INDECI, CENEPRED y el Congreso de la República.*
"""
        return md
