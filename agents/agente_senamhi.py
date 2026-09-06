import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AMARU.AgenteSenamhi")

class AgenteSenamhi:
    """
    Monitorea avisos hidrometeorológicos y evalúa umbrales pluviométricos (SENAMHI / ENFEN).
    Soporta sincronización automatizada desde el portal web oficial del SENAMHI.
    """
    def __init__(self):
        self.nombre = "Agente Centinela SENAMHI"
        self.ultimos_avisos: List[Dict[str, Any]] = []
        self.nivel_alerta_actual = "AMARILLO"

    def sincronizar_avisos_en_vivo(self, ingestor: Optional[Any] = None) -> Dict[str, Any]:
        """
        Consulta en tiempo real la página de avisos meteorológicos de SENAMHI
        y actualiza el estado de alerta del agente.
        """
        if ingestor is None:
            try:
                from core.ingestor_oficial import IngestorOficialSenamhiEnfen
                ingestor = IngestorOficialSenamhiEnfen()
            except ImportError:
                logger.error("No se pudo importar IngestorOficialSenamhiEnfen")
                return {"estado": "ERROR", "mensaje": "Ingestor no disponible"}

        self.ultimos_avisos = ingestor.obtener_avisos_meteorologicos()
        
        # Calcular severidad máxima
        niveles = [a.get("nivel_alerta", "AMARILLO") for a in self.ultimos_avisos]
        if "ROJO" in niveles:
            self.nivel_alerta_actual = "ROJO"
        elif "NARANJA" in niveles:
            self.nivel_alerta_actual = "NARANJA"
        else:
            self.nivel_alerta_actual = "AMARILLO"

        return {
            "agente": self.nombre,
            "estado": "SINCRONIZADO",
            "total_avisos_vigentes": len(self.ultimos_avisos),
            "nivel_alerta_dominante": self.nivel_alerta_actual,
            "avisos": self.ultimos_avisos
        }

    def procesar_aviso_meteorologico(self, aviso: Dict[str, Any]) -> Dict[str, Any]:
        region = aviso.get("region", "Costa Norte")
        nivel_alerta = aviso.get("nivel_alerta", self.nivel_alerta_actual).upper() # AMARILLO, NARANJA, ROJO
        lluvia_estimada_mm = aviso.get("lluvia_estimada_mm", 25.0)
        
        riesgo_activacion = "BAJO"
        if nivel_alerta == "ROJO" or lluvia_estimada_mm >= 70.0:
            riesgo_activacion = "INMINENTE_EXTREMO"
        elif nivel_alerta == "NARANJA" or lluvia_estimada_mm >= 40.0:
            riesgo_activacion = "ALTO"
        elif lluvia_estimada_mm >= 20.0:
            riesgo_activacion = "MODERADO"

        evaluacion = {
            "agente": self.nombre,
            "region": region,
            "nivel_alerta_senamhi": nivel_alerta,
            "lluvia_estimada_mm": lluvia_estimada_mm,
            "riesgo_activacion": riesgo_activacion,
            "requiere_alerta_sismate": riesgo_activacion in ["ALTO", "INMINENTE_EXTREMO"],
            "recomendacion_operativa": (
                "Activar evacuación preventiva y desplegar maquinaria pesada en puntos de estrangulamiento de cauce."
                if riesgo_activacion == "INMINENTE_EXTREMO"
                else "Monitoreo continuo de caudales y aviso a brigadistas locales."
            )
        }
        return evaluacion

    def consultar_satelite_goes19(self) -> Dict[str, Any]:
        """
        Retorna la telemetría y especificaciones de nowcasting del satélite meteorológico
        geoestacionario GOES-19 (GOES-East a 75.2°W) transmitido en el portal oficial de SENAMHI.
        """
        return {
            "agente": self.nombre,
            "satelite": "GOES-19 (GOES-East / NOAA-NASA)",
            "posicion_orbital": "75.2° W (cobertura total de Sudamérica, Perú y Pacífico Oriental)",
            "portal_senamhi_url": "https://www.senamhi.gob.pe/?p=satelites-goes19",
            "frecuencia_actualizacion": "Cada 10-15 minutos (Full Disk) / 1 minuto (Mesoscale)",
            "instrumentos_clave": {
                "ABI_Advanced_Baseline_Imager": {
                    "Canal_13_Infrarrojo_Limpio_10_3um": "Mide temperatura de brillo de topes de nubes. Topes < -65°C indican nubes Cumulonimbus (Cb) de desarrollo vertical violento.",
                    "Canal_14_Infrarrojo_11_2um": "Detección de tormentas severas y núcleos de precipitación convectiva en cuencas altas.",
                    "Canales_8_9_10_Vapor_Agua": "Mide transporte de humedad troposférica desde la Amazonía hacia la vertiente occidental andina."
                },
                "GLM_Geostationary_Lightning_Mapper": {
                    "funcion": "Detección en tiempo real de actividad eléctrica total (rayos nube-nube y nube-tierra).",
                    "utilidad_nowcasting": "Los saltos abruptos de descargas ('lightning jumps') preceden en 15-30 minutos la activación violenta de quebradas y huaicos."
                }
            },
            "utilidad_operativa_amaru": "Nowcasting de ultra-corta latencia: permite emitir alertas de evacuación SISMATE antes de que los pluviómetros de tierra registren las lluvias torrenciales."
        }

    def consultar_portal_fen_oficial(self, ingestor: Optional[Any] = None) -> Dict[str, Any]:
        """
        Retorna la información consolidada del Portal Oficial del Fenómeno El Niño de SENAMHI.
        URL: https://www.senamhi.gob.pe/?p=fenomeno-el-nino
        """
        if ingestor is None:
            from core.ingestor_oficial import IngestorOficialSenamhiEnfen
            ingestor = IngestorOficialSenamhiEnfen()
        return ingestor.obtener_portal_fen_senamhi()



