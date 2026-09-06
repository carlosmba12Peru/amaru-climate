from typing import Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PreposicionamientoLogistico(BaseModel):
    region: str
    almacenes_itinerantes: int
    motobombas_desplegadas: int
    calaminas_unidades: int
    vacunas_dengue_leptospirosis: int
    sueros_antiofidicos: int
    plantas_potabilizadoras_moviles: int
    costo_estimado_pen: float
    estado: str  # PRE_APROBADO, EN_TRANSITO, EN_POSICION

class EvaluacionGobernanzaAnticipatoria(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    anomalia_tsm_nino12: float
    nivel_advertencia: str  # NORMAL, VIGILANCIA, ADVERTENCIA_TEMPRANA, EMERGENCIA_ANTICIPADA
    trigger_presupuestal_activo: bool
    fase_accion_anticipada: str
    preposicionamiento_norte: List[PreposicionamientoLogistico]
    alerta_dual_sur_sequias: Dict[str, Any]
    recomendaciones_politica_publica: List[str]

class MotorGobernanzaAnticipatoria:
    """
    Implementa el Marco de Gobernanza Anticipatoria (CAF / PUCP 2026)
    cruzando anomalías térmicas del Pacífico Oriental (NOAA / ENFEN / IGP)
    con vulnerabilidad socioeconómica del INEI y directivas de CEPLAN.
    """
    def __init__(self):
        self.nombre = "Motor de Gobernanza Anticipatoria y Triggers FEN"

    def evaluar_triggers_climaticos(self, anomalia_tsm_nino12: float, mes_actual: int = 8) -> EvaluacionGobernanzaAnticipatoria:
        """
        Evalúa si la anomalía de Temperatura Superficial del Mar (TSM)
        en la zona Niño 1+2 activa disparadores automáticos de gasto y logística
        meses antes del inicio del periodo pluvial (Diciembre-Marzo).
        """
        # 1. Definición de Nivel y Triggers
        if anomalia_tsm_nino12 >= 2.0:
            nivel = "EMERGENCIA_ANTICIPADA"
            trigger_gasto = True
            fase = "Despliegue Inmediato de Almacenes Itinerantes y Pre-Evacuación de Quebradas Críticas"
        elif anomalia_tsm_nino12 >= 1.5:
            nivel = "ADVERTENCIA_TEMPRANA"
            trigger_gasto = True
            fase = "Pre-aprobación de Fondos de Contingencia y Traslado Preventivo de Bienes de Ayuda Humanitaria (BAH)"
        elif anomalia_tsm_nino12 >= 0.8:
            nivel = "VIGILANCIA"
            trigger_gasto = False
            fase = "Escaneo Continuo de Horizontes y Mantenimiento de Descolmatación de Cuencas"
        else:
            nivel = "NORMAL"
            trigger_gasto = False
            fase = "Monitoreo Basal de Rutina"

        # 2. Escenario Logístico Preventivo Norte (Piura, Lambayeque, Tumbes, La Libertad)
        factor = 1.0 if anomalia_tsm_nino12 < 1.5 else (1.5 if anomalia_tsm_nino12 < 2.0 else 2.5)
        
        preposicionamiento = [
            PreposicionamientoLogistico(
                region="Piura",
                almacenes_itinerantes=int(4 * factor),
                motobombas_desplegadas=int(25 * factor),
                calaminas_unidades=int(15000 * factor),
                vacunas_dengue_leptospirosis=int(8000 * factor),
                sueros_antiofidicos=int(200 * factor),
                plantas_potabilizadoras_moviles=int(3 * factor),
                costo_estimado_pen=1200000.0 * factor,
                estado="EN_POSICION" if trigger_gasto else "PRE_APROBADO"
            ),
            PreposicionamientoLogistico(
                region="Lambayeque",
                almacenes_itinerantes=int(3 * factor),
                motobombas_desplegadas=int(18 * factor),
                calaminas_unidades=int(10000 * factor),
                vacunas_dengue_leptospirosis=int(5000 * factor),
                sueros_antiofidicos=int(120 * factor),
                plantas_potabilizadoras_moviles=int(2 * factor),
                costo_estimado_pen=850000.0 * factor,
                estado="EN_POSICION" if trigger_gasto else "PRE_APROBADO"
            ),
            PreposicionamientoLogistico(
                region="Tumbes",
                almacenes_itinerantes=int(2 * factor),
                motobombas_desplegadas=int(12 * factor),
                calaminas_unidades=int(6000 * factor),
                vacunas_dengue_leptospirosis=int(3000 * factor),
                sueros_antiofidicos=int(80 * factor),
                plantas_potabilizadoras_moviles=int(1 * factor),
                costo_estimado_pen=520000.0 * factor,
                estado="EN_POSICION" if trigger_gasto else "PRE_APROBADO"
            ),
            PreposicionamientoLogistico(
                region="La Libertad",
                almacenes_itinerantes=int(3 * factor),
                motobombas_desplegadas=int(15 * factor),
                calaminas_unidades=int(12000 * factor),
                vacunas_dengue_leptospirosis=int(6000 * factor),
                sueros_antiofidicos=int(90 * factor),
                plantas_potabilizadoras_moviles=int(2 * factor),
                costo_estimado_pen=920000.0 * factor,
                estado="EN_POSICION" if trigger_gasto else "PRE_APROBADO"
            )
        ]

        # 3. Alerta Dual: Impacto en el Sur Andino (Sequías según lecciones CEPAL e IGP)
        alerta_sur = {
            "fenomeno_asociado": "Déficit hídrico severo y heladas anómalas en el Altiplano",
            "regiones_afectadas": ["Puno", "Cusco", "Huancavelica", "Arequipa (Alturas)"],
            "riesgo_agropecuario": "Pérdida de cultivos de papa/quinua y mortandad de camélidos sudamericanos",
            "trigger_activo": anomalia_tsm_nino12 >= 1.2,
            "acciones_preventivas": [
                "Entrega de pacas de heno y kits veterinarios antes de Octubre",
                "Construcción y rehabilitación de qochas y reservorios familiares de agua",
                "Monitoreo comunitario mediante agentes de voz IVR en Quechua y Aimara"
            ]
        }

        # 4. Recomendaciones de Política Pública (Gobernanza Anticipatoria)
        recomendaciones = [
            "Interoperar en tiempo real los datos térmicos de NOAA/ENFEN con el Sistema Integrado de Administración Financiera (SIAF-MEF).",
            "Sustituir la Declaratoria de Estado de Emergencia post-desastre por una 'Declaratoria de Acción Temprana Presupuestal'.",
            "Desplegar centros de distribución logística en zonas altas no inundables de Piura y Lambayeque entre julio y octubre."
        ]

        return EvaluacionGobernanzaAnticipatoria(
            anomalia_tsm_nino12=anomalia_tsm_nino12,
            nivel_advertencia=nivel,
            trigger_presupuestal_activo=trigger_gasto,
            fase_accion_anticipada=fase,
            preposicionamiento_norte=preposicionamiento,
            alerta_dual_sur_sequias=alerta_sur,
            recomendaciones_politica_publica=recomendaciones
        )
