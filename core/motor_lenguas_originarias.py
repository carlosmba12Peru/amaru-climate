"""
Módulo de Traducción y Despacho en Lenguas Originarias del Perú
Sistema AMARU-FEN - Cumplimiento Ley N° 29735 (Uso y Difusión de Lenguas Originarias)
Protección de la Seguridad Alimentaria y Agricultores de Última Milla (PMA / WFP - AFCIA)
"""
from typing import Dict, Any, Optional

class MotorLenguasOriginarias:
    """
    Genera alertas tempranas hiperlocalizadas en lenguas originarias oficiales del Perú
    (Quechua / Runasimi, Aimara y Castellano Agrícola) para pequeños agricultores,
    comunidades campesinas y operadores de compuertas (tomeros).
    """

    NIVELES_ALERTA_ORIGINARIAS = {
        "ROJO": {
            "qu": "PUKA WILLAKUY (Hatun Llaky)",
            "ay": "WILA YATIYAWI (Jach'a Ch'axwa)",
            "es": "ALERTA ROJA (Emergencia Inminente)"
        },
        "NARANJA": {
            "qu": "KILLU-PUKA WILLAKUY (Paqta Llaky)",
            "ay": "CHUPÍKA YATIYAWI (Amuyasiri)",
            "es": "ALERTA NARANJA (Preparación Activa)"
        },
        "AMARILLO": {
            "qu": "Q'ILLU WILLAKUY (Rikch'ariy)",
            "ay": "Q'ILLU YATIYAWI (Uñjasiñani)",
            "es": "ALERTA AMARILLA (Vigilancia Hidrológica)"
        }
    }

    @classmethod
    def generar_despacho_agricola_multilingue(
        cls,
        distrito: str,
        quebrada_nombre: str,
        t_lag_minutos: int,
        iph_score: float,
        nivel_alerta: str = "ROJO"
    ) -> Dict[str, Any]:
        """
        Genera el paquete trilingüe de alertas operativas formateado para:
        1. SMS de baja conectividad (menos de 160 caracteres).
        2. Mensajería Instantánea / WhatsApp Comunitario.
        3. Guion de Audio para Radio Comunitaria y Megáfonos de Alerta Local.
        """
        nivel = nivel_alerta.upper() if nivel_alerta.upper() in ["ROJO", "NARANJA", "AMARILLO"] else "ROJO"
        etiqueta_qu = cls.NIVELES_ALERTA_ORIGINARIAS[nivel]["qu"]
        etiqueta_ay = cls.NIVELES_ALERTA_ORIGINARIAS[nivel]["ay"]
        etiqueta_es = cls.NIVELES_ALERTA_ORIGINARIAS[nivel]["es"]

        # =========================================================================
        # 1. RUNASIMI / QUECHUA (Chanka / Collao / Central)
        # =========================================================================
        sms_quechua = (
            f"AMARU-FEN {etiqueta_qu}: {distrito}! Lloclla hamuchkan {quebrada_nombre} patapi ({t_lag_minutos} min). "
            f"Yarqa compuertata WICHQ'AY! Uywakunata pata urquman aysay!"
        )
        if len(sms_quechua) > 160:
            sms_quechua = sms_quechua[:157] + "..."

        whatsapp_quechua = f"""🚨 *AMARU-FEN — {etiqueta_qu}*
📍 *Llaqta:* {distrito} | *Mayu/Wayq'u:* {quebrada_nombre}
⏱️ *Chayamunan pacha (Tiempo estimado):* {t_lag_minutos} k'iti (minutos)
🌊 *Lloclla kallpa (Índice IPH):* {iph_score:.1f}%

⚡ *CHAYLLAPACHA RUWANAKUNA (Acciones Inmediatas):*
1️⃣ *Yarqa compuertata wichq'ay:* Lloclla qillita ama chakraman yaykuchunñachu.
2️⃣ *Uywakunata qispichiy:* Wakakunata, uwihakunata pata pampaman aysay.
3️⃣ *Wayq'u kantumanta anchuy:* Ama mayu patapi qhipakuychu.
4️⃣ *Ayllumasikunata willay:* Takiwan, qaparikuwan yanapanakuychik.

📻 *Willakuq:* AMARU-FEN & SINAGERD — Hatun Llaqta Kamachiq."""

        audio_radio_quechua = (
            f"Allillanchu masiykuna! AMARU-FEN willamusunkichik {distrito} llaqtapi: "
            f"Hatun lloclla hamuchkan {quebrada_nombre} wayq'unta. "
            f"{t_lag_minutos} k'iti minutosllatam chayamunqa. "
            f"Tukuy tomerokuna, chakrayuqkuna: yarqa compuertata utqayman wichq'amuychik! "
            f"Uywakunata pata urqukunaman aysaychik! Mayu patamanta lluqsiychik!"
        )

        # =========================================================================
        # 2. AYMAR ARU / AIMARA (Puno, Moquegua, Tacna)
        # =========================================================================
        sms_aimara = (
            f"AMARU-FEN {etiqueta_ay}: {distrito}! Juqhu/Llaqlla jutaskiw {quebrada_nombre} ({t_lag_minutos} min). "
            f"Larq'a punkunak jist'antam! Uywanak qulluru irptam!"
        )
        if len(sms_aimara) > 160:
            sms_aimara = sms_aimara[:157] + "..."

        whatsapp_aimara = f"""🚨 *AMARU-FEN — {etiqueta_ay}*
📍 *Marka:* {distrito} | *Jawira/Qullu:* {quebrada_nombre}
⏱️ *Pacha jutiwi (Tiempo estimado):* {t_lag_minutos} quta (minutos)
🌊 *Juqhu ch'ama (Índice IPH):* {iph_score:.1f}%

⚡ *JANK'AKI LURAÑANAKA (Acciones Inmediatas):*
1️⃣ *Larq'a punkunak jist'antaña:* Uma ch'iwxt'ata ama yapuru mantanpati.
2️⃣ *Uywanaka qulluru apaniña:* Wakanaka, iwisanaka qullunakaru irpañani.
3️⃣ *Jawira thiyanaka jaytjaña:* Jawira lakata anqaru jalsuñani.
4️⃣ *Ayllu jilat kullakanakaru yatiyaña:* Taqpachani mayacht'ata uñjasiñani.

📻 *Yatiyiri:* AMARU-FEN & SINAGERD — Jach'a Kamachiwi."""

        audio_radio_aimara = (
            f"Kamisaraki jilatanaka, kullakanaka! AMARU-FEN yatiyaskapxtam {distrito} markana: "
            f"Jach'a juqhu uma jutaskiw {quebrada_nombre} jawirnama. "
            f"{t_lag_minutos} k'ata minutonakawa puriskani. "
            f"Taqi yapuchirinaka: larq'a punkunaka jank'aki jist'antapxam! "
            f"Uywanaka qullu pataru irptapxam! Jawira thiyat mistupxam!"
        )

        # =========================================================================
        # 3. CASTELLANO AGRÍCOLA (Español para Juntas de Usuarios y Agricultores)
        # =========================================================================
        sms_castellano = (
            f"AMARU-FEN {etiqueta_es}: {distrito}! Huaico inminente en Qda {quebrada_nombre} ({t_lag_minutos} min). "
            f"CIERRE INMEDIATO DE BOCATOMAS y compuertas. Evacue ganado a partes altas."
        )
        if len(sms_castellano) > 160:
            sms_castellano = sms_castellano[:157] + "..."

        whatsapp_castellano = f"""🚨 *AMARU-FEN — {etiqueta_es}*
📍 *Distrito:* {distrito} | *Quebrada:* {quebrada_nombre}
⏱️ *Tiempo Estimado de Impacto (T_lag):* {t_lag_minutos} minutos
🌊 *Severidad de Activación (IPH):* {iph_score:.1f}%

⚡ *DIRECTIVAS INMEDIATAS PARA AGRICULTORES Y TOMEROS:*
1️⃣ *CIERRE URGENTE DE BOCATOMAS:* Cierre compuertas de captación para evitar colmatación de canales y destrucción de tomas.
2️⃣ *EVACUACIÓN DE GANADO Y MAQUINARIA:* Mueva bombas de agua, tractores y animales a terrazas altas.
3️⃣ *DESPEJE DEL CAUCE:* Prohibido el tránsito de personas en badenes, vados y fajas marginales.
4️⃣ *COMUNICACIÓN COMUNAL:* Alerte a los sectores aguas abajo mediante silbatos o grupos de WhatsApp.

📻 *Emisor:* AMARU-FEN Oráculo Hidrográfico | Ley N° 29664 (SINAGERD)."""

        audio_radio_castellano = (
            f"Atención vecinos y agricultores del valle de {distrito}. "
            f"El sistema AMARU-FEN emite ALERTA DE HUAICO INMINENTE en la quebrada {quebrada_nombre}. "
            f"Tiempo de llegada estimado en {t_lag_minutos} minutos. "
            f"Se ordena el cierre inmediato de todas las compuertas de captación y bocatomas de riego. "
            f"Ponga a buen recaudo a su ganado y aléjese de las orillas del río."
        )

        return {
            "distrito": distrito,
            "quebrada": quebrada_nombre,
            "t_lag_minutos": t_lag_minutos,
            "iph_score": iph_score,
            "nivel_alerta": nivel,
            "lenguas": {
                "quechua": {
                    "idioma": "Runasimi / Quechua",
                    "familia": "Quechua Chanka / Collao / Central",
                    "sms_160": sms_quechua,
                    "whatsapp": whatsapp_quechua,
                    "guion_audio_radio": audio_radio_quechua
                },
                "aimara": {
                    "idioma": "Aymar Aru / Aimara",
                    "familia": "Jaqui / Aimara Altiplánico",
                    "sms_160": sms_aimara,
                    "whatsapp": whatsapp_aimara,
                    "guion_audio_radio": audio_radio_aimara
                },
                "castellano": {
                    "idioma": "Castellano Agrícola",
                    "familia": "Español Claro",
                    "sms_160": sms_castellano,
                    "whatsapp": whatsapp_castellano,
                    "guion_audio_radio": audio_radio_castellano
                }
            },
            "marco_legal": "Ley N° 29735 (Lenguas Originarias del Perú) y Ley N° 29664 (SINAGERD)"
        }
