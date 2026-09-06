"""
Módulo de Despacho y Notificación Táctica a Unidades de Defensa Civil Municipal
Sistema AMARU-FEN - Cumplimiento Ley N° 29664 (SINAGERD) y Ley N° 31814 (Soberanía Humana)
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class DespachadorDefensaCivilMunicipal:
    """
    Gestiona el directorio de contactos institucionales de Gestión del Riesgo de Desastres
    y emite notificaciones tácticas por correo electrónico a los Jefes de Defensa Civil distritales.
    """

    def __init__(self):
        self.ruta_directorio = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "contactos_defensa_civil", "directorio_nacional_grd.json"
        )
        self.ruta_log_despachos = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "contactos_defensa_civil", "registro_despachos_defensa_civil.json"
        )
        self.contactos = self._cargar_directorio()

    def _cargar_directorio(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.ruta_directorio):
                with open(self.ruta_directorio, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("contactos_municipales", [])
        except Exception as e:
            logger.error(f"Error cargando directorio de defensa civil: {e}")
        return []

    def buscar_contacto_por_ubigeo(self, ubigeo: str) -> Optional[Dict[str, Any]]:
        """Busca el contacto institucional de Defensa Civil según código UBIGEO."""
        for c in self.contactos:
            if c.get("ubigeo") == str(ubigeo):
                return c
        return None

    def buscar_contacto_por_distrito(self, nombre_distrito: str) -> Optional[Dict[str, Any]]:
        """Busca el contacto por nombre de distrito (aproximado sin distinción de mayúsculas)."""
        nom = nombre_distrito.strip().upper()
        for c in self.contactos:
            if c.get("distrito", "").upper() in nom or nom in c.get("distrito", "").upper():
                return c
        return None

    def generar_dossier_alerta_correo(
        self,
        ubigeo: str,
        datos_irce: Dict[str, Any],
        anomalia_tsm: float = 1.8,
        precipitacion_estimada_mm: float = 65.0
    ) -> Dict[str, Any]:
        """
        Genera el paquete completo de información técnica, directivas operativas y
        plantilla formal del correo electrónico dirigido al Jefe de Defensa Civil.
        """
        contacto = self.buscar_contacto_por_ubigeo(ubigeo)
        if not contacto:
            # Fallback estructurado si no está en el directorio piloto
            distrito = datos_irce.get("distrito", "DISTRITO")
            departamento = datos_irce.get("departamento", "DEPARTAMENTO")
            contacto = {
                "ubigeo": ubigeo,
                "departamento": departamento,
                "provincia": datos_irce.get("provincia", "PROVINCIA"),
                "distrito": distrito,
                "municipalidad": f"Municipalidad Distrital de {distrito}",
                "unidad_organica": "Unidad de Gestión del Riesgo de Desastres y Defensa Civil",
                "responsable": {
                    "cargo": "Jefe de la Unidad de Defensa Civil",
                    "nombre_completo": "Coordinador de Defensa Civil / COEL",
                    "acto_resolutivo_designacion": "RGM Vigente",
                    "estado": "ACTIVO"
                },
                "canales_comunicacion": {
                    "correo_institucional_principal": f"defensacivil@muni{distrito.lower().replace(' ', '')}.gob.pe",
                    "telefonos_emergencia": ["Central COEL / Seguridad Ciudadana"],
                    "anexo_central": "101"
                },
                "amenazas_predominantes": ["Inundación pluvial y desborde fluvial El Niño"]
            }

        score_irce = datos_irce.get("score_irce", 0.85)
        nivel_alerta = datos_irce.get("nivel_alerta", "CRITICO_ROJO")
        semaforo = datos_irce.get("semaforo", "🔴 ROJO (Evacuación Inminente)")
        timestamp_ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Asunto formal del correo
        asunto = f"🚨 [ALERTA FEN {nivel_alerta}] AMARU-FEN: Acción Temprana en {contacto['distrito']} (UBIGEO {contacto['ubigeo']}) - IRCE: {score_irce}"

        # Cuerpo del mensaje en texto estructurado
        cuerpo_texto = f"""
========================================================================================
ALERTA TÁCTICA TEMPRANA DE GESTIÓN DEL RIESGO DE DESASTRES (SINAGERD / AMARU-FEN)
========================================================================================
FECHA Y HORA OFICIAL DE EMISIÓN: {timestamp_ahora} (Hora Oficial del Perú)
DESTINATARIO: {contacto['responsable']['nombre_completo']}
CARGO: {contacto['responsable']['cargo']}
ENTIDAD: {contacto['municipalidad']}
CORREO INSTITUCIONAL: {contacto['canales_comunicacion']['correo_institucional_principal']}
UBIGEO: {contacto['ubigeo']} | DISTRITO: {contacto['distrito']}, {contacto['provincia']}, {contacto['departamento']}
----------------------------------------------------------------------------------------

1. EVALUACIÓN DE AMENAZA Y VULNERABILIDAD (ÍNDICE IRCE-FEN)
----------------------------------------------------------------------------------------
• ÍNDICE DE RIESGO COMPUESTO (IRCE-FEN): {score_irce} / 1.000
• SEMÁFORO DE SITUACIÓN: {semaforo}
• ANOMALÍA TÉRMICA SUPERFICIAL DEL MAR (ENFEN Niño 1+2): +{anomalia_tsm:.1f} °C
• PRECIPITACIÓN ESTIMADA (24 Horas / SENAMHI): {precipitacion_estimada_mm:.1f} mm
• POBLACIÓN EN ZONA DE EXPOSICIÓN: {datos_irce.get('poblacion', 0):,} habitantes
• AMENAZAS LOCALES ESPECÍFICAS:
  {chr(10).join('  - ' + a for a in contacto.get('amenazas_predominantes', []))}

2. DIRECTIVAS TÁCTICAS INMEDIATAS PARA EL GRUPO DE TRABAJO (GT-GRD) Y PLATAFORMA LOCAL:
----------------------------------------------------------------------------------------
[1] CONVOCATORIA EXTRAORDINARIA:
    Solicitar al Alcalde Distrital (Presidente de la Plataforma de Defensa Civil) la 
    instalación permanente del Grupo de Trabajo de la Gestión del Riesgo de Desastres.
[2] ACTIVACIÓN DEL COEL:
    Poner en régimen de guardia de 24 horas al Centro de Operaciones de Emergencia Local.
[3] INSPECCIÓN DE PUNTOS CRÍTICOS:
    Supervisión inmediata de defensas ribereñas, cauces de ríos y drenes colectores urbanos.
[4] PLATAFORMA SINPAD v2.0 (INDECI):
    Iniciar el pre-llenado de la Evaluación de Daños y Análisis de Necesidades (Ficha EDAN)
    en caso de desborde inminente para canalizar ayuda humanitaria de Nivel 3 / 4.
[5] ALBERGUES TEMPORALES:
    Inspeccionar losas deportivas, colegios y locales comunales empadronados para refugio.

----------------------------------------------------------------------------------------
3. CLÁUSULA OBLIGATORIA DE SOBERANÍA HUMANA (LEY N° 31814 - REGLAMENTO DS 085-2024-PCM):
----------------------------------------------------------------------------------------
"Este mensaje ha sido generado por el Sistema de Soporte de Decisiones AMARU-FEN con base en 
telemetría oficial autorizada del SENAMHI, ENFEN y ANA. 
CONFORME A LA LEY N° 31814, LA INTELIGENCIA ARTIFICIAL NO SUSTITUYE LA RESPONSABILIDAD NI LA 
DECISIÓN HUMANA. Toda orden de evacuación masiva, declaratoria de emergencia, alerta SISMATE 
o ejecución presupuestal es de exclusiva atribución y suscripción de las autoridades humanas 
competentes (Alcalde Distrital y Jefe de Defensa Civil)."
========================================================================================
Contacto de Soporte Técnico AMARU-FEN / COEN: soporte-amaru@indeci.gob.pe
"""

        # Formato HTML enriquecido para clientes de correo modernos
        cuerpo_html = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:680px;margin:0 auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;background:#ffffff;">
            <div style="background:linear-gradient(135deg,#0a192f,#1e3c72);color:#ffffff;padding:24px;border-bottom:4px solid #e63946;">
                <h3 style="margin:0;color:#ffb703;letter-spacing:1px;font-size:12px;text-transform:uppercase;">Sistema Táctico AMARU-FEN | SINAGERD</h3>
                <h1 style="margin:8px 0 0;font-size:22px;">🚨 Notificación de Alerta Temprana ante El Niño</h1>
                <p style="margin:6px 0 0;font-size:13px;opacity:0.85;">Distrito de {contacto['distrito']} — Código UBIGEO: {contacto['ubigeo']}</p>
            </div>
            <div style="padding:24px;">
                <div style="background:#f8f9fa;border-left:4px solid #e63946;padding:14px;border-radius:6px;margin-bottom:20px;">
                    <div style="font-size:12px;color:#6c757d;">ESTADO DE SITUACIÓN EN EL TERRITORIO:</div>
                    <div style="font-size:20px;font-weight:bold;color:#d90429;margin:4px 0;">{semaforo}</div>
                    <div style="font-size:13px;color:#333;">Índice Compuesto IRCE-FEN: <strong>{score_irce:.3f}</strong> | Fecha: <strong>{timestamp_ahora}</strong></div>
                </div>

                <h3 style="color:#0a192f;border-bottom:2px solid #eef2f7;padding-bottom:6px;font-size:16px;">👤 Destinatario Institucional Designado</h3>
                <table style="width:100%;font-size:13px;border-collapse:collapse;margin-bottom:20px;">
                    <tr><td style="padding:6px;color:#666;width:160px;">Funcionario a Cargo:</td><td style="padding:6px;font-weight:600;">{contacto['responsable']['nombre_completo']}</td></tr>
                    <tr><td style="padding:6px;color:#666;">Cargo Oficial:</td><td style="padding:6px;">{contacto['responsable']['cargo']}</td></tr>
                    <tr><td style="padding:6px;color:#666;">Resolución de Designación:</td><td style="padding:6px;"><code>{contacto['responsable']['acto_resolutivo_designacion']}</code></td></tr>
                    <tr><td style="padding:6px;color:#666;">Correo Institucional:</td><td style="padding:6px;color:#0e4e9b;font-weight:bold;">{contacto['canales_comunicacion']['correo_institucional_principal']}</td></tr>
                </table>

                <h3 style="color:#0a192f;border-bottom:2px solid #eef2f7;padding-bottom:6px;font-size:16px;">📊 Telemetría y Amenazas Locales</h3>
                <div style="display:flex;gap:12px;margin-bottom:18px;">
                    <div style="flex:1;background:#eef4fb;padding:12px;border-radius:6px;text-align:center;">
                        <div style="font-size:11px;color:#555;">TSM Niño 1+2</div>
                        <div style="font-size:18px;font-weight:bold;color:#0e4e9b;">+{anomalia_tsm:.1f} °C</div>
                    </div>
                    <div style="flex:1;background:#fff2e6;padding:12px;border-radius:6px;text-align:center;">
                        <div style="font-size:11px;color:#555;">Lluvia Proyectada 24h</div>
                        <div style="font-size:18px;font-weight:bold;color:#d90429;">{precipitacion_estimada_mm:.1f} mm</div>
                    </div>
                    <div style="flex:1;background:#eef7f2;padding:12px;border-radius:6px;text-align:center;">
                        <div style="font-size:11px;color:#555;">Población Expuesta</div>
                        <div style="font-size:18px;font-weight:bold;color:#1e8a45;">{datos_irce.get('poblacion', 0):,} hab.</div>
                    </div>
                </div>

                <h3 style="color:#0a192f;border-bottom:2px solid #eef2f7;padding-bottom:6px;font-size:16px;">📋 Directivas Tácticas para el GT-GRD y Defensa Civil</h3>
                <ul style="font-size:13px;line-height:1.6;color:#2b2d42;padding-left:20px;">
                    <li><strong>Convocatoria Inmediata:</strong> Convocar sesión de emergencia del Grupo de Trabajo de GRD presidido por el Alcalde Distrital.</li>
                    <li><strong>Monitoreo de Drenes y Cauces:</strong> Inspeccionar de inmediato los puntos de estrangulamiento fluvial y drenes colectores.</li>
                    <li><strong>Pre-llenado EDAN / SINPAD:</strong> Alistar personal técnico para registro preliminar en el Sistema Nacional de Información para la Prevención y Atención de Desastres.</li>
                    <li><strong>Habilitación de Refugios:</strong> Verificar disponibilidad de agua, carpas y servicios básicos en albergues temporales designados.</li>
                </ul>

                <div style="background:#fff3cd;border:1px solid #ffeeba;color:#856404;padding:14px;border-radius:6px;font-size:12px;margin-top:20px;line-height:1.5;">
                    ⚖️ <strong>Cláusula de Soberanía Humana (Ley N° 31814 - DS 085-2024-PCM):</strong><br>
                    Este despacho es un servicio automatizado de alerta temprana para soporte de decisiones. Las decisiones operativas, emisión de órdenes de evacuación, alertas a la población y contrataciones directas son de <strong>exclusiva competencia y responsabilidad de las autoridades humanas</strong> de la Municipalidad.
                </div>
            </div>
            <div style="background:#f4f6f9;padding:14px;text-align:center;font-size:11px;color:#6c757d;border-top:1px solid #e3e8ee;">
                AMARU-FEN &copy; 2026 — Plataforma de Gobernanza Anticipatoria ante El Niño | República del Perú
            </div>
        </div>
        """

        return {
            "contacto_municipal": contacto,
            "asunto": asunto,
            "destinatario_correo": contacto['canales_comunicacion']['correo_institucional_principal'],
            "destinatario_nombre": contacto['responsable']['nombre_completo'],
            "cuerpo_texto": cuerpo_texto,
            "cuerpo_html": cuerpo_html,
            "timestamp": timestamp_ahora,
            "ubigeo": ubigeo,
            "score_irce": score_irce,
            "nivel_alerta": nivel_alerta
        }

    def generar_alerta_corta_telegram(self, dossier: Dict[str, Any]) -> str:
        """
        Genera un informe sintetizado, directo y estructurado para canales de mensajería instantánea
        móvil táctica (Telegram / WhatsApp COEL), optimizado para lectura rápida en smartphone.
        """
        contacto = dossier.get("contacto_municipal", {})
        score_irce = dossier.get("score_irce", 0.85)
        nivel_alerta = dossier.get("nivel_alerta", "CRITICO_ROJO")
        ubigeo = dossier.get("ubigeo", "")
        distrito = contacto.get("distrito", "DISTRITO")
        provincia = contacto.get("provincia", "PROVINCIA")
        departamento = contacto.get("departamento", "DEPARTAMENTO")
        funcionario = contacto.get("responsable", {}).get("nombre_completo", "Jefe de Defensa Civil")

        emoji_nivel = "🔴" if "ROJO" in nivel_alerta else ("🟠" if "NARANJA" in nivel_alerta or "AMBAR" in nivel_alerta else "🟡")

        mensaje_telegram = f"""🚨 *ALERTA TÁCTICA FEN — AMARU / SINAGERD*
📍 *UBIGEO {ubigeo}:* {distrito} ({provincia}, {departamento})
{emoji_nivel} *ESTADO:* {nivel_alerta} | *IRCE-FEN:* `{score_irce:.3f}`

👤 *Destinatario GRD:* {funcionario}
🏛️ *Entidad:* {contacto.get('municipalidad', 'Municipalidad Distrital')}
🕒 *Emisión:* {dossier.get('timestamp')} (PET)

📊 *TELEMETRÍA CRÍTICA:*
• *TSM Niño 1+2 (ENFEN):* +2.0 °C (Onda Kelvin)
• *Precipitación 24h (SENAMHI):* Alerta Roja / Saturación
• *Población Expuesta:* {contacto.get('poblacion', 68400):,} hab.
• *Amenaza:* Desborde fluvial / Anegamiento pluvial

⚡ *DIRECTIVAS INMEDIATAS PARA EL COEL:*
1️⃣ Convocar Sesión Urgente del GT-GRD con el Alcalde.
2️⃣ Poner en alerta de 24h al Centro de Operaciones Local.
3️⃣ Pre-llenar Ficha EDAN preliminar en SINPAD v2.0.
4️⃣ Despeje de drenes y refuerzo de fajas marginales.

⚖️ *SOBERANÍA HUMANA (Ley N° 31814):*
_El presente despacho es un soporte técnico de IA. La orden de evacuación y acciones ejecutivas corresponden con exclusividad a la autoridad humana competente._

🔗 *Canal Oficial COEN-INDECI:* https://portal.indeci.gob.pe"""
        return mensaje_telegram

    def enmascarar_dato_personal(self, texto: str) -> str:
        """
        Enmascara correos y teléfonos según la Ley N° 29733 (Protección de Datos Personales de Perú).
        Ejemplo: carlosedubanos@gmail.com -> ca*****os@gmail.com
        """
        if not texto:
            return ""
        if "@" in texto:
            partes = texto.split("@")
            user, dom = partes[0], partes[1]
            if len(user) <= 3:
                return f"{user[0]}***@{dom}"
            return f"{user[:2]}*****{user[-2:]}@{dom}"
        elif len(texto) >= 6 and texto.replace("-", "").isdigit():
            return f"{texto[:3]}-*****-{texto[-2:]}"
        return texto

    def disparar_correo_alerta(
        self,
        ubigeo: str,
        datos_irce: Dict[str, Any],
        anomalia_tsm: float = 1.8,
        precipitacion_estimada_mm: float = 65.0,
        modo_simulacion: bool = True,
        firma_humana: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el despacho del dossier formal aplicando la Compuerta de Soberanía Humana (Human-in-the-Loop).
        La IA NUNCA dispara correos oficiales sin autorización humana explícita.
        """
        dossier = self.generar_dossier_alerta_correo(
            ubigeo=ubigeo,
            datos_irce=datos_irce,
            anomalia_tsm=anomalia_tsm,
            precipitacion_estimada_mm=precipitacion_estimada_mm
        )

        # Generar versión corta para Telegram
        dossier["mensaje_telegram_corto"] = self.generar_alerta_corta_telegram(dossier)

        # COMPUERTA DE SOBERANÍA HUMANA (Ley N° 31814 / DS 085-2024-PCM):
        # Si no es simulación sintética y no hay firma humana autorizadora, SE BLOQUEA EL DISPARO.
        if not modo_simulacion and not firma_humana:
            dossier["estado_gobernanza"] = "BLOQUEADO_POR_FALTA_DE_AUTORIZACION_HUMANA"
            dossier["requiere_firma_humana"] = True
            dossier["mensaje_seguridad"] = "BLOQUEO DE SEGURIDAD: La IA no tiene facultades para emitir despachos oficiales sin la validación y firma de una autoridad humana competente (Ley N° 31814)."
            return dossier

        # Registro formal con protección de datos personales (Ley N° 29733)
        correo_destino = dossier["destinatario_correo"]
        correo_enmascarado = self.enmascarar_dato_personal(correo_destino)

        registro_despacho = {
            "id_despacho": f"DESP-GRD-{int(datetime.now().timestamp())}",
            "fecha_hora": dossier["timestamp"],
            "ubigeo": ubigeo,
            "distrito": dossier["contacto_municipal"]["distrito"],
            "departamento": dossier["contacto_municipal"]["departamento"],
            "destinatario_correo_enmascarado_lpdp": correo_enmascarado,
            "destinatario_funcionario": dossier["destinatario_nombre"],
            "score_irce": dossier["score_irce"],
            "nivel_alerta": dossier["nivel_alerta"],
            "modo_ejecucion": "SIMULACION_SINTETICA_CONTROLADA" if modo_simulacion else "DESPACHO_OFICIAL_AUTORIZADO",
            "estado_envio": "ENTREGADO_SIMULADO" if modo_simulacion else "ENVIADO_CON_FIRMA_HUMANA",
            "autorizacion_humana": firma_humana if firma_humana else {
                "tipo": "SIMULACION_AUDITADA_EVALUADOR",
                "autorizador": "Operador de Sala C2 AMARU-FEN",
                "declaracion": "Entorno controlado de prueba sintética"
            },
            "asunto": dossier["asunto"]
        }

        self._guardar_registro(registro_despacho)
        dossier["registro_auditoria"] = registro_despacho
        dossier["correo_enmascarado_lpdp"] = correo_enmascarado
        dossier["estado_gobernanza"] = "AUTORIZADO_Y_REGISTRADO"
        return dossier

    def _guardar_registro(self, registro: Dict[str, Any]):
        try:
            os.makedirs(os.path.dirname(self.ruta_log_despachos), exist_ok=True)
            historial = []
            if os.path.exists(self.ruta_log_despachos):
                with open(self.ruta_log_despachos, "r", encoding="utf-8") as f:
                    historial = json.load(f)
            historial.append(registro)
            with open(self.ruta_log_despachos, "w", encoding="utf-8") as f:
                json.dump(historial, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"No se pudo guardar registro de despacho: {e}")

    def consultar_historial_despachos(self) -> List[Dict[str, Any]]:
        """Retorna la lista de todos los despachos ejecutados con protección de datos personales."""
        if os.path.exists(self.ruta_log_despachos):
            try:
                with open(self.ruta_log_despachos, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

