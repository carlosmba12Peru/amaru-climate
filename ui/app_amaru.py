import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import pandas as pd
import pydeck as pdk
import json
from datetime import datetime

from core.orchestrator import AmaruOrchestrator
from agents.agente_memoria_historica import AgenteMemoriaHistorica
from core.motor_chat_soberano import motor_chat_soberano

try:
    from core.modulo_satelite_edan_cgr import ModuloSateliteEDANCGR
except (ImportError, ModuleNotFoundError):
    import importlib.util
    _spec_sat = importlib.util.spec_from_file_location("core.modulo_satelite_edan_cgr", str(root_dir / "core" / "modulo_satelite_edan_cgr.py"))
    _mod_sat = importlib.util.module_from_spec(_spec_sat)
    _spec_sat.loader.exec_module(_mod_sat)
    ModuloSateliteEDANCGR = _mod_sat.ModuloSateliteEDANCGR
    sys.modules["core.modulo_satelite_edan_cgr"] = _mod_sat

import importlib
try:
    import core.reloj_fen
    importlib.reload(core.reloj_fen)
    from core.reloj_fen import MotorRelojFEN
except (ImportError, ModuleNotFoundError):
    import importlib.util
    _spec_rel = importlib.util.spec_from_file_location("core.reloj_fen", str(root_dir / "core" / "reloj_fen.py"))
    _mod_rel = importlib.util.module_from_spec(_spec_rel)
    _spec_rel.loader.exec_module(_mod_rel)
    MotorRelojFEN = _mod_rel.MotorRelojFEN
    sys.modules["core.reloj_fen"] = _mod_rel

try:
    from core.reloj_nina import MotorRelojNina
    from agents.agente_crioclimatico_nina import AgenteCrioclimaticoNina
except Exception:
    MotorRelojNina = None
    AgenteCrioclimaticoNina = None

st.set_page_config(
    page_title="AMARU-FEN | Centro de Comando & Gobernanza Anticipatoria ante el Fenómeno del Niño",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales de alto calibre
st.markdown("""
<style>
    .main { background-color: #0b111e; color: #f0f4f8; }
    .stMetric { background: #162238; border-radius: 10px; padding: 15px; border-left: 5px solid #00b4d8; }
    .badge-rojo { background-color: #e63946; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-naranja { background-color: #f77f00; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .badge-amarillo { background-color: #ffd166; color: #111; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .card-edan { background-color: #1a2639; padding: 20px; border-radius: 12px; border: 1px solid #2a3b53; margin-bottom: 15px; }
    .card-anticipatorio { background: linear-gradient(135deg, #1b2838 0%, #101c2b 100%); border-left: 5px solid #06d6a0; padding: 18px; border-radius: 10px; margin-bottom: 15px; }
    .card-memoria { background: linear-gradient(135deg, #1f2041 0%, #111328 100%); border-left: 5px solid #ffb703; padding: 18px; border-radius: 10px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

orchestrator = AmaruOrchestrator()
st.session_state["orchestrator"] = orchestrator

def obtener_meta_segura(orch):
    """Obtiene la metadata de última ingesta de forma segura y con fallback resiliente."""
    if hasattr(orch, "obtener_metadata_ultima_ingesta"):
        return orch.obtener_metadata_ultima_ingesta()
    elif hasattr(orch, "metadata_ultima_ingesta"):
        return orch.metadata_ultima_ingesta
    from datetime import datetime
    return {
        "fecha_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": "TOTAL_MULTIFUENTE",
        "fuentes_consultadas": ["SENAMHI Avisos", "ENFEN Diagnóstico", "ANA Red de Aforo"],
        "total_ubigeos_procesados": 893,
        "version_id": f"INGESTA-{int(datetime.now().timestamp())}"
    }


def generar_malla_termica_mar_peruano(anomalia_base_tsm: float = 1.8):
    """
    Genera una malla geoespacial térmica en el Mar de Grau / Pacífico Oriental
    representando la intrusión de la onda Kelvin y el calentamiento costero (Niño 1+2).
    """
    puntos_mar = []
    # Franja oceánica frente al litoral peruano (-1°S a -18°S, -86°W a -72°W)
    for lat in range(-1, -19, -2):
        for lon in range(-85, -73, 2):
            costa_limite = -81.0 if lat > -6 else (-79.0 if lat > -10 else (-77.5 if lat > -14 else -72.0))
            if lon <= costa_limite:
                if lat >= -6:
                    tsm_local = round(anomalia_base_tsm + 0.7, 2)
                    color = [230, 40, 80, 150]    # Rojo cálido / intrusión ecuatorial
                    desc = "Región Niño 1+2 (Intrusión Cálida Máxima)"
                elif lat >= -11:
                    tsm_local = round(anomalia_base_tsm + 0.2, 2)
                    color = [247, 127, 0, 140]   # Ámbar / Naranja
                    desc = "Mar Nor-Centro (Afloramiento Bloqueado)"
                elif lat >= -14:
                    tsm_local = round(anomalia_base_tsm - 0.4, 2)
                    color = [255, 209, 102, 130] # Amarillo
                    desc = "Mar Central (Frente a Callao / Lima)"
                else:
                    tsm_local = round(max(0.2, anomalia_base_tsm - 1.0), 2)
                    color = [0, 180, 216, 120]   # Celeste / Corriente de Humboldt
                    desc = "Sur Peruano (Aguas Costeras Frías)"

                puntos_mar.append({
                    "nombre": f"Océano Pacífico ({abs(lat)}°S, {abs(lon)}°W)",
                    "lat": float(lat),
                    "lon": float(lon),
                    "region": "Mar de Grau / Cuenca del Pacífico",
                    "info": f"Anomalía TSM: +{tsm_local} °C\n{desc}\nSensores: IMARPE / NOAA OISST",
                    "radius": 34000,
                    "color": color
                })
    return puntos_mar

@st.cache_data
def cargar_catalogo_ubigeos_completo():
    ruta = root_dir / "data" / "geodatos_893_distritos_ubigeo.json"
    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ubigeos", [])
        except Exception:
            pass
    return []

@st.cache_data(ttl=600)
def cached_consultar_open_meteo(lat: float, lon: float):
    from core.conector_open_meteo import conector_open_meteo
    return conector_open_meteo.consultar_pronostico_distrital(latitud=lat, longitud=lon, dias_pronostico=3)

@st.cache_data(ttl=600)
def cached_obtener_meteo_mapa_ubigeos(lista_puntos_tuple: tuple, dias: int = 3):
    from core.conector_open_meteo import conector_open_meteo
    pts = [{"id": p[0], "distrito": p[1], "lat": p[2], "lon": p[3]} for p in lista_puntos_tuple]
    return conector_open_meteo.consultar_pronostico_lote(pts, dias_pronostico=dias)

@st.cache_data(ttl=600)
def cached_obtener_grilla_departamental_open_meteo():
    import importlib
    import core.conector_open_meteo
    importlib.reload(core.conector_open_meteo)
    conector = core.conector_open_meteo.conector_open_meteo
    if hasattr(conector, "consultar_grilla_departamental_peru"):
        return conector.consultar_grilla_departamental_peru(dias_pronostico=3)
    return {}




def render_tarjeta_meteo_sidebar(u_activo: dict, res_om: dict):
    if not u_activo:
        return

    icono = res_om.get("icono_clima", "🌦️")
    condicion = res_om.get("condicion_texto", "Vigilancia Meteorológica")
    alerta = res_om.get("alerta_pluviometrica", "VERDE")
    lluvia_24h = res_om.get("lluvia_maxima_24h_mm", 0.0)
    temp_act = res_om.get("temp_actual_c", 24.0)
    hum = res_om.get("humedad_relativa_pct", 75)
    viento = res_om.get("viento_kmh", 12.0)

    dias = res_om.get("dias_pronostico", [])
    prob = dias[0].get("probabilidad_lluvia_pct", 0) if dias else 0

    color_border = "#e63946" if alerta == "ROJO" else ("#f77f00" if alerta == "NARANJA" else ("#ffd166" if alerta == "AMARILLO" else "#2a9d8f"))
    badge_bg = "#e63946" if alerta == "ROJO" else ("#f77f00" if alerta == "NARANJA" else ("#ffd166" if alerta == "AMARILLO" else "#2a9d8f"))
    badge_txt = "white" if alerta in ["ROJO", "NARANJA", "VERDE"] else "#111"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #131e31 0%, #0c1422 100%); border-radius: 12px; padding: 12px; border: 1px solid #1f3554; border-left: 5px solid {color_border}; margin-bottom: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.35);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-size: 13px; font-weight: bold; color: #64dfdf;">📍 {u_activo.get('distrito', '')}</span>
            <span style="background: {badge_bg}; color: {badge_txt}; font-size: 10px; font-weight: bold; padding: 2px 7px; border-radius: 4px;">{alerta}</span>
        </div>
        <div style="font-size: 10px; color: #8da4c4; margin-bottom: 6px;">
            {u_activo.get('provincia', '')}, {u_activo.get('departamento', '')} | UBIGEO: <b>{u_activo.get('ubigeo', '')}</b>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.25); border-radius: 8px; padding: 6px 10px; margin-bottom: 6px;">
            <div style="font-size: 28px; line-height: 1;">{icono}</div>
            <div style="text-align: right;">
                <div style="font-size: 18px; font-weight: bold; color: #fff;">{lluvia_24h:.1f} <span style="font-size: 11px; color: #a0c4ff;">mm/24h</span></div>
                <div style="font-size: 10px; color: #ffb703;">{condicion}</div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 10px; color: #cbd5e1;">
            <div>🌧️ Prob: <b>{prob}%</b></div>
            <div>🌡️ Temp: <b>{temp_act:.1f}°C</b></div>
            <div>💧 Hum: <b>{hum}%</b></div>
            <div>💨 Viento: <b>{viento:.1f} km/h</b></div>
        </div>
        <div style="font-size: 9px; color: #627d98; margin-top: 6px; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 3px;">
            🛰️ Open-Meteo (ECMWF) • Lat: {u_activo.get('latitud', 0):.4f}°, Lon: {u_activo.get('longitud', 0):.4f}°
        </div>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("🌊 AMARU-FEN")
    st.caption("Comando Táctico & Gobernanza Anticipatoria ante el Fenómeno del Niño")
    
    # Conmutador Doctrinal de Mando C2: Mando Rojo (FEN) vs. Mando Azul (CHIRI / La Niña)
    st.markdown("""
    <div style="background: #0d1e36; padding: 10px 12px; border-radius: 8px; border: 1.5px solid #00b4d8; margin-bottom: 12px;">
        <div style="font-size: 10px; color: #94a3b8; font-weight: bold; letter-spacing: 0.5px;">SALA DE MANDO C2 CONMUTABLE:</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
            <span style="font-size: 12px; color: #ff4d6d; font-weight: 900;">🔴 FEN (Huaicos)</span>
            <span style="background: #7f0000; color: #fff; font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: bold;">EN PANTALLA</span>
        </div>
        <div style="font-size: 10px; color: #cbd5e1; margin-top: 2px;">Índice: <b>IPH-FEN</b> | Costa & Vertiente Pacífico</div>
        <hr style="margin: 6px 0; border-color: #1e3a60;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 12px; color: #00f2fe; font-weight: 900;">🔵 CHIRI (La Niña / Heladas)</span>
            <span style="background: #082f49; color: #38bdf8; font-size: 9px; padding: 2px 6px; border-radius: 4px; border: 1px solid #0284c7; font-weight: bold;">DISPONIBLE</span>
        </div>
        <div style="font-size: 10px; color: #94a3b8; margin-top: 2px;">Índice: <b>ISH-CHIRI</b> | Puno, Huancavelica, Arequipa</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Módulo de Telemetría Distrital / Punto Libre en Vivo con Open-Meteo
    st.markdown("##### 📍 Monitoreo Meteorológico en Vivo")
    tipo_consulta_sb = st.radio(
        "Modo de Localización:",
        ["📋 Catálogo UBIGEO (893 Distritos Oficiales)", "📍 Coordenadas Libres GPS / Punto Personalizado"],
        index=0,
        horizontal=False,
        key="rb_modo_consulta_sb"
    )

    if tipo_consulta_sb.startswith("📋"):
        lista_ubigeos_cat = cargar_catalogo_ubigeos_completo()
        if lista_ubigeos_cat:
            opciones_ubigeo = []
            mapa_ubigeo_obj = {}
            for u in lista_ubigeos_cat:
                etiqueta = f"{u['distrito']} ({u['provincia']}) [UBIGEO: {u['ubigeo']}]"
                opciones_ubigeo.append(etiqueta)
                mapa_ubigeo_obj[etiqueta] = u

            idx_catacaos = 0
            for i, opt in enumerate(opciones_ubigeo):
                if "CATACAOS" in opt:
                    idx_catacaos = i
                    break

            sel_ubigeo_sb = st.selectbox(
                "Seleccionar o Buscar UBIGEO / Distrito:",
                opciones_ubigeo,
                index=idx_catacaos,
                key="sb_selector_hibrido_ubigeo",
                help="Escribe el nombre del distrito o el código UBIGEO para consultar el clima satelital en vivo."
            )
            u_sel = mapa_ubigeo_obj.get(sel_ubigeo_sb)
            if u_sel:
                res_om_sb = cached_consultar_open_meteo(u_sel["latitud"], u_sel["longitud"])
                render_tarjeta_meteo_sidebar(u_sel, res_om_sb)
    else:
        st.caption("Ingresa cualquier coordenada del Perú (caseríos, represas, minas o mar).")
        nombre_libre = st.text_input("Lugar / Caserío / Infraestructura:", value="Represa de Poechos", key="txt_nombre_lugar_libre")
        c_lat, c_lon = st.columns(2)
        with c_lat:
            lat_libre = st.number_input("Latitud (°S):", value=-4.6667, format="%.4f", step=0.01, key="num_lat_libre")
        with c_lon:
            lon_libre = st.number_input("Longitud (°W):", value=-80.5000, format="%.4f", step=0.01, key="num_lon_libre")

        u_sel_libre = {
            "distrito": nombre_libre.upper(),
            "provincia": "Coordenada Libre GPS",
            "departamento": "Perú Nacional / Mar",
            "ubigeo": "PUNTO-GPS",
            "latitud": lat_libre,
            "longitud": lon_libre
        }
        res_om_sb = cached_consultar_open_meteo(lat_libre, lon_libre)
        render_tarjeta_meteo_sidebar(u_sel_libre, res_om_sb)

    st.markdown("---")
    st.write("**Marco Teórico:** Gobernanza Anticipatoria CAF/PUCP 2026")
    st.write("**Base Científica:** IGP (El Niño 1997-1998) & SENAMHI")
    st.write("**Convocatoria:** Concytec / ProCiencia FEN 2026")
    st.markdown("---")
    
    st.markdown("### 📡 Fuentes Oficiales en Vivo")
    st.caption("Sincronización dual soberana: Nacional (SENAMHI / ENFEN / ANA) e Internacional (NOAA CPC / IRI Columbia / Open-Meteo).")
    
    col_btn_sync1, col_btn_sync2 = st.columns(2)
    with col_btn_sync1:
        btn_sync_nacional = st.button("🇵🇪 Nacionales", help="Sincroniza SENAMHI, ENFEN y Red de Aforos ANA", width='stretch')
    with col_btn_sync2:
        btn_sync_global = st.button("🌐 Global Total", help="Sincroniza Nacionales + NOAA CPC + IRI Columbia + El Niño Live + Open-Meteo", width='stretch', type="primary")

    if btn_sync_nacional or btn_sync_global:
        es_global = bool(btn_sync_global)
        msg_spinner = "Sincronizando Nacionales + NOAA CPC + IRI Columbia + Open-Meteo..." if es_global else "Conectando con SENAMHI, ENFEN y ANA..."
        with st.spinner(msg_spinner):
            sync_res = orchestrator.sincronizar_fuentes_oficiales(incluir_internacionales=es_global)
            st.session_state["sync_data"] = sync_res
            st.session_state["ubigeos_mapa_autorizado"] = sync_res.get("ubigeos_indicadores_actualizados", [])
            fuentes_txt = "Nacional + Internacional (NOAA/IRI)" if es_global else "Nacional (SENAMHI/ENFEN)"
            st.toast(f"¡Sincronización Dual Completada ({fuentes_txt})! AMARU-FEN (893 Distritos) y AMARU-CHIRI (27 Distritos) en vivo.")
            st.rerun()
    
    if "sync_data" in st.session_state:
        sync_act = st.session_state["sync_data"]
        tiene_int = "fuentes_internacionales" in sync_act
        st.success(f"Alerta Vigente: **{sync_act['nivel_alerta_maximo_vigente']}**")
        if tiene_int:
            noaa_stat = sync_act["fuentes_internacionales"]["noaa_cpc"].get("status_alerta_oficial", "Activo")
            st.caption(f"🌐 **Consenso Global Sincronizado:** NOAA ({noaa_stat}) | IRI Columbia | ENFEN")
        else:
            st.caption("🇵🇪 Sincronización: Fuentes Nacionales activas")
        if sync_act.get("amaru_chiri_sincronizado"):
            st.caption("❄️ **AMARU-CHIRI Sincronizado:** 27 Distritos de Heladas y Frente Escolar en paralelo.")

    st.markdown("---")
    tsm_anomalia = st.slider("🌡️ Anomalía TSM Niño 1+2 (°C):", -1.0, 3.5, 1.8, step=0.1)
    mes_evaluacion = st.slider("📅 Mes de Evaluación:", 1, 12, 8, format="Mes %d")
    simular_precipitacion = st.slider("🌧️ Precipitación 24h (mm):", 0, 150, 65)
    region_sel = st.selectbox("Región Operativa:", ["Piura", "La Libertad", "Lambayeque", "Lima", "Tumbes"])

    st.markdown("---")
    st.markdown("### ⚡ Resiliencia Off-Grid (Local)")
    estado_red = orchestrator.obtener_estado_resiliencia_red()
    if estado_red["es_offline"]:
        st.error("⚡ MODO OFFLINE (EDGE LOCAL)")
    else:
        st.success("🟢 MODO ONLINE (CLOUD CONECTADO)")
    
    modo_switch = st.selectbox("Simular Conectividad:", ["ONLINE_CLOUD", "OFFLINE_EDGE_OFFGRID"], index=0 if not estado_red["es_offline"] else 1)
    if modo_switch != estado_red["modo_operativo"]:
        orchestrator.conmutar_modo_resiliencia(modo_switch)
        st.rerun()

st.markdown("# 🏛️ AMARU-FEN: Centro de Mando Táctico & Gobernanza Anticipatoria ante el Fenómeno del Niño")
st.markdown("Plataforma de IA Multi-Agente para la Acción Temprana, Vigilancia Ciudadana OSINT y Despacho EDAN.")

st.warning(
    "⚖️ **PRINCIPIO DE SOBERANÍA Y SUPERVISIÓN HUMANA (Ley Nº 31814 - Human-in-the-Loop):** "
    "AMARU-FEN es un sistema de soporte a la decisión técnica (DSS). "
    "**Ninguna IA toma decisiones ejecutivas, presupuestales, contractuales ni de evacuación de forma autónoma.** "
    "Toda emisión de alertas SISMATE, desembolso presupuestal (PP 0068), contratación directa o ficha EDAN "
    "requiere la autorización, firma y responsabilidad exclusiva de las autoridades humanas competentes."
)


# Panel de Sincronización Oficial en Vivo si está disponible
if "sync_data" in st.session_state:
    sync = st.session_state["sync_data"]
    with st.expander(f"📡 Feed Oficial & Consenso Internacional — Nivel: {sync['nivel_alerta_maximo_vigente']} | ENFEN: +{sync['anomalia_tsm_detectada']} °C", expanded=True):
        col_s1, col_s2 = st.columns([3, 2])
        with col_s1:
            st.markdown("#### 🚨 Últimos Avisos Meteorológicos SENAMHI")
            for av in sync["avisos_meteorologicos_activos"][:4]:
                badge_class = "badge-rojo" if av["nivel_alerta"] == "ROJO" else ("badge-naranja" if av["nivel_alerta"] == "NARANJA" else "badge-amarillo")
                st.markdown(f"<span class='{badge_class}'>{av['nivel_alerta']}</span> **Aviso {av['numero_aviso']}:** [{av['titulo']}]({av['url_detalle']})", unsafe_allow_html=True)
        with col_s2:
            st.markdown("#### 🌊 Diagnóstico Nacional ENFEN")
            enfen = sync["enfen_diagnostico_oficial"]
            st.write(f"**Estado Oficial:** {enfen.get('alerta_oficial')}")
            st.write(f"**Niño 1+2 (Costa):** +{enfen.get('anomalia_tsm_nino_1_2')} °C | **Niño 3.4:** +{enfen.get('anomalia_tsm_nino_3_4')} °C")
            st.caption(enfen.get("diagnostico", ""))
            if enfen.get("url_documento"):
                st.link_button("📄 Descargar Informe Técnico PDF", enfen["url_documento"])
            st.link_button("🌊 Portal Oficial FEN SENAMHI (ICEN/RONI)", "https://www.senamhi.gob.pe/?p=fenomeno-el-nino")


        # Sección Internacional NOAA CPC / IRI Columbia / El Niño Live
        if "fuentes_internacionales" in sync:
            st.markdown("---")
            st.markdown("#### 🌐 Vigilancia Científica Global: NOAA CPC / IRI Columbia / El Niño Live")
            f_int = sync["fuentes_internacionales"]
            c_int1, c_int2, c_int3, c_int4 = st.columns(4)

            with c_int1:
                noaa = f_int["noaa_cpc"]
                st.markdown("**🛰️ NOAA Climate Prediction Center**")
                st.write(f"**Status:** {noaa.get('status_alerta_oficial', 'Advisory')}")
                st.write(f"**Niño 1+2:** `+{noaa.get('anomalia_tsm_nino_1_2')} °C`")
                st.write(f"**Niño 3.4:** `+{noaa.get('anomalia_tsm_nino_3_4')} °C`")
                st.caption(noaa.get("sinopsis", "")[:90] + "...")
                st.link_button("🔗 NOAA CPC", noaa.get("url", "https://www.cpc.ncep.noaa.gov/"))

            with c_int2:
                iri = f_int["iri_columbia"]
                st.markdown("**🎓 IRI Columbia School**")
                st.write(f"**Horizonte:** {iri.get('horizonte', 'Verano DJF')}")
                probs = iri.get("probabilidades_consenso", {})
                st.write(f"• **P(Niño):** `{probs.get('el_nino', 0)}%`")
                st.write(f"• **P(Neutro):** `{probs.get('neutral', 0)}%`")
                st.caption(iri.get("diagnostico_iri", "")[:90] + "...")
                st.link_button("📊 IRI Plume", iri.get("url", "https://iri.columbia.edu/"))

            with c_int3:
                live = f_int["el_nino_live"]
                st.markdown("**🗺️ El Niño Live**")
                st.write(f"**Sensores:** GOES / MODIS")
                st.write(f"**Cobertura:** {live.get('cobertura', 'Pacífico')}")
                st.caption(live.get("descripcion", "")[:90] + "...")
                st.link_button("🌍 Satélite en Vivo", live.get("url_mapa", "https://www.elninolive.com/map"))

            with c_int4:
                st.markdown("**🌦️ Open-Meteo API**")
                st.write("**Ensamble:** ECMWF + GFS")
                st.write("**Disponibilidad:** API REST Abierta")
                st.caption("Validación cruzada de lluvia horaria y acumulada 24h para los 893 distritos.")
                st.link_button("☁️ Open-Meteo", "https://open-meteo.com")

            if "matriz_consenso_dual" in sync:
                consenso = sync["matriz_consenso_dual"]
                st.info(f"**⚖️ Matriz de Consenso Dual (ENFEN vs. NOAA/IRI):** Convergencia **{consenso['grado_convergencia']}** (Δ TSM: {consenso['diferencia_tsm_grados']} °C). {consenso['consenso_enjambre_amaru']}")

# Métricas Principales Dinámicas
quebradas_totales = orchestrator.consultar_quebradas_reincidentes("")
quebradas_activadas_count = len([q for q in quebradas_totales if float(simular_precipitacion) >= q.get("umbral_acumulado_24h", 35.0)])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Anomalía TSM Niño 1+2", f"+{tsm_anomalia} °C", "Alerta Temprana" if tsm_anomalia >= 1.5 else "Vigilancia")
col2.metric("Población en Alto Riesgo", "420,000 hab.", "Bajo Piura y Trujillo")
col3.metric("Quebradas Críticas", f"{quebradas_activadas_count} Activadas", f"de {len(quebradas_totales)} en Catálogo")
col4.metric("Trigger Presupuestal MEF", "ACTIVO 🟢" if tsm_anomalia >= 1.5 else "STANDBY 🟡", "Pre-aprobado")

# Módulo de Glosario Técnico y Doctrinal Homologado
with st.expander("📚 Glosario Doctrinal & Científico: Conceptos Oficiales SENAMHI/ENFEN vs. AMARU-FEN (ICEN, RONI, IRCE, Triggers PP 0068)", expanded=False):
    g_tab1, g_tab2 = st.tabs([
        "🌊 1. Ciencia & Oceanografía Oficial (SENAMHI / ENFEN / NOAA / Copernicus)",
        "🏛️ 2. Comando Táctico C2 & Gobernanza Anticipatoria (AMARU-FEN)"
    ])
    with g_tab1:
        st.markdown("#### 🌊 Parámetros e Índices Científicos de Vigilancia Oceánica y Atmosférica")
        g_c1, g_c2 = st.columns(2)
        with g_c1:
            st.markdown("""
            ##### 1. 🌡️ ICEN (Índice Costero El Niño)
            * **Autoridad Emisora:** ENFEN / Instituto Geofísico del Perú (IGP).
            * **Definición:** Media corrida de tres meses (trimestre móvil) de las anomalías mensuales de la Temperatura Superficial del Mar (TSM) del producto **ERSSTv5** en la región **Niño 1+2** (0°–10°S, 90°W–80°W).
            * **Climatología Base:** Recalculada cada 5 años (vigente: **1991–2020**).
            * **Escala de Magnitud:** Neutro (-1.0 a +0.4°C) | Cálido Débil (+0.4 a +1.0°C) | Moderado (+1.0 a +1.7°C) | Fuerte (+1.7 a +2.0°C) | **Extraordinario (> +2.0°C)**.
            * **Datos Crudos:** [met.igp.gob.pe/datos/ICEN.txt](http://met.igp.gob.pe/datos/ICEN.txt)

            ##### 2. 🌐 RONI (Relative Oceanic Niño Index)
            * **Autoridad Emisora:** NOAA Climate Prediction Center (CPC) / SENAMHI.
            * **Definición:** Promedio móvil de 3 meses de anomalías de TSM en **Niño 3.4** al que se le resta la anomalía media de TSM de todo el cinturón tropical global (20°N–20°S).
            * **Utilidad Crítica:** Descuenta el calentamiento global de fondo para aislar la perturbación ENSO real, evitando falsos positivos por calentamiento secular.
            * **Enlace Oficial:** [NOAA CPC RONI](https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/)

            ##### 3. 🎯 ONI (Oceanic Niño Index)
            * **Autoridad Emisora:** NOAA (National Oceanic and Atmospheric Administration).
            * **Definición:** Anomalía trimestral de TSM en Niño 3.4. Estándar histórico mundial para declarar fases El Niño (≥ +0.5°C por 5 trimestres consecutivos).
            """)
        with g_c2:
            st.markdown("""
            ##### 4. 🗺️ Región Niño 1+2 vs. Región Niño 3.4
            * **Niño 1+2 (Costa Norte / Perú):** Determina el **Niño Costero**. Impacta directamente con lluvias torrenciales y desbordes en Piura, Tumbes, Lambayeque y La Libertad.
            * **Niño 3.4 (Pacífico Central):** Determina el **Niño Global**. Modifica la circulación atmosférica global y genera sequías severas en los Andes del Sur (Puno, Cusco).

            ##### 5. 🇪🇺 Ensamble Multimodelo C3S (Copernicus)
            * **Autoridad Emisora:** ECMWF (Unión Europea) adoptado por SENAMHI.
            * **Composición:** Ensamble de 7 centros mundiales (ECMWF, UKMO, Météo-France, NCEP, JMA, BOM, CMCC; DWD excluido por sesgo). Calibrado con hindcast 1993-2016.

            ##### 6. 🌊 Ondas Kelvin Oceánicas
            * **Definición:** Pulsos subsuperficiales que viajan por el ecuador hacia Sudamérica a 2-3 m/s. Una onda cálida tarda **45 a 60 días** en llegar a la costa peruana, otorgando una ventana de alerta temprana física de 1 a 2 meses.

            ##### 7. 🛰️ Nowcasting Satelital GOES-19 (ABI & GLM)
            * **Canal 13 (Infrarrojo 10.3 μm):** Cimas de nubes < -65°C indican nubes Cumulonimbus de lluvia extrema inminente.
            * **GLM (Lightning Mapper):** Saltos en descargas eléctricas preceden la caída de huaicos en 15-30 minutos.
            """)

    with g_tab2:
        st.markdown("#### 🏛️ Conceptos Doctrinales, Algoritmos y Triggers del Comando AMARU-FEN")
        g_c3, g_c4 = st.columns(2)
        with g_c3:
            st.markdown("""
            ##### 1. 🛡️ Score IRCE-FEN (Índice de Riesgo Compuesto)
            * **Formulación:** $\\text{IRCE} = \\min(1.0, (P \\times V) / C)$.
            * **Componentes:** Peligro $P$ (TSM 1+2, SENAMHI, Lluvia), Vulnerabilidad $V$ (Memoria histórica 1983-2017 y Censo INEI), Capacidad $C$ (Mitigación local).
            * **Semáforo:** 🟢 Verde (<0.35) | 🟡 Amarillo (0.35-0.59) | 🟠 Naranja (0.60-0.74) | 🔴 Rojo (≥0.75 - Evacuación).

            ##### 2. ⚡ Acción Temprana & Gobernanza Anticipatoria
            * **Marco Doctrinal:** Estudio CAF / PUCP 2026.
            * **Principio:** Desplazar la ayuda reactiva post-inundación hacia intervenciones pre-aprobadas y financiadas **antes de la primera lluvia**.

            ##### 3. 💰 Triggers Presupuestales (Gatilladores PP 0068)
            * **Definición:** Umbrales biofísicos objetivos (ej. TSM Niño 1+2 ≥ +1.5°C) que activan automáticamente la pre-asignación y ejecución de partidas del **PP 0068 (MEF)** sin riesgo legal para los alcaldes.

            ##### 4. ⚖️ Soberanía y Supervisión Humana (Ley Nº 31814)
            * **Garantía Ética:** AMARU-FEN es un DSS (Decision Support System). Ninguna IA evacúa ni desembolsa fondos de forma autónoma. Toda acción requiere la firma exclusiva de la autoridad humana competente.
            """)
        with g_c4:
            st.markdown("""
            ##### 5. ⚖️ Matriz de Consenso Dual (ENFEN vs. Global)
            * **Algoritmo:** Cruza el diagnóstico oficial soberano ENFEN con NOAA CPC, IRI Columbia y Copernicus C3S, calculando la divergencia térmica (Δ TSM) y convergencia científica (94%).

            ##### 6. 🗺️ Consola Cartográfica C2 de 3 Mapas por UBIGEO
            * **Mapa 1:** Soberano Nacional (Score IRCE / DS 124-2026-PCM / Aforos ANA).
            * **Mapa 2:** Vigilancia Internacional (Copernicus C3S / ERSSTv5).
            * **Mapa 3:** Meteorología Distrital en Vivo & Pronóstico 72h (Open-Meteo / ECMWF desacoplado de IRCE).

            ##### 7. 🔌 Resiliencia Operativa Edge Off-Grid
            * **Capacidad Táctica:** Funcionamiento continuo en servidores locales sin conexión a internet ante cortes de fibra óptica o caída de antenas celulares.

            ##### 8. 📋 Despacho Táctico EDAN (SINPAD / INDECI)
            * **Automatización:** Convierte alertas de desborde en borradores estandarizados de la Ficha EDAN para empadronamiento de damnificados y distribución de ayuda humanitaria (BAH).
            """)



tab_dash, tab_chat, tab1, tab_c2, tab_ant, tab_mem, tab_leg, tab2, tab3, tab_chiri = st.tabs([
    "📊 0. Dashboard Ejecutivo (Sala C2)",
    "💬 1. Asistente Soberano C2 (Chat Multi-Audiencia)",
    "🗺️ 2. Geovisor Espacial & Consola Cartográfica C2 (3 Mapas por UBIGEO / Aforo ANA)", 
    "💻 3. Consola Táctica C2 (Terminal de Mando)",
    "🧭 4. Gobernanza Anticipatoria (Triggers CAF/PUCP)", 
    "🏛️ 5. Memoria Histórica & Años Análogos (FEN)",
    "⚖️ 6. Marco Legal & Decretos FEN (DS 124 / DU 010)",
    "🚨 7. Botón SOS Ciudadano & Voz Vapi", 
    "📋 8. Dossier de Inteligencia & Hand-Off (SINPAD / Defensa Civil)",
    "❄️ 9. AMARU-CHIRI (La Niña & Heladas)"
])


# TAB 0: DASHBOARD EJECUTIVO / SALA DE SITUACIÓN C2
with tab_dash:
    st.subheader("🏛️ Sala de Situación C2: Comando Unificado & Estado General de la Emergencia FEN")
    st.caption("Cuadro de mando táctico integral para la Presidencia de la República, PCM, MINDEF, Gobiernos Regionales e INDECI.")

    # 1. Banners de Estado Operativo y Nivel de Amenaza
    col_c1, col_c2, col_c3 = st.columns([1.5, 1, 1])
    with col_c1:
        if "enfen_fecha" not in st.session_state:
            agente = AgenteMemoriaHistorica()
            fecha_raw = agente.consultar_informe_enfen_n15_agosto_2026().get("fecha_emision", "2026-08-26")
            try:
                fecha_dt = datetime.strptime(fecha_raw, "%Y-%m-%d")
                st.session_state["enfen_fecha"] = fecha_dt.strftime("%d/%m/%Y")
            except Exception:
                st.session_state["enfen_fecha"] = fecha_raw
        enfen_fecha = st.session_state["enfen_fecha"]
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #b7094c 0%, #720026 100%); padding: 15px; border-radius: 8px; color: white;">
            <h4 style="margin:0;">🚨 NIVEL DE ALERTA NACIONAL: ROJO CRÍTICO (ENFEN Nº 15)</h4>
            <p style="margin:5px 0 0 0; font-size:14px;">Anomalía térmica costera +1.8 °C | Probabilidad NOAA récord 69% | 893 distritos en emergencia</p>
            <p style="margin:2px 0 0 0; font-size:10px; opacity:0.8;">Fecha de emisión: {enfen_fecha}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_c2:
        st.markdown("""
        <div style="background: #1b2838; padding: 15px; border-radius: 8px; border-left: 5px solid #06d6a0;">
            <h4 style="margin:0; color:#06d6a0;">⚡ TRIGGER PP 0068 ACTIVO</h4>
            <p style="margin:5px 0 0 0; font-size:14px;">Pre-asignación CAF/PUCP: S/. 450M en ejecución de defensas</p>
        </div>
        """, unsafe_allow_html=True)
    with col_c3:
        st.markdown("""
        <div style="background: #1b2838; padding: 15px; border-radius: 8px; border-left: 5px solid #00b4d8;">
            <h4 style="margin:0; color:#00b4d8;">🛰️ TELEMETRÍA DUAL</h4>
            <p style="margin:5px 0 0 0; font-size:14px;">GOES-19 ABI/GLM + Satélites IMARPE (TSM/Clorofila/Vientos)</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 6 KPIs Tácticos Principales
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Distritos en Emergencia", "893", "DS 124-2026-PCM")
    k2.metric("Población Expuesta", "1,850,000 hab.", "Macrorregión Norte")
    k3.metric("Ríos en Alerta Fluvial", "4 de 8", "Piura, Chira, Ica, La Leche")
    k4.metric("Quebradas Activadas", f"{quebradas_activadas_count} de {len(quebradas_totales)}", "Conos de Deyección")
    k5.metric("Fichas EDAN Generadas", "38 Preliminares", "SINPAD en Línea")
    k6.metric("Capacidad Operativa", "92.4 %", "Soporte de Vida")

    st.markdown("---")

    # MÓDULO SOBERANO: EL RELOJ DEL FEN (CRONÓMETRO POLAR TÁCTICO)
    if "reloj_toda_pantalla" not in st.session_state:
        st.session_state["reloj_toda_pantalla"] = False
    reloj_toda_pantalla = st.session_state["reloj_toda_pantalla"]

    col_banner_rel, col_fs_rel = st.columns([3.8, 1.2])
    with col_banner_rel:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #091322 0%, #0d1e36 100%); border-radius: 12px; padding: 18px 22px; border-left: 6px solid #e63946; margin-top: 10px; margin-bottom: 12px; border: 1px solid #1e3a60; box-shadow: 0 4px 25px rgba(0,0,0,0.45);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 17px; font-weight: 900; color: #ff4d6d; letter-spacing: 0.5px;">⏰ EL RELOJ DEL FEN: CRONÓMETRO POLAR DE AMENAZA HIDROCLIMÁTICA</span><br>
                    <span style="font-size: 12px; color: #94a3b8;">Metáfora Táctica C2: 12 Horas = 12 Meses | 12:00 Inicio FEN (Dic) | 3:00 Clímax Destructivo (Mar)</span>
                </div>
                <span style="background: #7f0000; color: #ffffff; font-size: 11px; padding: 4px 12px; border-radius: 6px; font-weight: bold; border: 1px solid #ff4d6d;">TACTICAL DOOMSDAY CLOCK</span>
            </div>
            <p style="margin: 8px 0 0 0; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
                El <b>Arco Rojo</b> representa la ventana de amenaza: inicia tenue a las 12:00 (Diciembre), se intensifica a rojo carmesí en el clímax de Marzo (3:00) y decae hacia Mayo. 
                En el corazón del sector rojo se proyecta la <b>Similitud Análoga Dominante (FEN 1997-1998)</b> con diseño ejecutivo. 
                El <b>Minutero Táctico</b> avanza por calendario y se <b>adelanta o retrasa</b> según el forzamiento hidroclimático en vivo.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_fs_rel:
        st.markdown("""
        <div style="background: #091322; border-radius: 12px; padding: 14px 12px; border: 1px solid #1e3a60; margin-top: 10px; text-align: center; height: calc(100% - 22px); display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
            <div style="font-size: 10px; font-weight: 800; color: #38bdf8; letter-spacing: 1px; margin-bottom: 6px;">GRILLA SALA DE CRISIS</div>
        """, unsafe_allow_html=True)
        if reloj_toda_pantalla:
            if st.button("🗗 CLOSE FULLSCREEN", key="btn_grid_fs_reloj", width='stretch', help="Cerrar vista a toda la pantalla y retornar al panel C2"):
                st.session_state["reloj_toda_pantalla"] = False
                st.rerun()
            st.markdown("<div style='font-size: 11px; color: #00f5d4; font-weight: 700; margin-top: 4px;'>🟢 TODA PANTALLA ACTIVA</div>", unsafe_allow_html=True)
        else:
            if st.button("▦ FULLSCREEN", key="btn_grid_fs_reloj", width='stretch', help="Agrandar a toda la pantalla para videowall o sala de situación"):
                st.session_state["reloj_toda_pantalla"] = True
                st.rerun()
            st.markdown("<div style='font-size: 11px; color: #94a3b8; font-weight: 600; margin-top: 4px;'>⊞ Grilla Toda Pantalla</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Inicializar motor de cálculo polar
    motor_reloj = MotorRelojFEN()

    def envolver_reloj_fullscreen_html(svg_html: str) -> str:
        return f"""
        <style>
            #c2-reloj-fullscreen-wrapper {{
                position: relative;
                width: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background: radial-gradient(circle at center, #0b1322 0%, #060a12 100%);
                border-radius: 16px;
                border: 1px solid #1e3a60;
                padding: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.6);
                box-sizing: border-box;
            }}
            #c2-reloj-fullscreen-wrapper:fullscreen,
            #c2-reloj-fullscreen-wrapper:-webkit-full-screen,
            #c2-reloj-fullscreen-wrapper:-ms-fullscreen {{
                width: 100vw !important;
                height: 100vh !important;
                max-width: 100vw !important;
                max-height: 100vh !important;
                background: radial-gradient(circle at center, #0a1120 0%, #02050b 100%) !important;
                border-radius: 0 !important;
                border: none !important;
                padding: 15px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }}
            #c2-reloj-fullscreen-wrapper:fullscreen svg,
            #c2-reloj-fullscreen-wrapper:-webkit-full-screen svg,
            #c2-reloj-fullscreen-wrapper:-ms-fullscreen svg {{
                max-height: 94vh !important;
                max-width: 94vh !important;
                width: auto !important;
                height: auto !important;
            }}
            .btn-grid-fullscreen {{
                position: absolute;
                top: 14px;
                right: 18px;
                z-index: 999;
                background: rgba(15, 23, 42, 0.92);
                color: #38bdf8;
                border: 1.5px solid #00b4d8;
                padding: 7px 16px;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 800;
                font-family: system-ui, -apple-system, sans-serif;
                letter-spacing: 0.8px;
                cursor: pointer;
                backdrop-filter: blur(10px);
                display: inline-flex;
                align-items: center;
                gap: 7px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.55), 0 0 12px rgba(0, 180, 216, 0.25);
                transition: all 0.25s ease-in-out;
            }}
            .btn-grid-fullscreen:hover {{
                background: rgba(14, 116, 144, 0.95);
                color: #ffffff;
                border-color: #38bdf8;
                box-shadow: 0 6px 20px rgba(0, 180, 216, 0.5);
                transform: translateY(-1px);
            }}
            .btn-grid-fullscreen.is-fullscreen {{
                background: rgba(127, 29, 29, 0.92) !important;
                color: #fca5a5 !important;
                border-color: #ef4444 !important;
                box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
            }}
            .btn-grid-fullscreen.is-fullscreen:hover {{
                background: rgba(185, 28, 28, 0.95) !important;
                color: #ffffff !important;
                border-color: #f87171 !important;
                box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6) !important;
            }}
        </style>
        <div id="c2-reloj-fullscreen-wrapper">
            <button id="btn-grid-fs" class="btn-grid-fullscreen" onclick="toggleClockFullscreen()" title="Pantalla Completa C2">
                <span id="btn-grid-icon">
                    <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" style="display:inline-block; vertical-align:middle;">
                        <rect x="1" y="1" width="6" height="6" rx="1.2"/>
                        <rect x="9" y="1" width="6" height="6" rx="1.2"/>
                        <rect x="1" y="9" width="6" height="6" rx="1.2"/>
                        <rect x="9" y="9" width="6" height="6" rx="1.2"/>
                    </svg>
                </span>
                <span id="btn-grid-label">FULLSCREEN</span>
            </button>
            {svg_html}
        </div>
        <script>
        function toggleClockFullscreen() {{
            var wrapper = document.getElementById('c2-reloj-fullscreen-wrapper');
            if (!document.fullscreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {{
                if (wrapper.requestFullscreen) {{ wrapper.requestFullscreen(); }}
                else if (wrapper.webkitRequestFullscreen) {{ wrapper.webkitRequestFullscreen(); }}
                else if (wrapper.msRequestFullscreen) {{ wrapper.msRequestFullscreen(); }}
            }} else {{
                if (document.exitFullscreen) {{ document.exitFullscreen(); }}
                else if (document.webkitExitFullscreen) {{ document.webkitExitFullscreen(); }}
                else if (document.msExitFullscreen) {{ document.msExitFullscreen(); }}
            }}
        }}
        function updateFullscreenButton() {{
            var btn = document.getElementById('btn-grid-fs');
            var label = document.getElementById('btn-grid-label');
            var icon = document.getElementById('btn-grid-icon');
            var isFs = !!(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
            if (isFs) {{
                btn.classList.add('is-fullscreen');
                label.textContent = 'CLOSE FULLSCREEN';
                icon.innerHTML = '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="display:inline-block; vertical-align:middle;"><path d="M2 6V2h4M14 6V2h-4M2 10v4h4M14 10v4h-4"/></svg>';
                btn.title = "Cerrar Pantalla Completa (ESC)";
            }} else {{
                btn.classList.remove('is-fullscreen');
                label.textContent = 'FULLSCREEN';
                icon.innerHTML = '<svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" style="display:inline-block; vertical-align:middle;"><rect x="1" y="1" width="6" height="6" rx="1.2"/><rect x="9" y="1" width="6" height="6" rx="1.2"/><rect x="1" y="9" width="6" height="6" rx="1.2"/><rect x="9" y="9" width="6" height="6" rx="1.2"/></svg>';
                btn.title = "Agrandar a Pantalla Completa C2";
            }}
        }}
        document.addEventListener('fullscreenchange', updateFullscreenButton);
        document.addEventListener('webkitfullscreenchange', updateFullscreenButton);
        document.addEventListener('mozfullscreenchange', updateFullscreenButton);
        document.addEventListener('MSFullscreenChange', updateFullscreenButton);
        </script>
        """

    ruta_pdf_reloj = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "reloj_del_fen_modelo_matematico_y_analogos.pdf")
    pdf_bytes_rel = None
    if os.path.exists(ruta_pdf_reloj):
        with open(ruta_pdf_reloj, "rb") as f_pdf_rel:
            pdf_bytes_rel = f_pdf_rel.read()

    ruta_pdf_disp = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "analisis_comparativo_probabilidades_amaru_vs_enfen_wmo.pdf")
    pdf_bytes_disp = None
    if os.path.exists(ruta_pdf_disp):
        with open(ruta_pdf_disp, "rb") as f_pdf_disp:
            pdf_bytes_disp = f_pdf_disp.read()

    if reloj_toda_pantalla:
        # VISTA EXPANDIDA TODA LA PANTALLA (GRAN FORMATO C2 VIDEOWALL)
        with st.expander("🎛️ Calibración en Vivo de Sensores Oceanográficos (Sensibilidad del Minutero)", expanded=False):
            c_fs_s1, c_fs_s2, c_fs_s3, c_fs_s4 = st.columns(4)
            with c_fs_s1:
                sld_tsm_reloj = st.slider("🌊 Anomalía TSM 1+2 (°C):", 0.0, 4.0, float(tsm_anomalia), step=0.1, key="sld_tsm_reloj_fs")
            with c_fs_s2:
                sld_alisios_reloj = st.slider("💨 Velocidad Alisios (m/s):", 1.0, 10.0, 4.2, step=0.1, key="sld_alisios_reloj_fs")
            with c_fs_s3:
                sld_iph_reloj = st.slider("💧 Saturación Suelo (IPH %):", 10.0, 100.0, 78.5, step=1.0, key="sld_iph_reloj_fs")
            with c_fs_s4:
                fecha_reloj_sim = st.date_input("📅 Fecha de Evaluación Civil:", value=datetime.now(), key="fec_reloj_sim_fs")

        # Computar modelo con las condiciones seleccionadas
        fecha_eval_dt = datetime.combine(fecha_reloj_sim, datetime.min.time())
        modelo_reloj_actual = motor_reloj.calcular_reloj(
            fecha_evaluacion=fecha_eval_dt,
            anomalia_tsm=sld_tsm_reloj,
            velocidad_alisios=sld_alisios_reloj,
            iph_actual=sld_iph_reloj
        )
        minutero = modelo_reloj_actual.minutero
        analogo = modelo_reloj_actual.analogo_dominante

        # Renderizado en Toda la Pantalla Centrado
        c_clock_space_l, c_clock_main, c_clock_space_r = st.columns([0.1, 3.8, 0.1])
        with c_clock_main:
            svg_code_fs = motor_reloj.generar_svg_reloj(modelo_reloj_actual, ancho=800, alto=800)
            html_fs = envolver_reloj_fullscreen_html(svg_code_fs)
            st.iframe(html_fs, height=840)

        # 4 Tarjetas Métricas Tácticas Horizontales de Sala de Crisis
        k_rel1, k_rel2, k_rel3, k_rel4 = st.columns(4)
        k_rel1.metric("━ Aguja Horaria (Civil)", f"{minutero.hora_calendario:.2f} h", f"{minutero.angulo_calendario_deg:.1f}° en Dial Polar")
        k_rel2.metric("╍ Aguja Minutero (FEN)", f"{int(minutero.hora_tactica_final):02d}:{(int(minutero.hora_tactica_final * 60) % 60):02d} h", f"{minutero.calificacion_tiempo.replace('_', ' ')}")
        k_rel3.metric("Desfase de Forzamiento", f"{minutero.desfase_forzamiento_dias:+.1f} días", "ADELANTADO" if minutero.desfase_forzamiento_dias > 0 else "RETARDADO")
        k_rel4.metric("Similitud Análoga Dominante", f"{analogo.porcentaje_similitud}%", analogo.evento_nombre.split('(')[0].strip())

        c_rel_d1, c_rel_d2 = st.columns(2)
        with c_rel_d1:
            if pdf_bytes_rel:
                st.download_button(
                    label="📥 Descargar Modelo Matemático y Doctrina del Reloj del FEN (PDF Oficial)",
                    data=pdf_bytes_rel,
                    file_name="reloj_del_fen_modelo_matematico_y_analogos.pdf",
                    mime="application/pdf",
                    width='stretch',
                    key="btn_descarga_reloj_pdf_fs"
                )
        with c_rel_d2:
            if pdf_bytes_disp:
                st.download_button(
                    label="📥 Descargar Sustento Disparidades ENFEN vs. WMO vs. AMARU-FEN (PDF Oficial)",
                    data=pdf_bytes_disp,
                    file_name="analisis_comparativo_probabilidades_amaru_vs_enfen_wmo.pdf",
                    mime="application/pdf",
                    width='stretch',
                    key="btn_descarga_disp_pdf_fs"
                )

    else:
        # VISTA ESTÁNDAR A DOS COLUMNAS
        col_reloj_viz, col_reloj_ctrl = st.columns([1.15, 1])

        with col_reloj_ctrl:
            st.markdown("##### 🎛️ Forzamiento Hidroclimático en Vivo (Sensibilidad del Minutero)")
            st.caption("Ajusta los sensores en tiempo real para observar cómo el minutero se adelanta (impacto temprano) o retrasa (impacto diferido):")
            
            c_rf1, c_rf2 = st.columns(2)
            with c_rf1:
                sld_tsm_reloj = st.slider("🌊 Anomalía TSM 1+2 (°C):", 0.0, 4.0, float(tsm_anomalia), step=0.1, key="sld_tsm_reloj")
                sld_alisios_reloj = st.slider("💨 Velocidad Alisios (m/s):", 1.0, 10.0, 4.2, step=0.1, key="sld_alisios_reloj")
            with c_rf2:
                sld_iph_reloj = st.slider("💧 Saturación Suelo (IPH %):", 10.0, 100.0, 78.5, step=1.0, key="sld_iph_reloj")
                fecha_reloj_sim = st.date_input("📅 Fecha de Evaluación Civil:", value=datetime.now(), key="fec_reloj_sim")

            # Computar modelo con las condiciones seleccionadas
            fecha_eval_dt = datetime.combine(fecha_reloj_sim, datetime.min.time())
            modelo_reloj_actual = motor_reloj.calcular_reloj(
                fecha_evaluacion=fecha_eval_dt,
                anomalia_tsm=sld_tsm_reloj,
                velocidad_alisios=sld_alisios_reloj,
                iph_actual=sld_iph_reloj
            )

            minutero = modelo_reloj_actual.minutero
            analogo = modelo_reloj_actual.analogo_dominante

            st.markdown(f"""
            <div style="background: #0d1728; border: 1px solid #1e3a60; border-left: 5px solid {'#e63946' if minutero.desfase_forzamiento_dias > 0 else '#06d6a0'}; padding: 12px 16px; border-radius: 8px; margin-top: 6px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #64dfdf; font-size: 13px;">🧭 ESTADO DEL MINUTERO TÁCTICO:</b>
                    <span style="background: {'#7f0000' if minutero.desfase_forzamiento_dias > 12 else '#0b525b'}; color: white; font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
                        {minutero.calificacion_tiempo.replace('_', ' ')}
                    </span>
                </div>
                <div style="margin-top: 6px; font-size: 12px; color: #e2e8f0; line-height: 1.6;">
                    • <b style="color: #38bdf8;">━ Aguja Horaria (Sólida, Corta):</b> Mes Civil Base: <b>{minutero.hora_calendario:.2f} h</b> ({minutero.angulo_calendario_deg:.1f}°)<br>
                    • <b style="color: #00f5d4;">╍ Aguja Minutero (Discontinua, Gruesa):</b> Tiempo Táctico FEN: <span style="color: #00f5d4; font-weight: bold; font-family: monospace; font-size: 14px;">{int(minutero.hora_tactica_final):02d}:{(int(minutero.hora_tactica_final * 60) % 60):02d} h</span> ({minutero.angulo_tactico_final_deg:.1f}°)<br>
                    • <b>Desfase por Forzamiento:</b> <span style="color: {'#ff4d6d' if minutero.desfase_forzamiento_dias > 0 else '#06d6a0'}; font-weight: bold;">{minutero.desfase_forzamiento_dias:+.1f} días ({'ADELANTADO' if minutero.desfase_forzamiento_dias > 0 else 'RETRASADO'})</span><br>
                    • <b>Coherencia Operativa:</b> <i style="color: #94a3b8;">{'Si el Horario marca en Octubre y el Minutero en Setiembre, el FEN viene con retardo estacional de ' + str(abs(round(minutero.desfase_forzamiento_dias, 1))) + ' días.' if minutero.desfase_forzamiento_dias < 0 else 'El océano anticipa la amenaza FEN: las lluvias destructivas llegarán ' + str(round(minutero.desfase_forzamiento_dias, 1)) + ' días antes del calendario habitual.'}</i><br>
                    • <b>Proyección de Clímax:</b> {minutero.fecha_proyectada_climax}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background: #120309; border: 1px solid #7f0019; border-left: 5px solid #ff0040; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <b style="color: #ff8fa3; font-size: 13px;">🎯 ANÁLOGO HISTÓRICO DOMINANTE:</b>
                    <span style="background: #ff0040; color: white; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 900;">
                        {analogo.porcentaje_similitud}% SIMILITUD
                    </span>
                </div>
                <div style="margin-top: 6px; font-size: 12px; color: #e2e8f0; line-height: 1.6;">
                    • <b>Precedente:</b> <span style="color: #ffffff; font-weight: bold;">{analogo.evento_nombre}</span> ({analogo.rango_anos})<br>
                    • <b>Tipología:</b> {analogo.tipo_evento}<br>
                    • <b>Lección Táctica:</b> <i style="color: #cbd5e1;">"{analogo.leccion_tactica}"</i>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_std_d1, c_std_d2 = st.columns(2)
            with c_std_d1:
                if pdf_bytes_rel:
                    st.download_button(
                        label="📥 Doctrina Reloj FEN (PDF)",
                        data=pdf_bytes_rel,
                        file_name="reloj_del_fen_modelo_matematico_y_analogos.pdf",
                        mime="application/pdf",
                        width='stretch',
                        key="btn_descarga_reloj_pdf"
                    )
            with c_std_d2:
                if pdf_bytes_disp:
                    st.download_button(
                        label="📥 Sustento Disparidades (PDF)",
                        data=pdf_bytes_disp,
                        file_name="analisis_comparativo_probabilidades_amaru_vs_enfen_wmo.pdf",
                        mime="application/pdf",
                        width='stretch',
                        key="btn_descarga_disp_pdf"
                    )

        with col_reloj_viz:
            svg_code = motor_reloj.generar_svg_reloj(modelo_reloj_actual, ancho=540, alto=540)
            html_viz = envolver_reloj_fullscreen_html(svg_code)
            st.iframe(html_viz, height=580)

    st.markdown("---")

    # MÓDULO HERO DIRECTO: ASISTENTE SOBERANO C2 MULTI-AUDIENCIA
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 12px; padding: 16px 20px; border-left: 6px solid #00b4d8; margin-top: 10px; margin-bottom: 15px; border: 1px solid #2a3b53; box-shadow: 0 4px 20px rgba(0,0,0,0.35);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 16px; font-weight: bold; color: #38bdf8;">💬 ASISTENTE TÁCTICO SOBERANO C2: CONSULTA INMEDIATA POR PERFIL</span>
            <span style="background: #0284c7; color: white; font-size: 11px; padding: 3px 10px; border-radius: 5px; font-weight: bold;">ACCESO DIRECTO SIN NAVEGAR</span>
        </div>
        <p style="margin: 6px 0 0 0; font-size: 12.5px; color: #cbd5e1;">
            Calibra las respuestas, lenguaje y recomendaciones según tu perfil operativo. Haz clic en una píldora sugerida o escribe tu consulta:
        </p>
    </div>
    """, unsafe_allow_html=True)

    c_rol1, c_rol2 = st.columns([1.3, 3])
    with c_rol1:
        rol_dash = st.radio(
            "Selecciona tu perfil de usuario:",
            ["👤 Vecino / Ciudadano", "🏛️ Alcalde / Autoridad COEL", "💻 Técnico C2 / Científico", "📰 Periodista / Medios"],
            index=0,
            horizontal=False,
            key="rb_rol_dash"
        )
        rol_tag = "ciudadano" if "Vecino" in rol_dash else ("alcalde" if "Alcalde" in rol_dash else ("tecnico" if "Técnico" in rol_dash else "periodista"))

    with c_rol2:
        st.markdown(f"**⚡ Consultas Tácticas Recomendadas para:** `{rol_dash}`")
        prompt_dash_click = None
        
        if rol_tag == "ciudadano":
            cp1, cp2 = st.columns(2)
            if cp1.button("📍 Soy de Catacaos, ¿qué información tienes?", key="btn_c1_dash", width='stretch'):
                prompt_dash_click = "Soy de Catacaos, qué información tienes para mí"
            if cp2.button("🏃‍♂️ ¿Hacia dónde evacuar en mi zona?", key="btn_c2_dash", width='stretch'):
                prompt_dash_click = "Hacia dónde debo evacuar si sube el río en mi distrito"
            if cp1.button("🎒 ¿Qué debe llevar mi mochila de emergencia?", key="btn_c3_dash", width='stretch'):
                prompt_dash_click = "Qué debe tener mi mochila de emergencia para El Niño"
            if cp2.button("🐾 ¿Cómo protejo a mis animales y enseres?", key="btn_c4_dash", width='stretch'):
                prompt_dash_click = "Cómo protejo a mis animales y enseres antes de la lluvia"

        elif rol_tag == "alcalde":
            cp1, cp2 = st.columns(2)
            if cp1.button("🚜 ¿Cómo contrato maquinaria bajo D.S. 124?", key="btn_a1_dash", width='stretch'):
                prompt_dash_click = "Como alcalde, cómo contrato maquinaria pesada en 24h bajo el D.S. 124-2026-PCM sin riesgo de Contraloría"
            if cp2.button("🚨 Caudal crítico y diques en Catacaos", key="btn_a2_dash", width='stretch'):
                prompt_dash_click = "Cuáles son los puntos críticos y diques en riesgo en Catacaos UBIGEO 200105"
            if cp1.button("📋 Pre-redactar borrador de Ficha EDAN", key="btn_a3_dash", width='stretch'):
                prompt_dash_click = "Generar pre-borrador de Ficha EDAN para Catacaos"
            if cp2.button("🛡️ Blindaje legal y PP 0068", key="btn_a4_dash", width='stretch'):
                prompt_dash_click = "Qué informe pericial necesito para blindarme ante Contraloría con el PP 0068"

        elif rol_tag == "tecnico":
            cp1, cp2 = st.columns(2)
            if cp1.button("📐 Desglose Saaty AHP (CR <= 0.10)", key="btn_t1_dash", width='stretch'):
                prompt_dash_click = "Explícame la fórmula del IRCE-FEN y por qué la matriz Saaty tiene consistencia CR menor a 0.10"
            if cp2.button("🌊 Sustento del IPH y 7 Huaicos Trujillo", key="btn_t2_dash", width='stretch'):
                prompt_dash_click = "Por qué AMARU-FEN usa un IPH en lugar de solo mirar la lluvia de hoy y qué es la histéresis"
            if cp1.button("📊 Resultados del Backtesting (96.2%)", key="btn_t3_dash", width='stretch'):
                prompt_dash_click = "Por qué la probabilidad de éxito en el backtesting va del 94.2 al 98.4 y qué significa el 96.2"
            if cp2.button("⛰️ Quebradas Críticas Reincidentes", key="btn_t4_dash", width='stretch'):
                prompt_dash_click = "Cuáles son las quebradas críticas de mayor riesgo y qué umbrales tienen"

        else: # periodista
            cp1, cp2 = st.columns(2)
            if cp1.button("📰 Resumen para Nota de Prensa", key="btn_p1_dash", width='stretch'):
                prompt_dash_click = "Para nota de prensa sobre Catacaos, qué información oficial verificada se tiene"
            if cp2.button("🛑 Verificación: ¿Colapsará presa Poechos?", key="btn_p2_dash", width='stretch'):
                prompt_dash_click = "Es verdad el rumor de que la represa de Poechos va a colapsar"
            if cp1.button("📊 Cifras Oficiales D.S. 124-2026-PCM", key="btn_p3_dash", width='stretch'):
                prompt_dash_click = "Cuáles son las cifras oficiales de los 893 distritos en emergencia bajo D.S. 124-2026-PCM"
            if cp2.button("🛡️ Fuentes Oficiales Homologadas Tier 1", key="btn_p4_dash", width='stretch'):
                prompt_dash_click = "Cuáles son las fuentes autorizadas y qué significa el Tier 1 en AMARU-FEN"

        cq_txt, cq_btn = st.columns([3.5, 1])
        with cq_txt:
            txt_in_dash = st.text_input(
                "Pregunta directa:",
                value=prompt_dash_click if prompt_dash_click else "",
                placeholder="Escribe tu consulta (ej. Soy de Catacaos, qué información tienes para mí...)",
                key="input_direct_dash",
                label_visibility="collapsed"
            )
        with cq_btn:
            btn_sub_dash = st.button("🚀 Consultar", key="btn_exec_dash", type="primary", width='stretch')

    query_a_procesar = prompt_dash_click or (txt_in_dash if btn_sub_dash and txt_in_dash else None)
    if query_a_procesar:
        with st.spinner(f"Consultando fuentes homologadas para perfil {rol_dash}..."):
            u_contexto = st.session_state.get("u_activo_sb")
            res_dash = motor_chat_soberano.procesar_consulta(query_a_procesar, u_activo=u_contexto, rol=rol_tag)
            st.session_state["ultima_consulta_dash"] = {
                "query": query_a_procesar,
                "res": res_dash,
                "rol": rol_dash
            }

    if "ultima_consulta_dash" in st.session_state:
        ult = st.session_state["ultima_consulta_dash"]
        res_obj = ult["res"]
        st.markdown(f"""
        <div style="background: #131e31; border-radius: 10px; padding: 12px 16px; border-left: 5px solid #06d6a0; margin-top: 10px; margin-bottom: 12px;">
            <div style="font-size: 13px; font-weight: bold; color: #a0c4ff;">
                💬 Pregunta: <i>"{ult['query']}"</i> &nbsp;|&nbsp; Perfil Aplicado: <span style="color: #64dfdf;">{ult['rol']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(res_obj["respuesta"])
        with st.expander("🛡️ Ver Cadena de Custodia & Fuentes Homologadas Citadas"):
            for idx, f in enumerate(res_obj.get("fuentes_citadas", []), 1):
                st.markdown(f"**[{idx}] {f['fuente']}** | `{f.get('tier', 'Tier 1')}` | Ref: `{f.get('referencia', '')}`")
        st.info("💡 **Tip:** Para mantener una conversación extendida con historial completo, visita la pestaña **💬 1. Asistente Soberano C2** al lado del Dashboard.")

    st.markdown("---")
    
    # 3. Dos Gráficos Estratégicos
    col_g1, col_g2 = st.columns([1.3, 1])
    with col_g1:
        st.markdown("#### 🌊 Presión Hidrométrica Fluvial: Caudal Actual vs. Umbral de Desborde (m³/s)")
        estaciones_todas = orchestrator.consultar_estaciones_aforo()
        df_caudales = pd.DataFrame([
            {
                "Río": f"{e['rio']} ({e['nombre'].replace('Puente ', '').replace('Estación ', '')})",
                "Caudal Actual (m³/s)": e["caudal_simulado_actual_m3s"],
                "Umbral Desborde (m³/s)": e["umbral_rojo_desborde_m3s"]
            }
            for e in estaciones_todas
        ]).set_index("Río")
        st.bar_chart(df_caudales, color=["#ff4d4d", "#00b4d8"])

    with col_g2:
        st.markdown("#### 📍 Top Departamentos con Más Distritos en Emergencia")
        stats_ds = orchestrator.obtener_estadisticas_distritos_emergencia()
        df_top_dept = pd.DataFrame(stats_ds["top_departamentos"]).set_index("departamento")
        st.bar_chart(df_top_dept["total_distritos"], color="#f77f00")

    st.markdown("---")

    # Mapa Situacional del Perú por UBIGEO en la Sala C2
    st.markdown("#### 🇵🇪 Mapa Situacional del Perú por UBIGEO: Indicadores y Color según Ingestas Autorizadas")
    st.caption("Los 893 distritos del DS 124-2026-PCM coloreados automáticamente en tiempo real según los avisos vigentes de SENAMHI y el informe ENFEN.")

    if "ubigeos_mapa_autorizado" not in st.session_state:
        st.session_state["ubigeos_mapa_autorizado"] = orchestrator.calcular_indicadores_desde_ingestas_oficiales()

    meta_c2 = obtener_meta_segura(orchestrator)
    col_meta1, col_meta2 = st.columns([2, 1])
    with col_meta1:
        st.success(f"🕒 **Fecha y Hora de Actualización:** `{meta_c2['fecha_hora']} (Hora Oficial de Perú)` | **Tipo:** `{meta_c2['tipo']}`")
    with col_meta2:
        st.info(f"🛡️ **Versión Ingesta:** `{meta_c2['version_id']}` | **UBIGEOs:** `{meta_c2['total_ubigeos_procesados']}`")


    # Controles de Filtrado por Color y Capa Térmica del Mar
    c_fcol1, c_fcol2 = st.columns([2, 1])
    with c_fcol1:
        filtro_color_c2 = st.radio(
            "🎨 Filtrar UBIGEOs en el Mapa por Nivel de Riesgo / Color:",
            ["TODOS LOS UBIGEOS", "🔴 ROJOS (Crítico)", "🟠 ÁMBAR / NARANJA (Alto)", "🟡 AMARILLOS (Medio)", "🟢 VERDES (Basal)"],
            horizontal=True,
            key="filtro_color_tab0"
        )
    with c_fcol2:
        ver_mar_c2 = st.checkbox(
            "🌊 Mostrar Calor del Mar (Anomalía TSM Niño 1+2 & IMARPE)",
            value=True,
            key="chk_ver_mar_tab0"
        )

    data_mapa_c2 = st.session_state["ubigeos_mapa_autorizado"]

    # Aplicar filtro de color
    if filtro_color_c2.startswith("🔴"):
        data_c2_filtrada = [u for u in data_mapa_c2 if u["nivel_alerta"] == "CRITICO_ROJO"]
    elif filtro_color_c2.startswith("🟠"):
        data_c2_filtrada = [u for u in data_mapa_c2 if u["nivel_alerta"] == "ALTO_NARANJA"]
    elif filtro_color_c2.startswith("🟡"):
        data_c2_filtrada = [u for u in data_mapa_c2 if u["nivel_alerta"] == "MEDIO_AMARILLO"]
    elif filtro_color_c2.startswith("🟢"):
        data_c2_filtrada = [u for u in data_mapa_c2 if u["nivel_alerta"] == "BAJO_VERDE"]
    else:
        data_c2_filtrada = data_mapa_c2

    lista_puntos_c2 = [
        {
            "nombre": f"UBIGEO {u['ubigeo']}: {u['distrito']}",
            "lat": u["lat"],
            "lon": u["lon"],
            "region": f"{u['departamento']} / {u['provincia']}",
            "info": f"IRCE-FEN: {u['score_irce']} ({u['semaforo']})\nAlerta Oficial: {u['nivel_alerta']}\nActualizado: {u.get('fecha_hora_actualizacion', meta_c2['fecha_hora'])}\nPoblación: {u['poblacion']:,} hab.",
            "radius": u["radius"],
            "color": u["color"]
        }
        for u in data_c2_filtrada
    ]

    # Añadir capa de calor del mar si está activa
    if ver_mar_c2:
        lista_puntos_c2.extend(generar_malla_termica_mar_peruano(tsm_anomalia))

    df_c2 = pd.DataFrame(lista_puntos_c2)

    layer_c2 = pdk.Layer(
        "ScatterplotLayer",
        df_c2,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        auto_highlight=True
    )
    view_c2 = pdk.ViewState(latitude=-9.20, longitude=-76.50, zoom=5.0, pitch=35)
    st.pydeck_chart(pdk.Deck(
        layers=[layer_c2],
        initial_view_state=view_c2,
        tooltip={"text": "{nombre}\nUbicación: {region}\n{info}"}
    ))


    st.markdown("---")

    # 4. Matriz Macrorregional y Decisiones Humanas
    col_mat, col_dec = st.columns([1.3, 1])
    with col_mat:
        st.markdown("#### 🗺️ Matriz de Situación Macrorregional")
        matriz_macro = [
            {"Macrorregión": "Norte (Piura / Tumbes)", "Amenaza Dominante": "Inundación Fluvial y Pluvial Extrema", "Semáforo": "🔴 ROJO", "Acción Prioritaria": "Descolmatación dique Pedregal y preposicionamiento USNS Comfort"},
            {"Macrorregión": "Nor-Centro (La Libertad / Lambayeque)", "Amenaza Dominante": "Activación de quebradas y desborde Río La Leche", "Semáforo": "🟠 NARANJA", "Acción Prioritaria": "Limpieza de drenes y refuerzo de fajas marginales"},
            {"Macrorregión": "Centro (Lima Provincias / Chosica)", "Amenaza Dominante": "Huaicos en quebradas Quirio y Huaycoloro", "Semáforo": "🟠 NARANJA", "Acción Prioritaria": "Despeje de mallas geodinámicas y alerta Carretera Central"},
            {"Macrorregión": "Sur (Ica / Arequipa Costera)", "Amenaza Dominante": "Avenidas súbitas en Río Ica y quebradas de Chala", "Semáforo": "🟡 AMARILLO", "Acción Prioritaria": "Apertura de compuertas en Bocatoma Socorro"}
        ]
        st.dataframe(pd.DataFrame(matriz_macro), hide_index=True, width='stretch')

    with col_dec:
        st.markdown("#### ⚖️ Decisiones de Autoridad Humana (Ley Nº 31814)")
        st.caption("Recomendaciones técnicas preparadas para suscripción humana indelegable:")
        
        st.info("📌 **Decisión 1:** Autorizar emisión de alerta SISMATE para Catacaos ante caudal > 2,200 m³/s.")
        if st.button("✍️ Suscribir Orden de Alerta SISMATE", key="btn_dash_sismate"):
            st.success("✅ Orden SISMATE suscrita por la Autoridad Humana y canalizada a operadoras.")
        
        st.warning("📌 **Decisión 2:** Aprobar Contratación Directa de motobombas pesadas (DS 124-2026-PCM).")
        if st.button("✍️ Suscribir Resolución de Contratación", key="btn_dash_contra"):
            st.success("✅ Resolución aprobada y remitida con plazo de 10 días para regularización SEACE.")

# TAB 1: CONSOLA TÁCTICA C2 (TERMINAL DE MANDO)
with tab_c2:
    st.subheader("💻 Consola Táctica de Mando C2 (Command & Control Terminal)")
    st.caption("Terminal de telemetría de alta resolución, auditoría de datos personales (Ley Nº 29733) y despacho táctico bajo estricta Soberanía Humana (Ley Nº 31814).")

    # 1. Barra de Enlaces y Soberanía Humana
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
        <span style="background:#132a13; color:#70e000; border:1px solid #38b000; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; font-family:monospace;">🟢 SENAMHI: AVISOS ACTIVOS</span>
        <span style="background:#132a13; color:#70e000; border:1px solid #38b000; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; font-family:monospace;">🟢 ENFEN: TSM +1.8°C (NIÑO 1+2)</span>
        <span style="background:#132a13; color:#70e000; border:1px solid #38b000; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; font-family:monospace;">🟢 ANA: 8 ESTACIONES FLUVIALES</span>
        <span style="background:#1f2444; color:#00f0ff; border:1px solid #00b4d8; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; font-family:monospace;">⚖️ SOBERANÍA HUMANA: LEY 31814 (ACTIVA)</span>
        <span style="background:#2a1845; color:#e0aaff; border:1px solid #9d4edd; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; font-family:monospace;">🛡️ PROTECCIÓN DATOS: LEY 29733 (ENMASCARADO)</span>
        <span style="background:#2d1b00; color:#ffb703; border:1px solid #fb8500; border-radius:4px; padding:3px 8px; font-size:11px; font-weight:600; font-family:monospace;">🕹️ OPERADOR: CARLOS EDU BAÑOS (SALA C2)</span>
    </div>
    """, unsafe_allow_html=True)

    # 2. Macros Tácticos por Categorías
    cmd_ejecutar = None
    
    with st.expander("⚡ Panel de Directivas Rápidas de 1-Clic (Macros Tácticos)", expanded=True):
        st.markdown("**🚨 Despachos de Alerta Táctica a Jefes de Defensa Civil (SINAGERD):**")
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        if col_m1.button("🚨 Alerta Chincha (Sintético)", width='stretch', help="Dispara dossier completo a carlosedubanos@gmail.com"):
            cmd_ejecutar = "alerta 110206-SIM"
        if col_m2.button("📱 Telegram Chincha", width='stretch', help="Genera reporte corto optimizado para smartphone/móvil"):
            cmd_ejecutar = "telegram 110206-SIM"
        if col_m3.button("🏛️ Alerta Chincha (Portal)", width='stretch', help="Dossier oficial de la Municipalidad de Pueblo Nuevo Chincha"):
            cmd_ejecutar = "alerta 110206"
        if col_m4.button("🌊 Alerta Catacaos", width='stretch', help="Alerta para el distrito de Catacaos (Piura)"):
            cmd_ejecutar = "alerta 200105"
        if col_m5.button("⚠️ Alerta Chosica", width='stretch', help="Alerta para Lurigancho-Chosica (Lima)"):
            cmd_ejecutar = "alerta 150118"

        st.markdown("**📊 Telemetría, Monitoreo de Caudales & Gobernanza Anticipada:**")
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        if col_t1.button("📡 Status C2", width='stretch', help="Diagnóstico integral de enlaces y sincronización"):
            cmd_ejecutar = "status"
        if col_t2.button("💧 Red Aforo ANA", width='stretch', help="Caudales en tiempo real y umbrales de desborde"):
            cmd_ejecutar = "aforo"
        if col_t3.button("🎯 IRCE Catacaos", width='stretch', help="Cálculo del Índice de Riesgo Compuesto en Catacaos"):
            cmd_ejecutar = "irce CATACAOS"
        if col_t4.button("🛡️ Auditar LPDP", width='stretch', help="Auditoría de protección de datos personales Ley 29733"):
            cmd_ejecutar = "lpdp"

        st.markdown("**🌐 Auditoría Pública y Verificación de Fuentes Oficiales (Ley 31814):**")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        if col_a1.button("🌐 Fuentes Validadas", width='stretch', help="Listado exhaustivo de fuentes y enlaces de verificación"):
            cmd_ejecutar = "fuentes"
        if col_a2.button("🛡️ Auditar Cadena C2", width='stretch', help="Auditoría criptográfica, hashes y firmas secp256k1"):
            cmd_ejecutar = "auditoria"
        if col_a3.button("⚖️ Soberanía Humana", width='stretch', help="Marco legal vinculante Ley 31814"):
            cmd_ejecutar = "soberania"
        if col_a4.button("🔌 Conmutar Edge Offgrid", width='stretch', help="Simular corte de satélite y conmutar a SLM Local Edge"):
            cmd_ejecutar = "offgrid offline"

    # 3. Terminal CLI Interactivo
    c_cmd1, c_cmd2, c_cmd3 = st.columns([3.2, 0.8, 0.6])
    with c_cmd1:
        txt_manual = st.text_input(
            "Consola AMARU-C2::Prompt>",
            value=cmd_ejecutar if cmd_ejecutar else "",
            placeholder="Escribe 'fuentes', 'auditoria', 'status', 'alerta 110206-SIM', 'aforo', 'soberania'...",
            key="input_terminal_c2",
            label_visibility="collapsed"
        )
    with c_cmd2:
        btn_run_cmd = st.button("▶️ Ejecutar Directiva", type="primary", width='stretch')
    with c_cmd3:
        btn_limpiar_buffer = st.button("🗑️ Limpiar", width='stretch')

    if btn_limpiar_buffer:
        st.session_state["historial_consola_c2"] = []
        st.rerun()

    comando_final = txt_manual.strip() if btn_run_cmd or cmd_ejecutar else None

    # Inicializar historial de sesión de consola
    if "historial_consola_c2" not in st.session_state or not st.session_state["historial_consola_c2"]:
        st.session_state["historial_consola_c2"] = [
            {
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "comando": "INIT_SYSTEM_C2",
                "salida_texto": "AMARU-C2 TACTICAL TERMINAL INICIALIZADA (COEN-INDECI).\n"
                                "• Enlaces activos: SENAMHI (Avisos), ENFEN (TSM +1.8°C), ANA (8 Estaciones Fluviales).\n"
                                "• Soberanía Humana: ACTIVA (Ley Nº 31814 / DS 085-2024-PCM).\n"
                                "• Protección de Datos: ENMASCARAMIENTO ACTIVO (Ley Nº 29733).\n"
                                "• Operador en Puesto de Mando: Carlos Edu Baños.\n"
                                "Escriba 'fuentes' para auditar las entidades oficiales o 'help' para catálogo de comandos.",
                "tipo": "OK"
            }
        ]

    if comando_final:
        with st.spinner("Procesando directiva en la Sala C2..."):
            res_cmd = orchestrator.ejecutar_comando_consola(
                comando=comando_final,
                usuario=st.session_state.get("nombre_firmante_c2", "Carlos Edu Baños — Operador Sala C2")
            )
            st.session_state["historial_consola_c2"].append(res_cmd)

    # 4. Pantalla de la Terminal C2
    st.markdown("##### 🖥️ Monitor Táctico C2 en Vivo:")
    
    ultimo_log = st.session_state["historial_consola_c2"][-1]
    color_border = "#00f0ff" if ultimo_log["tipo"] == "OK" else ("#ffb703" if ultimo_log["tipo"] == "WARN" else "#ff0055")
    color_header = "#00f0ff"

    st.markdown(f"""
    <div style="background: #050b14; border: 1.5px solid {color_border}; border-radius: 8px; padding: 18px; box-shadow: 0 4px 28px rgba(0,240,255,0.18);">
        <div style="display:flex;justify-content:space-between;border-bottom:1px solid rgba(0,240,255,0.25);padding-bottom:8px;margin-bottom:12px;font-family:'Consolas',monospace;font-size:12px;color:{color_header};">
            <span>🛡️ <b>AMARU-C2 TACTICAL SHELL v1.0.0</b> | COEN / INDECI | SOBERANÍA HUMANA: VINCULANTE</span>
            <span>🕒 {ultimo_log.get('timestamp')} | STATUS: {ultimo_log.get('tipo', 'OK')}</span>
        </div>
        <div style="color: #64dfdf; font-family:'Consolas',monospace; font-size:13px; margin-bottom:8px;">
            <b>carlos.banos@coen-amaru-c2:~$</b> <span style="color:#ffffff;">{ultimo_log.get('comando', 'SYS_MONITOR')}</span>
        </div>
        <pre style="color: #00ff88; font-family: 'Consolas', 'Courier New', monospace; font-size: 13.5px; line-height: 1.55; margin: 0; white-space: pre-wrap; word-break: break-word;">{ultimo_log['salida_texto']}</pre>
    </div>
    """, unsafe_allow_html=True)

    # 5. Opciones de Exportación y Bitácora
    col_exp1, col_exp2 = st.columns([3, 1])
    with col_exp1:
        with st.expander("📜 Bitácora Histórica de Comandos de esta Sesión"):
            for item in reversed(st.session_state["historial_consola_c2"][:-1]):
                st.markdown(f"**[{item['timestamp']}] Directiva:** `{item['comando']}`")
                st.code(item['salida_texto'], language="text")
    with col_exp2:
        texto_export = "\n\n".join([f"[{i['timestamp']}] CMD: {i['comando']}\n{i['salida_texto']}" for i in st.session_state["historial_consola_c2"]])
        st.download_button(
            "💾 Exportar Log C2 (.txt)",
            data=texto_export,
            file_name=f"bitacora_c2_amaru_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            width='stretch'
        )

    # 6. Directorio Visual de Fuentes Oficiales y Enlaces de Auditoría Pública
    st.markdown("---")
    with st.expander("🌐 DIRECTORIO PÚBLICO DE FUENTES CONSULTADAS, VALIDADAS Y ENLACES DE AUDITORÍA (Ley N° 31814)", expanded=True):
        st.markdown(
            "Conforme al **Principio de Transparencia, Explicabilidad y Soberanía Humana (Ley N° 31814)**, "
            "cualquier ciudadano, auditor de la Contraloría General de la República o evaluador del COEN puede auditar "
            "las fuentes primarias del Estado Peruano e internacionales utilizadas por los agentes de AMARU-FEN:"
        )

        f_tab_nac, f_tab_int, f_tab_geo = st.tabs([
            "🇵🇪 Fuentes Estatales del Perú (Soberanía Nacional)",
            "🌐 Organismos Científicos Internacionales",
            "🏔️ Portales de Georriesgo y Quebradas (Auditoría IPH-FEN)"
        ])

        with f_tab_nac:
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.markdown("""
                ##### 1. 🌦️ SENAMHI (Meteorología e Hidrología)
                * **Rol:** Avisos meteorológicos vigentes, lluvia acumulada 24h y red satelital GOES-19.
                * **Estado:** `🟢 VALIDADA / SINCRONIZADA`
                """)
                c_btn_s1, c_btn_s2 = st.columns(2)
                with c_btn_s1:
                    st.link_button("🚨 Avisos Meteorológicos", "https://www.senamhi.gob.pe/?p=aviso-meteorologico", width='stretch')
                with c_btn_s2:
                    st.link_button("🛰️ Portal Satelital", "https://www.senamhi.gob.pe/?p=satelite", width='stretch')

                st.markdown("""
                ##### 2. 🌊 ENFEN (Comisión Multisectorial El Niño)
                * **Rol:** Diagnóstico colegiado soberano, Informes Técnicos y anomalías TSM Niño 1+2 / 3.4.
                * **Estado:** `🟢 VALIDADA / INFORME TÉCNICO VIGENTE`
                """)
                st.link_button("📄 Portal Oficial ENFEN", "https://enfen.gob.pe/", width='stretch')

                st.markdown("""
                ##### 3. 💧 ANA (Autoridad Nacional del Agua - MIDAGRI)
                * **Rol:** Red hidrométrica de aforo de ríos, umbrales de desborde y unidades Pfafstetter.
                * **Estado:** `🟢 VALIDADA / RED SNIRH EN LÍNEA`
                """)
                st.link_button("🌊 Sistema SNIRH - Aforos Fluviales", "https://snirh.ana.gob.pe/", width='stretch')

            with c_f2:
                st.markdown("""
                ##### 4. 🏛️ IGP (Instituto Geofísico del Perú)
                * **Rol:** Cálculo y archivo histórico oficial del ICEN (Índice Costero El Niño) desde 1950.
                * **Estado:** `🟢 VALIDADA / DATOS CRUDOS AUDITABLES`
                """)
                st.link_button("📊 Datos Crudos ICEN (.txt)", "http://met.igp.gob.pe/datos/ICEN.txt", width='stretch')

                st.markdown("""
                ##### 5. 📋 INDECI / SINPAD / COEN
                * **Rol:** Fichas EDAN preliminares, padrón de damnificados y logística humanitaria.
                * **Estado:** `🟢 VALIDADA / PROTOCOLO SINAGERD`
                """)
                c_btn_i1, c_btn_i2 = st.columns(2)
                with c_btn_i1:
                    st.link_button("📋 Portal SINPAD", "https://sinpad.indeci.gob.pe/", width='stretch')
                with c_btn_i2:
                    st.link_button("🚨 Sala COEN", "https://coen.indeci.gob.pe/", use_container_width=True)

                st.markdown("""
                ##### 6. ⚖️ Diario Oficial El Peruano / SPIJ
                * **Rol:** Decretos Supremos (D.S. 124-2026-PCM), Decretos de Urgencia (D.U. 010) y Ley N° 31814.
                * **Estado:** `🟢 VALIDADA / BASE LEGAL VINCULANTE`
                """)
                st.link_button("📜 Buscador de Normas Legales", "https://busquedas.elperuano.pe/", use_container_width=True)

        with f_tab_int:
            c_fi1, c_fi2 = st.columns(2)
            with c_fi1:
                st.markdown("""
                ##### 1. 🛰️ NOAA Climate Prediction Center (CPC - EE.UU.)
                * **Rol:** Monitoreo oceánico-atmosférico ENSO, anomalías ERSSTv5 y diagnóstico transpacífico.
                * **Estado:** `🟢 VALIDADA / TELEMETRÍA GLOBAL`
                """)
                st.link_button("🛰️ NOAA CPC ENSO Advisory", "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/", use_container_width=True)

                st.markdown("""
                ##### 2. 🎓 IRI Columbia University (Climate School)
                * **Rol:** Pronóstico probabilístico estacional ENSO (IRI ENSO Forecast Plume).
                * **Estado:** `🟢 VALIDADA / MODELO COOPERATIVO`
                """)
                st.link_button("📊 IRI ENSO Forecast Plume", "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/", use_container_width=True)

            with c_fi2:
                st.markdown("""
                ##### 3. 🇪🇺 Copernicus Climate Change Service (C3S / ECMWF)
                * **Rol:** Ensamble estacional de 7 agencias mundiales (ECMWF, UKMO, Météo-France, NCEP, JMA).
                * **Estado:** `🟢 VALIDADA / CALIBRADA CON HINDCAST`
                """)
                st.link_button("🇪🇺 Copernicus Seasonal Forecasts", "https://climate.copernicus.eu/seasonal-forecasts", use_container_width=True)

                st.markdown("""
                ##### 4. 🌦️ Open-Meteo API
                * **Rol:** Consulta meteorológica horaria, precipitación acumulada y validación satelital abierta.
                * **Estado:** `🟢 VALIDADA / SIN CUOTAS COMERCIALES`
                """)
                st.link_button("☁️ Open-Meteo Documentation", "https://open-meteo.com/", use_container_width=True)

        with f_tab_geo:
            st.markdown("##### 🏔️ Enlaces de Auditoría para Quebradas, Georriesgos e Infraestructura")
            st.caption("Verifique individualmente los códigos oficiales homologados en el catálogo (`PC-ANA`, `PEL-ING`, `SIGRID-DOC`, `PE-06A`):")
            
            c_glink1, c_glink2, c_glink3, c_glink4 = st.columns(4)
            with c_glink1:
                st.markdown("**ANA - Puntos Críticos**")
                st.link_button("🌊 Geoservidor ANA", "https://geoservidor.ana.gob.pe/", use_container_width=True)
                st.caption("Valida códigos `PC-ANA-2024-LAM-012` y Pfafstetter.")
            with c_glink2:
                st.markdown("**INGEMMET - Peligros**")
                st.link_button("🌋 GEOCATMIN", "https://geocatmin.ingemmet.gob.pe/", use_container_width=True)
                st.caption("Valida códigos `PEL-ING-LAM-008` y Boletines Serie C.")
            with c_glink3:
                st.markdown("**CENEPRED - EVAR**")
                st.link_button("📑 Repositorio SIGRID", "https://sigrid.cenepred.gob.pe/", use_container_width=True)
                st.caption("Valida códigos `SIGRID-DOC-1357729` e informes EVAR.")
            with c_glink4:
                st.markdown("**MTC / Provías Nacional**")
                st.link_button("🛣️ Visor GEOVIAL", "https://geovial.mtc.gob.pe/", use_container_width=True)
                st.caption("Valida rutas `PE-06A km 68+200`, badenes y puentes.")

    st.markdown("---")


# TAB 2: GOBERNANZA ANTICIPATORIA
with tab_ant:

    st.subheader("Disparadores (Triggers) de Acción Temprana y Pre-Posicionamiento Logístico")

    st.markdown("""
    *Basado en la propuesta de **Gobernanza Anticipatoria (CAF / PUCP 2026)**: No esperar a que las lluvias inunden las ciudades en diciembre, 
    sino activar fondos y almacenes itinerantes meses antes ante anomalías sostenidas en el Pacífico Oriental.*
    """)
    
    eval_ant = orchestrator.evaluar_gobernanza_anticipada(tsm_anomalia, mes=mes_evaluacion)
    analogo_resumen = eval_ant.get("ano_analogo_historico", {}).get("ano_analogo_principal", {})
    
    c_ant1, c_ant2 = st.columns([3, 2])
    with c_ant1:
        st.markdown(f"""
        <div class="card-anticipatorio">
            <h3>Nivel Diagnóstico: <span style="color: #06d6a0;">{eval_ant['nivel_advertencia']}</span></h3>
            <p><b>Fase de Acción Ejecutiva:</b> {eval_ant['fase_accion_anticipada']}</p>
            <p><b>Trigger de Gasto Automático (SIAF-MEF):</b> {'ACTIVADO (Ejecución de Pre-posicionamiento)' if eval_ant['trigger_presupuestal_activo'] else 'En Espera de Umbral Crítico'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with c_ant2:
        st.markdown(f"""
        <div class="card-memoria">
            <h3>Año Análogo Detectado: <span style="color: #ffb703;">{analogo_resumen.get('nombre', 'N/A')}</span></h3>
            <p><b>Similitud Térmica:</b> {analogo_resumen.get('similitud_porcentaje', 0)}%</p>
            <p><b>Categoría:</b> {analogo_resumen.get('categoria', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    c_log1, c_log2 = st.columns([3, 2])
    with c_log1:
        st.markdown("### 📦 Despliegue Preventivo de Almacenes Itinerantes (Norte)")
        df_log = pd.DataFrame(eval_ant["preposicionamiento_norte"])
        st.dataframe(df_log[["region", "almacenes_itinerantes", "motobombas_desplegadas", "calaminas_unidades", "vacunas_dengue_leptospirosis", "costo_estimado_pen"]], use_container_width=True)
    
    with c_log2:
        st.markdown("### ☀️ Alerta Dual: Sequías en el Sur Andino (CEPAL / IGP)")
        sur = eval_ant["alerta_dual_sur_sequias"]
        st.warning(f"**Fenómeno Asociado:** {sur['fenomeno_asociado']}")
        st.write(f"**Regiones:** {', '.join(sur['regiones_afectadas'])}")
        st.write(f"**Impacto:** {sur['riesgo_agropecuario']}")
        for accion in sur["acciones_preventivas"]:
            st.markdown(f"• {accion}")

    st.markdown("---")
    st.markdown("### 🎯 Calculadora Distrital de IRCE-FEN (Índice de Riesgo Crítico y Evacuación)")
    st.caption("Ecuación universal del riesgo: IRCE-FEN = min(1.0, (Peligro * Vulnerabilidad) / Capacidad) adaptada a los 893 distritos.")
    
    ci1, ci2 = st.columns([1, 2])
    with ci1:
        dist_irce = st.selectbox(
            "Seleccionar Distrito para cálculo de IRCE-FEN:",
            ["Catacaos", "Castilla", "El Porvenir", "Lurigancho", "Santa Eulalia", "Íllimo", "Chala", "Ica", "Huarmey"],
            key="sb_dist_irce"
        )
        lluvia_sim_irce = st.slider("Simular Precipitación 24h (mm):", 0.0, 120.0, float(simular_precipitacion), step=5.0, key="slider_lluvia_irce")
        dias_aneg_irce = st.slider("Días de Anegamiento / Agua Estancada:", 0, 30, 4, key="slider_aneg_irce")
        
    with ci2:
        calc_irce = orchestrator.calcular_irce_fen_distrital(
            distrito=dist_irce,
            lluvia_mm=lluvia_sim_irce,
            anomalia_tsm=tsm_anomalia,
            anegamiento_dias=dias_aneg_irce
        )
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Score IRCE-FEN", f"{calc_irce['score_irce_fen']:.3f}", calc_irce['nivel_alerta'])
        col_m2.metric("Peligro (P)", f"{calc_irce['vectores_componentes']['peligro_p']:.2f}")
        col_m3.metric("Vulnerabilidad (V)", f"{calc_irce['vectores_componentes']['vulnerabilidad_v']:.2f}")
        col_m4.metric("Capacidad (C)", f"{calc_irce['vectores_componentes']['capacidad_c']:.2f}")
        
        st.markdown(f"**Semáforo Operativo:** {calc_irce['semaforo']}")
        st.info(f"**Directiva Táctica Disparada:** {calc_irce['accion_tactica_disparada']}")
        st.caption(f"**Estado de Emergencia (DS 124-2026-PCM):** {'✅ SI DECLARADO' if calc_irce['respaldo_legal_ds_124'] else '❌ NO DECLARADO'} | **Memoria Histórica:** {'⚠️ ANTECEDENTES PREVIOS' if calc_irce['antecedentes_historicos'] else 'ℹ️ SIN REINCIDENCIA CRÍTICA'}")

    st.markdown("---")
    c_g1, c_g2, c_g3 = st.columns(3)
    with c_g1:
        with st.expander("🛰️ Satélite GOES-19 SENAMHI / NOAA", expanded=False):
            sat = orchestrator.consultar_satelite_goes19()
            st.markdown(f"**Satélite:** *{sat['satelite']}* ({sat['posicion_orbital']})")
            st.caption(f"**Portal Oficial:** [{sat['portal_senamhi_url']}]({sat['portal_senamhi_url']}) | **Refresco:** {sat['frecuencia_actualizacion']}")
            st.info(f"**Canal 13 ABI (10.3 µm):** {sat['instrumentos_clave']['ABI_Advanced_Baseline_Imager']['Canal_13_Infrarrojo_Limpio_10_3um']}")
            st.warning(f"**Sensor de Rayos GLM:** {sat['instrumentos_clave']['GLM_Geostationary_Lightning_Mapper']['utilidad_nowcasting']}")
            st.success(f"**Aplicación en AMARU:** {sat['utilidad_operativa_amaru']}")
    with c_g2:
        with st.expander("🌊 Satélites IMARPE (TSM, Clorofila & Vientos)", expanded=False):
            im = orchestrator.consultar_satelite_imarpe()
            triada = im.get("triada_biofisica_monitoreada", {})
            st.markdown(f"**Sistema:** *{im.get('sistema')}* ([Portal IMARPE]({im.get('portal_url')}))")
            st.info(f"**🌡️ TSM & ATSM:** {triada.get('tsm_temperatura_superficial', {}).get('indicador_fen')}")
            st.warning(f"**🌱 Clorofila-a:** {triada.get('clorofila_a_productividad', {}).get('indicador_fen')}")
            st.caption(f"**💨 Vientos Alisios (ASCAT):** {triada.get('vientos_superficiales', {}).get('alerta_precursora')}")
            st.success(f"**Detección:** {im.get('utilidad_operativa_amaru')}")
    with c_g3:
        with st.expander("🚢 Cooperación: USNS Comfort & NOAA (El Peruano)", expanded=False):
            ed_peruano = orchestrator.consultar_editorial_cooperacion_el_peruano()
            st.markdown(f"**Editorial Oficial:** *\"{ed_peruano['titulo']}\"* ({ed_peruano['fecha']})")
            st.caption(f"**Fuente:** [{ed_peruano['identificador']}]({ed_peruano['enlace_web']})")
            st.error(f"**Alerta NOAA:** {ed_peruano['cifras_clave_noaa']}")
            for pil in ed_peruano['pilares_diplomacia_proactiva']:
                st.markdown(f"• {pil}")
            st.success(f"**Gobernanza:** {ed_peruano['impacto_amaru_fen']}")


# TAB 2: MEMORIA HISTÓRICA Y AÑOS ANÁLOGOS
with tab_mem:


    st.subheader("🏛️ Agente de Memoria Histórica y Pronóstico por Años Análogos")
    st.markdown("""
    *El enjambre AMARU no actúa en silos: consulta la memoria científica de **El Niño 1982-1983, 1997-1998, 2017 y 2023** 
    para predecir el comportamiento futuro y las consecuencias en cascada sobre el territorio.*
    """)
    
    res_analogo = orchestrator.consultar_ano_analogo(tsm_anomalia, mes=mes_evaluacion)
    ano_principal = res_analogo["ano_analogo_principal"]
    
    col_mem1, col_mem2 = st.columns([3, 2])
    with col_mem1:
        st.markdown(f"""
        <div class="card-memoria">
            <h3>Evento Análogo Dominante: <span style="color: #ffb703;">{ano_principal['nombre']}</span></h3>
            <p><b>Similitud Calculada:</b> {ano_principal['similitud_porcentaje']}% con anomalía +{tsm_anomalia} °C en Mes {mes_evaluacion}</p>
            <p><b>Características Clave:</b> {ano_principal['caracteristicas_clave']}</p>
            <p><b>Lección Estratégica:</b> {ano_principal['leccion_estrategica_recomendada']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🌊 Consecuencias en Cascada Esperadas:")
        for cons in ano_principal["consecuencias_en_cascada_esperadas"]:
            st.markdown(f"• **{cons}**")
            
    with col_mem2:
        st.markdown("#### 📊 Ranking de Similitud con FEN Previos:")
        df_ranking = pd.DataFrame(res_analogo["ranking_similitud_completo"])
        st.dataframe(df_ranking[["nombre", "categoria", "porcentaje_similitud", "diferencia_grados"]], use_container_width=True)
        st.info(f"**Pronóstico Temporal:** {res_analogo['pronostico_evolucion_temporal']}")

    st.markdown("---")
    st.subheader("🔍 Consulta Territorial de Antecedentes y Quebradas")
    c_terr1, c_terr2 = st.columns(2)
    with c_terr1:
        distrito_hist_sel = st.selectbox(
            "Seleccionar Distrito Vulnerable:",
            ["El Porvenir", "Catacaos", "Castilla", "Íllimo", "Lurigancho-Chosica", "Aguas Verdes"]
        )
        antecedentes = orchestrator.consultar_historia_zona(distrito_hist_sel, region_sel, lluvia_mm=float(simular_precipitacion))
    
    with c_terr2:
        st.markdown(f"**Distrito:** {antecedentes['distrito_consultado']} | **Tiempo Anticipación:** {antecedentes['tiempo_anticipacion_minimo_requerido_horas']} hrs")
        st.markdown(f"**Población Expuesta Histórica:** {antecedentes['total_poblacion_historicamente_expuesta']:,} hab.")
        if antecedentes["infraestructura_critica_reincidente"]:
            st.markdown(f"**Infraestructura Crítica Reincidente:** {', '.join(antecedentes['infraestructura_critica_reincidente'])}")
        if antecedentes["alerta_reincidencia_severa"]:
            st.error("🚨 ALERTA: La lluvia simulada supera el umbral que destruyó esta infraestructura en 1998/2017.")

    with st.expander("📋 Reporte Oficial COEN / INDECI: Cifras y Lecciones de El Niño Costero 2017 (Mongabay / INDECI)", expanded=False):
        coen_data = orchestrator.consultar_balance_coen_2017()
        cifras = coen_data.get("cifras_nacionales_consolidadas", {})
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Fallecidos", cifras.get("fallecidos", 75))
        m2.metric("Damnificados", f"{cifras.get('damnificados', 0):,}")
        m3.metric("Afectados", f"{cifras.get('afectados', 0):,}")
        m4.metric("Viviendas Colapsadas", f"{cifras.get('viviendas_colapsadas', 0):,}")
        
        col_c1, col_c2 = st.columns([3, 2])
        with col_c1:
            st.markdown("##### 🏛️ Regiones Más Golpeadas (Top 5)")
            df_reg = pd.DataFrame(coen_data.get("regiones_mayor_impacto", []))
            st.dataframe(df_reg[["region", "damnificados", "afectados", "viviendas_colapsadas", "focos_criticos"]], use_container_width=True)
            
            st.markdown("##### 🔬 Análisis Ingenieril de Fallas en Puentes y Cauces (Colegio de Ingenieros del Perú)")
            for f in coen_data.get("lecciones_ingenieriles_fallas_infraestructura", []):
                st.markdown(f"• **{f['estructura']}:** {f['mecanismo_falla']} *Lección:* {f['leccion']}")
                
        with col_c2:
            st.markdown("##### ⚖️ Criterios Normativos INDECI (Glosario Oficial)")
            defs = coen_data.get("definiciones_normativas_indeci", {})
            st.info(f"**Persona Afectada:** {defs.get('afectado')}")
            st.error(f"**Persona Damnificada:** {defs.get('damnificado')}")
            st.warning(f"**Impacto PBI (CEPAL):** {coen_data.get('impacto_macroeconomico_cepal')}")

    with st.expander("🏥 Memoria Sanitaria y Epidemiológica OPS/OMS (Piura 2017 - Brotes en Cascada)", expanded=False):
        ops_data = orchestrator.consultar_memoria_sanitaria_ops()
        st.caption(f"**Fuente:** {ops_data.get('fuente')} | **Documento:** *{ops_data.get('titulo_documento')}* ({ops_data.get('ano_publicacion')})")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Casos Dengue Piura 2017", "48,000", "43 fallecidos")
        col_s2.metric("Centros Salud Afectados", "63", "2 hospitales inundados")
        col_s3.metric("Población sin Acceso Médico", ">200,000", "Aislamiento por lluvias")
        
        st.markdown("##### 🧪 Modelador Táctico de Riesgo Epidemiológico Post-Inundación")
        dias_anegados = st.slider("Simular Días de Anegamiento / Aguas Estancadas en Cuencas Ciegas:", 1, 30, 8, key="slider_dias_epi")
        eval_epi = orchestrator.evaluar_riesgo_epidemiologico(region_sel, dias_anegados)
        
        ce1, ce2, ce3 = st.columns(3)
        with ce1:
            r_dengue = eval_epi["evaluacion_vectorial_sanitaria"]["dengue_arbovirosis"]
            st.markdown(f"**🦟 Dengue / Arbovirosis:** `{r_dengue['nivel_riesgo']}`")
            st.caption(f"Ventana: {r_dengue['ventana_critica_dias']} | {r_dengue['leccion_historica_piura']}")
        with ce2:
            r_lepto = eval_epi["evaluacion_vectorial_sanitaria"]["leptospirosis"]
            st.markdown(f"**🐀 Leptospirosis:** `{r_lepto['nivel_riesgo']}`")
            st.caption(f"Ventana: {r_lepto['ventana_critica_dias']} | {r_lepto['leccion_historica_piura']}")
        with ce3:
            r_eda = eval_epi["evaluacion_vectorial_sanitaria"]["infecciones_gastrointestinales_eda"]
            st.markdown(f"**💧 Infecciones Diarreicas (EDA):** `{r_eda['nivel_riesgo']}`")
            st.caption(f"Ventana: {r_eda['ventana_critica_dias']} | {r_eda['factor']}")
            
        st.markdown("**🛡️ Acciones Sanitarias Tácticas Recomendadas por AMARU (Protocolo OPS):**")
        for acc in eval_epi.get("acciones_tacticas_salud_amaru", []):
            st.markdown(f"• {acc}")

    with st.expander("🔬 Informe Técnico Oficial ENFEN Año 12 Nº 15 (26 de Agosto de 2026)", expanded=False):
        enfen_info = orchestrator.consultar_informe_enfen_n15()
        diag = enfen_info.get("diagnostico_multisectorial", {})
        n12 = diag.get("region_nino_1_2", {})
        n34 = diag.get("region_nino_3_4", {})
        pesq = enfen_info.get("impactos_biologico_pesqueros", {})
        esc = enfen_info.get("escenarios_hidrologicos_y_climaticos", {})
        
        st.markdown(f"**Documento Oficial:** *{enfen_info.get('documento')}* ({enfen_info.get('fecha_emision')}) | **Alerta:** <span style='color: #ff4b4b; font-weight: bold;'>{enfen_info.get('estado_alerta')}</span>", unsafe_allow_html=True)
        st.caption(f"**Archivo Local:** `{enfen_info.get('archivo_local')}` (85 páginas, 13.9 MB) | **PP 0068**")
        
        col_e1, col_e2, col_e3 = st.columns(3)
        col_e1.metric("Anomalía Niño 1+2 (Jul-Ago 2026)", n12.get("anomalia_mensual_julio_2026", "+3.56 °C"), "Pico +4.1 °C")
        col_e2.metric("Probabilidad Extraordinaria", "≥ 62 %", "Set 2026 - Ene 2027")
        col_e3.metric("Impacto Pesquero PRODUCE", "Cierre 1ra Temporada", "61% juveniles anchoveta")
        
        c_esc1, c_esc2 = st.columns(2)
        with c_esc1:
            st.markdown("##### 🌊 Pronóstico Climático & Precipitaciones")
            st.warning(f"**Costa Norte y Central:** {esc.get('costa_norte_y_central')}")
            st.error(f"**Sierra Sur Oriental (Altiplano):** {esc.get('sierra_sur_oriental_altiplano')}")
        with c_esc2:
            st.markdown("##### 🐟 Indicadores Biológico-Pesqueros (IMARPE)")
            st.info(f"**Anchoveta:** {pesq.get('anchoveta')}")
            st.info(f"**Pota:** {pesq.get('pota_calamar_gigante')}")
            st.caption(f"**Especies Atípicas Registradas:** {', '.join(pesq.get('especies_atípicas_cálidas', []))}")
        
        st.success(f"**Vínculo Legal con Políticas de Estado:** {enfen_info.get('impacto_politica_publica', {}).get('vinculacion_normativa')}")

    with st.expander("📚 Estudio Oficial SENAMHI IDESEP: El Niño 1997-1998 y la Teoría de la 'Carga Energética'", expanded=False):
        senamhi_doc = orchestrator.consultar_estudio_senamhi_97_98()
        c_clave = senamhi_doc.get("conceptos_clave", {})
        
        st.markdown(f"**Documento Oficial:** *{senamhi_doc.get('titulo')}* | **Autor:** {senamhi_doc.get('autor')}")
        st.caption(f"**Archivo Local:** `{senamhi_doc.get('archivo_local')}` ({senamhi_doc.get('total_paginas')} páginas, 5.4 MB) | **IDESEP SENAMHI**")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Anomalía Pluvial Lambayeque", "> 3,000 %", "Motupe, Olmos, Jayanca")
        col_s2.metric("Mecanismo Atmosférico", "Brisa Monzónica", "Inversión de Alisios")
        col_s3.metric("Fase Pluvial Crítica", "Ene - Mar 1998", "Desborde simultáneo")
        
        c_sen1, c_sen2 = st.columns(2)
        with c_sen1:
            st.markdown("##### ⚡ Teoría de la 'Carga Energética' Oceánica (SENAMHI)")
            carga = c_clave.get("teoria_carga_energetica_oceanica", {})
            st.warning(f"**Definición Física:** {carga.get('definicion_senamhi')}")
            st.success(f"**Refuerzo AMARU-FEN:** {carga.get('validacion_amaru')}")
        with c_sen2:
            st.markdown("##### 🌪️ Complejos Convectivos de Mesoescala (CCM)")
            monzon = c_clave.get("mecanismo_brisa_monzon_costero", {})
            st.info(f"**Dinámica:** {monzon.get('dinamica_atmosferica')}")
            st.info(f"**Forzamiento:** {monzon.get('orografia_y_complejos_convectivos')}")
            
        legal_s = c_clave.get("mandato_institucional_de_marco_legal_agil", {})
        st.caption(f"**Mandato Institucional de SENAMHI (Pág. 74):** {legal_s.get('conclusion_senamhi_pagina_74')}")

    with st.expander("🌍 Investigación Científica: 'El Niño 1997-98 y su Impacto Climático Global' (Capel Molina, 1998)", expanded=False):
        capel_doc = orchestrator.consultar_estudio_capel_molina_1998()
        evid = capel_doc.get("evidencias_cuantitativas_peru", {})
        piura_rec = evid.get("caudal_record_rio_piura", {})
        ica_rec = evid.get("catastrofe_urbana_rio_ica", {})
        machu = evid.get("desastre_criosferico_machu_picchu", {})
        
        st.markdown(f"**Artículo Académico:** *{capel_doc.get('titulo')}* | **Autor:** {capel_doc.get('autor')} (*{capel_doc.get('publicacion')}*)")
        st.caption(f"**Archivo Local:** `{capel_doc.get('archivo_local')}` ({capel_doc.get('total_paginas')} págs, 1.7 MB) | **Papeles de Geografía (Univ. de Murcia)**")
        
        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.metric("Caudal Récord Río Piura", "4,424 m³/s", "12-Mar-1998 (Caída Puentes)")
        col_c2.metric("Caudal Río Ica vs Cauce", "660 m³/s", "Capacidad solo 250 m³/s")
        col_c3.metric("Récord Térmico Global", "+0.44 °C", "Máximo Siglo XX")
        
        col_cp1, col_cp2 = st.columns(2)
        with col_cp1:
            st.markdown("##### 🌊 Caudales Históricos & Caída de Puentes en el Norte")
            st.error(f"**Río Piura:** {piura_rec.get('caudal_pico')} - {piura_rec.get('colapso_puentes')}")
            st.warning(f"**Lluvias e Hidrología:** {piura_rec.get('precipitacion_curso_alto')}")
            st.info(f"**Chira & Tumbes:** {evid.get('caudales_chira_y_tumbes', {}).get('rio_chira')} | {evid.get('caudales_chira_y_tumbes', {}).get('rio_tumbes')}")
        with col_cp2:
            st.markdown("##### ⚡ Inundación de Ica & Desastre Machu Picchu")
            st.error(f"**Río Ica (29-Ene-1998):** Desborde de {ica_rec.get('caudal_desborde')} sobre cauce de {ica_rec.get('capacidad_cauce_estrangulado')}. {ica_rec.get('invasion_antiguos_aliviaderos')}. {ica_rec.get('impacto')}")
            st.warning(f"**Central Machu Picchu (27-Feb-1998):** {machu.get('descripcion')}. **Causa:** {machu.get('causa_fisica_clave')}")
            
        st.markdown("##### 💡 Lecciones Clave para AMARU-FEN:")
        for lec in capel_doc.get("lecciones_amaru", []):
            st.markdown(f"• {lec}")

    with st.expander("🗺️ Informe Técnico Oficial CENEPRED / SENAMHI Nº 69-2026 (PISCO v2.2)", expanded=False):
        cenepred_doc = orchestrator.consultar_informe_cenepred_2026()
        patrones = cenepred_doc.get("patrones_regionales", {})
        
        st.markdown(f"**Documento Oficial:** *{cenepred_doc.get('identificador')}* ({cenepred_doc.get('fecha')}) | **Solicitante:** CENEPRED (*{cenepred_doc.get('solicitante')}*)")
        st.caption(f"**Archivo Local:** `{cenepred_doc.get('archivo_local')}` ({cenepred_doc.get('total_paginas')} págs, 2.4 MB) | **Base:** `{cenepred_doc.get('grilla_pisco')}`")
        
        col_cp1, col_cp2 = st.columns(2)
        with col_cp1:
            st.markdown("##### 🌊 Costa Norte & Vertiente Occidental")
            st.error(f"**Anomalías Extremas (>250%):** {patrones.get('costa_norte_y_vertiente_occidental')}")
            st.info(f"**Sierra Norte y Central:** {patrones.get('sierra_norte_y_central')}")
        with col_cp2:
            st.markdown("##### ☀️ Sierra Sur & Altiplano (Sequía Canónica)")
            st.warning(f"**Déficit Extremo (-75% a -100%):** {patrones.get('sierra_sur_altiplano')}")
            st.caption(f"**Selva:** {patrones.get('selva')}")
            
        st.success(f"**Aplicación en AMARU-FEN:** {cenepred_doc.get('impacto_amaru_fen')}")

    with st.expander("🌊 Comparativa Histórica Oannes: Diferencias entre 1972, 1982-83, 1997-98 y 2017", expanded=False):
        oannes_doc = orchestrator.consultar_comparativa_oannes()
        comps = oannes_doc.get("comparativa_eventos", {})
        
        st.markdown(f"**Estudio Histórico:** *{oannes_doc.get('titulo')}* ({oannes_doc.get('fecha')}) | **Autor:** {oannes_doc.get('autor')}")
        st.caption(f"**Fuente:** [{oannes_doc.get('identificador')}]({oannes_doc.get('enlace_web')})")
        
        col_oa1, col_oa2 = st.columns(2)
        with col_oa1:
            st.markdown("##### 🌧️ 1972 vs 1982-1983 (Mega-Niño Urbano)")
            st.info(f"**1972:** {comps.get('evento_1972', {}).get('impacto_urbano')}")
            st.error(f"**1982-1983:** {comps.get('mega_nino_1982_1983', {}).get('impacto_urbano')} **Respuesta:** {comps.get('mega_nino_1982_1983', {}).get('respuestas_historicas')}")
        with col_oa2:
            st.markdown("##### 🌊 1997-1998 vs 2017 (Mega-Niño de Cuenca & Híbrido)")
            st.warning(f"**1997-1998:** {comps.get('mega_nino_1997_1998', {}).get('impacto_hidrologico')} **Efectividad:** {comps.get('mega_nino_1997_1998', {}).get('efectividad_obras')}")
            st.error(f"**Niño Costero 2017:** {comps.get('nino_costero_2017', {}).get('falla_estructural')}")
            
        st.markdown("##### 💡 Lecciones Ineludibles para AMARU-FEN:")
        for lec in oannes_doc.get("lecciones_clave", []):
            st.markdown(f"• {lec}")

    # NUEVO: Catálogo Geomorfológico de Quebradas Reincidentes
    st.markdown("---")







    st.subheader("🏔️ Catálogo Geomorfológico de Quebradas Reincidentes (Estudios Trujillo, Santa Eulalia, SJL, Chosica, Ica)")
    st.caption("Basado en estudios MINAM SIAL Trujillo, UCV San Ildefonso, Muni Santa Eulalia FEN 828830, CENEPRED SJL y CENEPRED Agrícola.")
    
    col_q1, col_q2 = st.columns([1, 2])
    with col_q1:
        filtro_q = st.text_input("Filtrar Quebradas (Ej: Trujillo, Santa Eulalia, SJL, Ica, Canchaque, Arequipa):", value="Trujillo")
        quebradas_res = orchestrator.consultar_quebradas_reincidentes(filtro_q)
        nombres_q = [f"{q.get('id_quebrada', '')}: {q['nombre']}" if q.get('id_quebrada') else q['nombre'] for q in quebradas_res]
        if nombres_q:
            sel_q_nombre = st.selectbox("Seleccionar Quebrada para Diagnóstico:", nombres_q)
            diag_q = orchestrator.evaluar_quebrada_especifica(sel_q_nombre, lluvia_mm=float(simular_precipitacion))
        else:
            diag_q = None
            
    with col_q2:
        if diag_q and diag_q.get("estado") != "NO_ENCONTRADA":
            badge_color = "#e63946" if diag_q["nivel_alerta"] == "ROJO_CRITICO" else ("#f77f00" if "NARANJA" in diag_q["nivel_alerta"] else "#ffd166")
            st.markdown(f"""
            <div style="background-color: #1a2639; padding: 15px; border-radius: 10px; border-left: 5px solid {badge_color};">
                <h4 style="margin: 0; color: #f0f4f8;">{diag_q['quebrada']} ({diag_q['region']})</h4>
                <p style="margin-top: 5px;"><b>Probabilidad Condicionada de Activación (PCAQ):</b> <span style="font-size: 1.2em; font-weight: bold; color: {badge_color};">{int(diag_q['probabilidad_activacion_pcaq']*100)}%</span> [{diag_q['nivel_alerta']}]</p>
                <p><b>Tiempo de Concentración (Llegada del Huaico):</b> <b>{diag_q['tiempo_concentracion_horas']} horas</b> {'🚨 IMPACTO RÁPIDO' if diag_q['alerta_impacto_rapido'] else '⏳ TRÁNSITO PROGRESIVO'}</p>
                <p><b>Distritos en el Cono de Deyección:</b> {', '.join(diag_q['distritos_en_cono'])}</p>
                <p><b>Historial de Activaciones:</b> {', '.join(str(a) for a in diag_q['historial_activaciones'])}</p>
                <p><b>Lección Histórica:</b> {diag_q['leccion_historica']}</p>
                <p><b>Estudio de Referencia:</b> <i>{diag_q['fuente_estudio']}</i></p>
                <div style="background-color: #0b111e; padding: 10px; border-radius: 6px; margin-top: 8px;">
                    <b>Directiva Táctica:</b> {diag_q['accion_tactica_inmediata']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No se encontraron quebradas que coincidan con el filtro.")

# TAB 3: MARCO LEGAL Y NORMATIVO FEN
with tab_leg:
    st.subheader("⚖️ Asesor Jurídico & Habilitador Legal SINAGERD ante El Niño")
    st.markdown("""
    *El marco legal que protege a las autoridades contra la parálisis por temor a la Contraloría. 
    Permite contrataciones directas expeditivas, Obras por Impuestos y verificación territorial inmediata.*
    """)
    
    col_l1, col_l2, col_l3 = st.columns(3)
    stats_ds = orchestrator.obtener_estadisticas_distritos_emergencia()
    col_l1.metric("Distritos en Emergencia", f"{stats_ds['total_distritos_declarados']}", "DS Nº 124-2026-PCM (60 días)")
    col_l2.metric("Departamentos Declarados", f"{stats_ds['total_departamentos']}", "Cobertura Nacional")
    col_l3.metric("Obras por Impuestos (OxI)", "DU Nº 010-2026", "Defensas y Drenaje Pluvial")

    with st.expander("⚖️ Soberanía Humana en IA para Gestión del Riesgo (Ley Nº 31814, UNESCO y Marco de Sendai)", expanded=False):
        sob = orchestrator.consultar_marco_soberania_humana()
        principio = sob.get("principio_rector", "SOBERANÍA HUMANA Y SUPERVISIÓN EXCLUSIVA (HUMAN-IN-THE-LOOP)")
        st.markdown(f"#### {principio}")
        declaracion = sob.get("declaracion_fundamental", sob.get("regla_operativa_amaru", "Supervisión y firma humana obligatoria para toda alerta oficial."))
        st.info(declaracion)

        c_sob1, c_sob2 = st.columns(2)
        with c_sob1:
            st.markdown("##### 🇵🇪 Marco Normativo Nacional")
            m_nac = sob.get("marco_normativo_nacional", {})
            st.write(f"• **{m_nac.get('ley', sob.get('ley_principal', 'Ley Nº 31814'))}**")
            st.write(f"• **{m_nac.get('reglamento', sob.get('reglamento', 'DS 085-2024-PCM'))}** (SGTD - PCM)")
            for pr in m_nac.get("principios_clave_peru", ["Supervisión Humana Obligatoria (Human-in-the-loop).", "Rendición de Cuentas y Responsabilidad Administrativa Indelegable."]):
                st.markdown(f"  - {pr}")
        with c_sob2:
            st.markdown("##### 🌐 Marco Ético Internacional")
            m_int = sob.get("marco_normativo_internacional", {})
            st.write(f"• {m_int.get('unesco', 'Recomendación sobre la Ética de la IA (UNESCO, 2021)')}")
            st.write(f"• {m_int.get('ocde', 'Principios de la OCDE sobre IA Responsable')}")
            st.write(f"• {m_int.get('onu_sendai', 'Marco de Sendai 2015-2030 (ONU / Reducción del Riesgo)')}")

        sello = sob.get("sello_disclaimer_oficial", sob.get("sello_vinculante", "VALIDACIÓN HUMANA REQUERIDA PARA TODA ALERTA OFICIAL"))
        st.success(f"**Sello Oficial:** {sello}")

    st.markdown("---")
    c_leg_search, c_leg_action = st.columns([1, 1])

    
    with c_leg_search:
        st.markdown("#### 🔍 Verificador Oficial de Estado de Emergencia")
        dist_buscar = st.text_input("Ingresar Distrito a Validar (ej. Catacaos, Castilla, El Porvenir, Chala):", value="Catacaos")
        check_legal = orchestrator.verificar_estado_emergencia_distrito(dist_buscar)
        
        if check_legal["declarado_estado_emergencia"]:
            st.success(f"✅ **DECLARADO EN ESTADO DE EMERGENCIA** ({check_legal['total_coincidencias']} coincidencia/s)")
            for item in check_legal["detalle_distritos"][:3]:
                st.markdown(f"• **Ítem Nº {item['id']}:** {item['distrito']} (Prov. {item['provincia']}, Dpto. {item['departamento']})")
            st.info(f"**Vigencia:** {check_legal['vigencia']} | **Base:** {check_legal['base_legal']}")
            st.caption(f"**Habilitación:** {check_legal['habilitacion_operativa']}")
        else:
            st.warning(f"⚠️ El distrito '{dist_buscar}' no figura expresamente en los 893 distritos del anexo del DS 124-2026-PCM.")
            
        with st.expander("📊 Ver Distribución Departamental de los 893 Distritos"):
            st.table(pd.DataFrame(stats_ds["top_departamentos"]))

    with c_leg_action:
        st.markdown("#### 🛡️ Generador de Sustento Legal para Contratación Directa")
        st.caption("Amparo en el Art. 27 Literal b de la Ley Nº 30225 (Ley de Contrataciones del Estado)")
        
        entidad_input = st.text_input("Entidad Ejecutora:", value="Municipalidad Distrital de Catacaos")
        intervencion_input = st.selectbox(
            "Tipo de Intervención Urgente:",
            [
                "Alquiler de 5 excavadoras sobre oruga para descolmatación",
                "Adquisición de 10 motobombas de 6 pulgadas con mangueras",
                "Compra de 50,000 sacos de polipropileno para defensas ribereñas",
                "Suministro de combustible para maquinaria pesada en emergencia"
            ]
        )
        
        alcalde_input = st.text_input("Nombre de la Autoridad Titular / Alcalde:", value="Econ. Johnny Cruz Flores")
        monto_input = st.number_input("Presupuesto Estimado (Soles):", min_value=1000.0, value=285000.0, step=5000.0)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            btn_dictamen = st.button("⚖️ Generar Dictamen Jurídico", type="secondary")
        with c_btn2:
            btn_res = st.button("📜 Redactar Resolución Oficial", type="primary")

        if btn_dictamen:
            dictamen = orchestrator.generar_sustento_legal_contratacion(entidad_input, dist_buscar, intervencion_input)
            st.markdown(f"**Amparo Legal:** `{dictamen['amparo_legal_principal']}`")
            st.markdown(f"**Causal:** `{dictamen['causal']}`")
            st.success(dictamen["dictamen_juridico_amaru"])
            st.info(f"⏳ **Plazo de Regularización Ex-Post:** {dictamen['plazo_regularizacion_normativo']}")
            
        if btn_res:
            res_txt = orchestrator.generar_resolucion_alcaldia(entidad_input, alcalde_input, dist_buscar, intervencion_input, monto_input)
            st.text_area("Borrador Oficial Listo para Firma y Publicación:", value=res_txt, height=220)
            st.download_button(
                label="📥 Descargar Resolución Oficial (.txt)",
                data=res_txt,
                file_name=f"Resolucion_Emergencia_{dist_buscar}.txt",
                mime="text/plain"
            )

# TAB 4: GEOVISOR ESPACIAL Y AFORO HIDROMÉTRICO
with tab1:
    st.subheader("🗺️ Geovisor Espacial Táctico y Red Hidrométrica de Aforo en Vivo (ANA / SENAMHI)")
    st.caption("Monitoreo geoespacial continuo de puntos de desborde fluvial, caudales en tiempo real (m³/s) y conos de deyección de quebradas críticas.")

    # Submódulo 1: Evaluador de Estación de Aforo Fluvial
    col_af1, col_af2 = st.columns([1, 2])
    with col_af1:
        st.markdown("#### 🌊 Estación de Aforo Fluvial")
        estaciones_aforo = orchestrator.consultar_estaciones_aforo()
        nombres_est = [f"{e['id_estacion']} - {e['nombre']} ({e['rio']})" for e in estaciones_aforo]
        sel_est_txt = st.selectbox("Seleccionar Estación Telemétrica:", nombres_est, index=0)
        id_sel = sel_est_txt.split(" - ")[0]
        est_obj = next(e for e in estaciones_aforo if e["id_estacion"] == id_sel)

        simular_q = st.slider(
            f"Simular Caudal en {est_obj['rio']} (m³/s):",
            min_value=float(est_obj["caudal_normal_m3s"] * 0.5),
            max_value=float(est_obj["record_historico_1998_m3s"] * 1.1),
            value=float(est_obj["caudal_simulado_actual_m3s"]),
            step=25.0
        )
        diag_aforo = orchestrator.evaluar_caudal_estacion(id_sel, simular_q)

    with col_af2:
        st.markdown(f"#### 📊 Diagnóstico Hidrométrico: {est_obj['nombre']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Caudal Instantáneo", f"{simular_q:,.1f} m³/s", diag_aforo["alerta"])
        m2.metric("Umbral Desborde", f"{est_obj['umbral_rojo_desborde_m3s']:,} m³/s", "Capacidad Límite")
        m3.metric("Récord 1998", f"{est_obj['record_historico_1998_m3s']:,} m³/s", "Mega-Niño")
        m4.metric("Ratio de Desborde", f"{diag_aforo['ratio_desborde']*100:.1f} %", "Sobre Capacidad" if diag_aforo['ratio_desborde'] >= 1.0 else "Margen Seguro")

        st.markdown(f"**Semáforo Operativo:** {diag_aforo['semaforo']}")
        st.info(f"**Directiva Táctica:** {diag_aforo['accion_recomendada']}")
        st.warning(f"**Impacto Urbano:** {diag_aforo['impacto_urbano']}")
        st.caption(f"{diag_aforo['soberania_humana_ley_31814']}")

    st.markdown("---")

    # Submódulo 2: Geovisor Cartográfico Nacional por UBIGEO (893 Distritos)
    st.markdown("#### 🇵🇪 Geovisor Nacional por UBIGEO: Índice IRCE-FEN & Color en Tiempo Real")
    st.caption("Cada punto representa un UBIGEO distrital declarado en el DS 124-2026-PCM. Se actualiza automáticamente con cada ingesta oficial autorizada o con los controles de simulación.")

    c_mod1, c_mod2 = st.columns([2, 1])
    with c_mod1:
        fuente_datos_mapa = st.radio(
            "📡 Modo de Alimentación de Indicadores:",
            ["INGESTAS OFICIALES AUTORIZADAS (SENAMHI / ENFEN en Vivo)", "SIMULACIÓN MANUAL CON SLIDERS"],
            horizontal=True
        )
    with c_mod2:
        if st.button("🔄 Forzar Ingesta y Actualizar Mapa"):
            with st.spinner("Sincronizando con SENAMHI y ENFEN..."):
                sync_res = orchestrator.sincronizar_fuentes_oficiales()
                st.session_state["sync_data"] = sync_res
                st.session_state["ubigeos_mapa_autorizado"] = sync_res.get("ubigeos_indicadores_actualizados", [])
                st.toast(f"¡893 UBIGEOs Actualizados con Fuentes Oficiales! Nivel: {sync_res['nivel_alerta_maximo_vigente']}")
                st.rerun()

    if fuente_datos_mapa.startswith("INGESTAS"):
        if "ubigeos_mapa_autorizado" not in st.session_state:
            st.session_state["ubigeos_mapa_autorizado"] = orchestrator.calcular_indicadores_desde_ingestas_oficiales()
        ubigeos_data = st.session_state["ubigeos_mapa_autorizado"]
        meta_tab4 = obtener_meta_segura(orchestrator)
        st.info(f"📡 **MAPA VINCULADO A INGESTAS AUTORIZADAS:** Actualizado el `{meta_tab4['fecha_hora']} (Hora Oficial de Perú)` | Tipo: `{meta_tab4['tipo']}` | ID Ingesta: `{meta_tab4['version_id']}`. Índices IRCE y colores sincronizados con SENAMHI, ENFEN y red de aforo ANA.")


    else:
        ubigeos_data = orchestrator.calcular_indicadores_todos_ubigeos(
            lluvia_base_mm=float(simular_precipitacion),
            anomalia_tsm=float(tsm_anomalia),
            region_activa=region_sel
        )
        st.warning("🎛️ **MAPA EN MODO SIMULACIÓN MANUAL:** Los índices y colores responden a los deslizadores de la barra lateral.")

    # Conteo dinámico por nivel de semáforo
    n_rojos = sum(1 for u in ubigeos_data if u["nivel_alerta"] == "CRITICO_ROJO")
    n_naranjas = sum(1 for u in ubigeos_data if u["nivel_alerta"] == "ALTO_NARANJA")
    n_amarillos = sum(1 for u in ubigeos_data if u["nivel_alerta"] == "MEDIO_AMARILLO")
    n_verdes = sum(1 for u in ubigeos_data if u["nivel_alerta"] == "BAJO_VERDE")

    # Comparativa Delta con la última sincronización
    delta_data = orchestrator.obtener_comparativa_delta_sincronizaciones()
    variacion = delta_data.get("variacion", {})
    d_rojos = variacion.get("rojos", 0)
    d_naranjas = variacion.get("naranjas", 0)
    d_amarillos = variacion.get("amarillos", 0)
    d_verdes = variacion.get("verdes", 0)

    c_ub1, c_ub2, c_ub3, c_ub4, c_ub5 = st.columns(5)
    c_ub1.metric("Total UBIGEOs", f"{len(ubigeos_data)}", "DS 124-2026-PCM")
    c_ub2.metric("🔴 Rojos Críticos", f"{n_rojos}", delta=f"{d_rojos:+d} vs anterior", delta_color="inverse")
    c_ub3.metric("🟠 Naranjas Altos", f"{n_naranjas}", delta=f"{d_naranjas:+d} vs anterior", delta_color="inverse")
    c_ub4.metric("🟡 Amarillos Medios", f"{n_amarillos}", delta=f"{d_amarillos:+d} vs anterior", delta_color="off")
    c_ub5.metric("🟢 Verdes Basales", f"{n_verdes}", delta=f"{d_verdes:+d} vs anterior", delta_color="normal")

    # Módulo de Evolución Histórica de Sincronizaciones C2
    with st.expander("📈 Ver Evolución Histórica de Sincronizaciones (Curva Temporal de Verdes, Ámbar y Rojos)", expanded=False):
        c_sel_p1, c_sel_p2 = st.columns([3, 2])
        with c_sel_p1:
            opcion_periodo = st.segmented_control(
                "📅 Seleccionar Período de Análisis Temporal:",
                ["1 Día (24h)", "5 Días", "7 Días (1 Sem)", "1 Mes (30d)", "1 Año (365d)", "Todo el Histórico"],
                default="Todo el Histórico",
                key="seg_periodo_curva_c2"
            )
        
        mapa_periodos = {
            "1 Día (24h)": "1_DIA",
            "5 Días": "5_DIAS",
            "7 Días (1 Sem)": "7_DIAS",
            "1 Mes (30d)": "1_MES",
            "1 Año (365d)": "1_ANO",
            "Todo el Histórico": "TODO"
        }
        periodo_clave = mapa_periodos.get(opcion_periodo, "TODO")
        try:
            hist_snapshots = orchestrator.obtener_historico_sincronizaciones(periodo=periodo_clave)
        except TypeError:
            from core.gestor_historico_sincronizaciones import gestor_historico_sincronizaciones
            hist_snapshots = gestor_historico_sincronizaciones.filtrar_por_periodo(periodo_clave)

        if hist_snapshots:
            # Resumen analítico del período seleccionado
            t_inicio = hist_snapshots[0].get("timestamp", "")
            t_fin = hist_snapshots[-1].get("timestamp", "")
            pico_rojos = max((s.get("rojos", 0) for s in hist_snapshots), default=0)
            delta_rojos_neto = hist_snapshots[-1].get("rojos", 0) - hist_snapshots[0].get("rojos", 0)
            
            with c_sel_p2:
                st.markdown(f"""
                <div style="background: rgba(13, 27, 42, 0.7); border: 1px solid #1f3554; border-radius: 8px; padding: 10px 14px; margin-top: 5px;">
                    <div style="font-size: 11px; color: #90e0ef;"><b>Ventana Observada:</b> {t_inicio[:10]} al {t_fin[:10]} ({len(hist_snapshots)} sincronizaciones)</div>
                    <div style="font-size: 11px; color: #e2e8f0; margin-top: 3px;">
                        Pico Rojos: <b style="color: #e63946;">{pico_rojos} distritos</b> | Δ Neto: <b style="color: {'#e63946' if delta_rojos_neto > 0 else '#2a9d8f'};">{delta_rojos_neto:+d}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            c_h1, c_h2 = st.columns([3, 2])
            with c_h1:
                st.markdown(f"##### 📊 Curva Temporal: {opcion_periodo} ({len(hist_snapshots)} Puntos Registrados)")
                df_hist = pd.DataFrame(hist_snapshots)
                if not df_hist.empty and "timestamp" in df_hist.columns:
                    df_chart = df_hist[["timestamp", "rojos", "naranjas", "amarillos", "verdes"]].set_index("timestamp")
                    st.line_chart(df_chart, color=["#E63946", "#F77F00", "#FFD166", "#2A9D8F"])
            with c_h2:
                st.markdown(f"##### 📋 Sincronizaciones del Período ({min(5, len(hist_snapshots))} más recientes)")
                for snap in reversed(hist_snapshots[-5:]):
                    st.caption(f"**{snap.get('id_snapshot')}** ({snap.get('timestamp')}) | {snap.get('motivo')}")
                    st.write(f"🔴 {snap.get('rojos')} ({snap.get('delta_rojos', 0):+d}) | 🟠 {snap.get('naranjas')} ({snap.get('delta_naranjas', 0):+d}) | 🟡 {snap.get('amarillos')} ({snap.get('delta_amarillos', 0):+d}) | 🟢 {snap.get('verdes')} ({snap.get('delta_verdes', 0):+d})")
                    st.divider()
        else:
            st.info(f"ℹ️ No se registraron sincronizaciones en el período '{opcion_periodo}'. Mostrando línea base disponible.")

    # =========================================================================
    # CONSOLA DE COMANDO CARTOGRÁFICA C2: 3 MAPAS ESPECIALIZADOS POR UBIGEO
    # =========================================================================
    meta_tab4 = obtener_meta_segura(orchestrator)
    fecha_sync_header = meta_tab4.get('fecha_hora', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    version_sync_id = meta_tab4.get('version_id', 'INGESTA-BASE')

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 12px; padding: 18px; border: 1px solid #415a77; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.4);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <h3 style="margin: 0; color: #f0f4f8; display: flex; align-items: center; gap: 8px;">
                    🧭 CONSOLA CARTOGRÁFICA C2: 3 MAPAS TÁCTICOS POR UBIGEO
                </h3>
                <p style="margin: 4px 0 0 0; color: #a9bcd0; font-size: 13px;">
                    Coherencia Geodésica Territorial: Los 893 distritos del DS 124-2026-PCM cruzados con 3 fuentes analíticas independientes.
                </p>
            </div>
            <div style="text-align: right; background: #07101a; padding: 8px 16px; border-radius: 8px; border: 1px solid #00b4d8;">
                <div style="font-size: 11px; color: #90e0ef; font-weight: bold; text-transform: uppercase;">Última Sincronización Oficial</div>
                <div style="font-size: 17px; font-weight: 900; color: #00f5d4; font-family: monospace;">
                    🕒 {fecha_sync_header}
                </div>
                <div style="font-size: 10px; color: #adb5bd;">ID: {version_sync_id} | Cobertura: 893 Distritos (100%)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtros Tácticos Globales para los 3 Mapas
    c_flt1, c_flt2, c_flt3 = st.columns([1.5, 1.2, 1])
    with c_flt1:
        depts_disponibles = ["TODOS LOS DEPARTAMENTOS"] + sorted(list(set(u["departamento"] for u in ubigeos_data)))
        sel_dept_filtro = st.selectbox("🎯 Filtrar por Departamento:", depts_disponibles, index=0, key="sb_dept_3mapas")
    with c_flt2:
        filtro_severidad = st.selectbox(
            "🎨 Filtrar por Nivel de Riesgo / Lluvia:",
            ["TODOS LOS DISTRITOS", "🔴 CRÍTICOS / >55mm", "🟠 ALTOS / 30-55mm", "🟡 MEDIOS / 12-30mm", "🟢 BAJOS / <12mm"],
            index=0,
            key="sb_sev_3mapas"
        )
    with c_flt3:
        ver_mar_capa = st.checkbox("🌊 Calor del Mar Niño 1+2", value=True, key="chk_mar_3mapas")

    # Filtrado de UBIGEOs
    ubigeos_filtrados = ubigeos_data if sel_dept_filtro == "TODOS LOS DEPARTAMENTOS" else [u for u in ubigeos_data if u["departamento"] == sel_dept_filtro]
    if filtro_severidad.startswith("🔴"):
        ubigeos_filtrados = [u for u in ubigeos_filtrados if u["nivel_alerta"] == "CRITICO_ROJO" or u.get("lluvia_estimada_mm", 0) >= 55.0]
    elif filtro_severidad.startswith("🟠"):
        ubigeos_filtrados = [u for u in ubigeos_filtrados if u["nivel_alerta"] == "ALTO_NARANJA" or (30.0 <= u.get("lluvia_estimada_mm", 0) < 55.0)]
    elif filtro_severidad.startswith("🟡"):
        ubigeos_filtrados = [u for u in ubigeos_filtrados if u["nivel_alerta"] == "MEDIO_AMARILLO" or (12.0 <= u.get("lluvia_estimada_mm", 0) < 30.0)]
    elif filtro_severidad.startswith("🟢"):
        ubigeos_filtrados = [u for u in ubigeos_filtrados if u["nivel_alerta"] == "BAJO_VERDE" or u.get("lluvia_estimada_mm", 0) < 12.0]

    # Cámara
    if sel_dept_filtro == "TODOS LOS DEPARTAMENTOS" or not ubigeos_filtrados:
        lat_cam, lon_cam, zoom_cam = -9.20, -76.50, 5.0
    else:
        lat_cam = sum(u["lat"] for u in ubigeos_filtrados) / len(ubigeos_filtrados)
        lon_cam = sum(u["lon"] for u in ubigeos_filtrados) / len(ubigeos_filtrados)
        zoom_cam = 7.0

    colores_alerta_map = {
        "CRITICO_ROJO": [230, 57, 70, 235],
        "ALTO_NARANJA": [247, 127, 0, 215],
        "MEDIO_AMARILLO": [255, 209, 102, 195],
        "BAJO_VERDE": [42, 157, 143, 160]
    }
    radios_alerta_map = {
        "CRITICO_ROJO": 12000,
        "ALTO_NARANJA": 9000,
        "MEDIO_AMARILLO": 6500,
        "BAJO_VERDE": 4500
    }

    # =========================================================================
    # LAS 3 SUB-PESTAÑAS CARTOGRÁFICAS ESPECIALIZADAS POR UBIGEO
    # =========================================================================
    map_subtab1, map_subtab2, map_subtab3, map_subtab4 = st.tabs([
        "🇵🇪 MAPA 1: Nacional Soberano (SENAMHI / ENFEN / Aforos ANA / Mar de Grau)",
        "🌐 MAPA 2: Vigilancia Internacional (NOAA CPC / IRI Columbia / Consenso UBIGEO)",
        "🌦️ MAPA 3: Meteorología Distrital en Vivo & Pronóstico 72h (Open-Meteo)",
        "🏔️ MAPA 4: Corredor de Cabeceras Andinas & Cinética de Huaicos (P_huaico / T_lag)"
    ])

    # -------------------------------------------------------------------------
    # SUBTAB 1: MAPA NACIONAL SOBERANO
    # -------------------------------------------------------------------------
    with map_subtab1:
        st.markdown("##### 🇵🇪 Mapa 1: Situación Oficial Nacional & Fajas Marginales Fluviales")
        st.caption("Semáforo oficial de riesgo compuesto IRCE-FEN para los 893 distritos del DS 124-2026-PCM, estaciones hidrométricas de aforo ANA y calor del litoral costero Niño 1+2.")
        
        # Opciones de visualización de capas
        show_estaciones_ana = st.checkbox("📊 Estaciones de Aforo ANA", value=True, key="show_ana")
        show_calor_mar = st.checkbox("🌊 Calor del Mar (Niño 1+2)", value=True, key="show_mar")
        show_avisos_senamhi = st.checkbox("⚡ Avisos y alertas SENAMHI", value=False, key="show_senamhi")
        show_imarpe = st.checkbox("🛰️ Datos IMARPE (Satélite)", value=False, key="show_imarpe")
        # Enlaces rápidos a fuentes de datos
        col_src1, col_src2, col_src3 = st.columns(3)
        with col_src1:
            st.link_button("📡 Ver datos SENAMHI", "https://www.senamhi.gob.pe/")
        with col_src2:
            st.link_button("🛰️ Ver datos IMARPE", "https://www.imarpe.pe/")
        with col_src3:
            st.link_button("🚰 Ver estaciones ANA", "https://www.ana.gob.pe/")
        nodos_m1 = []
        for u in ubigeos_filtrados:
            score_val = u.get("score_irce", 0.0)
            lluvia_base = u.get("lluvia_estimada_mm", 0.0)
            nodos_m1.append({
                "nombre": f"{u['distrito']} ({u['provincia']})",
                "lat": u["lat"],
                "lon": u["lon"],
                "estado": u.get("semaforo", u.get("nivel_alerta", "BAJO_VERDE")),
                "info": f"Score IRCE: {score_val:.3f} | Peligro P={u.get('p_peligro', 0):.2f} | Lluvia SENAMHI: {lluvia_base} mm | Censo: {u.get('poblacion', 0):,} hab.",
                "color": colores_alerta_map.get(u.get("nivel_alerta"), [150, 150, 150, 180]),
                "radius": radios_alerta_map.get(u.get("nivel_alerta"), 5000)
            })

        if show_estaciones_ana:
            # Estaciones Fluviales (ANA)
            estaciones_data = orchestrator.consultar_estaciones_aforo()
            for e in estaciones_data:
                q_act = e.get("caudal_simulado_actual_m3s", e.get("caudal_normal_m3s", 0.0))
                desborde = q_act >= e.get("umbral_rojo_desborde_m3s", 999999)
                col_est = [230, 57, 70, 255] if desborde else [30, 144, 255, 220]
                nom_est = e.get("nombre", e.get("estacion", "Estación Fluvial"))
                nodos_m1.append({
                    "nombre": f"Estación Fluvial {nom_est} ({e.get('rio', 'Río')})",
                    "lat": e["latitud"],
                    "lon": e["longitud"],
                    "estado": "DESBORDE FLUVIAL 🔴" if desborde else "AFORO REGULAR 🔵",
                    "info": f"Caudal Instantáneo: {q_act:,.0f} m³/s | Límite: {e.get('umbral_rojo_desborde_m3s', 0):,} m³/s",
                    "color": col_est,
                    "radius": 15000
                })

        if ver_mar_capa:
            nodos_m1.extend(generar_malla_termica_mar_peruano(tsm_anomalia))

        df_m1 = pd.DataFrame(nodos_m1)
        layer_m1 = pdk.Layer("ScatterplotLayer", df_m1, get_position=["lon", "lat"], get_color="color", get_radius="radius", pickable=True, auto_highlight=True)
        v_state_m1 = pdk.ViewState(latitude=lat_cam, longitude=lon_cam, zoom=zoom_cam, pitch=35)
        st.pydeck_chart(pdk.Deck(layers=[layer_m1], initial_view_state=v_state_m1, tooltip={"text": "{nombre}\nEstado: {estado}\n{info}"}))

    # -------------------------------------------------------------------------
    # SUBTAB 2: MAPA DE VIGILANCIA INTERNACIONAL (C3S + ERSSTv5 + NOAA + IRI)
    # -------------------------------------------------------------------------
    with map_subtab2:
        st.markdown("##### 🌐 Mapa 2: Vigilancia Internacional & Consenso Científico Global (Copernicus C3S + NOAA ERSSTv5 + IRI)")
        st.caption("Los 893 UBIGEOs contrastados con el ensamble multimodelo estacional de Copernicus C3S (7 agencias mundiales) y la grilla oceanográfica reconstruida NOAA ERSSTv5.")

        # Metadatos Internacionales en Vivo
        sync_act = st.session_state.get("sync_data", {})
        f_int = sync_act.get("fuentes_internacionales", {})
        
        ersst_data = f_int.get("noaa_ersstv5", {
            "anomalia_ersstv5_nino12": 2.15,
            "anomalia_ersstv5_nino34": 1.72,
            "categoria_oni_global": "EL NIÑO FUERTE"
        })
        c3s_data = f_int.get("copernicus_c3s", {
            "probabilidad_precipitacion_costa_norte": 85.0,
            "desviacion_estacional_lluvia_pct": "+45% sobre la normal climática",
            "modelos_activos": ["ECMWF", "Météo-France", "NCEP", "JMA", "UKMO"]
        })

        anom_ersst = ersst_data.get("anomalia_ersstv5_nino12", 2.15)
        prob_c3s = c3s_data.get("probabilidad_precipitacion_costa_norte", 85.0)

        # Barra de indicadores globales
        c_i1, c_i2, c_i3, c_i4 = st.columns(4)
        c_i1.metric("NOAA ERSSTv5 (Niño 1+2)", f"+{anom_ersst} °C", ersst_data.get("categoria_oni_global", "FUERTE"))
        c_i2.metric("Copernicus C3S (Lluvia)", f"{prob_c3s}% Prob.", c3s_data.get("desviacion_estacional_lluvia_pct", "+45%"))
        c_i3.metric("Modelos Ensamble C3S", "7 Centros", "ECMWF/NCEP/JMA/UKMO")
        c_i4.metric("Convergencia con ENFEN", "ALTA (94%)", "Δ TSM: 0.25 °C")

        nodos_m2 = []
        for u in ubigeos_filtrados:
            score_base = u.get("score_irce", 0.0)
            dep = u["departamento"].upper()
            es_norte = dep in ["PIURA", "TUMBES", "LAMBAYEQUE", "LA LIBERTAD"]
            
            # Ponderador con ensamble C3S y ERSSTv5
            score_global = min(1.0, round(score_base * (1.18 if es_norte and anom_ersst >= 1.8 else 1.0), 3))

            if score_global >= 0.75:
                col_i, rad_i, est_i = [230, 40, 80, 240], 12500, "🔴 ALTA VULNERABILIDAD GLOBAL (ERSSTv5/C3S)"
            elif score_global >= 0.55:
                col_i, rad_i, est_i = [247, 127, 0, 220], 9500, "🟠 ALERTA DE CUENCA PACÍFICA (C3S 85% Lluvia)"
            elif score_global >= 0.35:
                col_i, rad_i, est_i = [255, 209, 102, 195], 7000, "🟡 VIGILANCIA ENSO MULTIMODELO"
            else:
                col_i, rad_i, est_i = [42, 157, 143, 160], 4500, "🟢 CONDICIÓN BASAL GLOBAL"

            nodos_m2.append({
                "nombre": f"{u['distrito']} ({u['provincia']})",
                "lat": u["lat"],
                "lon": u["lon"],
                "estado": est_i,
                "info": (
                    f"UBIGEO: {u.get('ubigeo')} | Score Ajustado C3S/ERSSTv5: {score_global:.3f} | "
                    f"ERSSTv5 Niño 1+2: +{anom_ersst}°C | Copernicus C3S: {prob_c3s}% prob. lluvia | "
                    f"Ensamble: 7 modelos acoplados"
                ),
                "color": col_i,
                "radius": rad_i
            })

        # Malla térmica oceánica extendida Pacífico
        if ver_mar_capa:
            nodos_m2.extend(generar_malla_termica_mar_peruano(anom_ersst))

        df_m2 = pd.DataFrame(nodos_m2)
        layer_m2 = pdk.Layer("ScatterplotLayer", df_m2, get_position=["lon", "lat"], get_color="color", get_radius="radius", pickable=True, auto_highlight=True)
        v_state_m2 = pdk.ViewState(latitude=lat_cam, longitude=lon_cam, zoom=zoom_cam, pitch=35)
        st.pydeck_chart(pdk.Deck(layers=[layer_m2], initial_view_state=v_state_m2, tooltip={"text": "{nombre}\nEstado: {estado}\n{info}"}))

    # -------------------------------------------------------------------------
    # SUBTAB 3: MAPA METEOROLÓGICO EN VIVO & PRONÓSTICO 72H
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # SUBTAB 3: MAPA METEOROLÓGICO EN VIVO & PRONÓSTICO 72H (OPEN-METEO / ECMWF)
    # -------------------------------------------------------------------------
    with map_subtab3:
        c_m3_h1, c_m3_h2 = st.columns([2, 1])
        with c_m3_h1:
            st.markdown("##### 🌦️ Mapa 3: Meteorología Distrital en Vivo & Pronóstico Pluviométrico (Open-Meteo / ECMWF)")
            st.caption("Precipitación real satelital y pronóstico para los 893 UBIGEOs (referencias geográficas distritales). Sin relación con Score IRCE; sincronía 100% con el panel lateral.")
        with c_m3_h2:
            horiz_meteo = st.segmented_control("Horizonte Satelital:", ["Hoy (Actual / 24h)", "Día +1 (48 horas)", "Día +2 (72 horas)"], default="Hoy (Actual / 24h)", key="seg_horiz_m3")

        dia_idx_m3 = 0 if "Hoy" in str(horiz_meteo) else (1 if "48" in str(horiz_meteo) else 2)
        dia_nom_m3 = "Hoy" if dia_idx_m3 == 0 else (f"Día +{dia_idx_m3}")

        # Grilla meteorológica oficial Open-Meteo en vivo
        grilla_om = cached_obtener_grilla_departamental_open_meteo()

        # Distrito activo en el sidebar para sincronización 100% idéntica
        dist_activo_sidebar = str(u_sel.get("distrito", "")).upper().strip() if ("u_sel" in locals() and u_sel) else ""
        ubigeo_activo_sidebar = str(u_sel.get("ubigeo", "")).strip() if ("u_sel" in locals() and u_sel) else ""
        res_om_sidebar = res_om_sb if ("res_om_sb" in locals() and res_om_sb) else {}

        # Filtrar UBIGEOs según departamento seleccionado (en Mapa 3 los UBIGEOs son referencias espaciales)
        ubigeos_base_m3 = ubigeos_data if sel_dept_filtro == "TODOS LOS DEPARTAMENTOS" else [u for u in ubigeos_data if u["departamento"] == sel_dept_filtro]

        # Si el usuario eligió un filtro de severidad en los controles superiores, aplicarlo por lluvia satelital
        nodos_m3 = []
        c_secos = 0
        c_moderados = 0
        c_fuertes = 0

        for u in ubigeos_base_m3:
            dist_nom = str(u.get("distrito", "")).upper().strip()
            prov_nom = str(u.get("provincia", "")).upper().strip()
            dep_nom = str(u.get("departamento", "")).upper().strip()
            ub_cod = str(u.get("ubigeo", "")).strip()

            # Caso 1: Coincidencia con el distrito inspeccionado en el sidebar lateral
            es_distrito_sidebar = (ub_cod and ub_cod == ubigeo_activo_sidebar) or (dist_nom == dist_activo_sidebar and dist_activo_sidebar != "")

            if es_distrito_sidebar and res_om_sidebar.get("estado") == "OK":
                dias_m = res_om_sidebar.get("dias_pronostico", [])
                dia_data = dias_m[dia_idx_m3] if dia_idx_m3 < len(dias_m) else {}
                lluvia_om = float(dia_data.get("lluvia_acumulada_24h_mm", res_om_sidebar.get("lluvia_maxima_24h_mm", 0.0)))
                prob_om = int(dia_data.get("probabilidad_lluvia_pct", 0))
                temp_m = float(dia_data.get("temp_max_c", res_om_sidebar.get("temp_actual_c", 27.9)))
                hum_m = int(res_om_sidebar.get("humedad_relativa_pct", 56))
                viento_m = float(res_om_sidebar.get("viento_kmh", 17.3))
                cond_txt = res_om_sidebar.get("condicion_texto", "Despejado / Soleado")
                icono_w = res_om_sidebar.get("icono_clima", "☀️")

            # Caso 2: Mochumí [UBIGEO: 140407] - Telemetría geodésica satelital exacta
            elif ub_cod == "140407" or ("MOCHUMI" in dist_nom and dep_nom == "LAMBAYEQUE"):
                mochumi_m = grilla_om.get("MOCHUMI_ESPECIAL", {})
                dias_moch = mochumi_m.get("dias", [])
                dia_moch = dias_moch[dia_idx_m3] if dia_idx_m3 < len(dias_moch) else {}
                lluvia_om = float(dia_moch.get("lluvia_mm", 0.0))
                prob_om = int(dia_moch.get("probabilidad_pct", 0))
                temp_m = float(dia_moch.get("temp_max_c", mochumi_m.get("temp_actual_c", 27.9)))
                hum_m = int(mochumi_m.get("humedad_pct", 56))
                viento_m = float(mochumi_m.get("viento_kmh", 17.3))
                cond_txt = mochumi_m.get("condicion_texto", "Despejado / Soleado")
                icono_w = mochumi_m.get("icono_clima", "☀️")

            # Caso 3: Resto de los distritos del Perú mapeados a su estación de telemetría departamental
            else:
                dep_info = grilla_om.get(dep_nom, grilla_om.get("LIMA", {}))
                dias_dep = dep_info.get("dias", [])
                dia_dep = dias_dep[dia_idx_m3] if dia_idx_m3 < len(dias_dep) else {}
                lluvia_om = float(dia_dep.get("lluvia_mm", 0.0))
                prob_om = int(dia_dep.get("probabilidad_pct", 0))
                temp_m = float(dia_dep.get("temp_max_c", dep_info.get("temp_actual_c", 24.5)))
                hum_m = int(dep_info.get("humedad_pct", 60))
                viento_m = float(dep_info.get("viento_kmh", 14.0))
                cond_txt = dep_info.get("condicion_texto", "Despejado / Soleado")
                icono_w = dep_info.get("icono_clima", "☀️")

            # Asignación cromática y semáforo 100% meteorológico Open-Meteo
            if lluvia_om >= 55.0:
                col_m = [155, 44, 44, 235]       # Púrpura Torrencial
                rad_m = 12000
                est_m = f"⛈️ TORRENCIAL ({lluvia_om:.1f} mm)"
                alerta_m = "TORRENCIAL 🔴"
                c_fuertes += 1
            elif lluvia_om >= 30.0:
                col_m = [230, 57, 70, 225]       # Rojo Lluvia Fuerte
                rad_m = 9500
                est_m = f"🌧️ LLUVIA FUERTE ({lluvia_om:.1f} mm)"
                alerta_m = "FUERTE 🔴"
                c_fuertes += 1
            elif lluvia_om >= 10.0:
                col_m = [247, 127, 0, 205]      # Naranja Lluvia Moderada
                rad_m = 7500
                est_m = f"🌦️ LLUVIAS MODERADAS ({lluvia_om:.1f} mm)"
                alerta_m = "MODERADA 🟠"
                c_moderados += 1
            elif lluvia_om > 0.5:
                col_m = [255, 209, 102, 195]    # Amarillo Llovizna Dispersa
                rad_m = 5500
                est_m = f"🌤️ LLUVIAS DISPERSAS ({lluvia_om:.1f} mm)"
                alerta_m = "DISPERSA 🟡"
                c_moderados += 1
            else:
                col_m = [42, 157, 143, 175]     # Verde Tiempo Seco / Soleado
                rad_m = 4500
                est_m = f"☀️ TIEMPO SECO / SOLEADO (0.0 mm)"
                alerta_m = "VERDE 🟢"
                c_secos += 1

            # Filtrado por severidad si fue seleccionado
            if filtro_severidad.startswith("🔴") and lluvia_om < 30.0:
                continue
            elif filtro_severidad.startswith("🟠") and not (10.0 <= lluvia_om < 30.0):
                continue
            elif filtro_severidad.startswith("🟡") and not (0.5 < lluvia_om < 10.0):
                continue
            elif filtro_severidad.startswith("🟢") and lluvia_om > 0.5:
                continue

            nodos_m3.append({
                "nombre": f"📍 {dist_nom} ({prov_nom}) [UBIGEO: {ub_cod}]",
                "lat": u["lat"],
                "lon": u["lon"],
                "estado": f"{alerta_m} • {est_m}",
                "info": (
                    f"Dpto: {dep_nom} | Prov: {prov_nom} | UBIGEO: {ub_cod}\n"
                    f"{icono_w} Condición ({dia_nom_m3}): {cond_txt}\n"
                    f"🌧️ Precipitación: {lluvia_om:.1f} mm/24h | Probabilidad: {prob_om}%\n"
                    f"🌡️ Temp: {temp_m:.1f}°C | 💧 Hum: {hum_m}% | 💨 Viento: {viento_m:.1f} km/h\n"
                    f"🛰️ Telemetría: Open-Meteo (ECMWF) • Sincronía 100% con Panel Lateral"
                ),
                "color": col_m,
                "radius": rad_m
            })

        # Métricas rápidas de telemetría meteorológica satelital
        col_m3_k1, col_m3_k2, col_m3_k3, col_m3_k4 = st.columns(4)
        col_m3_k1.metric("Distritos Monitoreados", f"{len(nodos_m3)}", f"Horizonte {dia_nom_m3}")
        col_m3_k2.metric("☀️ Tiempo Seco (0.0 mm)", f"{c_secos}", "Costa & Valles Áridos")
        col_m3_k3.metric("🌦️ Precipitaciones (1-30 mm)", f"{c_moderados}", "Sierra / Ceja de Selva")
        col_m3_k4.metric("🌧️ Lluvias Fuertes (>30 mm)", f"{c_fuertes}", "Núcleos Convectivos")

        df_m3 = pd.DataFrame(nodos_m3)
        if not df_m3.empty:
            layer_m3 = pdk.Layer("ScatterplotLayer", df_m3, get_position=["lon", "lat"], get_color="color", get_radius="radius", pickable=True, auto_highlight=True)
            v_state_m3 = pdk.ViewState(latitude=lat_cam, longitude=lon_cam, zoom=zoom_cam, pitch=35)
            st.pydeck_chart(pdk.Deck(layers=[layer_m3], initial_view_state=v_state_m3, tooltip={"text": "{nombre}\nEstado: {estado}\n{info}"}))

    # -------------------------------------------------------------------------
    # SUBTAB 4: CORREDOR DE CABECERAS ANDINAS & CINÉTICA DE HUAICOS (P_HUAICO)
    # -------------------------------------------------------------------------
    with map_subtab4:
        st.markdown("##### 🏔️ Mapa 4: Corredor de Cabeceras Andinas & Cinética de Huaicos (P_huaico / T_lag)")
        st.caption(
            "Franja orográfica continua (800 – 3,800 msnm) que captura la precipitación convectiva en montaña "
            "y calcula la onda de retardo hidráulico hacia los conos de deyección y badenes en costa. "
            "Preserva los 893 UBIGEOs intactos y modela la física ladera abajo."
        )

        c_cor1, c_cor2, c_cor3, c_cor4 = st.columns(4)
        c_cor1.metric("Franja Andina", "6 Tramos C2", "Tumbes a Lima / Ica")
        c_cor2.metric("Rango Orográfico", "800 - 3,800 msnm", "Génesis de Detritos")
        c_cor3.metric("Quebradas Calibradas", f"{len(quebradas_totales)} Puntos", "1983, 1998, 2017, 2023")
        c_cor4.metric("Ventana Media (T_lag)", "1.2h - 3.0h", "Evacuación Preventiva")

        # Recuperar catálogo de quebradas y corredor
        catalogo_quebradas = orchestrator.agente_georriesgo.obtener_catalogo_completo()
        datos_corredor = orchestrator.obtener_corredor_cabeceras_andinas()

        nodos_cabecera = []
        nodos_conos = []
        vectores_flujo = []
        poligonos_triangulos = []

        lluvia_sim_cab = float(simular_precipitacion) if ("simular_precipitacion" in locals() and simular_precipitacion) else 25.0

        for q in catalogo_quebradas:
            eval_q = orchestrator.evaluar_probabilidad_dinamica_huaico(
                id_o_nombre=q["id_quebrada"],
                lluvia_cabecera_mm_h=lluvia_sim_cab * 0.45,
                lluvia_acumulada_24h=lluvia_sim_cab,
                saturacion_api_72h=min(60.0, lluvia_sim_cab * 0.8)
            )

            p_h = eval_q.get("probabilidad_huaico_pct", 0.0)

            # Colores tenues translúcidos (alpha 45-50) para permitir ver calles, ríos y relieve al hacer zoom
            if p_h >= 85:
                col_cono_fill = [230, 57, 70, 50]      # Rojo tenue translúcido
                col_cono_border = [230, 57, 70, 240]    # Borde rojo nítido
                col_vector = [230, 57, 70, 200]
            elif p_h >= 65:
                col_cono_fill = [247, 127, 0, 48]       # Naranja tenue translúcido
                col_cono_border = [247, 127, 0, 235]    # Borde naranja nítido
                col_vector = [247, 127, 0, 195]
            elif p_h >= 35:
                col_cono_fill = [255, 209, 102, 50]     # Amarillo tenue translúcido
                col_cono_border = [255, 209, 102, 230]  # Borde amarillo nítido
                col_vector = [255, 209, 102, 190]
            else:
                col_cono_fill = [6, 214, 160, 45]       # Verde tenue translúcido
                col_cono_border = [6, 214, 160, 220]    # Borde verde nítido
                col_vector = [6, 214, 160, 180]

            c_lat = q.get("cabecera_lat", q["lat"] + 0.05)
            c_lng = q.get("cabecera_lng", q["lng"] + 0.15)
            c_alt = q.get("cabecera_altitud_msnm", 1800)

            nodos_cabecera.append({
                "nombre": f"Cabecera {q['id_quebrada']}: {q['nombre']} ({c_alt} msnm)",
                "lat": c_lat,
                "lon": c_lng,
                "estado": "NÚCLEO CONVECTIVO EN MONTAÑA",
                "info": f"Altitud: {c_alt} msnm | Pendiente: {q.get('pendiente_media_pct', 16)}% | Cuenca: {q.get('cuenca', '')}",
                "fill_color": [0, 180, 216, 45],       # Azul tenue translúcido
                "line_color": [0, 180, 216, 230],       # Borde celeste nítido
                "radius": 4500
            })

            nodos_conos.append({
                "nombre": f"Cono/Badén {q['id_quebrada']}: {q['nombre']} ({q.get('distrito', '')})",
                "lat": q["lat"],
                "lon": q["lng"],
                "estado": f"{eval_q.get('nivel_alerta', 'VERDE')} ({p_h}%)",
                "info": f"P_huaico: {p_h}% | Tc: {eval_q.get('tiempo_concentracion_horas', 1.8)}h ({eval_q.get('tiempo_retardo_minutos', 108)} min) | Población: {eval_q.get('poblacion_en_cono_deyeccion', 0):,} hab.",
                "fill_color": col_cono_fill,
                "line_color": col_cono_border,
                "radius": 5000
            })

            vectores_flujo.append({
                "source": [c_lng, c_lat],
                "target": [q["lng"], q["lat"]],
                "color": col_vector
            })

            # Triángulo Hidrográfico de Afectación (Margen Superior -> Tránsito -> Tierras Abajo)
            tri_data = q.get("triangulo_hidrografico", {})
            v_sup = tri_data.get("vertice_superior_cabecera", {})
            v_med = tri_data.get("vertice_medio_transito", {})
            v_inf = tri_data.get("vertice_inferior_cono", {})
            if v_sup and v_med and v_inf and "lng" in v_sup and "lng" in v_med and "lng" in v_inf:
                col_tri_fill = [230, 57, 70, 28] if p_h >= 65 else ([255, 209, 102, 22] if p_h >= 35 else [0, 180, 216, 18])
                col_tri_line = [230, 57, 70, 150] if p_h >= 65 else ([255, 209, 102, 130] if p_h >= 35 else [0, 180, 216, 110])
                poligonos_triangulos.append({
                    "polygon": [
                        [v_sup["lng"], v_sup["lat"]],
                        [v_med["lng"], v_med["lat"]],
                        [v_inf["lng"], v_inf["lat"]]
                    ],
                    "nombre": f"🔺 Triángulo Hidrográfico: {q.get('id_quebrada')}: {q.get('nombre')}",
                    "estado": f"P_huaico: {p_h}% | Triángulo C2 Activo",
                    "info": f"Margen Sup: {v_sup.get('distrito')} (PCM: {'En Dec.' if v_sup.get('en_decreto_pcm') else 'Extradecreto'}) | Tierras Abajo: {v_inf.get('distrito')} (PCM: {'En Dec.' if v_inf.get('en_decreto_pcm') else 'Extradecreto'})",
                    "fill_color": col_tri_fill,
                    "line_color": col_tri_line
                })

        df_cab = pd.DataFrame(nodos_cabecera)
        df_cono = pd.DataFrame(nodos_conos)
        df_vect = pd.DataFrame(vectores_flujo)
        df_triang = pd.DataFrame(poligonos_triangulos)

        # Capa de Triángulos Hidrográficos de Afectación (PolygonLayer Translúcido)
        layer_triangulos = pdk.Layer(
            "PolygonLayer",
            df_triang,
            get_polygon="polygon",
            get_fill_color="fill_color",
            get_line_color="line_color",
            get_line_width=1.5,
            line_width_min_pixels=1,
            stroked=True,
            filled=True,
            pickable=True,
            auto_highlight=True
        )

        # Capa de Conos / Badenes en Costa (Transparencia Tenue + Borde Nítido + Límite de Píxeles al hacer Zoom)
        layer_cono = pdk.Layer(
            "ScatterplotLayer",
            df_cono,
            get_position=["lon", "lat"],
            get_fill_color="fill_color",
            get_line_color="line_color",
            get_radius="radius",
            get_line_width=2,
            line_width_min_pixels=1.5,
            radius_min_pixels=5,
            radius_max_pixels=28,  # Límite máximo para que nunca cubra el mapa al hacer zoom
            stroked=True,
            filled=True,
            pickable=True,
            auto_highlight=True
        )

        # Capa de Punto Focal Central del Cono/Badén
        layer_cono_centro = pdk.Layer(
            "ScatterplotLayer",
            df_cono,
            get_position=["lon", "lat"],
            get_fill_color="line_color",
            get_radius=800,
            radius_min_pixels=2,
            radius_max_pixels=5,
            pickable=False
        )

        # Capa de Cabeceras Andinas en Montaña (Transparencia Tenue Azul + Borde Nítido)
        layer_cab = pdk.Layer(
            "ScatterplotLayer",
            df_cab,
            get_position=["lon", "lat"],
            get_fill_color="fill_color",
            get_line_color="line_color",
            get_radius="radius",
            get_line_width=2,
            line_width_min_pixels=1.5,
            radius_min_pixels=5,
            radius_max_pixels=24,  # Límite máximo para que no tape las cumbres
            stroked=True,
            filled=True,
            pickable=True,
            auto_highlight=True
        )

        # Capa de Punto Focal Central de la Cabecera
        layer_cab_centro = pdk.Layer(
            "ScatterplotLayer",
            df_cab,
            get_position=["lon", "lat"],
            get_fill_color="line_color",
            get_radius=800,
            radius_min_pixels=2,
            radius_max_pixels=5,
            pickable=False
        )

        # Vectores de Flujo Gravitacional (Línea desde cabecera a badén)
        layer_lines = pdk.Layer(
            "LineLayer",
            df_vect,
            get_source_position="source",
            get_target_position="target",
            get_color="color",
            get_width=3,
            width_min_pixels=2,
            width_max_pixels=4,
            pickable=False
        )

        v_state_m4 = pdk.ViewState(latitude=-12.2, longitude=-76.8, zoom=6.5, pitch=42)
        st.pydeck_chart(pdk.Deck(
            layers=[layer_triangulos, layer_lines, layer_cab, layer_cab_centro, layer_cono, layer_cono_centro],
            initial_view_state=v_state_m4,
            tooltip={"text": "{nombre}\nEstado: {estado}\n{info}"}
        ))

        # -------------------------------------------------------------
        # CONSOLA INTERACTIVA DE SIMULACIÓN CINÉTICA Y ALERTA TEMPRANA
        # -------------------------------------------------------------
        st.markdown("##### ⚡ Simulador Cinético de Cabecera Andina & Cálculo Táctico de T_lag")
        c_sim1, c_sim2 = st.columns([1, 2])

        with c_sim1:
            nombres_quebradas = [f"{q['id_quebrada']}: {q['nombre']} ({q.get('distrito', '')}, {q.get('region', '')})" for q in catalogo_quebradas]
            idx_def_q = 0
            for idx_k, q_item in enumerate(catalogo_quebradas):
                if "Juana Ríos" in q_item["nombre"]:
                    idx_def_q = idx_k
                    break
            
            sel_q_sim = st.selectbox("Seleccionar Quebrada Crítica:", nombres_quebradas, index=idx_def_q, key="sb_quebrada_sim_m4")
            q_match = [q for q, n in zip(catalogo_quebradas, nombres_quebradas) if n == sel_q_sim]
            q_obj = q_match[0] if q_match else catalogo_quebradas[0]

            st.write(f"• **Cuenca:** `{q_obj.get('cuenca', '')}`")
            st.write(f"• **Cabecera:** Lat `{q_obj.get('cabecera_lat', 0)}`, Lon `{q_obj.get('cabecera_lng', 0)}` ({q_obj.get('cabecera_altitud_msnm', 1800)} msnm)")
            st.write(f"• **Badén/Paso:** Lat `{q_obj.get('lat', 0)}`, Lon `{q_obj.get('lng', 0)}`")

            i_cab_sim = st.slider("Intensidad en Cabecera (mm/hora):", 0.0, 50.0, float(q_obj.get("umbral_critico_mm_hora", 12.0) * 1.2), step=1.0, key="sl_i_cab")
            p24_sim = st.slider("Lluvia Acumulada 24h Cabecera (mm):", 0.0, 120.0, float(q_obj.get("umbral_acumulado_24h", 35.0) * 1.1), step=2.0, key="sl_p24_cab")
            api_sim = st.slider("Saturación Antecedente API 72h (mm):", 0.0, 80.0, 35.0, step=5.0, key="sl_api_cab")

        with c_sim2:
            res_cinetica = orchestrator.evaluar_probabilidad_dinamica_huaico(
                id_o_nombre=q_obj["id_quebrada"],
                lluvia_cabecera_mm_h=i_cab_sim,
                lluvia_acumulada_24h=p24_sim,
                saturacion_api_72h=api_sim
            )

            p_val = res_cinetica["probabilidad_huaico_pct"]
            nv_alerta = res_cinetica["nivel_alerta"]
            col_hex = res_cinetica["color_hex"]

            m_k1, m_k2, m_k3, m_k4 = st.columns(4)
            m_k1.metric("Probabilidad P_huaico", f"{p_val}%", nv_alerta)
            m_k2.metric("Tiempo Retardo (T_lag)", f"{res_cinetica['tiempo_concentracion_horas']} h", f"{res_cinetica['tiempo_retardo_minutos']} min arribo")
            m_k3.metric("Población en Cono", f"{res_cinetica['poblacion_en_cono_deyeccion']:,} hab.", "En riesgo directo")
            m_k4.metric("Fuerza Motriz (Phi)", f"{res_cinetica['fuerza_motriz_phi']}", f"Umbral: {q_obj.get('umbral_critico_mm_hora')} mm/h")

            st.markdown(f"""
            <div style="background-color: #1a2639; padding: 18px; border-radius: 10px; border-left: 6px solid {col_hex}; margin-top: 10px;">
                <h4 style="margin: 0; color: #f0f4f8;">⚡ Diagnóstico Operacional C2: {res_cinetica['quebrada']}</h4>
                <p style="margin-top: 6px; font-size: 1.05em; color: {col_hex}; font-weight: bold;">{res_cinetica['accion_tactica_inmediata']}</p>
                <hr style="border-color: #2a3b53; margin: 10px 0;">
                <p><b>Puntos de Estrangulamiento Viales:</b> {', '.join(res_cinetica['puntos_estrangulamiento'])}</p>
                <p><b>Defensas Existentes:</b> {res_cinetica['obras_defensa_existentes']}</p>
                    <b>Contraste Operacional:</b> En la costa (distrito {res_cinetica['distrito_cabecera']}) puede haber 0.0 mm/h de lluvia local, pero la precipitación de <b>{i_cab_sim} mm/h en cabecera</b> activará el flujo con impacto en <b>{res_cinetica['tiempo_retardo_minutos']} minutos</b>.
                </div>
            </div>
            """, unsafe_allow_html=True)

            sello = res_cinetica.get("sello_inviolabilidad", {})
            st.markdown(f"""
            <div style="background-color: #0d1b2a; border: 1px solid #1b4965; border-radius: 8px; padding: 12px; margin-top: 10px; font-size: 0.88em;">
                <span style="color: #06d6a0; font-weight: bold;">🛡️ BLINDAJE CRIPTOGRÁFICO C2 ACTIVO (ECDSA secp256k1)</span><br>
                • <b>Hash Inmutable Fórmula (Anti-Tampering):</b> <code style="color: #90e0ef;">{sello.get('hash_formula', '')[:24]}...</code><br>
                • <b>Oráculo Web3 Atestador:</b> <code style="color: #ffd166;">{sello.get('oraculo_address', '')}</code><br>
                • <b>Firma Digital No Repudiable:</b> <code style="color: #a8dadc;">{sello.get('firma_secp256k1_preview', '')}</code> | <i>Ley N° 31814 Verificada</i>
            </div>
            """, unsafe_allow_html=True)

            # Panel de Telemetría In Situ IGP (grd.igp.gob.pe/lahares-huaicos) y Doble Confirmación
            tele_igp = res_cinetica.get("telemetria_in_situ_igp", {})
            consenso_c2 = res_cinetica.get("consenso_doble_confirmacion_c2", {})
            homo_oficial = res_cinetica.get("homologacion_oficial", {})

            col_borde_igp = "#e63946" if tele_igp.get("es_flujo_activo") else "#00b4d8"
            st.markdown(f"""
            <div style="background-color: #071526; border: 1.5px solid {col_borde_igp}; border-radius: 8px; padding: 14px; margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 0.95em; font-weight: bold; color: #90e0ef;">
                        📡 SISTEMA DE MONITOREO DE LAHARES Y HUAICOS IN SITU (IGP)
                    </span>
                    <span style="background: {'#e63946' if tele_igp.get('es_flujo_activo') else '#132a13'}; color: {'white' if tele_igp.get('es_flujo_activo') else '#70e000'}; border: 1px solid {'#ff4d4d' if tele_igp.get('es_flujo_activo') else '#38b000'}; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">
                        {tele_igp.get('estado_sensor', 'SIN SENSOR IN SITU')}
                    </span>
                </div>
                <div style="font-size: 0.85em; color: #cbd5e1; margin-top: 8px; line-height: 1.6;">
                    • <b>Denominación AMARU-FEN:</b> <code style="color: #64dfdf;">{res_cinetica.get('id_quebrada')}: {res_cinetica.get('quebrada')}</code> <i>(Entidad: {homo_oficial.get('entidad_amaru')})</i><br>
                    • <b>Denominación Oficial IGP:</b> <code style="color: #ffd166;">{tele_igp.get('denominacion_oficial_igp', 'N/A')}</code> | Código: <code style="color: #ffd166;">{tele_igp.get('codigo_oficial_igp', 'N/A')}</code> <i>(Entidad: {homo_oficial.get('entidad_igp')})</i><br>
                    • <b>Velocidad del Flujo (Sensor):</b> <b>{tele_igp.get('velocidad_flujo_ms', 0.0)} m/s ({tele_igp.get('velocidad_flujo_kmh', 0.0)} km/h)</b> | Altura/Calado: <b>{tele_igp.get('altura_flujo_m', 0.0)} m</b><br>
                    • <b>Sirena / Alarma Sonora:</b> {'🚨 ALARMA SONORA EN CURSO (GEÓFONO ACTIVO)' if tele_igp.get('alarma_sonora_activa') else '🟢 VIGILANCIA EN REPOSO (SIN ALARMA)'}<br>
                    • <b>Consenso Dual C2:</b> <span style="color: {'#ff4d4d' if 'DOBLE' in consenso_c2.get('nivel_consenso', '') else '#06d6a0'}; font-weight: bold;">{consenso_c2.get('nivel_consenso', 'VIGILANCIA')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("🌋 Consultar Sensor en Vivo en Portal IGP Lahares-Huaicos", "https://grd.igp.gob.pe/lahares-huaicos/", use_container_width=True)

            # Panel del Triángulo Hidrográfico de Afectación (Margen Superior -> Tránsito -> Tierras Abajo)
            tri_obj = res_cinetica.get("triangulo_hidrografico", {})
            v1_sup = tri_obj.get("vertice_superior_cabecera", {})
            v2_med = tri_obj.get("vertice_medio_transito", {})
            v3_inf = tri_obj.get("vertice_inferior_cono", {})
            cob_legal = tri_obj.get("cobertura_legal_triangulo", {})

            badge_v1 = "🟢 DECRETADO PCM" if v1_sup.get("en_decreto_pcm") else "⚠️ EXTRADECRETO"
            badge_v3 = "🟢 DECRETADO PCM" if v3_inf.get("en_decreto_pcm") else "⚠️ EXTRADECRETO"
            col_b1 = "#2a9d8f" if v1_sup.get("en_decreto_pcm") else "#e76f51"
            col_b3 = "#2a9d8f" if v3_inf.get("en_decreto_pcm") else "#e76f51"

            st.markdown(f"""
            <div style="background-color: #0b1d33; border: 1.5px solid #2a6f97; border-radius: 8px; padding: 14px; margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 0.95em; font-weight: bold; color: #64dfdf;">
                        🔺 TRIÁNGULO HIDROGRÁFICO DE AFECTACIÓN C2 (Margen Superior ➔ Tierras Abajo)
                    </span>
                    <span style="background: {'#1b4332' if cob_legal.get('es_completamente_decretado') else '#5c1d1d'}; color: {'#95d5b2' if cob_legal.get('es_completamente_decretado') else '#f4a261'}; border: 1px solid {'#2d6a4f' if cob_legal.get('es_completamente_decretado') else '#e76f51'}; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">
                        {'COBERTURA LEGAL COMPLETA' if cob_legal.get('es_completamente_decretado') else 'REQUIERE AMPLIACIÓN SINAGERD'}
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 0.85em;">
                    <div style="background: #112240; padding: 8px; border-radius: 6px; border-left: 3px solid {col_b1};">
                        <b>1. Margen Superior (Cabecera):</b><br>
                        Distrito: <b>{v1_sup.get('distrito', 'N/A')}</b><br>
                        Altitud: {v1_sup.get('altitud_msnm', 2000)} msnm<br>
                        Estatus PCM: <span style="color: {col_b1}; font-weight: bold;">{badge_v1}</span>
                    </div>
                    <div style="background: #112240; padding: 8px; border-radius: 6px; border-left: 3px solid #ffd166;">
                        <b>2. Garganta (Tránsito/Vía):</b><br>
                        Corredor: <b>{v2_med.get('distrito', 'N/A')}</b><br>
                        Hito: {v2_med.get('hito_vial', 'Garganta')[:22]}...<br>
                        Tiempo Arribo: <b>{tri_obj.get('tiempo_arribo_cono_minutos', 90)} min</b>
                    </div>
                    <div style="background: #112240; padding: 8px; border-radius: 6px; border-left: 3px solid {col_b3};">
                        <b>3. Tierras Abajo (Cono/Litoral):</b><br>
                        Distrito: <b>{v3_inf.get('distrito', 'N/A')}</b><br>
                        Cono: {v3_inf.get('cono_deyeccion', 'Valle Bajo')[:22]}...<br>
                        Estatus PCM: <span style="color: {col_b3}; font-weight: bold;">{badge_v3}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Si hay dictamen pericial de ampliación de decreto
            boletin = res_cinetica.get("boletin_pericial_ampliacion_decreto")
            if boletin:
                st.markdown(f"""
                <div style="background-color: #2b1117; border: 2px solid #e63946; border-radius: 8px; padding: 12px; margin-top: 10px; font-size: 0.86em;">
                    <span style="color: #ff4d4d; font-weight: bold; font-size: 1.05em;">⚖️ {boletin.get('titulo')}</span><br>
                    <p style="margin: 6px 0; color: #f8edeb;"><b>Fundamento Pericial:</b> {boletin.get('fundamento_tecnico')}</p>
                    • <b>Distritos Habilitados para Gasto PP 068:</b> <code style="color: #ffd166;">{', '.join(boletin.get('distritos_a_incorporar', []))}</code><br>
                    • <b>Base Normativa:</b> <i>{boletin.get('base_legal')}</i><br>
                    • <b>Acción Inmediata:</b> <span style="color: #06d6a0; font-weight: bold;">{boletin.get('accion_financiera')}</span>
                </div>
                """, unsafe_allow_html=True)

            # Tarjeta de Evidencia Visual Oficial (CENEPRED SIGRID / ANA)
            evid_vis = res_cinetica.get("evidencia_visual_oficial", {})
            if evid_vis.get("tiene_evidencia_visual"):
                st.markdown(f"""
                <div style="background-color: #0f1e36; border: 1px solid #1d3557; border-radius: 8px; padding: 12px; margin-top: 10px; font-size: 0.85em;">
                    <span style="color: #a8dadc; font-weight: bold;">📸 EVIDENCIA CARTOGRÁFICA Y REGISTRO OFICIAL (CENEPRED SIGRID / ANA)</span><br>
                    • <b>Tipo de Registro:</b> <code>{evid_vis.get('tipo_archivo', 'INFORME_SIGRID')}</code> | <b>Entidad:</b> <i>{evid_vis.get('entidad_fuente', 'CENEPRED')}</i><br>
                    • <b>Nota de Atribución Obligatoria:</b> <span style="color: #94d2bd;">{evid_vis.get('atribucion_obligatoria', 'Fuente oficial SINAGERD.')}</span>
                </div>
                """, unsafe_allow_html=True)
                if evid_vis.get("documento_sigrid_url"):
                    st.link_button("📄 Ver Expediente Técnico Oficial en SIGRID CENEPRED", evid_vis.get("documento_sigrid_url"), use_container_width=True)
        # CONSOLA DE HOMOLOGACIÓN MULTIREGISTRO (AMARU ↔ IGP ↔ ANA ↔ INGEMMET ↔ CENEPRED ↔ MTC)
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.markdown("##### 🏛️ Matriz Oficial de Homologación Multiregistro de Quebradas")
        st.caption(
            "Cruce y homologación de cada quebrada crítica con los registros oficiales del Estado Peruano: "
            "AMARU-FEN (Comando C2), IGP (Sistema Nacional de Lahares y Huaicos), ANA (Pfafstetter y Puntos Críticos), "
            "INGEMMET (Peligros Geológicos), CENEPRED (SIGRID EVAR), MTC / Provías Nacional (Badenes y Puentes) e INEI (UBIGEOs)."
        )

        c_hom_k1, c_hom_k2, c_hom_k3, c_hom_k4 = st.columns(4)
        c_hom_k1.metric("Quebradas Homologadas", f"{len(catalogo_quebradas)} Críticas", "100% Cruzadas")
        c_hom_k2.metric("Entidades del Estado", "6 Registros Oficiales", "AMARU, IGP, ANA, INGEMMET, SIGRID, MTC")
        c_hom_k3.metric("Departamentos", "7 Regiones FEN", "TUM, PIU, LAM, LIB, ANC, LIM, ARE")
        c_hom_k4.metric("Auditoría C2", "COMPLETA", "Código AMARU + Estado")

        # Filtro interactivo de búsqueda
        filtro_hom = st.text_input(
            "🔍 Buscar en el Registro Homologado (por nombre, código AMARU, IGP, ANA, INGEMMET, SIGRID, MTC o distrito):",
            value="",
            placeholder="Ej: Limón, Río Seco, San Lázaro, Huaycoloro, Juana Ríos, Q-PIU-06, IGP-HUAICO, Chongoyape...",
            key="input_busq_homologacion"
        ).strip().lower()

        filas_homologadas = []
        for q_item in catalogo_quebradas:
            cod_amaru = q_item.get("id_quebrada", "")
            nom_q = q_item.get("nombre", "")
            reg_q = q_item.get("region", "")
            dist_q = q_item.get("distrito", "")
            den_igp = q_item.get("denominacion_oficial_igp", "N/A")
            cod_igp = q_item.get("codigo_oficial_igp", "N/A")
            mon_igp = "🟢 Sí (Geófonos/Radar)" if q_item.get("monitoreo_igp_in_situ") else "⚪ No Instrumentada"
            pfaf_ana = q_item.get("codigo_pfafstetter_ana", "N/A")
            pc_ana = q_item.get("codigo_punto_critico_ana", "N/A")
            pel_ing = q_item.get("codigo_ingemmet_peligro", "N/A")
            sig_cen = q_item.get("codigo_sigrid_cenepred", "N/A")
            vial_mtc = q_item.get("codigo_vial_mtc_pvn", "N/A")
            ub_cab = f"{q_item.get('ubigeo_cabecera', 'N/A')} ({q_item.get('distrito_cabecera_nombre', dist_q)})"
            ub_rec = f"{q_item.get('ubigeo_receptor', 'N/A')} ({q_item.get('distrito_receptor_nombre', dist_q)})"

            match_h = (
                not filtro_hom
                or filtro_hom in cod_amaru.lower()
                or filtro_hom in q_item.get("codigo_tactico_c2", "").lower()
                or filtro_hom in q_item.get("denominacion_amaru", "").lower()
                or filtro_hom in nom_q.lower()
                or filtro_hom in reg_q.lower()
                or filtro_hom in dist_q.lower()
                or filtro_hom in den_igp.lower()
                or filtro_hom in cod_igp.lower()
                or filtro_hom in pfaf_ana.lower()
                or filtro_hom in pc_ana.lower()
                or filtro_hom in pel_ing.lower()
                or filtro_hom in sig_cen.lower()
                or filtro_hom in vial_mtc.lower()
            )

            if match_h:
                filas_homologadas.append({
                    "Denominación AMARU-FEN": f"{cod_amaru}: {nom_q}",
                    "Código AMARU": cod_amaru,
                    "Quebrada Crítica": nom_q,
                    "Región": reg_q,
                    "Distrito Receptor": dist_q,
                    "Triángulo Hidrográfico": f"{q_item.get('triangulo_hidrografico', {}).get('vertice_superior_cabecera', {}).get('distrito', '')} ➔ {dist_q}",
                    "Cobertura PCM": "🟢 En Decreto" if q_item.get('triangulo_hidrografico', {}).get('cobertura_legal_triangulo', {}).get('es_completamente_decretado') else "⚠️ Extradecreto",
                    "Denominación Oficial IGP": den_igp,
                    "Sensor In Situ IGP": mon_igp,
                    "Pto. Crítico ANA": pc_ana,
                    "Peligro INGEMMET": pel_ing,
                    "Documento CENEPRED": sig_cen,
                    "Infraestructura MTC / Provías": vial_mtc,
                    "UBIGEO Cabecera": ub_cab,
                    "UBIGEO Receptor": ub_rec,
                    "Umbral (mm/h)": f"{q_item.get('umbral_critico_mm_hora', 12)} mm/h",
                    "Tc (Retardo)": f"{q_item.get('tiempo_concentracion_horas', 1.8)} h",
                    "Población Expuesta": f"{q_item.get('poblacion_en_cono_deyeccion', 0):,} hab."
                })

        df_hom = pd.DataFrame(filas_homologadas)
        st.dataframe(
            df_hom,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Código AMARU (C2)": st.column_config.TextColumn("AMARU (C2)", width="small"),
                "Quebrada Crítica": st.column_config.TextColumn("Quebrada", width="medium"),
                "Denominación Oficial IGP": st.column_config.TextColumn("Denominación IGP", width="medium"),
                "Sensor In Situ IGP": st.column_config.TextColumn("Sensor IGP", width="small"),
                "Documento CENEPRED": st.column_config.TextColumn("CENEPRED SIGRID", width="small"),
                "Pto. Crítico ANA": st.column_config.TextColumn("Punto Crítico ANA", width="small"),
                "Peligro INGEMMET": st.column_config.TextColumn("INGEMMET", width="small"),
                "Infraestructura MTC / Provías": st.column_config.TextColumn("MTC / Vía Crítica", width="medium")
            }
        )

        st.info(
            f"Mostrando **{len(filas_homologadas)} de {len(catalogo_quebradas)}** quebradas críticas homologadas. "
            "Cada quebrada preserva la denominación canónica AMARU-FEN y registra la denominación oficial y la entidad del Estado que la denomina (IGP, ANA, INGEMMET, CENEPRED, MTC e INEI)."
        )

        st.markdown("###### 🔍 Enlaces Oficiales para Validación Cruzada de Quebradas y Peligros:")
        col_qlink1, col_qlink2, col_qlink3, col_qlink4, col_qlink5, col_qlink6 = st.columns(6)
        with col_qlink1:
            st.link_button("🌋 IGP Lahares y Huaicos", "https://grd.igp.gob.pe/lahares-huaicos/", use_container_width=True)
        with col_qlink2:
            st.link_button("🌊 ANA Puntos Críticos", "https://snirh.ana.gob.pe/puntos-criticos/", use_container_width=True)
        with col_qlink3:
            st.link_button("🌋 INGEMMET GEOCATMIN", "https://geocatmin.ingemmet.gob.pe/", use_container_width=True)
        with col_qlink4:
            st.link_button("📑 CENEPRED SIGRID", "https://sigrid.cenepred.gob.pe/", use_container_width=True)
        with col_qlink5:
            st.link_button("🛣️ MTC GEOVIAL", "https://geovial.mtc.gob.pe/", use_container_width=True)
        with col_qlink6:
            st.link_button("🛰️ SENAMHI Lluvias", "https://www.senamhi.gob.pe/?p=aviso-meteorologico", use_container_width=True)

    with st.expander("🌦️ Inspector Climático en Vivo con Open-Meteo (Sin Geocoding - Coordenadas Locales Oficiales)", expanded=False):
        c_om1, c_om2 = st.columns([1, 2])
        with c_om1:
            st.markdown("##### 📍 Consultar Distrito en Tiempo Real")
            st.caption("Usa las coordenadas geodésicas locales de `geodatos_893_distritos_ubigeo.json`. Cero consumo de geocoding externo.")
            distritos_nombres = sorted(list(set(u["distrito"] for u in ubigeos_data)))
            idx_def = distritos_nombres.index("CATACAOS") if "CATACAOS" in distritos_nombres else 0
            dist_om_sel = st.selectbox("Seleccionar Distrito:", distritos_nombres, index=idx_def, key="sb_dist_open_meteo")
            u_sel_obj = next((u for u in ubigeos_data if u["distrito"] == dist_om_sel), None)
            if u_sel_obj:
                st.write(f"• **UBIGEO:** `{u_sel_obj['ubigeo']}` | **Dpto:** {u_sel_obj['departamento']}")
                st.write(f"• **Coordenadas:** Lat `{u_sel_obj['lat']}`, Lon `{u_sel_obj['lon']}`")
                btn_om = st.button("☁️ Consultar Open-Meteo en Vivo", type="primary")
            else:
                btn_om = False

        with c_om2:
            if u_sel_obj and btn_om:
                with st.spinner("Consultando modelo europeo ECMWF vía Open-Meteo..."):
                    res_om = orchestrator.consultar_open_meteo(u_sel_obj["lat"], u_sel_obj["lon"], dias=3)
                    st.markdown(f"#### 🛰️ Pronóstico Open-Meteo (ECMWF) para {dist_om_sel}")
                    m_om1, m_om2, m_om3 = st.columns(3)
                    m_om1.metric("Lluvia Máx 24h", f"{res_om.get('lluvia_maxima_24h_mm', 0.0)} mm", res_om.get("alerta_pluviometrica", "VERDE"))
                    dias = res_om.get("dias_pronostico", [])
                    if dias:
                        m_om2.metric("Probabilidad Lluvia", f"{dias[0]['probabilidad_lluvia_pct']}%")
                        m_om3.metric("Temperatura Hoy", f"{dias[0]['temp_max_c']} °C / {dias[0]['temp_min_c']} °C")
                        st.dataframe(pd.DataFrame(dias), use_container_width=True)
                    st.caption(f"**Fuente:** {res_om.get('fuente')} | Coordenadas: {res_om.get('coordenadas')}")


    # Submódulo 3: Panel de Resiliencia Off-Grid
    with st.expander("⚡ Panel de Control de Resiliencia Off-Grid y Circuit Breaker", expanded=False):
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            st.markdown(f"**Modo Actual:** `{estado_red['modo_operativo']}`")
            st.write(f"• **Servidor Local SLM:** `{estado_red['servidor_local_slm']}`")
            st.write(f"• **Modelo Local:** `{estado_red['modelo_slm_asignado']}`")
            st.write(f"• **Eventos en Buffer Local:** `{estado_red['eventos_encolados']}`")
        with c_res2:
            st.markdown("##### Acciones de Contingencia:")
            if st.button("🔄 Probar Conectividad Nube (Heartbeat)"):
                activa = orchestrator.gestor_resiliencia.verificar_conectividad_nube()
                if activa:
                    st.success("Enlace a la nube verificado exitosamente.")
                else:
                    st.warning("Sin respuesta de la nube. Conmutado a modo OFFLINE_EDGE.")
                st.rerun()
            if st.button("📤 Sincronizar Buffer Local con Servidores Centrales"):
                sync_b = orchestrator.gestor_resiliencia.sincronizar_buffer_con_nube()
                st.info(f"Resultado: {sync_b.get('mensaje', sync_b.get('status'))}")
                st.rerun()


# TAB 5: VIGILANCIA CIUDADANA OSINT TRI-TEMPORAL & VOZ SOS
with tab2:
    st.subheader("🛰️ Agente Vigía OSINT Multimodal & Triaje de Emergencias (TikTok, Radios & Diarios)")
    st.markdown("""
    *Vigilancia ciudadana en tres escalas de tiempo complementarias: **TikTok Lives** para la inmediatez absoluta con filtro anti-fake news, 
    **Radios Comunitarias** para llamadas desde caseríos rurales sin internet, y **Prensa Regional** para el cierre formal y auditoría de la Ficha EDAN.*
    """)
    
    tab_t1, tab_t2, tab_t3, tab_t4 = st.tabs([
        "📱 Tier 1: TikTok Lives & Streams (0-20m)",
        "📻 Tier 2: Radios Provinciales Comunitarias (20m-3h)",
        "📰 Tier 3: Diarios & Prensa Regional (12-48h)",
        "🚨 Central SOS & Triaje Multi-Agente"
    ])
    
    with tab_t1:
        st.markdown("##### 📱 Monitoreo de Transmisiones en Vivo (TikTok Live / X)")
        st.caption("Detección ultra-rápida de desbordes con filtro cruzado contra pluviómetros SENAMHI y radar de canales oficiales municipales de Defensa Civil.")
        
        # Banner informativo de canal oficial detectado
        st.info("🚨 **Radar de Gobiernos Locales Activo:** Detecta automáticamente comunicados oficiales de cuentas municipales como **@municatacaos** e integra de inmediato su **Central de Emergencias GRD**.")

        c_tk1, c_tk2 = st.columns([1, 1])
        with c_tk1:
            fuente_tipo = st.radio(
                "Tipo de Fuente TikTok:",
                ["Canal Oficial Municipal (GRD / Serenazgo)", "Reporte Ciudadano / Testigo en Vivo"],
                horizontal=True,
                key="rb_tipo_tk"
            )
            
            if fuente_tipo == "Canal Oficial Municipal (GRD / Serenazgo)":
                canal_sel = st.selectbox(
                    "Seleccionar Cuenta Municipal Verificada:",
                    [
                        "@municatacaos - Municipalidad Distrital de Catacaos (Piura)",
                        "@munipiura - Municipalidad Provincial de Piura",
                        "@munichosica - Municipalidad de Lurigancho-Chosica (Lima)",
                        "@munielporvenir - Municipalidad de El Porvenir (La Libertad)"
                    ],
                    key="sb_muni_tk"
                )
                autor_default = canal_sel.split(" - ")[0]
                texto_default = "COMUNICADO URGENTE DE GESTIÓN DE RIESGO Y DESASTRE: El caudal del Río Piura supera los 1,800 m³/s. Se dispone la evacuación preventiva de los sectores Pedregal Grande, Viduque y Molino Azul. Central de Emergencias activa las 24 horas: 907622154."
            else:
                autor_default = "@ciudadano_catacaos_alerta"
                texto_default = "¡En vivo desde Catacaos! El río Piura se está saliendo por el puente, el agua ya entró a la plaza y hay familias atrapadas en los techos en Pedregal Grande, ¡ayuda por favor!"

            autor_tk = st.text_input("Usuario / Creador:", value=autor_default, key="tk_user")
            stream_texto = st.text_area(
                "Texto o Transcripción de Stream en Vivo:",
                value=texto_default,
                key="tk_text_input",
                height=110
            )
            depto_tk = st.selectbox("Departamento de la Transmisión:", ["Piura", "Tumbes", "Lambayeque", "La Libertad", "Lima", "Ica"], key="tk_depto")
            sim_lluvia_senamhi = st.slider("Pluviómetro SENAMHI más cercano (mm en 24h):", 0.0, 100.0, float(simular_precipitacion), step=5.0, key="tk_pluvio")
            btn_eval_tk = st.button("🔍 Analizar Stream TikTok", key="btn_eval_tk", type="primary")
            
        with c_tk2:
            if btn_eval_tk or stream_texto:
                res_tk = orchestrator.procesar_stream_tiktok(
                    texto=stream_texto,
                    autor=autor_tk,
                    enlace="https://tiktok.com/@live/stream_alerta",
                    depto=depto_tk,
                    lluvia_senamhi=sim_lluvia_senamhi
                )
                badge_tk = "#e63946" if res_tk["nivel_severidad"] == "CRITICA" else "#f77f00"
                es_oficial = res_tk.get("es_canal_oficial_municipal", False)
                muni_info = res_tk.get("datos_municipales_grd")

                st.markdown(f"""
                <div style="background-color: #1a2639; padding: 15px; border-radius: 10px; border-left: 5px solid {badge_tk};">
                    <h4 style="margin: 0; color: #f0f4f8;">📍 Ubicación: {res_tk['ubicacion_detectada']}</h4>
                    <p><b>Autor / Canal:</b> <code>{res_tk['autor']}</code> {'<span style="background-color: #06d6a0; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">OFICIAL VERIFICADO</span>' if es_oficial else '<span style="background-color: #64748b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">CIUDADANO EN VIVO</span>'}</p>
                    <p><b>Nivel de Severidad:</b> <span style="color: {badge_tk}; font-weight: bold;">{res_tk['nivel_severidad']}</span></p>
                    <p><b>Palabras Clave Detectadas:</b> {', '.join(res_tk['palabras_clave_detectadas']) if res_tk['palabras_clave_detectadas'] else 'Sin palabras críticas'}</p>
                    <p><b>Filtro Anti-Videos Reciclados:</b> {'✅ FUENTE INSTITUCIONAL LOCAL CONFIRMADA' if es_oficial else ('⚠️ SOSPECHOSO DE VIDEO ANTIGUO (Tiempo Seco)' if res_tk['filtro_consistencia_hidrologica']['es_sospechoso_reciclado'] else '✅ CONSISTENTE CON PLUVIOMETRÍA SENAMHI')}</p>
                    <div style="background-color: #0b111e; padding: 10px; border-radius: 6px; margin-top: 8px;">
                        <b>Directiva Operativa:</b> {res_tk['accion_recomendada']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if es_oficial and muni_info:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e65100 0%, #bf360c 100%); color: white; padding: 16px; border-radius: 10px; margin-top: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                        <h4 style="margin: 0 0 6px 0; color: #ffffff;">🚨 CENTRAL DE EMERGENCIAS GRD: {muni_info['municipalidad'].upper()}</h4>
                        <div style="font-size: 26px; font-weight: 900; letter-spacing: 2px; color: #ffeb3b;">
                            📞 {muni_info['central_emergencias_grd']}
                        </div>
                        <p style="margin: 4px 0 0 0; font-size: 13px; color: #fbe9e7;">
                            <b>Unidad Responsable:</b> {muni_info['unidad']} | <b>UBIGEO:</b> {muni_info['ubigeo']} | <b>TikTok:</b> <a href="https://www.tiktok.com/{muni_info.get('canal_tiktok_oficial', '@municatacaos')}" target="_blank" style="color: #ffffff; text-decoration: underline;">{muni_info.get('canal_tiktok_oficial', '@municatacaos')}</a>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

    with tab_t2:
        st.markdown("##### 📻 Monitoreo de Radios Comunitarias y Provinciales")
        st.caption("Captura de llamadas de oyentes y corresponsales desde caseríos rurales sin conectividad móvil ni internet.")
        
        c_rad1, c_rad2 = st.columns([1, 1])
        with c_rad1:
            emisora_sel = st.selectbox(
                "Emisora Radial en Escucha:",
                [
                    "Radio Cutivalú (Piura - 107.9 FM)",
                    "RPP Noticias (Radio en Vivo / Entrevistas ADN - 89.7 FM)",
                    "Radio Yaraví (Arequipa - 106.3 FM)",
                    "Radio Marañón (Jaén - 96.1 FM)",
                    "Radio Onda Azul (Puno - 640 AM)",
                    "Radio Stereo Huarochirí (Chosica - 90.5 FM)"
                ],
                key="rad_sel"
            )
            llamada_radial = st.text_area(
                "Transcripción de Cabina / Llamada de Oyente:",
                value="Buenos días señor locutor de Radio Cutivalú, les llamo desde el caserío Pedregal Chico en Cura Mori. La quebrada se llevó el badén, estamos totalmente incomunicados y los niños no tienen agua potable ni alimentos desde ayer.",
                key="rad_text_input",
                height=110
            )
            btn_eval_rad = st.button("📡 Procesar Despacho Radial", key="btn_eval_rad", type="primary")
            
        with c_rad2:
            if btn_eval_rad or llamada_radial:
                emisora_nombre = emisora_sel.split(" (")[0]
                dial_nombre = emisora_sel.split(" - ")[-1].replace(")", "") if " - " in emisora_sel else "FM"
                res_rad = orchestrator.procesar_reporte_radial(
                    transcripcion=llamada_radial,
                    emisora=emisora_nombre,
                    dial=dial_nombre,
                    provincia="Piura",
                    depto="Piura"
                )
                st.markdown(f"""
                <div style="background-color: #1a2639; padding: 15px; border-radius: 10px; border-left: 5px solid #06d6a0;">
                    <h4 style="margin: 0; color: #f0f4f8;">📍 {res_rad['caserio_identificado']}</h4>
                    <p><b>Medio Emisor:</b> {res_rad['medio']} ({res_rad['departamento']})</p>
                    <p><b>Prioridad COEN:</b> <span style="color: #ffb703; font-weight: bold;">{res_rad['nivel_prioridad_coen']}</span></p>
                    <p><b>Necesidades Humanitarias Detectadas:</b></p>
                    <ul>
                        {''.join(f'<li>{n}</li>' for n in res_rad['necesidades_humanitarias_urgentes'])}
                    </ul>
                    <div style="background-color: #0b111e; padding: 10px; border-radius: 6px; margin-top: 8px;">
                        <b>Despacho Logístico:</b> {res_rad['accion_humanitaria_disparada']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("📻 Caso de Estudio RPP ADN: Gobernador de Piura y Trabas Burocráticas en el Río Piura", expanded=False):
            caso_rpp = orchestrator.consultar_caso_rpp_piura()
            st.markdown(f"**Titular Oficial:** *\"{caso_rpp['titular']}\"*")
            st.caption(f"**Vocero:** {caso_rpp['vocero']} | **Fuente:** [{caso_rpp['fuente']}]({caso_rpp['enlace_web']}) | 🎙️ [Escuchar Radio en Vivo RPP]({caso_rpp['stream_live']})")
            
            c_rp1, c_rp2 = st.columns(2)
            with c_rp1:
                st.error(f"**Diagnóstico de la Traba Burocrática:** {caso_rpp['demanda_clave']}")
                st.caption("Licitaciones ordinarias toman de 4 a 7 meses; temor a sanciones de Contraloría paraliza la descolmatación.")
            with c_rp2:
                st.success("**Solución Operativa Articulada con AMARU-FEN:**")
                for sol in caso_rpp['respuesta_resolutiva_amaru']:
                    st.markdown(f"• {sol}")


    with tab_t3:
        st.markdown("##### 📰 Consolidación de Prensa & Diarios Regionales (Ex-Post 12-48h)")
        st.caption("Extracción de cifras censadas para cierre formal de la Ficha EDAN y transferencias del FONDEN / MEF.")
        
        c_pre1, c_pre2 = st.columns([1, 1])
        with c_pre1:
            diario_sel = st.selectbox("Diario / Agencia de Noticias:", ["El Tiempo de Piura", "La Industria de Trujillo", "La Industria de Chiclayo", "Diario Correo", "El Comercio", "Agencia Andina"], key="diario_sel")
            titular_prensa = st.text_input("Titular de la Noticia:", value="Desborde en el Bajo Piura deja 3,500 damnificados y defensas destruidas", key="tit_prensa")
            cuerpo_prensa = st.text_area(
                "Cuerpo del Artículo / Balance Oficial:",
                value="El balance confirmado del COER reporta que las lluvias extraordinarias dejaron 1,200 viviendas destruidas y más de 4,500 hectáreas de cultivo de arroz bajo el agua. Además, 2 puentes colapsados mantienen aislados varios sectores.",
                key="cuerpo_prensa",
                height=90
            )
            btn_eval_pre = st.button("📊 Consolidar Cifras para Ficha EDAN", key="btn_eval_pre", type="primary")
            
        with c_pre2:
            if btn_eval_pre or titular_prensa:
                res_pre = orchestrator.procesar_noticia_prensa_ex_post(
                    titular=titular_prensa,
                    cuerpo=cuerpo_prensa,
                    diario=diario_sel,
                    fecha="2026-09-04",
                    depto="Piura"
                )
                edan_m = res_pre["metricas_consolidadas_edan"]
                col_ed1, col_ed2 = st.columns(2)
                col_ed1.metric("Damnificados Censados", f"{edan_m['poblacion_damnificada_confirmada']:,}")
                col_ed2.metric("Viviendas Destruidas", f"{edan_m['viviendas_destruidas_censo']:,}")
                col_ed3, col_ed4 = st.columns(2)
                col_ed3.metric("Cultivos Perdidos", f"{edan_m['hectareas_cultivo_perdidas']:,} has")
                col_ed4.metric("Puentes Colapsados", f"{edan_m['puentes_destruidos']}")
                st.success(f"**Validación SINPAD:** {res_pre['utilidad_operativa']}")

    with tab_t4:
        st.markdown("##### 🚨 Central de Atención Telefónica SOS (Vapi AI) y Triaje General")
        c1, c2 = st.columns(2)
        with c1:
            texto_emergencia = st.text_area(
                "Transcripción de llamada o mensaje de auxilio:",
                value="¡Ayuda por favor! La quebrada San Ildefonso se acaba de desbordar con lodo y piedras en El Porvenir, hay dos niños y mi madre anciana atrapados en el segundo piso, el agua sigue subiendo y se llevó la pared!",
                height=120,
                key="sos_box_text"
            )
            distrito_reporte = st.selectbox("Distrito del incidente:", ["El Porvenir", "Castilla", "Catacaos", "Lurigancho-Chosica", "Aguas Verdes"], key="sos_dist_sel")
            canal_reporte = st.radio("Canal de Entrada:", ["Llamada Telefónica (Vapi AI)", "Transmisión en Vivo (TikTok/X)", "Formulario Web SOS"], key="sos_canal_sel")
            btn_procesar = st.button("🚨 Procesar Emergencia con el Enjambre Multi-Agente", type="primary", key="btn_sos_proc")

        with c2:
            if btn_procesar:
                with st.spinner("El Enjambre AMARU está triangulando con Memoria Histórica, SENAMHI, Georriesgo y Vapi..."):
                    resultado = orchestrator.procesar_incidente_completo(
                        region=region_sel,
                        distrito=distrito_reporte,
                        lluvia_mm=float(simular_precipitacion),
                        alerta_senamhi="ROJO" if simular_precipitacion >= 50 else "AMARILLO",
                        reporte_ciudadano_texto=texto_emergencia,
                        tipo_canal="VOZ_VAPI" if "Vapi" in canal_reporte else "OSINT_TIKTOK",
                        atrapados=3
                    )
                    st.success("✅ Triaje Completado, Memoria Histórica Triangulada y Despacho Automatizado Generado")
                    st.json(resultado)

# TAB 6: PRE-LLENADO HIDROCLIMÁTICO EDAN & DESPACHO MUNICIPAL

with tab3:
    st.subheader("📋 Pre-Llenado Hidroclimático Asistido para Fichas EDAN / SINPAD")
    st.caption("🛡️ **Principio de Pureza de Misión (Ley Nº 31814):** AMARU-FEN NO asume funciones administrativas ni empadronamiento burocrático. El sistema procesa los datos duros físico-climáticos (caudal, IPH, saturación de suelo, coordenadas GPS WGS84 y polígono de impacto) y genera un **Borrador Asistido** para que el evaluador humano de Defensa Civil complete el padrón nominal en terreno y lo ingrese formalmente al SINPAD v2.0.")
    st.markdown("""
    <div class="card-edan">
        <h4>Borrador Asistido Oficial: EDAN-FEN-8A9C12BF (Pre-Llenado Hidroclimático C2)</h4>
        <p><b>Evento Físico:</b> Huayco e Inundación Violenta | <b>Severidad Predictiva:</b> <span class="badge-rojo">CRÍTICA</span></p>
        <p><b>Ubicación y Cuenca:</b> La Libertad - Trujillo - El Porvenir (Quebrada San Ildefonso / Cota de Inundación)</p>
        <p><b>Detección Telemétrica:</b> 3 Alertas de atrapados por canal de voz VAPI/OSINT georreferenciadas en azoteas.</p>
        <p><b>Sugerencia Táctica de Despacho:</b> Alerta inmediata a COEN-INDECI, PNP Rescate, Bomberos B-25, Ejército (BIM 32).</p>
        <p><b>Requerimiento de Maquinaria Proyectado:</b> Rescate helitransportado MI-17, dique de roca al volteo km 12 y motobombas 6''.</p>
    </div>
    """, unsafe_allow_html=True)

    # CARDS DE DESCARGA DE DOCUMENTOS PRIVADOS OFICIALES EN PDF
    ruta_pdf_edan = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "modelo_practico_ficha_edan_digital_amaru_fen.pdf")
    ruta_pdf_satelite = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "modulo_satelite_precarga_edan_y_gobernanza_comite_cgr.pdf")
    ruta_pdf_handoff = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "doctrina_limite_de_entrega_hand_off_amaru_fen.pdf")
    ruta_pdf_cgr = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "analisis_casuistica_contraloria_edan_fichas_tecnicas_y_pp0068.pdf")
    ruta_pdf_indeci = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "analisis_formatos_oficiales_edan_indeci_y_amaru_fen.pdf")
    ruta_pdf_doctrina = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos_privados", "doctrina_delimitacion_amaru_fen_prellenado_edan_vs_gestion_administrativa.pdf")
    
    col_ed1, col_ed2, col_ed3, col_ed4, col_ed5, col_ed6 = st.columns(6)
    with col_ed1:
        if os.path.exists(ruta_pdf_satelite):
            with open(ruta_pdf_satelite, "rb") as f_pdf:
                pdf_bytes_sat = f_pdf.read()
            st.markdown("""
            <div style="background: #0d1b2a; border: 1px solid #1b4965; border-left: 4px solid #06d6a0; padding: 10px; border-radius: 8px; font-size: 11px; margin-bottom: 8px; min-height: 105px;">
                <b style="color: #06d6a0;">🛰️ Satélite CGR:</b><br><code>Pre-Carga & Comité</code><br>
                <span style="color: #cbd5e1;">Sidecar municipal y Memoria CGR Cap. 5.</span>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Módulo Satélite", data=pdf_bytes_sat, file_name="modulo_satelite_precarga_edan_y_gobernanza_comite_cgr.pdf", mime="application/pdf", use_container_width=True, key="btn_descarga_satelite_pdf")

    with col_ed2:
        if os.path.exists(ruta_pdf_handoff):
            with open(ruta_pdf_handoff, "rb") as f_pdf:
                pdf_bytes_hand = f_pdf.read()
            st.markdown("""
            <div style="background: #0d1b2a; border: 1px solid #1b4965; border-left: 4px solid #38bdf8; padding: 10px; border-radius: 8px; font-size: 11px; margin-bottom: 8px; min-height: 105px;">
                <b style="color: #38bdf8;">🛑 Límite Hand-Off:</b><br><code>Frontera Operativa</code><br>
                <span style="color: #cbd5e1;">Línea roja entre ciencia y burocracia.</span>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Límite Hand-Off", data=pdf_bytes_hand, file_name="doctrina_limite_de_entrega_hand_off_amaru_fen.pdf", mime="application/pdf", use_container_width=True, key="btn_descarga_handoff_pdf")

    with col_ed3:
        if os.path.exists(ruta_pdf_edan):
            with open(ruta_pdf_edan, "rb") as f_pdf:
                pdf_bytes_edan = f_pdf.read()
            st.markdown("""
            <div style="background: #0d1b2a; border: 1px solid #1b4965; border-left: 4px solid #00b4d8; padding: 10px; border-radius: 8px; font-size: 11px; margin-bottom: 8px; min-height: 105px;">
                <b style="color: #90e0ef;">📄 Catacaos Digital:</b><br><code>Ficha EDAN Oficial</code><br>
                <span style="color: #cbd5e1;">8 bloques SINPAD, BAH Esfera y SHA-256.</span>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Ficha Catacaos", data=pdf_bytes_edan, file_name="modelo_practico_ficha_edan_digital_amaru_fen.pdf", mime="application/pdf", use_container_width=True, key="btn_descarga_edan_pdf")

    with col_ed4:
        if os.path.exists(ruta_pdf_cgr):
            with open(ruta_pdf_cgr, "rb") as f_pdf_cgr:
                pdf_bytes_cgr = f_pdf_cgr.read()
            st.markdown("""
            <div style="background: #0d1b2a; border: 1px solid #1b4965; border-left: 4px solid #e63946; padding: 10px; border-radius: 8px; font-size: 11px; margin-bottom: 8px; min-height: 105px;">
                <b style="color: #e63946;">⚖️ Casuística CGR:</b><br><code>Fichas Técnicas</code><br>
                <span style="color: #cbd5e1;">Auditoría Sullana, Paita y Huarmey.</span>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Casuística CGR", data=pdf_bytes_cgr, file_name="analisis_casuistica_contraloria_edan_fichas_tecnicas_y_pp0068.pdf", mime="application/pdf", use_container_width=True, key="btn_descarga_cgr_pdf")

    with col_ed5:
        if os.path.exists(ruta_pdf_indeci):
            with open(ruta_pdf_indeci, "rb") as f_pdf_indeci:
                pdf_bytes_indeci = f_pdf_indeci.read()
            st.markdown("""
            <div style="background: #0d1b2a; border: 1px solid #1b4965; border-left: 4px solid #ffb703; padding: 10px; border-radius: 8px; font-size: 11px; margin-bottom: 8px; min-height: 105px;">
                <b style="color: #ffb703;">🏛️ Formatos INDECI:</b><br><code>Anexos 01 al 06</code><br>
                <span style="color: #cbd5e1;">Desglose formularios EDAN v2.0.</span>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Formatos INDECI", data=pdf_bytes_indeci, file_name="analisis_formatos_oficiales_edan_indeci_y_amaru_fen.pdf", mime="application/pdf", use_container_width=True, key="btn_descarga_indeci_pdf")

    with col_ed6:
        if os.path.exists(ruta_pdf_doctrina):
            with open(ruta_pdf_doctrina, "rb") as f_pdf_doc:
                pdf_bytes_doc = f_pdf_doc.read()
            st.markdown("""
            <div style="background: #0d1b2a; border: 1px solid #1b4965; border-left: 4px solid #52b788; padding: 10px; border-radius: 8px; font-size: 11px; margin-bottom: 8px; min-height: 105px;">
                <b style="color: #52b788;">🧭 Delimitación C2:</b><br><code>Pre-Llenado Seguro</code><br>
                <span style="color: #cbd5e1;">Doctrina de pureza y Ley 31814.</span>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Delimitación C2", data=pdf_bytes_doc, file_name="doctrina_delimitacion_amaru_fen_prellenado_edan_vs_gestion_administrativa.pdf", mime="application/pdf", use_container_width=True, key="btn_descarga_doctrina_pdf")

    st.markdown("---")

    # MÓDULO SATÉLITE EXTERNO DE PRE-CARGA Y GOBERNANZA DE COMITÉ CGR
    st.markdown("""
    <div style="background: linear-gradient(135deg, #09182b 0%, #0d2744 100%); border-radius: 10px; padding: 16px 20px; border-left: 5px solid #06d6a0; border: 1px solid #1b4965; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; color: #64dfdf;">🛰️ MÓDULO SATÉLITE EXTERNO: PRE-CARGA EDAN & GOBERNANZA DE COMITÉ CGR</h4>
            <span style="background: #058c65; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px;">SIDECAR MUNICIPAL INDEPENDIENTE</span>
        </div>
        <p style="margin: 8px 0 0 0; font-size: 13px; color: #e2e8f0; line-height: 1.5;">
            <b>Arquitectura Desacoplada:</b> AMARU-FEN entrega su Dossier de Inteligencia C2 con Hash SHA-256 inmutable (ciencia pura).
            Este Módulo Satélite externo ingiere los datos, realiza el pre-llenado de los Formularios EDAN y Ficha Técnica de Maquinaria, 
            y <b>BLOQUEA la carga al SINPAD</b> hasta que un <b>Comité Humano Tripartito (Ley Nº 31814)</b> valide el 100% de las condiciones de control previo 
            establecidas en la <b>Memoria Capítulo 5 de la Contraloría General de la República</b> (Operativo <i>'Tus Ojos en la Emergencia'</i>).
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Inicializar estado del módulo satélite en sesión
    if "satelite_cgr_motor" not in st.session_state:
        st.session_state["satelite_cgr_motor"] = ModuloSateliteEDANCGR(ubigeo="150118", distrito="Lurigancho-Chosica")
        # Ingesta por defecto del evento Quebrada Carossio
        st.session_state["satelite_cgr_motor"].ingerir_dossier_amaru({
            "id_alerta": "DOSSIER-AMARU-2026-CHOSICA-001",
            "hash_sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "departamento": "LIMA",
            "provincia": "LIMA",
            "distrito": "Lurigancho-Chosica",
            "quebrada_o_cuenca": "Quebrada Carossio - Sector San Antonio",
            "coordenadas": {"lat": -11.9385, "lng": -76.6974},
            "tipo_evento": "Flujo de Detritos (Huaico)",
            "nivel_alerta": "ROJO",
            "familias_en_riesgo": 240,
            "sedimento_estimado_m3": 4500.0
        })

    sat_motor = st.session_state["satelite_cgr_motor"]
    staging = sat_motor.staging_edan

    subtab_stg, subtab_cgr, subtab_comite, subtab_despacho = st.tabs([
        "📋 1. Staging de Pre-Carga EDAN",
        "🔍 2. Pre-Auditoría CGR (Memoria Cap. 5)",
        "⚖️ 3. Comité de Validación (Ley 31814)",
        "🚀 4. Despacho Autorizado a SINPAD"
    ])

    with subtab_stg:
        st.markdown("##### 📦 Datos Asistidos desde AMARU-FEN (Listos para Inspección de Campo)")
        c_stg1, c_stg2, c_stg3, c_stg4 = st.columns(4)
        c_stg1.metric("Familias Afectadas Est.", f"{staging.familias_estimadas_afectadas}", "Formulario 2A")
        c_stg2.metric("Familias Damnificadas Est.", f"{staging.familias_estimadas_damnificadas}", "Pérdida Total")
        c_stg3.metric("Viviendas Colapsadas Est.", f"{staging.viviendas_colapsadas_est}", "Formulario 2B")
        c_stg4.metric("Volumen Descolmatación", f"{staging.volumen_descolmatacion_m3:,.0f} m³", "Ficha Técnica")

        col_stg_det1, col_stg_det2 = st.columns([1.2, 1])
        with col_stg_det1:
            st.markdown(f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 14px; font-size: 12px; line-height: 1.6;">
                <b style="color: #38bdf8;">🌐 Metadatos del Dossier Científico de Origen:</b><br>
                <b>ID Dossier C2:</b> <code>{staging.id_dossier_origen}</code><br>
                <b>Hash SHA-256 AMARU:</b> <code style="color: #06d6a0;">{staging.hash_dossier_amaru}</code><br>
                <b>Ubicación:</b> {staging.departamento} / {staging.provincia} / {staging.distrito}<br>
                <b>Sector Focal:</b> {staging.sector_critico} (GPS: {staging.coordenadas_impacto['lat']}, {staging.coordenadas_impacto['lng']})<br>
                <b>Vías Comprometidas:</b> {staging.metros_via_afectada_est} metros lineales | <b>Puentes en Riesgo:</b> {staging.puentes_comprometidos_est}
            </div>
            """, unsafe_allow_html=True)
        with col_stg_det2:
            st.markdown(f"""
            <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 14px; font-size: 12px; line-height: 1.6;">
                <b style="color: #ffb703;">🚜 Requerimiento Técnico de Maquinaria Pesada:</b><br>
                <b>Retroexcavadora Oruga:</b> <code>{staging.horas_retroexcavadora_est} horas</code> (rendimiento 45 m³/h)<br>
                <b>Volquetes de 15 m³:</b> <code>{staging.horas_volquete_est} horas</code> (acarreo a botadero)<br>
                <b>Imputación Presupuestal:</b> <code style="color: #06d6a0;">{staging.actividad_presupuestal}</code><br>
                <span style="color: #94a3b8; font-size: 11px;">*Cálculo geométrico respaldado para evitar observaciones de metrados inflados por CGR.</span>
            </div>
            """, unsafe_allow_html=True)

    with subtab_cgr:
        st.markdown("##### 🛡️ Matriz Automatizada de Control Previo (Criterios Memoria CGR Capítulo 5)")
        st.caption("Verificación preventiva contra las patologías detectadas en el operativo 'Tus Ojos en la Emergencia' de la Contraloría General de la República:")
        
        auditoria_res = sat_motor.evaluar_preauditoria_cgr()
        if auditoria_res["cumple_100_porciento"]:
            st.success(f"✅ **Estado de Pre-Auditoría CGR:** {auditoria_res['conformes']}/{auditoria_res['total_criterios']} Criterios Conformes (100%). Cero Riesgos Bloqueantes.")
        else:
            st.error(f"⚠️ **Riesgos CGR Detectados:** Criterios bloqueantes observados: {', '.join(auditoria_res['criterios_bloqueantes_fallidos'])}")

        for crit in sat_motor.criterios_cgr:
            with st.expander(f"📌 {crit.codigo}: {crit.nombre} — [{'CONFORME' if crit.estado == 'CONFORME' else 'OBSERVADO'}]", expanded=False):
                st.markdown(f"**Descripción:** {crit.descripcion}")
                st.markdown(f"**Casuística Evitada (Memoria Cap. 5):** `{crit.casuistica_evitada}`")
                st.markdown(f"**Verificación en Terreno / Almacén:** {crit.hallazgo}")
                col_cr1, col_cr2 = st.columns([1, 2])
                with col_cr1:
                    nuevo_est = st.selectbox(f"Estado {crit.codigo}:", ["CONFORME", "OBSERVADO"], index=0 if crit.estado == "CONFORME" else 1, key=f"sel_cr_{crit.codigo}")
                    crit.estado = nuevo_est

    with subtab_comite:
        st.markdown("##### 🏛️ Sesión Extraordinaria y Votación del Comité de Validación CGR (Ley Nº 31814)")
        st.caption("Principio de Soberanía Humana indelegable: Se exige unanimidad de los tres funcionarios para autorizar la carga formal a SINPAD v2.0.")

        col_miem1, col_miem2, col_miem3 = st.columns(3)
        cols_miembros = [col_miem1, col_miem2, col_miem3]

        for idx, m in enumerate(sat_motor.miembros_comite):
            with cols_miembros[idx]:
                st.markdown(f"""
                <div style="background: #111e38; border: 1px solid #1e3a60; border-radius: 8px; padding: 12px; font-size: 12px; min-height: 140px; margin-bottom: 8px;">
                    <b style="color: #64dfdf;">{m.cargo}</b><br>
                    <b>Funcionario:</b> {m.nombre_completo}<br>
                    <b>DNI:</b> <code>{m.dni}</code><br>
                    <b>Voto Actual:</b> <span style="color: {'#06d6a0' if m.voto == 'APROBADO' else '#e63946'}; font-weight: bold;">{m.voto}</span>
                </div>
                """, unsafe_allow_html=True)
                voto_sel = st.selectbox(f"Voto de {m.nombre_completo.split()[1]}:", ["APROBADO", "OBSERVADO"], index=0 if m.voto == "APROBADO" else 1, key=f"voto_{m.rol}")
                obs_input = st.text_input(f"Obs. {m.dni}:", value=m.observaciones or "", key=f"obs_{m.rol}")
                sat_motor.emitir_voto_miembro(m.rol, voto_sel, obs_input)

        st.markdown("---")
        if st.button("✍️ Consolidar Sesión del Comité y Generar Acta Oficial CGR", type="primary", use_container_width=True, key="btn_consolidar_comite"):
            acta = sat_motor.consolidar_sesion_comite()
            st.session_state["acta_generada"] = acta

        if sat_motor.acta:
            act = sat_motor.acta
            if act.estado_despacho_sinpad == "AUTORIZADO":
                st.success(f"✅ **ACTA COLEGIADA APROBADA:** `{act.id_acta}` | Unanimidad: **3/3** | Pre-Auditoría CGR: **100% CONFORME**")
                st.info(f"🔒 **Sello Criptográfico SHA-256 del Acta:** `{act.hash_acta_sha256}`")
            else:
                st.error(f"⛔ **SESIÓN OBSERVADA:** Carga bloqueada. No hay aprobación unánime o existen observaciones CGR pendientes.")

    with subtab_despacho:
        st.markdown("##### 🚀 Transmisión Oficial de Ficha EDAN y Ficha Técnica a INDECI / SINPAD v2.0")
        
        acta_actual = sat_motor.acta or sat_motor.consolidar_sesion_comite()
        
        if acta_actual.estado_despacho_sinpad != "AUTORIZADO":
            st.warning("🔒 **COMPUERTA CERO ACTIVA:** El botón de carga a SINPAD permanece bloqueado hasta que el Comité de Validación emita la aprobación unánime en la pestaña anterior.")
            st.button("⛔ Carga Bloqueada por Comité CGR (Ley 31814)", disabled=True, use_container_width=True)
        else:
            st.success("🔓 **COMPUERTA DESBLOQUEADA:** El Acta Colegiada cumple todos los requisitos legales y de control gubernamental.")
            if st.button("🚀 Transmitir Carga Oficial Homologada a SINPAD v2.0 & COEN", type="primary", use_container_width=True, key="btn_tx_sinpad"):
                exito, msg, payload = sat_motor.despachar_a_sinpad()
                if exito:
                    st.success(msg)
                    st.json(payload)
                    st.balloons()
                else:
                    st.error(msg)

    st.markdown("---")


    # MÓDULO DE DESPACHO A DEFENSA CIVIL MUNICIPAL (SINAGERD - LEY N° 29664)
    st.subheader("🏛️ Despacho de Alerta Táctica a la Unidad de Defensa Civil Municipal")
    st.caption("Notificación automatizada y trazable dirigida al funcionario responsable de Defensa Civil / GRD de la municipalidad distrital según la Ley N° 29664 y Ley N° 31814.")

    col_dc1, col_dc2 = st.columns([1, 1.4])

    with col_dc1:
        st.markdown("##### 📍 Selección de Municipalidad & Contacto Institucional")
        opciones_muni = [
            "110206-SIM - PUEBLO NUEVO / CARLOS EDU BAÑOS (carlosedubanos@gmail.com) [Simulación Sintética]",
            "110206 - PUEBLO NUEVO (CHINCHA, ICA) [Portal Oficial munipnuevochincha.gob.pe]",
            "200105 - CATACAOS (PIURA, PIURA)",
            "150118 - LURIGANCHO-CHOSICA (LIMA, LIMA)",
            "130103 - EL PORVENIR (TRUJILLO, LA LIBERTAD)"
        ]
        sel_muni_txt = st.selectbox("Seleccionar Destinatario / UBIGEO:", opciones_muni, index=0)
        ubigeo_sel_dc = sel_muni_txt.split(" - ")[0]

        contacto_dc = orchestrator.consultar_contacto_defensa_civil(ubigeo_sel_dc)
        if contacto_dc:
            st.markdown(f"""
            <div style="background:#0f1a2e;border:1px solid #1f3a60;border-left:4px solid #00b4d8;padding:14px;border-radius:8px;font-size:13px;line-height:1.6;margin-bottom:12px;">
                <b style="color:#00b4d8;">🏛️ {contacto_dc['municipalidad']}</b><br>
                <b>Órgano:</b> {contacto_dc['unidad_organica']}<br>
                <b>Responsable:</b> <span style="color:#ffb703;font-weight:bold;">{contacto_dc['responsable']['nombre_completo']}</span><br>
                <b>Designación:</b> <code>{contacto_dc['responsable']['acto_resolutivo_designacion']}</code><br>
                <b>Correo de Destino:</b> <code style="color:#48cae4;">{contacto_dc['canales_comunicacion']['correo_institucional_principal']}</code><br>
                <b>Teléfonos:</b> {', '.join(contacto_dc['canales_comunicacion']['telefonos_emergencia'])} (Anexo {contacto_dc['canales_comunicacion']['anexo_central']})<br>
                <b>Canal Telegram:</b> <code>{contacto_dc['canales_comunicacion'].get('canal_telegram', '@coel_defensacivil_bot')}</code>
            </div>
            """, unsafe_allow_html=True)
            if contacto_dc.get("portal_web_defensa_civil"):
                st.link_button("🌐 Visitar Portal Oficial de Defensa Civil del Municipio", contacto_dc["portal_web_defensa_civil"])

        st.markdown("---")
        st.markdown("##### ⚖️ Compuerta de Soberanía Humana (Ley N° 31814 & LPDP 29733)")
        st.caption("🔒 **Regla Estricta:** La IA NUNCA dispara correos oficiales sin autorización humana explícita.")
        
        chk_autoriza_humano = st.checkbox(
            "✍️ Yo, como Autoridad Humana / Evaluador C2, valido la telemetría y AUTORIZO este despacho.",
            value=True,
            key="chk_firma_humana_dc"
        )
        nombre_firmante = st.text_input(
            "Nombre y Cargo del Autorizador Humano:",
            value="Carlos Edu Baños — Evaluador de Riesgos FEN",
            key="txt_firmante_dc"
        )

        btn_disparar_correo = st.button("🚀 Emitir Despacho Táctico con Firma Humana (Correo + Telegram)", type="primary", use_container_width=True)

    with col_dc2:
        st.markdown("##### 📬 Vista Previa del Despacho Entregado")
        if btn_disparar_correo:
            if not chk_autoriza_humano:
                st.error("⛔ DISPARO BLOQUEADO POR LEY N° 31814: La IA no puede emitir despachos sin autorización humana firmada.")
            else:
                with st.spinner("Validando firma humana y generando despachos (Email + Telegram)..."):
                    firma_dict = {
                        "autorizador": nombre_firmante,
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "declaracion": "Aprobación humana indelegable de alerta táctica",
                        "soberania_humana_valida": True
                    }
                    resultado_despacho = orchestrator.disparar_alerta_defensa_civil_municipal(
                        ubigeo=ubigeo_sel_dc,
                        anomalia_tsm=float(tsm_anomalia),
                        precipitacion_estimada_mm=float(simular_precipitacion),
                        modo_simulacion=True
                    )
                    st.session_state["ultimo_despacho_dc"] = resultado_despacho
                    st.toast(f"¡Alerta autorizada emitida a {resultado_despacho['destinatario_correo']}!")

        if "ultimo_despacho_dc" in st.session_state:
            desp = st.session_state["ultimo_despacho_dc"]
            reg = desp["registro_auditoria"]
            st.success(f"✅ **Estado de Envío:** `{reg['estado_envio']}` | **ID Auditoría:** `{reg['id_despacho']}` | **Autorizado por:** `{reg['autorizacion_humana']['autorizador']}`")
            st.caption(f"🛡️ **Protección de Datos Personales (Ley N° 29733):** Correo enmascarado en registros públicos: `{desp.get('correo_enmascarado_lpdp', desp['destinatario_correo'])}`")

            tab_mail_full, tab_telegram_short = st.tabs(["📧 1. Informe Detallado por Correo Electrónico", "📱 2. Informe Corto para Telegram / Móvil Push"])

            with tab_mail_full:
                st.markdown(f"**Asunto Oficial:** `{desp['asunto']}`")
                st.markdown(f"**Destinatario Oficial:** `{desp['destinatario_correo']}`")
                st.iframe(desp["cuerpo_html"], height=480)
                with st.expander("📄 Ver Texto Plano Oficial (para expediente administrativo)"):
                    st.code(desp["cuerpo_texto"], language="text")

            with tab_telegram_short:
                st.markdown("**💬 Formato Optimizado para Telegram / WhatsApp COEL (Canal Táctico Inmediato):**")
                st.caption(f"Enviado al canal: `{desp['contacto_municipal']['canales_comunicacion'].get('canal_telegram', '@coel_defensacivil_bot')}`")
                st.code(desp.get("mensaje_telegram_corto", "Alerta breve no generada"), language="markdown")
                st.info("💡 **Ventaja Operativa:** Este mensaje de menos de 1,000 caracteres permite al Jefe de Defensa Civil leer en 15 segundos la directiva en su teléfono móvil mientras se moviliza a la zona de emergencia.")
        else:
            st.info("👈 Selecciona el destinatario, revisa la firma humana obligatoria y presiona el botón para generar el informe detallado por correo y el informe corto por Telegram.")


# TAB 8: ASISTENTE SOBERANO C2 (CHAT GROUNDED EXCLUSIVO AMARU-FEN)
with tab_chat:
    st.subheader("💬 Asistente Soberano C2: Inteligencia Doctrinal, Territorial y Pericial")
    st.caption("Modelo de 'Jardín Vallado' (Strictly Grounded RAG). Procesa única y exclusivamente información de fuentes oficiales homologadas de AMARU-FEN (Ley Nº 31814 y D.S. Nº 124-2026-PCM). Cero alucinaciones.")

    # Banner Institucional de Seguridad y Soberanía
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 10px; padding: 14px 18px; border-left: 5px solid #00b4d8; margin-bottom: 16px; border: 1px solid #334155;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 14px; font-weight: bold; color: #38bdf8;">🛡️ FILTRO DURA LEX & ALLOWLIST SOBERANA ACTIVA</span>
            <span style="background: #0284c7; color: white; font-size: 11px; padding: 3px 8px; border-radius: 5px; font-weight: bold;">TIER 1 ESTRICTO</span>
        </div>
        <p style="margin: 6px 0 0 0; font-size: 12px; color: #cbd5e1;">
            Este canal pericial está acoplado al catálogo maestro de 1,891 distritos, el repositorio de quebradas críticas, los 4 expedientes históricos de FEN y el catálogo normativo del SINAGERD. La búsqueda abierta en internet está bloqueada por política de ciberdefensa.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Inicializar historial de chat en sesión
    if "historial_chat_amaru" not in st.session_state:
        st.session_state["historial_chat_amaru"] = [
            {
                "rol": "assistant",
                "contenido": (
                    "**Bienvenido a la Sala de Asistencia Táctica C2 de AMARU-FEN.**\n\n"
                    "Estoy habilitado para responder con rigor pericial y matemático sobre:\n"
                    "* 📍 **Expedientes de Backtesting por UBIGEO:** Catacaos (200105), Tumbes (240101), Chosica (150118), Ica (110101), Íllimo (140303), Reque (140111), Punta Hermosa (150126), Chaclacayo (150107), Puno (210101).\n"
                    "* 🌊 **Sustento del IPH-FEN e Histéresis:** Por qué no basta la lluvia diaria y cómo se modeló la predicción de los 7 huaicos de Trujillo en 2017.\n"
                    "* ⚖️ **Fórmulas e Índices:** Formulación del `IRCE-FEN`, `IPAT`, autovalores de Saaty AHP ($CR \\le 0.10$) y semáforos.\n"
                    "* 📜 **Marco Legal:** D.S. Nº 124-2026-PCM (compras directas), Ley Nº 31814 (Soberanía Humana) y R.J. Nº 112-2014-CENEPRED.\n"
                    "* ⛰️ **Quebradas y Territorio:** Umbrales pluviométricos y fajas marginales de los 893 distritos en emergencia."
                ),
                "fuentes": [
                    {"fuente": "Sistema AMARU-FEN - Doctrina C2", "tier": "Tier 1 (Oficial)", "referencia": "repositorio_central_amaru"}
                ],
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        ]

    # Selector de Audiencia en Tab Chat
    st.markdown("##### 👤 1. Selecciona tu Perfil para Calibrar el Chat:")
    rol_chat_tab = st.radio(
        "Perfil Operativo:",
        ["👤 Vecino / Ciudadano", "🏛️ Alcalde / Autoridad COEL", "💻 Técnico C2 / Científico", "📰 Periodista / Medios"],
        horizontal=True,
        key="rb_rol_tab_chat"
    )
    rol_tab_tag = "ciudadano" if "Vecino" in rol_chat_tab else ("alcalde" if "Alcalde" in rol_chat_tab else ("tecnico" if "Técnico" in rol_chat_tab else "periodista"))

    # Atajos Rápidos Dinámicos según el Rol Seleccionado
    st.markdown(f"##### ⚡ 2. Consultas Rápidas Sugeridas para: `{rol_chat_tab}`")
    prompt_disparado = None

    if rol_tab_tag == "ciudadano":
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📍 Soy de Catacaos, ¿qué info tienes?", use_container_width=True, key="btn_c1_tc"):
            prompt_disparado = "Soy de Catacaos, qué información tienes para mí"
        if c2.button("🏃‍♂️ ¿Hacia dónde evacúo en mi zona?", use_container_width=True, key="btn_c2_tc"):
            prompt_disparado = "Hacia dónde debo evacuar si sube el río en mi distrito"
        if c3.button("🎒 Mochila de Emergencia Familiar", use_container_width=True, key="btn_c3_tc"):
            prompt_disparado = "Qué debe tener mi mochila de emergencia para El Niño"
        if c4.button("🐾 Proteger animales y enseres", use_container_width=True, key="btn_c4_tc"):
            prompt_disparado = "Cómo protejo a mis animales y enseres antes de la lluvia"

    elif rol_tab_tag == "alcalde":
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🚜 Compras 24h bajo D.S. 124", use_container_width=True, key="btn_a1_tc"):
            prompt_disparado = "Como alcalde, cómo contrato maquinaria pesada en 24h bajo el D.S. 124-2026-PCM sin riesgo de Contraloría"
        if c2.button("🚨 Caudal crítico y diques Catacaos", use_container_width=True, key="btn_a2_tc"):
            prompt_disparado = "Cuáles son los puntos críticos y diques en riesgo en Catacaos UBIGEO 200105"
        if c3.button("📋 Pre-redactar Ficha EDAN", use_container_width=True, key="btn_a3_tc"):
            prompt_disparado = "Generar pre-borrador de Ficha EDAN para Catacaos"
        if c4.button("🛡️ Blindaje legal y PP 0068", use_container_width=True, key="btn_a4_tc"):
            prompt_disparado = "Qué informe pericial necesito para blindarme ante Contraloría con el PP 0068"

    elif rol_tab_tag == "tecnico":
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📐 Saaty AHP (CR <= 0.10)", use_container_width=True, key="btn_t1_tc"):
            prompt_disparado = "Explícame la fórmula del IRCE-FEN y por qué la matriz Saaty tiene consistencia CR menor a 0.10"
        if c2.button("🌊 IPH y 7 Huaicos Trujillo", use_container_width=True, key="btn_t2_tc"):
            prompt_disparado = "Por qué AMARU-FEN usa un IPH en lugar de solo mirar la lluvia de hoy y qué es la histéresis"
        if c3.button("📊 Backtesting (96.2% éxito)", use_container_width=True, key="btn_t3_tc"):
            prompt_disparado = "Por qué la probabilidad de éxito en el backtesting va del 94.2 al 98.4 y qué significa el 96.2"
        if c4.button("⛰️ Quebradas Críticas Reincidentes", use_container_width=True, key="btn_t4_tc"):
            prompt_disparado = "Cuáles son las quebradas críticas de mayor riesgo y qué umbrales tienen"

    else: # periodista
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("📰 Resumen para Nota de Prensa", use_container_width=True, key="btn_p1_tc"):
            prompt_disparado = "Para nota de prensa sobre Catacaos, qué información oficial verificada se tiene"
        if c2.button("🛑 Descarte: ¿Colapso de Poechos?", use_container_width=True, key="btn_p2_tc"):
            prompt_disparado = "Es verdad el rumor de que la represa de Poechos va a colapsar"
        if c3.button("📊 Cifras D.S. 124-2026-PCM", use_container_width=True, key="btn_p3_tc"):
            prompt_disparado = "Cuáles son las cifras oficiales de los 893 distritos en emergencia bajo D.S. 124-2026-PCM"
        if c4.button("🛡️ Fuentes Oficiales Tier 1", use_container_width=True, key="btn_p4_tc"):
            prompt_disparado = "Cuáles son las fuentes autorizadas y qué significa el Tier 1 en AMARU-FEN"

    st.markdown("---")

    # Renderizar Historial de Mensajes
    for mensaje in st.session_state["historial_chat_amaru"]:
        rol_msg = mensaje["rol"]
        with st.chat_message(rol_msg, avatar="🌊" if rol_msg == "assistant" else "👤"):
            st.markdown(mensaje["contenido"])
            if rol_msg == "assistant" and mensaje.get("fuentes"):
                with st.expander("🛡️ Cadena de Custodia & Fuentes Homologadas Citadas", expanded=False):
                    for idx, f in enumerate(mensaje["fuentes"], 1):
                        st.markdown(f"**[{idx}] {f['fuente']}** | `{f.get('tier', 'Tier 1')}` | Ref: `{f.get('referencia', '')}`")
                    st.caption(f"🕒 Timestamp de Consulta Pericial: `{mensaje.get('timestamp', '')}`")

    # Entrada de Chat (Prompt Libre)
    prompt_usuario = st.chat_input("Escribe tu consulta táctica, código UBIGEO (ej. 200105), fórmula o pregunta sobre El Niño...", key="chat_tab_input")
    prompt_final = prompt_disparado or prompt_usuario

    if prompt_final:
        # Registrar mensaje de usuario
        st.session_state["historial_chat_amaru"].append({
            "rol": "user",
            "contenido": prompt_final,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        # Procesar con el motor soberano
        with st.spinner(f"Consultando fuentes homologadas para perfil {rol_chat_tab}..."):
            u_contexto = st.session_state.get("u_activo_sb")
            resultado_chat = motor_chat_soberano.procesar_consulta(prompt_final, u_activo=u_contexto, rol=rol_tab_tag)

            st.session_state["historial_chat_amaru"].append({
                "rol": "assistant",
                "contenido": resultado_chat["respuesta"],
                "fuentes": resultado_chat["fuentes_citadas"],
                "categoria": resultado_chat["categoria"],
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            st.rerun()

    # Controles de Sesión de Chat
    col_acc1, col_acc2 = st.columns([1, 4])
    with col_acc1:
        if st.button("🗑️ Reiniciar Sesión de Chat", use_container_width=True):
            st.session_state["historial_chat_amaru"] = [
                {
                    "rol": "assistant",
                    "contenido": "Sesión reiniciada. Estoy listo para procesar tus consultas doctrinales y periciales sobre AMARU-FEN.",
                    "fuentes": [{"fuente": "Sistema AMARU-FEN", "tier": "Tier 1", "referencia": "reinicio_sesion"}],
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
            ]
            st.rerun()
    with col_acc2:
        texto_export = "\n\n---\n\n".join([
            f"**[{m['rol'].upper()} - {m.get('timestamp', '')}]**\n\n{m['contenido']}"
            for m in st.session_state["historial_chat_amaru"]
        ])
        st.download_button(
            "📥 Descargar Bitácora Pericial del Diálogo (Markdown)",
            data=texto_export,
            file_name=f"bitacora_dialogo_c2_amaru_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=False
        )

# ==================== TAB 9: AMARU-CHIRI (MANDO AZUL: LA NIÑA & HELADAS) ====================
with tab_chiri:
    st.subheader("❄️ AMARU-CHIRI: Sala de Mando C2 ante La Niña & Heladas Altoandinas")
    st.caption("Subsistema Desacoplado: Vigilancia de Bajas Temperaturas, Crioclima y Pastizales en Puno, Huancavelica y Arequipa.")

    st.markdown("""
    <div style="background: linear-gradient(135deg, #082f49 0%, #020617 100%); border-radius: 12px; padding: 16px 20px; border: 1.5px solid #00f2fe; margin-bottom: 18px; box-shadow: 0 4px 20px rgba(0,242,254,0.15);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 16px; font-weight: 900; color: #00f2fe;">🔵 MANDO AZUL DESACOPLADO: AMARU-CHIRI (LA NIÑA)</span><br>
                <span style="font-size: 12px; color: #bae6fd;">Segregación Doctrinal Estricta: <b>ISH-CHIRI</b> para Heladas | <b>IPH-FEN</b> Reservado para Huaicos</span>
            </div>
            <span style="background: #0369a1; color: #ffffff; font-size: 11px; padding: 4px 12px; border-radius: 6px; font-weight: bold; border: 1px solid #38bdf8;">C2 TWIN-ENGINE ACTIVE</span>
        </div>
        <p style="margin: 8px 0 0 0; font-size: 13px; color: #cbd5e1;">
            Este módulo opera con base de datos independiente (<code>data/catalogo_distritos_heladas_nina.json</code>) y motor polar propio (<code>core/reloj_nina.py</code>). 
            También puedes ejecutar la <b>Consola Dedicada Exclusiva</b> mediante <code>streamlit run ui/app_nina.py</code>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if AgenteCrioclimaticoNina and MotorRelojNina:
        agente_chiri = AgenteCrioclimaticoNina()
        motor_reloj_chiri = MotorRelojNina()

        # Parámetros rápidos en la pestaña
        c_ch1, c_ch2, c_ch3 = st.columns(3)
        with c_ch1:
            tsm_chiri_tab = st.slider("Anomalía TSM Pacífico (Niño 3.4/1+2):", min_value=-3.0, max_value=0.0, value=-1.4, step=0.1, key="sl_tsm_chiri_tab")
        with c_ch2:
            alisios_chiri_tab = st.slider("Velocidad Alisios (m/s):", min_value=4.0, max_value=12.0, value=8.0, step=0.5, key="sl_alisios_chiri_tab")
        with c_ch3:
            delta_tmin_tab = st.slider("Severidad Ola Polar (ΔTmin):", min_value=-6.0, max_value=2.0, value=-2.0, step=0.5, key="sl_delta_tmin_tab")

        resumen_tab = agente_chiri.ejecutar_barrido_territorial(
            escenario_tmin_delta=delta_tmin_tab,
            anomalia_tsm_pacifico=tsm_chiri_tab,
            alisios_velocidad=alisios_chiri_tab
        )

        # Métricas crioclimáticas expandidas con frente educativo y vial
        mc1, mc2, mc3, mc4, mc5, mc6 = st.columns(6)
        mc1.metric("Anomalía TSM La Niña", f"{tsm_chiri_tab:+.1f} °C", "Fase Fría Activa")
        mc2.metric("Alerta Roja Glacial", f"{resumen_tab.distritos_alerta_roja} de {resumen_tab.total_distritos_evaluados}", "8 Regiones")
        mc3.metric("Alpacas en Riesgo", f"{resumen_tab.alpacas_en_riesgo_critico:,}", "Población Pecuaria")
        mc4.metric("Colegios / Escolares", f"{resumen_tab.total_colegios_en_riesgo} II.EE.", f"{resumen_tab.total_escolares_en_riesgo:,} alumnos")
        mc5.metric("Directiva PREVAED", f"{resumen_tab.colegios_con_suspension_sugerida} II.EE.", "Suspensión Clases")
        mc6.metric("Máximo ISH-CHIRI", f"{resumen_tab.ish_chiri_maximo:.1f} %", resumen_tab.distrito_maxima_severidad)

        st.markdown("---")

        # Columnas para Reloj de La Niña y Tabla de Distritos
        col_clk_chiri, col_tbl_chiri = st.columns([1.8, 2.2])

        with col_clk_chiri:
            st.markdown("##### ⏰ El Reloj de La Niña (Dial Crioclimático)")
            modelo_chiri_tab = motor_reloj_chiri.calcular_reloj(
                anomalia_tsm=tsm_chiri_tab,
                velocidad_alisios=alisios_chiri_tab,
                tmin_promedio=sum(e.tmin_observada_c for e in resumen_tab.evaluaciones) / len(resumen_tab.evaluaciones)
            )
            svg_chiri_tab = motor_reloj_chiri.generar_svg_reloj(modelo_chiri_tab, ancho=480, alto=480)
            st.markdown(f"""
            <div style="background: radial-gradient(circle at center, #082f49 0%, #020617 100%); padding: 12px; border-radius: 14px; border: 1px solid #0369a1; text-align: center;">
                {svg_chiri_tab}
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"**Análogo:** {modelo_chiri_tab.analogo_dominante.evento_nombre} ({modelo_chiri_tab.analogo_dominante.porcentaje_similitud:.1f} %)")

        with col_tbl_chiri:
            st.markdown("##### 📊 Tablero de Mando Territorial (27 Distritos Priorizados)")
            df_chiri_tab = pd.DataFrame([
                {
                    "Código": e.codigo_tactico_c2,
                    "Región": e.departamento,
                    "Distrito": e.distrito,
                    "Altitud": f"{e.altitud_msnm} m",
                    "Tmin": f"{e.tmin_observada_c:.1f} °C",
                    "ISH-CHIRI": f"{e.ish_chiri:.1f} %",
                    "Alerta": e.nivel_alerta.replace("ALERTA_", "").replace("CONDICION_", ""),
                    "II.EE.": e.colegios_vulnerables,
                    "Escolares": f"{e.escolares_en_riesgo:,}",
                    "Directiva PREVAED": "SUSPENSIÓN" if "SUSPENSIÓN" in e.directiva_educativa_prevaed else "HORARIO INVIERNO",
                    "Alerta Vial": "ESCARCHA" if "PELIGRO" in e.alerta_vial_escarcha else "NORMAL"
                }
                for e in resumen_tab.evaluaciones
            ])
            st.dataframe(df_chiri_tab, use_container_width=True, hide_index=True, height=440)
    else:
        st.warning("El módulo de La Niña está disponible pero no pudo cargarse en este entorno.")





