"""
AGENTE CRIOCLIMÁTICO DE LA NIÑA (AMARU-CHIRI)
==============================================
Sistema AMARU - Sala de Mando C2 & Gestión del Riesgo por Bajas Temperaturas

Doctrina y Responsabilidad Operativa:
- Monitorea los distritos críticos altoandinos (Puno, Huancavelica, Arequipa)
  definidos en 'data/catalogo_distritos_heladas_nina.json'.
- Computa el índice 'ISH-CHIRI' (Índice de Severidad de Helada / IPHe-CHIRI),
  diferenciado estrictamente del IPH-FEN (Índice de Previsión de Huaicos).
- Evalúa el estrés térmico acumulativo por persistencia de noches bajo cero,
  viento catabático y vulnerabilidad pecuaria (alpacas y camélidos sudamericanos).
- Genera recomendaciones tácticas C2 de protección comunitaria y veterinaria.
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import json
import os
import math

from core.reloj_nina import MotorRelojNina, ModeloRelojNina

class EvaluacionDistritoChiri(BaseModel):
    ubigeo: str
    departamento: str
    provincia: str
    distrito: str
    nombre_comun: str
    altitud_msnm: int
    tmin_observada_c: float
    viento_kmh: float
    dias_consecutivos_bajo_cero: int
    ish_chiri: float = Field(..., description="Índice de Severidad de Helada (0.0% a 100.0%)")
    nivel_alerta: str = Field(..., description="ALERTA_ROJA_GLACIAL, ALERTA_NARANJA_SEVERA, ALERTA_AMARILLA_PREVENTIVA, CONDICION_VERDE_NORMAL")
    accion_tactica_c2: str
    poblacion_vulnerable: int
    censo_alpacas: int
    estacion_senamhi: str
    codigo_tactico_c2: str
    # Nuevos campos de infraestructura educativa y seguridad vial (PRONIED / PREVAED)
    colegios_vulnerables: int = Field(default=0, description="Instituciones educativas sin aislamiento térmico")
    escolares_en_riesgo: int = Field(default=0, description="Alumnos de inicial y primaria en riesgo de IRA")
    modulos_pronied_requeridos: int = Field(default=0, description="Módulos térmicos prefabricados PRONIED urgentes")
    directiva_educativa_prevaed: str = Field(default="", description="Directiva C2 escolar (Horario de invierno / Suspensión)")
    corredor_vial: str = Field(default="", description="Vía de transporte principal del distrito")
    alerta_vial_escarcha: str = Field(default="", description="Alerta de hielo en asfalto / escarcha")

    @property
    def sensacion_termica_viento_c(self) -> float:
        """Sensación térmica por viento (Wind Chill JAG/TI)"""
        if self.viento_kmh > 4.8:
            v16 = self.viento_kmh ** 0.16
            return round(13.12 + 0.6215 * self.tmin_observada_c - 11.37 * v16 + 0.3965 * self.tmin_observada_c * v16, 1)
        return round(self.tmin_observada_c, 1)

    @property
    def alpacas_expuestas(self) -> int:
        """Alias de compatibilidad para censo de camélidos en riesgo"""
        return self.censo_alpacas

class ResumenEvaluacionChiri(BaseModel):
    timestamp_evaluacion: str
    total_distritos_evaluados: int
    distritos_alerta_roja: int
    distritos_alerta_naranja: int
    distritos_alerta_amarilla: int
    distritos_condicion_verde: int
    alpacas_en_riesgo_critico: int
    personas_vulnerables_en_riesgo_critico: int
    distrito_maxima_severidad: str
    ish_chiri_maximo: float
    # Resumen escolar y vial
    total_colegios_en_riesgo: int = 0
    total_escolares_en_riesgo: int = 0
    colegios_con_suspension_sugerida: int = 0
    vias_con_alerta_hielo: int = 0
    evaluaciones: List[EvaluacionDistritoChiri]
    estado_reloj_macro: Dict[str, Any]

class AgenteCrioclimaticoNina:
    """
    Agente especializado en análisis de heladas, crioclima y protección pecuaria/social ante La Niña.
    """

    def __init__(self, ruta_catalogo: str = "data/catalogo_distritos_heladas_nina.json"):
        self.ruta_catalogo = ruta_catalogo
        self.distritos_catalogo: List[Dict[str, Any]] = []
        self.motor_reloj = MotorRelojNina()
        self._cargar_catalogo()

    def _cargar_catalogo(self):
        if not os.path.exists(self.ruta_catalogo):
            raise FileNotFoundError(f"Catálogo no encontrado en {self.ruta_catalogo}")
        with open(self.ruta_catalogo, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.distritos_catalogo = data.get("distritos", [])

    def calcular_ish_chiri(
        self,
        tmin: float,
        umbral_severo: float,
        umbral_extremo: float,
        viento_kmh: float,
        dias_bajo_cero: int,
        es_prioridad_1: bool
    ) -> float:
        """
        Calcula el Índice de Severidad de Helada (ISH-CHIRI):
        ISH = Sigmoide( 0.35 * C_term + 0.25 * C_persist + 0.20 * C_viento + 0.20 * C_vuln )
        """
        # 1. Componente Térmico Instantáneo (C_term)
        if tmin >= 0.0:
            c_term = 0.0
        else:
            # Grado de penetración bajo cero hacia el récord o umbral extremo
            rango_frio = abs(umbral_extremo) if abs(umbral_extremo) > 0 else 15.0
            c_term = min(1.0, abs(tmin) / rango_frio)

        # 2. Componente de Persistencia Acumulada (C_persist)
        # 7 días consecutivos bajo cero representan estrés biológico máximo
        c_persist = min(1.0, max(0.0, dias_bajo_cero / 7.0))

        # 3. Componente de Viento Catabático / Sensación Térmica (C_viento)
        # Vientos > 35 km/h en el Altiplano generan hipotermia severa
        c_viento = min(1.0, max(0.0, viento_kmh / 35.0))

        # 4. Componente de Vulnerabilidad del Distrito (C_vuln)
        c_vuln = 0.85 if es_prioridad_1 else 0.65

        # Fuerza motriz del frío
        phi_chiri = (0.35 * c_term) + (0.25 * c_persist) + (0.20 * c_viento) + (0.20 * c_vuln)

        # Transformación sigmoidal logística normalizada (0% a 100%)
        prob = 1.0 / (1.0 + math.exp(-5.5 * (phi_chiri - 0.52)))
        ish = round(prob * 100.0, 1)

        # Reglas Duras Institucionales C2:
        # Si Tmin alcanza el umbral extremo histórico -> Alerta Roja Inmediata (>= 88%)
        if tmin <= umbral_extremo:
            ish = max(ish, 88.0)
        # Si Tmin supera la helada severa por 4 o más días continuos -> Alerta Roja por persistencia (>= 82%)
        elif tmin <= umbral_severo and dias_bajo_cero >= 4:
            ish = max(ish, 82.0)
        elif tmin <= umbral_severo and dias_bajo_cero >= 2:
            ish = max(ish, 72.0)

        return min(100.0, max(0.0, ish))

    def clasificar_alerta(self, ish: float) -> Tuple[str, str]:
        """
        Clasifica el nivel de alerta táctica y directiva C2 basada en el ISH-CHIRI.
        """
        if ish >= 80.0:
            return (
                "ALERTA_ROJA_GLACIAL",
                "¡EMERGENCIA CRIOCLIMÁTICA! Disponer confinamiento de alpacas en cobertizos, "
                "distribución de pacas de heno y antibióticos veterinarios. Alerta máxima en postas médicas."
            )
        elif ish >= 55.0:
            return (
                "ALERTA_NARANJA_SEVERA",
                "Alerta Severa. Proteger crías de camélidos y pastos en bofedales. "
                "Cierre preventivo nocturno de carreteras altoandinas por escarcha o hielo en asfalto."
            )
        elif ish >= 35.0:
            return (
                "ALERTA_AMARILLA_PREVENTIVA",
                "Condición de helada moderada estacional. Mantener vigilancia de temperaturas nocturnas."
            )
        else:
            return (
                "CONDICION_VERDE_NORMAL",
                "Régimen térmico basal sin amenaza inminente para la ganadería ni la población."
            )

    def evaluar_distrito(
        self,
        ubigeo: str,
        tmin_observada: float,
        viento_kmh: float = 18.0,
        dias_bajo_cero: int = 2
    ) -> EvaluacionDistritoChiri:
        """
        Evalúa un distrito específico por código UBIGEO.
        """
        dist_meta = next((d for d in self.distritos_catalogo if d["ubigeo"] == ubigeo), None)
        if not dist_meta:
            raise ValueError(f"UBIGEO {ubigeo} no encontrado en el catálogo de heladas.")

        es_p1 = "Prioridad 1" in dist_meta.get("prioridad_pmhf", "")
        ish = self.calcular_ish_chiri(
            tmin=tmin_observada,
            umbral_severo=dist_meta["umbral_helada_severa_c"],
            umbral_extremo=dist_meta["umbral_helada_extrema_c"],
            viento_kmh=viento_kmh,
            dias_bajo_cero=dias_bajo_cero,
            es_prioridad_1=es_p1
        )

        nivel_alerta, accion = self.clasificar_alerta(ish)

        # Directivas educativas PREVAED (Programa Presupuestal 0068 / MINEDU)
        if ish >= 80.0 or tmin_observada <= -12.0:
            directiva_ed = "¡SUSPENSIÓN DE LABORES ESCOLARES PRESENCIALES! (PREVAED PP-0068 / UGEL). Pase a clases remotas/radiales por frío extremo."
        elif ish >= 55.0 or tmin_observada <= -5.0:
            directiva_ed = "HORARIO DE INVIERNO OBLIGATORIO: Retrasar ingreso escolar 45 a 60 min para evitar la ventana de congelamiento matutino (PREVAED)."
        else:
            directiva_ed = "Jornada escolar estándar con vigilancia térmica en aulas."

        # Alerta de seguridad vial por escarcha / hielo en calzada
        corredor = dist_meta.get("corredor_vial_riesgo_escarcha", "Vía de transporte distrital")
        if tmin_observada <= -4.0:
            alerta_vial = f"PELIGRO DE CONGELAMIENTO: Formación de escarcha y placas de hielo en {corredor}. Reducir velocidad y restringir tránsito matinal."
        else:
            alerta_vial = f"Condiciones de tránsito normales con precaución en {corredor}."

        codigo_c2 = dist_meta.get("codigo_tactico_c2", f"AMARU-CHIRI-{ubigeo}")

        return EvaluacionDistritoChiri(
            ubigeo=dist_meta["ubigeo"],
            departamento=dist_meta["departamento"],
            provincia=dist_meta["provincia"],
            distrito=dist_meta["distrito"],
            nombre_comun=dist_meta["nombre_comun"],
            altitud_msnm=dist_meta["altitud_msnm"],
            tmin_observada_c=tmin_observada,
            viento_kmh=viento_kmh,
            dias_consecutivos_bajo_cero=dias_bajo_cero,
            ish_chiri=ish,
            nivel_alerta=nivel_alerta,
            accion_tactica_c2=accion,
            poblacion_vulnerable=dist_meta["poblacion_vulnerable_ninos_ancianos"],
            censo_alpacas=dist_meta["censo_camelidos_alpacas"],
            estacion_senamhi=dist_meta["estacion_senamhi_referencia"],
            codigo_tactico_c2=codigo_c2,
            colegios_vulnerables=dist_meta.get("colegios_vulnerables_sin_aislamiento", 10),
            escolares_en_riesgo=dist_meta.get("escolares_en_riesgo", 800),
            modulos_pronied_requeridos=dist_meta.get("modulos_termicos_pronied_requeridos", 8),
            directiva_educativa_prevaed=directiva_ed,
            corredor_vial=corredor,
            alerta_vial_escarcha=alerta_vial
        )

    def ejecutar_barrido_territorial(
        self,
        escenario_tmin_delta: float = 0.0,
        anomalia_tsm_pacifico: float = -1.4,
        alisios_velocidad: float = 7.8
    ) -> ResumenEvaluacionChiri:
        """
        Ejecuta un barrido completo sobre los distritos monitoreados por AMARU-CHIRI.
        Simula o ingesta la telemetría ajustada por el escenario crioclimático.
        """
        evaluaciones = []
        alpacas_rojas = 0
        vulnerables_rojos = 0

        # Para cada distrito, simulamos su Tmin coherente con su altitud y el escenario
        for d in self.distritos_catalogo:
            # Línea base basada en su umbral severo ajustada por la anomalía
            tmin_simulada = d["umbral_helada_severa_c"] + escenario_tmin_delta
            viento_simulado = 22.0 if "Muy Fuerte" in d.get("zona_viento_catabatico", "") else 16.0
            dias_simulados = 4 if tmin_simulada <= -8.0 else 2

            eval_d = self.evaluar_distrito(
                ubigeo=d["ubigeo"],
                tmin_observada=round(tmin_simulada, 1),
                viento_kmh=viento_simulado,
                dias_bajo_cero=dias_simulados
            )
            evaluaciones.append(eval_d)

            if eval_d.nivel_alerta == "ALERTA_ROJA_GLACIAL":
                alpacas_rojas += eval_d.censo_alpacas
                vulnerables_rojos += eval_d.poblacion_vulnerable

        # Ordenar distritos de mayor a menor severidad
        evaluaciones.sort(key=lambda x: x.ish_chiri, reverse=True)

        # Calcular estado macro del Reloj de La Niña
        tmin_promedio = sum(e.tmin_observada_c for e in evaluaciones) / len(evaluaciones)
        reloj_macro = self.motor_reloj.calcular_reloj(
            anomalia_tsm=anomalia_tsm_pacifico,
            velocidad_alisios=alisios_velocidad,
            tmin_promedio=tmin_promedio
        )

        rojas = sum(1 for e in evaluaciones if e.nivel_alerta == "ALERTA_ROJA_GLACIAL")
        naranjas = sum(1 for e in evaluaciones if e.nivel_alerta == "ALERTA_NARANJA_SEVERA")
        amarillas = sum(1 for e in evaluaciones if e.nivel_alerta == "ALERTA_AMARILLA_PREVENTIVA")
        verdes = sum(1 for e in evaluaciones if e.nivel_alerta == "CONDICION_VERDE_NORMAL")

        # Totales escolares y de seguridad vial
        colegios_riesgo = sum(e.colegios_vulnerables for e in evaluaciones if e.nivel_alerta in ["ALERTA_ROJA_GLACIAL", "ALERTA_NARANJA_SEVERA"])
        escolares_riesgo = sum(e.escolares_en_riesgo for e in evaluaciones if e.nivel_alerta in ["ALERTA_ROJA_GLACIAL", "ALERTA_NARANJA_SEVERA"])
        colegios_suspension = sum(e.colegios_vulnerables for e in evaluaciones if "SUSPENSIÓN" in e.directiva_educativa_prevaed)
        vias_hielo = sum(1 for e in evaluaciones if "PELIGRO DE CONGELAMIENTO" in e.alerta_vial_escarcha)

        return ResumenEvaluacionChiri(
            timestamp_evaluacion=datetime.now().isoformat(),
            total_distritos_evaluados=len(evaluaciones),
            distritos_alerta_roja=rojas,
            distritos_alerta_naranja=naranjas,
            distritos_alerta_amarilla=amarillas,
            distritos_condicion_verde=verdes,
            alpacas_en_riesgo_critico=alpacas_rojas,
            personas_vulnerables_en_riesgo_critico=vulnerables_rojos,
            distrito_maxima_severidad=evaluaciones[0].nombre_comun if evaluaciones else "N/A",
            ish_chiri_maximo=evaluaciones[0].ish_chiri if evaluaciones else 0.0,
            total_colegios_en_riesgo=colegios_riesgo,
            total_escolares_en_riesgo=escolares_riesgo,
            colegios_con_suspension_sugerida=colegios_suspension,
            vias_con_alerta_hielo=vias_hielo,
            evaluaciones=evaluaciones,
            estado_reloj_macro=reloj_macro.model_dump()
        )
