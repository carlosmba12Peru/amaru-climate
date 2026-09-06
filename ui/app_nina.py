"""
SISTEMA AMARU-CHIRI | CONSOLA TÁCTICA C2 DE LA NIÑA & HELADAS ALTOANDINAS
========================================================================
Fase Fría del ENOS: Monitoreo de Bajas Temperaturas, Crioclima y Protección Pecuaria
Regiones Priorizadas: Puno, Huancavelica, Arequipa Altoandina
Índice Oficial: ISH-CHIRI (Índice de Severidad de Heladas)
"""

import os
import sys
from pathlib import Path

# Configuración de ruta raíz
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import pandas as pd
import json
from datetime import datetime

from core.reloj_nina import MotorRelojNina, ModeloRelojNina
from agents.agente_crioclimatico_nina import AgenteCrioclimaticoNina, ResumenEvaluacionChiri

st.set_page_config(
    page_title="AMARU-CHIRI | Sala de Mando C2 & Gestión del Riesgo Crioclimático (La Niña & Heladas)",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales Glassmorphism Crioclimático (Paleta Dark Glacial)
st.markdown("""
<style>
    .main { background-color: #030712; color: #f0fdfa; }
    .stMetric { background: #082f49; border-radius: 10px; padding: 14px; border-left: 5px solid #00f2fe; }
    .badge-rojo-glacial { background-color: #0369a1; color: #ffffff; padding: 4px 10px; border-radius: 6px; font-weight: bold; border: 1px solid #38bdf8; }
    .card-chiri { background: linear-gradient(135deg, #082f49 0%, #020617 100%); border-radius: 12px; padding: 18px 22px; border: 1px solid #0369a1; box-shadow: 0 4px 20px rgba(0,242,254,0.15); margin-bottom: 15px; }
    .alerta-roja { background: rgba(127, 29, 29, 0.4); border-left: 5px solid #ef4444; padding: 12px; border-radius: 6px; }
    .alerta-naranja { background: rgba(124, 45, 18, 0.4); border-left: 5px solid #f97316; padding: 12px; border-radius: 6px; }
    .alerta-amarilla { background: rgba(113, 63, 18, 0.4); border-left: 5px solid #eab308; padding: 12px; border-radius: 6px; }
    .alerta-verde { background: rgba(6, 78, 59, 0.4); border-left: 5px solid #10b981; padding: 12px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# Inicializar Agente y Motor
@st.cache_resource
def get_agente():
    return AgenteCrioclimaticoNina()

agente = get_agente()
motor_reloj = MotorRelojNina()

# ==================== BARRA LATERAL (SIDEBAR C2) ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/snowflake.png", width=70)
    st.markdown("## ❄️ AMARU-CHIRI C2")
    st.caption("Subsistema Táctico ante La Niña & Heladas Altoandinas")
    
    # Conmutador de Mando Doctrinal
    st.markdown("""
    <div style="background: #020617; padding: 10px; border-radius: 8px; border: 1px solid #0369a1; margin-bottom: 15px;">
        <div style="font-size: 11px; color: #94a3b8; font-weight: bold;">SISTEMA ACTIVO:</div>
        <div style="font-size: 13px; color: #00f2fe; font-weight: 900;">🔵 MANDO AZUL: AMARU-CHIRI</div>
        <div style="font-size: 10px; color: #38bdf8;">Fase Fría / Heladas / Pasturas</div>
        <hr style="margin: 6px 0; border-color: #1e293b;">
        <div style="font-size: 10px; color: #64748b;">Mando Hermano:</div>
        <div style="font-size: 11px; color: #ff4d6d; font-weight: bold;">🔴 MANDO ROJO: AMARU-FEN</div>
        <div style="font-size: 9px; color: #94a3b8;">Fase Cálida / Huaicos / IPH-FEN</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎛️ Parámetros del Escenario Frío")
    tsm_sim = st.slider("Anomalía TSM Pacífico (°C)", min_value=-3.0, max_value=0.0, value=-1.4, step=0.1, help="Enfriamiento de aguas en región Niño 3.4 y 1+2")
    alisios_sim = st.slider("Velocidad Alisios (m/s)", min_value=4.0, max_value=12.0, value=8.0, step=0.5, help="Intensidad de vientos alisios y flujo polar")
    delta_tmin = st.slider("Intensidad de Ola Polar (ΔTmin)", min_value=-8.0, max_value=2.0, value=-2.0, step=0.5, help="Descenso adicional sobre umbrales históricos")

    st.markdown("---")
    st.markdown("### 📚 Doctrina de Índices")
    st.markdown("""
    * **`ISH-CHIRI`:** *Índice de Severidad de Helada* (0 a 100%). Mide acumulación de noches bajo cero y viento catabático en pastizales altoandinos.
    * **`IPH-FEN`:** *Índice de Previsión de Huaicos*. Reservado con exclusividad para lluvias y lodo en cuencas del Pacífico.
    """)

# ==================== BANNER PRINCIPAL C2 ====================
col_title, col_status = st.columns([3.5, 1.5])
with col_title:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px;">
        <div>
            <h2 style="margin: 0; color: #00f2fe; letter-spacing: 0.5px;">❄️ AMARU-CHIRI: SALA DE MANDO C2 ANTE LA NIÑA</h2>
            <div style="font-size: 13px; color: #bae6fd;">Centro de Comando Crioclimático: Monitoreo de Heladas Extremas, Bofedales y Camélidos Sudamericanos</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div style="background: #082f49; padding: 10px 14px; border-radius: 8px; border: 1px solid #00f2fe; text-align: right;">
        <span style="font-size: 11px; color: #38bdf8; font-weight: bold;">FASE ENOS ACTIVA:</span><br>
        <span style="font-size: 15px; color: #ffffff; font-weight: 900;">LA NIÑA (FASE FRÍA)</span><br>
        <span style="font-size: 10px; color: #7dd3fc;">Regiones: Puno | Huancavelica | Arequipa</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== EJECUTAR BARRIDO TERRITORIAL ====================
resumen = agente.ejecutar_barrido_territorial(
    escenario_tmin_delta=delta_tmin,
    anomalia_tsm_pacifico=tsm_sim,
    alisios_velocidad=alisios_sim
)

# ==================== BARRA DE MÉTRICAS C2 ====================
# ==================== BARRA DE MÉTRICAS C2 ====================
k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
k1.metric("Anomalía TSM", f"{tsm_sim:+.1f} °C", "Fase Fría Activa")
k2.metric("Alerta Roja", f"{resumen.distritos_alerta_roja} de {resumen.total_distritos_evaluados}", "8 Regiones")
k3.metric("Alpacas en Riesgo", f"{resumen.alpacas_en_riesgo_critico:,}", "Puno/Cusco/Tacna")
k4.metric("Pob. Vulnerable", f"{resumen.personas_vulnerables_en_riesgo_critico:,}", "Niños y Ancianos")
k5.metric("Colegios / Escolares", f"{resumen.total_colegios_en_riesgo} II.EE.", f"{resumen.total_escolares_en_riesgo:,} alumnos")
k6.metric("Directiva PREVAED", f"{resumen.colegios_con_suspension_sugerida} II.EE.", "Suspensión Clases")
k7.metric("Vías con Hielo", f"{resumen.vias_con_alerta_hielo} rutas", "Peligro Escarcha")

st.markdown("---")

# ==================== PESTAÑAS PRINCIPALES ====================
tab_reloj, tab_tablero, tab_inspector, tab_educacion, tab_doctrina = st.tabs([
    "⏰ 1. El Reloj de La Niña (Cronómetro Polar)",
    "📊 2. Tablero Táctico Territorial (27 Distritos)",
    "🔍 3. Inspector Distrital & Estación Virtual",
    "🏫 4. Frente Educativo & Vial (PRONIED / PREVAED)",
    "⚖️ 5. Doctrina de Mando & Marco Legal (PMHF)"
])

# ----------------- TAB 1: EL RELOJ DE LA NIÑA -----------------
with tab_reloj:
    st.subheader("⏰ El Reloj de La Niña: Dial Polar Crioclimático & Análogo Histórico")
    st.caption("Visualización polar estratégica: 12 Horas = 12 Meses | 6:00 Solsticio de Invierno (Jun) | 7:00 Clímax Glacial (Jul)")

    col_rel_svg, col_rel_meta = st.columns([2.5, 2.0])
    
    with col_rel_svg:
        # Recuperar y renderizar SVG
        modelo_reloj = motor_reloj.calcular_reloj(
            anomalia_tsm=tsm_sim,
            velocidad_alisios=alisios_sim,
            tmin_promedio=sum(e.tmin_observada_c for e in resumen.evaluaciones) / len(resumen.evaluaciones)
        )
        svg_code = motor_reloj.generar_svg_reloj(modelo_reloj, ancho=520, alto=520)
        st.components.v1.html(f"""
        <div style="display: flex; justify-content: center; align-items: center; background: radial-gradient(circle at center, #082f49 0%, #020617 100%); padding: 10px; border-radius: 16px; border: 1px solid #0369a1; box-shadow: 0 10px 30px rgba(0,242,254,0.15);">
            {svg_code}
        </div>
        """, height=560, scrolling=False)

    with col_rel_meta:
        st.markdown(f"""
        <div class="card-chiri">
            <h4 style="color: #00f2fe; margin-top: 0;">🧭 Estado Operacional del Reloj Crioclimático</h4>
            <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                <b>• Posición Táctica del Minutero:</b> <span style="color: #38bdf8; font-weight: bold;">{modelo_reloj.minutero.hora_tactica_final:.2f} h</span> ({modelo_reloj.minutero.calificacion_tiempo.replace('_', ' ')})<br>
                <b>• Desfase Dinámico Acumulado:</b> <span style="color: #00f2fe; font-weight: bold;">{modelo_reloj.minutero.desfase_forzamiento_dias:+.1f} días</span> frente al calendario solar.<br>
                <b>• Ventana Glacial de Amenaza:</b> Mayo (hora 4:45) a Agosto (hora 8:45) con clímax a las <b>6:45 - 7:00 (Julio)</b>.<br>
                <b>• Proyección del Clímax:</b> <span style="color: #fde047; font-weight: bold;">{modelo_reloj.minutero.fecha_proyectada_climax}</span>.
            </div>
            <hr style="border-color: #0369a1; margin: 12px 0;">
            <h5 style="color: #bae6fd; margin: 0 0 6px 0;">🏛️ Patrón Análogo Dominante</h5>
            <div style="background: #020617; padding: 10px; border-radius: 8px; border-left: 4px solid #00f2fe;">
                <div style="font-size: 14px; font-weight: bold; color: #ffffff;">{modelo_reloj.analogo_dominante.evento_nombre}</div>
                <div style="font-size: 11px; color: #38bdf8;">Similitud Multivariable: <b>{modelo_reloj.analogo_dominante.porcentaje_similitud:.1f} %</b></div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">{modelo_reloj.analogo_dominante.leccion_tactica}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info(f"📋 **Síntesis Ejecutiva C2:** {modelo_reloj.resumen_ejecutivo}")

# ----------------- TAB 2: TABLERO TÁCTICO TERRITORIAL -----------------
with tab_tablero:
    st.subheader("📊 Tablero Táctico Territorial: 27 Distritos Priorizados (8 Regiones)")
    st.caption("Monitoreo de Severidad Crioclimática (ISH-CHIRI) sobre Puno, Cusco, Tacna, Lima, Huancavelica, Pasco, Huánuco y Arequipa")

    # Filtro por Región
    f_c1, f_c2 = st.columns([1.5, 3.5])
    with f_c1:
        deps_disponibles = ["TODOS"] + sorted(list(set(e.departamento for e in resumen.evaluaciones)))
        filtro_dep = st.selectbox("Filtrar por Departamento:", deps_disponibles)
    
    lista_mostrar = resumen.evaluaciones
    if filtro_dep != "TODOS":
        lista_mostrar = [e for e in lista_mostrar if e.departamento == filtro_dep]

    # Crear tabla estructurada
    filas_tabla = []
    for e in lista_mostrar:
        filas_tabla.append({
            "Código C2": e.codigo_tactico_c2,
            "Región": e.departamento,
            "Provincia": e.provincia,
            "Distrito": e.distrito,
            "Altitud": f"{e.altitud_msnm:,} m",
            "Tmin": f"{e.tmin_observada_c:.1f} °C",
            "Viento": f"{e.viento_kmh:.0f} km/h",
            "Días <0°C": e.dias_consecutivos_bajo_cero,
            "ISH-CHIRI": f"{e.ish_chiri:.1f} %",
            "Nivel Alerta": e.nivel_alerta.replace("ALERTA_", "").replace("CONDICION_", ""),
            "II.EE. Riesgo": e.colegios_vulnerables,
            "Alumnos": f"{e.escolares_en_riesgo:,}",
            "Directiva PREVAED": "SUSPENSIÓN" if "SUSPENSIÓN" in e.directiva_educativa_prevaed else ("HORARIO INVIERNO" if "HORARIO" in e.directiva_educativa_prevaed else "NORMAL"),
            "Alerta Vial": "HIELO/ESCARCHA" if "PELIGRO" in e.alerta_vial_escarcha else "NORMAL"
        })

    df_chiri = pd.DataFrame(filas_tabla)
    st.dataframe(df_chiri, use_container_width=True, hide_index=True)

# ----------------- TAB 3: INSPECTOR DISTRITAL -----------------
with tab_inspector:
    st.subheader("🔍 Inspector Distrital de Bajas Temperaturas & Estación Virtual")
    st.caption("Ficha técnica detallada por código UBIGEO oficial")

    nombres_dist = [f"{e.ubigeo} - {e.departamento} - {e.nombre_comun}" for e in resumen.evaluaciones]
    dist_sel_txt = st.selectbox("Seleccione un distrito para inspección detallada:", nombres_dist)
    ubigeo_sel = dist_sel_txt.split(" - ")[0]
    
    eval_sel = next(e for e in resumen.evaluaciones if e.ubigeo == ubigeo_sel)
    meta_sel = next(d for d in agente.distritos_catalogo if d["ubigeo"] == ubigeo_sel)

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        st.markdown(f"""
        <div class="card-chiri">
            <h4 style="color: #00f2fe; margin-top: 0;">📍 {eval_sel.nombre_comun} ({eval_sel.departamento})</h4>
            <b>• UBIGEO Oficial:</b> <code>{eval_sel.ubigeo}</code><br>
            <b>• Altitud Capital / Cota Máx:</b> {eval_sel.altitud_msnm} m.s.n.m. / {meta_sel.get('cota_maxima_msnm', 'N/A')} m.s.n.m.<br>
            <b>• Prioridad PMHF / CENEPRED:</b> {meta_sel.get('prioridad_pmhf', 'N/A')}<br>
            <b>• Estación Meteorológica SENAMHI:</b> {eval_sel.estacion_senamhi}<br>
            <b>• Récord Histórico Tmin:</b> <span style="color: #38bdf8; font-weight: bold;">{meta_sel.get('record_historico_tmin_c', 'N/A')} °C</span><br>
            <b>• Umbral Helada Severa / Extrema:</b> {meta_sel.get('umbral_helada_severa_c')} °C / {meta_sel.get('umbral_helada_extrema_c')} °C<br>
            <b>• Corredor Vial de Acceso:</b> {eval_sel.corredor_vial}
        </div>
        """, unsafe_allow_html=True)

    with col_ins2:
        alerta_class = "alerta-roja" if "ROJA" in eval_sel.nivel_alerta else ("alerta-naranja" if "NARANJA" in eval_sel.nivel_alerta else "alerta-amarilla")
        st.markdown(f"""
        <div class="card-chiri">
            <h4 style="color: #38bdf8; margin-top: 0;">📊 Diagnóstico ISH-CHIRI: {eval_sel.ish_chiri:.1f} %</h4>
            <div class="{alerta_class}">
                <b>Nivel de Alerta:</b> {eval_sel.nivel_alerta}<br>
                <b>Directiva Pecuaria C2:</b> {eval_sel.accion_tactica_c2}
            </div>
            <div style="margin-top: 10px; font-size: 13px; color: #cbd5e1;">
                <b>• Censo de Camélidos:</b> {eval_sel.censo_alpacas:,} alpacas / {meta_sel.get('censo_ovinos', 0):,} ovinos.<br>
                <b>• Población Humana Vulnerable:</b> {eval_sel.poblacion_vulnerable:,} niños y adultos mayores.<br>
                <b>• Zona Topográfica:</b> {meta_sel.get('zona_empozamiento_termico', 'Cuenca Altoandina')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB 4: FRENTE EDUCATIVO & VIAL (PREVAED / PRONIED) -----------------
with tab_educacion:
    st.subheader("🏫 Frente Educativo & Seguridad Vial: PP 0068 / PREVAED & PRONIED")
    st.caption("Protección de la infancia escolar altoandina y transitabilidad segura en calzadas gélidas")

    col_ed1, col_ed2 = st.columns(2)
    with col_ed1:
        st.markdown(f"""
        <div class="card-chiri">
            <h4 style="color: #38bdf8; margin-top: 0;">🎒 Directiva Táctica Escolar para {eval_sel.distrito}</h4>
            <div style="background: rgba(14, 165, 233, 0.15); border: 1px solid #0284c7; padding: 12px; border-radius: 8px; font-size: 13px; color: #e0f2fe;">
                <b>Resolución UGEL / PREVAED:</b><br>
                {eval_sel.directiva_educativa_prevaed}
            </div>
            <div style="margin-top: 12px; font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                <b>• Instituciones Educativas Expuestas:</b> <span style="color: #f87171; font-weight: bold;">{eval_sel.colegios_vulnerables} colegios</span> sin aislamiento térmico.<br>
                <b>• Estudiantes en Riesgo Infeccioso:</b> <span style="color: #fca5a5; font-weight: bold;">{eval_sel.escolares_en_riesgo:,} escolares</span>.<br>
                <b>• Módulos Térmicos Requeridos (PRONIED):</b> <span style="color: #38bdf8; font-weight: bold;">{eval_sel.modulos_pronied_requeridos} aulas prefabricadas</span>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_ed2:
        st.markdown(f"""
        <div class="card-chiri">
            <h4 style="color: #f59e0b; margin-top: 0;">🚗 Estado de Transitabilidad Vial (Escarcha / Hielo)</h4>
            <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #d97706; padding: 12px; border-radius: 8px; font-size: 13px; color: #fef3c7;">
                <b>Alerta de Tránsito:</b><br>
                {eval_sel.alerta_vial_escarcha}
            </div>
            <div style="margin-top: 12px; font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                <b>• Corredor Vulnerable:</b> <code>{eval_sel.corredor_vial}</code><br>
                <b>• Temperatura Actual Calzada:</b> <span style="color: #00f2fe; font-weight: bold;">{eval_sel.tmin_observada_c:.1f} °C</span><br>
                <b>• Ventana Horaria de Mayor Riesgo:</b> 04:30 a. m. a 07:45 a. m. (congelamiento de humedad superficial).
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📱 Despacho Inmediato de Alerta Telegram (Transición a Rojo)")
    st.caption("Notificación instantánea C2 generada con declaración explícita de autoría por IA (Ley Nº 31814).")

    from core.telegram_notifier import TelegramNotifier
    notifier_chiri = TelegramNotifier()
    sensacion_val = getattr(eval_sel, "sensacion_termica_viento_c", eval_sel.tmin_observada_c - (eval_sel.viento_kmh * 0.15))
    alpacas_val = getattr(eval_sel, "alpacas_expuestas", getattr(eval_sel, "censo_alpacas", 0))
    dict_eval_sel = {
        "ubigeo": eval_sel.ubigeo,
        "distrito": eval_sel.distrito,
        "departamento": eval_sel.departamento,
        "ish_chiri": eval_sel.ish_chiri,
        "tmin_observada_c": eval_sel.tmin_observada_c,
        "sensacion_termica_viento_c": sensacion_val,
        "alpacas_expuestas": alpacas_val,
        "colegios_vulnerables": getattr(eval_sel, "colegios_vulnerables", 0),
        "directiva_escolar_prevaed": getattr(eval_sel, "directiva_educativa_prevaed", ""),
        "alerta_seguridad_vial": getattr(eval_sel, "alerta_vial_escarcha", ""),
        "nivel_alerta": eval_sel.nivel_alerta
    }
    msg_telegram = notifier_chiri.construir_mensaje_chiri(dict_eval_sel)

    col_t1, col_t2 = st.columns([3, 1.2])
    with col_t1:
        st.code(msg_telegram, language="markdown")
    with col_t2:
        if st.button("🚀 Enviar Alerta Telegram", type="primary", use_container_width=True):
            res_envio = notifier_chiri.enviar_mensaje_telegram(msg_telegram)
            st.success(f"Estado: {res_envio['estado']}")
            st.caption(f"Modo: {res_envio['modo']}")
            st.info("🤖 Autoría: Elaborado por Inteligencia Artificial (Ley Nº 31814)")

# ----------------- TAB 5: DOCTRINA & MARCO LEGAL -----------------
with tab_doctrina:
    st.subheader("⚖️ Marco Legal e Institucional: Plan Multisectorial ante Heladas y Friaje (PMHF)")
    st.markdown("""
    #### 1. Marco Normativo Vinculante
    * **Plan Multisectorial ante Heladas y Friaje (Decreto Supremo vigente):** Instrumento oficial del Estado Peruano que prioriza las intervenciones intersectoriales (Vivienda, Midagri, Minsa, Minedu) en distritos sobre los 3,500 m s.n.m.
    * **Ley Nº 29664 (SINAGERD):** Obligatoriedad de la gestión prospectiva y reactiva del riesgo por bajas temperaturas.
    * **Ley Nº 31814 (Inteligencia Artificial Soberana):** Todos los cálculos del `ISH-CHIRI` y clasificaciones de alerta mantienen supervisión y firma humana exclusiva de los directores de INDECI y alcaldes distritales (*Human-in-the-Loop*).

    #### 2. Segregación Doctrinal Estricta
    * **AMARU-FEN (Mando Rojo):** Supervisa el peligro hidroclimático de la fase cálida (**El Niño**, ondas Kelvin cálidas, lluvias torrenciales y huaicos en quebradas mediante el **`IPH-FEN`**).
    * **AMARU-CHIRI (Mando Azul):** Supervisa el peligro crioclimático de la fase fría (**La Niña**, heladas extremas y mortandad pecuaria mediante el **`ISH-CHIRI`**).
    """)
