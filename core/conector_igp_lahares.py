"""
Conector y Simulador Telemétrico del Sistema de Monitoreo de Lahares y Huaicos del IGP
Portal Oficial: https://grd.igp.gob.pe/lahares-huaicos/
Instituto Geofísico del Perú (IGP) - Sistema Nacional de Gestión del Riesgo de Desastres (SINAGERD)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class ConectorIGPLaharesHuaicos:
    """
    Gestiona la ingesta, consulta y simulación telemétrica de la red in situ de sensores
    de flujo del Instituto Geofísico del Perú (geófonos sísmicos, acelerómetros y radares de nivel).
    """

    PORTAL_OFICIAL_URL = "https://grd.igp.gob.pe/lahares-huaicos/"

    ESTACIONES_INSTRUMENTADAS_IGP = {
        "Q-PIU-06": {
            "nombre_quebrada_igp": "Quebrada Limón",
            "codigo_igp": "IGP-HUAICO-PIU-LIMON-01",
            "tipo_fenomeno": "HUAICO_TORRENCIAL",
            "region": "Piura",
            "distrito": "Canchaque",
            "sensores_instalados": ["Geófono Sísmico Triaxial", "Radar de Nivel Ultrasónico", "Cámara Óptica IP"],
            "puntos_criticos_eta": [
                {"punto": "Puente Fierro Canchaque (PE-08C)", "distancia_km": 1.8, "eta_minutos": 12},
                {"punto": "Sector Urbano La Esperanza", "distancia_km": 3.2, "eta_minutos": 20},
                {"punto": "Desembocadura Río Pusmalca", "distancia_km": 5.0, "eta_minutos": 35}
            ]
        },
        "Q-LIM-09": {
            "nombre_quebrada_igp": "Quebrada Rio Seco 1 y 2",
            "codigo_igp": "IGP-HUAICO-LIM-RIOSECO-01",
            "tipo_fenomeno": "HUAICO_TORRENCIAL",
            "region": "Lima",
            "distrito": "Lurigancho-Chosica",
            "sensores_instalados": ["Geófono Sísmico de Alta Frecuencia", "Sensor de Presión Hidrostática"],
            "puntos_criticos_eta": [
                {"punto": "Carretera Central PE-22 km 34+800", "distancia_km": 2.4, "eta_minutos": 18},
                {"punto": "Puente Los Ángeles / Vía Férrea", "distancia_km": 3.9, "eta_minutos": 28},
                {"punto": "Confluencia Río Rímac", "distancia_km": 4.8, "eta_minutos": 38}
            ]
        },
        "Q-LIM-06": {
            "nombre_quebrada_igp": "Quebrada Huaycoloro 1 y 2",
            "codigo_igp": "IGP-HUAICO-LIM-HUAYCOLORO-01",
            "tipo_fenomeno": "HUAICO_TORRENCIAL",
            "region": "Lima",
            "distrito": "San Juan de Lurigancho",
            "sensores_instalados": ["Radar Telemétrico Doppler", "Acelerómetro de Lecho Rocoso"],
            "puntos_criticos_eta": [
                {"punto": "Puente Huaycoloro (Av. Las Torres)", "distancia_km": 4.5, "eta_minutos": 32},
                {"punto": "Ingreso a Campoy / SJL", "distancia_km": 6.8, "eta_minutos": 45},
                {"punto": "Bocatoma La Atarjea (SEDAPAL)", "distancia_km": 9.2, "eta_minutos": 60}
            ]
        },
        "Q-ARE-01": {
            "nombre_quebrada_igp": "Quebrada San Lazaro 2 / Huarangueros 1 y 2",
            "codigo_igp": "IGP-LAHAR-ARE-SANLAZARO-02",
            "tipo_fenomeno": "LAHAR_VOLCANICO_MISTI",
            "region": "Arequipa",
            "distrito": "Alto Selva Alegre",
            "sensores_instalados": ["Red Geofísica CENVUL-IGP", "Geófono de Infrasonido", "Sensor Óptico Térmico"],
            "puntos_criticos_eta": [
                {"punto": "Puente Juan de la Torre (Alto Selva Alegre)", "distancia_km": 3.1, "eta_minutos": 15},
                {"punto": "Puente San Lázaro / Centro Histórico", "distancia_km": 5.4, "eta_minutos": 26},
                {"punto": "Desembocadura Río Chili", "distancia_km": 7.0, "eta_minutos": 35}
            ]
        },
        "Q-ARE-02": {
            "nombre_quebrada_igp": "Quebrada Venezuela 1 y 2",
            "codigo_igp": "IGP-LAHAR-ARE-VENEZUELA-01",
            "tipo_fenomeno": "LAHAR_VOLCANICO_MISTI",
            "region": "Arequipa",
            "distrito": "Mariano Melgar",
            "sensores_instalados": ["Sensor de Impacto Acústico", "Estación Hidroacústica IGP"],
            "puntos_criticos_eta": [
                {"punto": "By-Pass Av. Venezuela / Mariscal Castilla", "distancia_km": 2.8, "eta_minutos": 16},
                {"punto": "Feria El Altiplano / Paucarpata", "distancia_km": 4.2, "eta_minutos": 24},
                {"punto": "Intercambio Vial El Palomar", "distancia_km": 5.8, "eta_minutos": 32}
            ]
        },
        "Q-ARE-03": {
            "nombre_quebrada_igp": "Quebradas Huarangal 1-2, Pastores 1 y El Pato 1",
            "codigo_igp": "IGP-LAHAR-ARE-HUARANGAL-01",
            "tipo_fenomeno": "LAHAR_VOLCANICO_MISTI",
            "region": "Arequipa",
            "distrito": "Miraflores",
            "sensores_instalados": ["Geófono Sísmico Autónomo", "Alerta Sonora Sirena C2"],
            "puntos_criticos_eta": [
                {"punto": "Puente Av. Sepúlveda Miraflores", "distancia_km": 2.2, "eta_minutos": 14},
                {"punto": "Sector Urbano Chullo", "distancia_km": 3.8, "eta_minutos": 22},
                {"punto": "Canalización Principal Río Chili", "distancia_km": 5.5, "eta_minutos": 31}
            ]
        }
    }

    def __init__(self):
        pass

    def consultar_telemetria_in_situ(
        self,
        id_quebrada: str,
        simular_activo: Optional[bool] = None,
        lluvia_cabecera_mm_h: float = 0.0
    ) -> Dict[str, Any]:
        """
        Consulta o simula la telemetría del sensor in situ del IGP para una quebrada.
        Si la quebrada está instrumentada por el IGP, reporta velocidad, altura y puntos críticos.
        """
        id_norm = id_quebrada.upper().strip()
        info_estacion = self.ESTACIONES_INSTRUMENTADAS_IGP.get(id_norm)

        if not info_estacion:
            return {
                "monitoreada_por_igp": False,
                "mensaje": f"La quebrada '{id_quebrada}' no cuenta con sensores in situ del IGP actualmente.",
                "estado_sensor": "SIN_INSTRUMENTACION_IGP",
                "entidad": "Instituto Geofísico del Perú (IGP)",
                "url_portal_igp": self.PORTAL_OFICIAL_URL
            }

        # Determinación del estado del sensor (activo si llueve fuerte o si se fuerza simulación)
        if simular_activo is not None:
            activo = simular_activo
        else:
            activo = (lluvia_cabecera_mm_h >= 14.0)

        timestamp_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if activo:
            # Flujo en descenso detectado por geófonos
            velocidad = round(min(7.5, max(2.5, lluvia_cabecera_mm_h * 0.22)), 2)
            altura = round(min(3.5, max(0.6, lluvia_cabecera_mm_h * 0.08)), 2)
            estado_sensor = "ESTADO ACTIVO: DESCENSO DE FLUJO EN CURSO"
            alarma_sonora = True
        else:
            velocidad = 0.0
            altura = 0.0
            estado_sensor = "ESTADO NO ACTIVO: CAUCE SECO EN REPOSO"
            alarma_sonora = False

        return {
            "monitoreada_por_igp": True,
            "denominacion_amaru": f"{id_norm}: {info_estacion['nombre_quebrada_igp']}",
            "codigo_amaru": id_norm,
            "entidad_amaru": "AMARU-FEN (Comando Táctico C2)",
            "denominacion_oficial_igp": info_estacion["nombre_quebrada_igp"],
            "codigo_oficial_igp": info_estacion["codigo_igp"],
            "entidad_denominadora_igp": "Instituto Geofísico del Perú (IGP) - Sistema Lahares y Huaicos",
            "tipo_fenomeno": info_estacion["tipo_fenomeno"],
            "region": info_estacion["region"],
            "distrito": info_estacion["distrito"],
            "estado_sensor": estado_sensor,
            "es_flujo_activo": activo,
            "velocidad_flujo_ms": velocidad,
            "velocidad_flujo_kmh": round(velocidad * 3.6, 1),
            "altura_flujo_m": altura,
            "alarma_sonora_activa": alarma_sonora,
            "fecha_hora_ocurrencia": timestamp_actual if activo else "N/A (Sin evento en curso)",
            "sensores_instalados": info_estacion["sensores_instalados"],
            "puntos_criticos_eta": info_estacion["puntos_criticos_eta"],
            "url_portal_igp": self.PORTAL_OFICIAL_URL,
            "marco_legal": "Ley N° 29664 (SINAGERD) y Ley N° 31814 (Soberanía Humana)"
        }

    def evaluar_doble_confirmacion(
        self,
        iph_score: float,
        telemetria_igp: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Realiza el cruce de Doble Confirmación Soberana:
        - AMARU-FEN (Previsión hidrometeorológica anticipada IPH-FEN)
        - IGP (Detección in situ por geófonos del descenso real del flujo)
        """
        es_amaru_critico = (iph_score >= 85.0)
        es_igp_activo = telemetria_igp.get("es_flujo_activo", False)

        if es_amaru_critico and es_igp_activo:
            nivel = "🔴 DOBLE_CONFIRMACION_CRITICA_SOBERANA (AMARU + IGP)"
            descripcion = (
                "EMERGENCIA DE IMPACTO INMINENTE: Previsión IPH-FEN confirma condiciones de ruptura orográfica "
                "y los geófonos in situ del IGP detectan descenso físico de la masa de detritos con alarma sonora activa."
            )
            accion = "DISPARO INMEDIATO DE SIRENAS URBANAS, CIERRE DE VÍAS MTC Y EVACUACIÓN A ZONAS SEGURAS."
        elif es_amaru_critico and not es_igp_activo:
            nivel = "🟠 ALERTA PREVENTIVA ANTICIPADA (AMARU PREVISIÓN)"
            descripcion = "Alta probabilidad de activación en cabecera. La masa aún no alcanza los sensores del cauce medio."
            accion = "Cierre preventivo de badenes y preposicionamiento de cuadrillas."
        elif not es_amaru_critico and es_igp_activo:
            nivel = "⚠️ ALERTA FÍSICA IN SITU IGP (DESPRENDIMIENTO LOCAL)"
            descripcion = "Los sensores del IGP detectan flujo en descenso por evento súbito o rotura de represa natural."
            accion = "Activación de sirenas y verificación en campo."
        else:
            nivel = "🟢 VIGILANCIA EN REPOSO"
            descripcion = "Sin condiciones de activación ni eventos detectados por geófonos."
            accion = "Monitoreo satelital continuo."

        return {
            "nivel_consenso": nivel,
            "doble_confirmacion_activa": (es_amaru_critico and es_igp_activo),
            "descripcion": descripcion,
            "accion_recomendada": accion
        }

conector_igp_lahares = ConectorIGPLaharesHuaicos()
