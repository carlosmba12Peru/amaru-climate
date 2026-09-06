from typing import Dict, Any

class AgenteVozVapi:
    """
    Maneja la lógica de contención telefónica mediante Vapi AI.
    Contiene emocionalmente a la persona que llama y estructura los datos para la ficha EDAN.
    """
    def __init__(self):
        self.nombre = "Agente de Voz y Contención Vapi"

    def procesar_transcripcion_llamada(self, transcripcion: str, duracion_segundos: int = 60) -> Dict[str, Any]:
        text_lower = transcripcion.lower()
        
        # Detección de vulnerables
        ninos = any(w in text_lower for w in ["niño", "bebe", "hijo", "guagua"])
        ancianos = any(w in text_lower for w in ["abuelo", "anciano", "abuelita", "viejito"])
        heridos = any(w in text_lower for w in ["herido", "sangrando", "golpeado", "atrapado"])
        
        # Pautas de contención dadas al usuario
        pautas = [
            "Mantenga la calma, su llamada ha sido geolocalizada y registrada en AMARU-FEN.",
            "Si el nivel de agua sube, suba inmediatamente a la parte más alta de la vivienda.",
            "No intente cruzar a pie ni en vehículo corrientes de agua o huaicos.",
            "Las unidades de rescate y la Policía Nacional han sido notificadas."
        ]
        
        return {
            "agente": self.nombre,
            "duracion_llamada_seg": duracion_segundos,
            "poblacion_vulnerable_detectada": {
                "ninos_presentes": ninos,
                "ancianos_presentes": ancianos,
                "personas_heridas": heridos
            },
            "pautas_contencion_emitidas": pautas,
            "triaje_completado": True,
            "prioridad_atencion": "URGENCIA_MAXIMA" if heridos or ninos else "PRIORIDAD_ALTA"
        }
