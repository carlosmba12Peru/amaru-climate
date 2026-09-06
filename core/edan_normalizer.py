from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class PersonaAfectada(BaseModel):
    nombres: Optional[str] = "No identificado"
    edad_aproximada: Optional[int] = None
    es_nino_o_anciano: bool = False
    estado_salud: str = "Estable"  # Estable, Herido, Atrapado, Desaparecido

class EvaluacionDanosInfraestructura(BaseModel):
    viviendas_colapsadas: int = 0
    viviendas_inhabitables: int = 0
    viviendas_afectadas: int = 0
    vias_bloqueadas_metros: float = 0.0
    puentes_destruidos: int = 0
    centros_salud_danados: int = 0
    colegios_danados: int = 0

class FichaEDAN(BaseModel):
    """
    Ficha estandarizada según directivas de INDECI / SINPAD
    para Evaluación de Daños y Análisis de Necesidades.
    """
    id_ficha: str
    fecha_registro: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    departamento: str
    provincia: str
    distrito: str
    localidad_o_sector: str
    coordenadas_gps: Optional[dict] = Field(default_factory=lambda: {"lat": -12.0464, "lng": -77.0428})
    tipo_evento: str  # Huayco, Inundacion, Deslizamiento, Lluvia_Extrema
    nivel_severidad: str  # BAJA, MEDIA, ALTA, CRITICA
    origen_reporte: str   # CIUDADANO_WEB, VOZ_VAPI, OSINT_TIKTOK, SENAMHI_ALERTA
    personas_atrapadas: int = 0
    personas_heridas: int = 0
    fallecidos_reportados: int = 0
    danos_infraestructura: EvaluacionDanosInfraestructura = Field(default_factory=EvaluacionDanosInfraestructura)
    necesidades_urgentes: List[str] = Field(default_factory=list) # ej: "Rescate aero-helitransportado", "Maquinaria pesada", "Agua potable"
    entidades_notificadas: List[str] = Field(default_factory=list) # ej: ["COEN", "PNP_RESCATE", "EJERCITO"]
    estado_gestion: str = "REGISTRADO" # REGISTRADO, EN_ATENCION, DESPACHADO, CERRADO
