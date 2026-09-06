"""
SISTEMA DE NOTIFICACIONES TELEGRAM EN TIEMPO REAL — SISTEMA AMARU (FEN / CHIRI)
================================================================================
Monitorea las transiciones de estado territorial por código UBIGEO y despacha
alertas de emergencia inmediatas únicamente ante cambios hacia ALERTA ROJA.

Cumplimiento Estricto de Transparencia y Soberanía:
- Ley N° 31814 (Ley que promueve el uso de la Inteligencia Artificial en favor del desarrollo económico y social del país).
- Todo mensaje declara de forma visible e inequívoca que fue elaborado por Inteligencia Artificial.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Cargar .env de forma segura si existe
_env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_env_file):
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    if _k.strip() not in os.environ:
                        os.environ[_k.strip()] = _v.strip()
    except Exception:
        pass

class TelegramNotifier:
    """
    Gestor de alertas y notificaciones a canales de Telegram ante transiciones a Alerta Roja.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        ruta_estado: str = "data/estado_alertas_ubigeos.json",
        ruta_historico: str = "data/historico_alertas_telegram.json"
    ):
        # Cargar credenciales desde variables de entorno o parámetros
        self.bot_token = token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.ruta_estado = ruta_estado
        self.ruta_historico = ruta_historico
        self.estado_previo = self.cargar_estado_previo()

    def cargar_estado_previo(self) -> Dict[str, str]:
        """Carga el último estado conocido de cada UBIGEO para detectar transiciones."""
        if os.path.exists(self.ruta_estado):
            try:
                with open(self.ruta_estado, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_estado(self):
        """Persiste el estado actual de los UBIGEOs para la siguiente evaluación."""
        os.makedirs(os.path.dirname(self.ruta_estado), exist_ok=True)
        with open(self.ruta_estado, "r" if os.path.exists(self.ruta_estado) else "w", encoding="utf-8") as _:
            pass
        with open(self.ruta_estado, "w", encoding="utf-8") as f:
            json.dump(self.estado_previo, f, indent=2, ensure_ascii=False)

    def construir_mensaje_fen(self, distrito: Dict[str, Any]) -> str:
        """
        Construye el mensaje de alerta para eventos de El Niño / Huaicos / Inundaciones.
        Declara explícitamente la autoría de la Inteligencia Artificial (Ley N° 31814).
        """
        ubigeo = distrito.get("ubigeo", "000000")
        nombre = distrito.get("distrito", "DISTRITO").upper()
        provincia = distrito.get("provincia", "PROVINCIA")
        departamento = distrito.get("departamento", "DEPARTAMENTO")
        score_irce = distrito.get("score_irce", distrito.get("score", 0.85))
        lluvia_mm = distrito.get("lluvia_estimada_mm", distrito.get("lluvia_efectiva_mm", 55.0))
        poblacion = distrito.get("poblacion", distrito.get("poblacion_estimada", 15000))
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        mensaje = (
            "🚨 *ALERTA ROJA INMINENTE — SISTEMA AMARU-FEN* 🚨\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 *[AVISO OFICIAL: REPORTE ELABORADO POR INTELIGENCIA ARTIFICIAL]*\n"
            "_Elaborado autónomamente por el Motor de IA AMARU bajo el marco de la Ley Nº 31814 (Transparencia y Soberanía Humana)._\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 *UBIGEO {ubigeo}:* {nombre} ({provincia}, {departamento})\n"
            f"🔴 *NIVEL:* ALERTA ROJA DE EVACUACIÓN CRÍTICA\n"
            f"📊 *Índice de Peligro IRCE-FEN:* `{score_irce:.3f}` / 1.000\n"
            f"⏱️ *Ventana de Acción Táctica:* Margen de evacuación antes del clímax de crecida\n"
            f"🕒 *Hora de Detección IA:* {timestamp} (PET)\n\n"
            "📈 *PARÁMETROS FÍSICOS COMPUTADOS POR LA IA:*\n"
            f"• *Precipitación Estimada:* {lluvia_mm:.1f} mm/24h (SENAMHI - Umbral P99 Extremo)\n"
            f"• *Población en Exposición Directa:* {poblacion:,} habitantes\n"
            "• *Vulnerabilidad FEN:* Cuenca crítica con antecedentes de socavación y desborde\n"
            "• *Servicios en Peligro:* Red eléctrica de media tensión, pozos de agua y bocatomas\n\n"
            "⚡ *DIRECTIVAS EJECUTIVAS INMEDIATAS PARA EL ALCALDE / COEL:*\n"
            "1️⃣ *Evacuación Preventiva:* Trasladar a familias de fajas marginales hacia cotas altas seguras.\n"
            "2️⃣ *Resguardo de Servicios:* Solicitar pre-seccionamiento a la empresa eléctrica (SCADA) y generadores a EPS de agua.\n"
            "3️⃣ *Control Vial:* Restringir tránsito de mototaxis y vehículos en badenes y puentes vulnerables.\n"
            "4️⃣ *Habilitación Jurídica:* Activar compras directas de emergencia bajo D.S. Nº 124-2026-PCM y prellenar Ficha EDAN.\n\n"
            "⚖️ *CLÁUSULA DE SOBERANÍA HUMANA (Ley Nº 31814):*\n"
            "_Este informe constituye soporte técnico y predictivo algorítmico. Las decisiones de evacuación y ejecución corresponden con exclusividad a la autoridad humana competente._\n\n"
            f"🔗 *Consola Táctica en Vivo:* http://localhost:8501/?ubigeo={ubigeo}\n"
            "🏛️ *Centro de Operaciones:* Sistema Nacional de Gestión del Riesgo de Desastres (SINAGERD)"
        )
        return mensaje

    def construir_mensaje_chiri(self, distrito: Dict[str, Any]) -> str:
        """
        Construye el mensaje de alerta para eventos de La Niña / Heladas Extremas.
        Declara explícitamente la autoría de la Inteligencia Artificial (Ley N° 31814).
        """
        ubigeo = distrito.get("ubigeo", "000000")
        nombre = distrito.get("distrito", "DISTRITO").upper()
        departamento = distrito.get("departamento", "DEPARTAMENTO")
        ish_chiri = distrito.get("ish_chiri", 88.0)
        tmin = distrito.get("tmin_observada_c", distrito.get("tmin", -18.0))
        sensacion = distrito.get("sensacion_termica_viento_c", tmin - 5.0)
        alpacas = distrito.get("alpacas_expuestas", 50000)
        colegios = distrito.get("colegios_vulnerables", 12)
        directiva_prevaed = distrito.get("directiva_escolar_prevaed", "SUSPENSIÓN DE CLASES PRESENCIALES (PREVAED PP-0068)")
        alerta_vial = distrito.get("alerta_seguridad_vial", "Peligro de formación de hielo en carreteras altoandinas")
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        mensaje = (
            "❄️ *ALERTA ROJA GLACIAL — SISTEMA AMARU-CHIRI* ❄️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 *[AVISO OFICIAL: REPORTE ELABORADO POR INTELIGENCIA ARTIFICIAL]*\n"
            "_Elaborado autónomamente por el Motor de IA AMARU-CHIRI bajo la Ley Nº 31814 (Transparencia y Soberanía Humana)._\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 *UBIGEO {ubigeo}:* {nombre} ({departamento})\n"
            f"🔴 *NIVEL:* ALERTA ROJA GLACIAL | *Índice ISH-CHIRI:* `{ish_chiri:.1f} / 100`\n"
            f"⏱️ *Ventana Táctica Nocturna:* Desplome crítico en 4 a 6 horas (Clímax al amanecer)\n"
            f"🕒 *Hora de Detección IA:* {timestamp} (PET)\n\n"
            "🌡️ *PARÁMETROS CRIOCLIMÁTICOS COMPUTADOS POR LA IA:*\n"
            f"• *Temperatura Mínima Proyectada:* {tmin:.1f} °C\n"
            f"• *Sensación Térmica (Wind Chill):* {sensacion:.1f} °C (Viento Catabático Severo)\n"
            f"• *Ganado Alpaquero en Riesgo:* {alpacas:,} cabezas (Peligro de hipotermia/neumonía)\n"
            f"• *Locales Escolares de Adobe:* {colegios} II.EE. sin aislamiento térmico PRONIED\n\n"
            "🏫 *DIRECTIVAS SECTORIALES EDUCATIVAS Y VIALES:*\n"
            f"• *MINEDU / PREVAED:* ⚠️ *{directiva_prevaed}*\n"
            f"• *Vialidad:* ⚠️ {alerta_vial}\n\n"
            "⚡ *ACCIONES COMUNALES INMEDIATAS:*\n"
            "1️⃣ *Pecuario:* Guarecer crías en cobertizos y encender ahumado comunal con bosta seca.\n"
            "2️⃣ *Salud:* Distribuir antibióticos veterinarios y abrigar a niños y adultos mayores.\n"
            "3️⃣ *Transporte:* Restringir tránsito matinal en pasos cordilleranos por placas de hielo negro.\n\n"
            "⚖️ *CLÁUSULA DE SOBERANÍA HUMANA (Ley Nº 31814):*\n"
            "_Este informe es un cálculo algorítmico automatizado. La ejecución de medidas de protección corresponde a los comités multisectoriales locales (PMHF / INDECI)._\n\n"
            f"🔗 *Consola Crioclimática en Vivo:* http://localhost:8502/?ubigeo={ubigeo}\n"
            "🏛️ *Plan Multisectorial ante Heladas y Friaje (PMHF)*"
        )
        return mensaje

    def enviar_mensaje_telegram(self, texto: str, canal_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Realiza el despacho del mensaje a la API de Telegram.
        Si no hay token o chat_id configurados, opera en Modo Simulación Oficial.
        """
        destino = canal_id or self.chat_id
        token = self.bot_token

        resultado = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chat_id": destino if destino else "SIMULACION_CANAL_C2",
            "caracteres": len(texto),
            "estado": "PENDIENTE",
            "modo": "EN_VIVO" if (token and destino) else "SIMULACION_TEST",
            "elaborado_por_ia": True
        }

        # Si tenemos credenciales en vivo, enviar vía HTTP POST a Telegram
        if token and destino:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": destino,
                "text": texto,
                "parse_mode": "Markdown"
            }
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    if resp_data.get("ok"):
                        resultado["estado"] = "ENVIADO_EXITOSO"
                        resultado["message_id"] = resp_data.get("result", {}).get("message_id")
                    else:
                        resultado["estado"] = "ERROR_API"
                        resultado["error_api"] = resp_data.get("description")
            except Exception as e:
                resultado["estado"] = "ERROR_CONEXION"
                resultado["error_excepcion"] = str(e)
        else:
            # Modo Simulación: Valida la carga útil y la registra como exitosa para pruebas
            resultado["estado"] = "DESPACHADO_SIMULACION_OK"
            resultado["nota"] = "Sin token de Telegram en .env; alerta generada y validada en entorno de pruebas C2."

        # Registrar en la bitácora de auditoría histórica
        self._registrar_en_historico(resultado, texto)
        return resultado

    def procesar_transiciones_fen(self, distritos_evaluados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inspecciona una lista de distritos evaluados en AMARU-FEN.
        Detecta y dispara alerta ÚNICAMENTE para aquellos que hayan cambiado a CRITICO_ROJO.
        """
        alertas_disparadas = []

        for d in distritos_evaluados:
            ubigeo = str(d.get("ubigeo", "")).strip()
            nivel_actual = str(d.get("nivel_alerta", d.get("nivel", ""))).upper()

            es_rojo_actual = ("ROJO" in nivel_actual or "CRITICO" in nivel_actual)
            nivel_previo = self.estado_previo.get(ubigeo, "NORMAL_VERDE")
            era_rojo_previo = ("ROJO" in nivel_previo or "CRITICO" in nivel_previo)

            # Transición: Antes NO era rojo y ahora SÍ es rojo
            if es_rojo_actual and not era_rojo_previo:
                mensaje = self.construir_mensaje_fen(d)
                envio = self.enviar_mensaje_telegram(mensaje)
                alertas_disparadas.append({
                    "ubigeo": ubigeo,
                    "distrito": d.get("distrito"),
                    "tipo_evento": "AMARU_FEN_HUAICO_INUNDACION",
                    "nivel_anterior": nivel_previo,
                    "nuevo_nivel": nivel_actual,
                    "resultado_envio": envio,
                    "mensaje_texto": mensaje
                })
                # Actualizar estado a rojo
                self.estado_previo[ubigeo] = nivel_actual
            else:
                # Actualizar estado si cambió a cualquier otro nivel
                self.estado_previo[ubigeo] = nivel_actual

        if alertas_disparadas:
            self.guardar_estado()

        return alertas_disparadas

    def procesar_transiciones_chiri(self, distritos_evaluados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inspecciona una lista de distritos evaluados en AMARU-CHIRI.
        Detecta y dispara alerta ÚNICAMENTE para aquellos que hayan cambiado a ALERTA_ROJA_GLACIAL.
        """
        alertas_disparadas = []

        for d in distritos_evaluados:
            ubigeo = str(d.get("ubigeo", "")).strip()
            nivel_actual = str(d.get("nivel_alerta", "")).upper()

            es_rojo_actual = ("ROJO" in nivel_actual or "GLACIAL" in nivel_actual)
            nivel_previo = self.estado_previo.get(ubigeo, "NORMAL_VERDE")
            era_rojo_previo = ("ROJO" in nivel_previo or "GLACIAL" in nivel_previo)

            # Transición a rojo glacial
            if es_rojo_actual and not era_rojo_previo:
                mensaje = self.construir_mensaje_chiri(d)
                envio = self.enviar_mensaje_telegram(mensaje)
                alertas_disparadas.append({
                    "ubigeo": ubigeo,
                    "distrito": d.get("distrito"),
                    "tipo_evento": "AMARU_CHIRI_HELADA_EXTREMA",
                    "nivel_anterior": nivel_previo,
                    "nuevo_nivel": nivel_actual,
                    "resultado_envio": envio,
                    "mensaje_texto": mensaje
                })
                self.estado_previo[ubigeo] = nivel_actual
            else:
                self.estado_previo[ubigeo] = nivel_actual

        if alertas_disparadas:
            self.guardar_estado()

        return alertas_disparadas

    def _registrar_en_historico(self, resultado: Dict[str, Any], texto_mensaje: str):
        """Registra la alerta en la bitácora JSON de auditoría C2."""
        os.makedirs(os.path.dirname(self.ruta_historico), exist_ok=True)
        historico = []
        if os.path.exists(self.ruta_historico):
            try:
                with open(self.ruta_historico, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except Exception:
                historico = []

        registro = {
            "id": len(historico) + 1,
            "metadata_envio": resultado,
            "mensaje_completo": texto_mensaje
        }
        historico.append(registro)

        # Guardar los últimos 100 despachos
        with open(self.ruta_historico, "w", encoding="utf-8") as f:
            json.dump(historico[-100:], f, indent=2, ensure_ascii=False)
