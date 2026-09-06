import uuid
from typing import Dict, Any
from core.edan_normalizer import FichaEDAN, EvaluacionDanosInfraestructura

class AgenteDespachoEDAN:
    """
    Consolida las evidencias recibidas (voz, OSINT, formulario web)
    en una Ficha EDAN oficial y despacha a las entidades de socorro.
    """
    def __init__(self):
        self.nombre = "Agente Despachador EDAN e Interinstitucional"

    def generar_y_despachar_ficha(
        self,
        departamento: str,
        provincia: str,
        distrito: str,
        localidad: str,
        tipo_evento: str,
        severidad: str,
        origen: str,
        atrapados: int = 0,
        heridos: int = 0,
        necesidades: list = None
    ) -> FichaEDAN:
        necesidades = necesidades or ["Evacuación táctica", "Suministro de agua"]
        
        entidades = ["COEN-INDECI", "MUNICIPALIDAD_LOCAL"]
        if atrapados > 0 or heridos > 0:
            entidades.extend(["PNP_RESCATE", "BOMBEROS_PERU"])
        if severidad == "CRITICA":
            entidades.append("EJERCITO_DEL_PERU")

        ficha = FichaEDAN(
            id_ficha=f"EDAN-FEN-{uuid.uuid4().hex[:8].upper()}",
            departamento=departamento,
            provincia=provincia,
            distrito=distrito,
            localidad_o_sector=localidad,
            tipo_evento=tipo_evento,
            nivel_severidad=severidad,
            origen_reporte=origen,
            personas_atrapadas=atrapados,
            personas_heridas=heridos,
            necesidades_urgentes=necesidades,
            entidades_notificadas=entidades,
            estado_gestion="DESPACHADO"
        )
        return ficha
