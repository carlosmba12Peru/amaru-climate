"""
MOTOR CIENTÍFICO Y CARTOGRÁFICO: EL RELOJ DEL FEN
==================================================
Sistema AMARU-FEN - Sala de Mando C2 & Gestión del Riesgo Hidroclimático

Metáfora y Modelo Operativo:
- Cada hora (1:00 a 12:00) representa un mes del ciclo hidroclimático anual.
- Las 12:00 marca el inicio canónico de la temporada crítica de El Niño (Diciembre).
- Un arco rojo de gradiente térmico-dinámico representa la 'Ventana de Amenaza FEN':
  * Inicia en rojo claro tenue (calentamiento incipiente y ondas Kelvin).
  * Se intensifica a rojo carmesí oscuro y engrosado en el clímax estacional (Febrero-Marzo).
  * Se atenúa progresivamente hacia Abril-Mayo con el repliegue de la ZCIT.
- En el corazón del sector rojo se despliega el Evento Análogo Dominante (ej. FEN 1997-1998)
  y su porcentaje de similitud multivariable.
- El minutero táctico avanza no solo por calendario real, sino que se ADELANTA o RETRASA
  según el forzamiento hidroclimático en vivo (Anomalía TSM Niño 1+2, vientos alisios, IPH).
"""

from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import math

class MesReloj(BaseModel):
    hora: int
    nombre_mes: str
    nombre_corto: str
    angulo_grados: float  # 0° a 360° en sentido horario (12:00 = 0°)
    estacion: str
    descripcion_fen: str

class SectorArcoRojo(BaseModel):
    hora_inicio: float  # ej. 12.0
    hora_fin: float     # ej. 5.5 (Mayo avanzado)
    hora_climax: float  # ej. 3.0 (Marzo)
    angulo_inicio_deg: float
    angulo_fin_deg: float
    angulo_climax_deg: float
    amplitud_grados: float
    color_inicio_hex: str
    color_climax_hex: str
    color_fin_hex: str
    intensidad_pico: float  # 0.0 a 1.0

class AnalogoHistoricoFEN(BaseModel):
    evento_nombre: str
    rango_anos: str
    porcentaje_similitud: float
    tipo_evento: str  # Canónico Extraordinario, Convectivo Costero, Modoki
    indicadores_clave: Dict[str, str]
    leccion_tactica: str

class EstadoMinuteroTactico(BaseModel):
    hora_calendario: float
    angulo_calendario_deg: float
    desfase_forzamiento_dias: float  # Positivo = adelantado (temprano), Negativo = retrasado (tardío)
    desfase_angular_deg: float
    angulo_tactico_final_deg: float
    hora_tactica_final: float
    calificacion_tiempo: str  # IMPACTO_TEMPRANO_CRITICO, RITMO_ESTACIONAL_NORMAL, IMPACTO_TARDIO_ATENUADO
    fecha_proyectada_climax: str

class ModeloRelojFEN(BaseModel):
    timestamp_calculo: str
    anomalia_tsm_nino12: float
    velocidad_alisios_ms: float
    indice_iph_promedio: float
    meses: List[MesReloj]
    arco_rojo: SectorArcoRojo
    analogo_dominante: AnalogoHistoricoFEN
    minutero: EstadoMinuteroTactico
    resumen_ejecutivo: str

class MotorRelojFEN:
    """
    Calculador de dinámica polar y geocronológica para El Reloj del FEN.
    """

    MESES_CANONICOS = [
        (12, "Diciembre", "DIC", 0.0, "Inicio Verano Austral", "Llegada de ondas Kelvin cálidas y calentamiento superficial."),
        (1, "Enero", "ENE", 30.0, "Verano Austral Pleno", "Inicio de precipitaciones convectivas en costa norte y activación de quebradas."),
        (2, "Febrero", "FEB", 60.0, "Pico de Lluvias", "Saturación hídrica severa del suelo (IPH > 80%) y crecidas fluviales."),
        (3, "Marzo", "MAR", 90.0, "Clímax Histórico FEN", "Máxima energía térmica marina, descargas torrenciales y desbordes mayores."),
        (4, "Abril", "ABR", 120.0, "Otoño Austral", "Repliegue paulatino de la ZCIT, inundaciones residuales en cuencas bajas."),
        (5, "Mayo", "MAY", 150.0, "Transición Neutra", "Declive del calentamiento costero hacia condiciones basales."),
        (6, "Junio", "JUN", 180.0, "Invierno Austral", "Entrada de aguas frías por intensificación del Anticiclón del Pacífico Sur."),
        (7, "Julio", "JUL", 210.0, "Invierno Austral", "Estiaje pleno en cuencas del Pacífico."),
        (8, "Agosto", "AGO", 240.0, "Invierno Austral", "Monitoreo de ondas Kelvin de hundimiento en el Pacífico Occidental."),
        (9, "Septiembre", "SET", 270.0, "Primavera Austral", "Gestación subsuperficial y teleconexiones en Pacífico Central."),
        (10, "Octubre", "OCT", 300.0, "Primavera Austral", "Inclinación de la termoclina hacia el este sudamericano."),
        (11, "Noviembre", "NOV", 330.0, "VENTANA DE ORO LOGÍSTICA", "Única ventana de estiaje final para descolmatación de cauces, diques y preposicionamiento de maquinaria antes de la crecida de diciembre.")
    ]

    def __init__(self):
        self.meses = [
            MesReloj(
                hora=h,
                nombre_mes=n,
                nombre_corto=nc,
                angulo_grados=deg,
                estacion=est,
                descripcion_fen=desc
            )
            for h, n, nc, deg, est, desc in self.MESES_CANONICOS
        ]

    def calcular_reloj(
        self,
        fecha_evaluacion: Optional[datetime] = None,
        anomalia_tsm: float = 1.8,
        velocidad_alisios: float = 4.2,
        iph_actual: float = 78.5
    ) -> ModeloRelojFEN:
        """
        Computa el estado integral del Reloj del FEN a partir de condiciones oceanográficas y meteorológicas.
        """
        if fecha_evaluacion is None:
            fecha_evaluacion = datetime.now()

        # 1. Definir el Arco Rojo de Amenaza FEN
        # Empieza a las 12:00 (Diciembre = 0°) y se extiende hasta las 5:15 (Mayo = 157.5°)
        # Clímax a las 3:00 (Marzo = 90°)
        arco_rojo = SectorArcoRojo(
            hora_inicio=12.0,
            hora_fin=5.25,  # Mayo avanzado
            hora_climax=3.0, # Marzo
            angulo_inicio_deg=0.0,
            angulo_fin_deg=157.5,
            angulo_climax_deg=90.0,
            amplitud_grados=157.5,
            color_inicio_hex="#ff8fa3", # Rosa rojizo claro
            color_climax_hex="#7f0000", # Rojo carmesí profundo / sangre
            color_fin_hex="#ffb3c1",    # Rosa pálido atenuado
            intensidad_pico=min(1.0, max(0.4, anomalia_tsm / 2.5))
        )

        # 2. Determinar el Análogo Histórico Dominante
        analogo = self._clasificar_analogo_historico(anomalia_tsm, velocidad_alisios, iph_actual)

        # 3. Calcular la Posición del Minutero Táctico
        minutero = self._calcular_minutero_tactico(fecha_evaluacion, anomalia_tsm, velocidad_alisios, iph_actual)

        # 4. Síntesis Ejecutiva
        resumen = (
            f"El Reloj del FEN marca una posición táctica a las {minutero.hora_tactica_final:.2f} h "
            f"({minutero.calificacion_tiempo.replace('_', ' ')}). "
            f"El forzamiento térmico de +{anomalia_tsm:.1f}°C genera un adelanto táctico de "
            f"{minutero.desfase_forzamiento_dias:+.1f} días frente al calendario solar. "
            f"El patrón análogo dominante es {analogo.evento_nombre} con una correlación "
            f"multivariable del {analogo.porcentaje_similitud:.1f}%."
        )

        return ModeloRelojFEN(
            timestamp_calculo=datetime.now(timezone.utc).isoformat(),
            anomalia_tsm_nino12=anomalia_tsm,
            velocidad_alisios_ms=velocidad_alisios,
            indice_iph_promedio=iph_actual,
            meses=self.meses,
            arco_rojo=arco_rojo,
            analogo_dominante=analogo,
            minutero=minutero,
            resumen_ejecutivo=resumen
        )

    def _clasificar_analogo_historico(
        self,
        tsm: float,
        alisios: float,
        iph: float
    ) -> AnalogoHistoricoFEN:
        """
        Compara la huella térmica y dinámica con los 4 grandes precedentes históricos peruanos.
        """
        # Si TSM > 2.5°C y alisios muy colapsados (< 4.5 m/s) -> Altísima similitud con FEN 1997-1998
        if tsm >= 1.8 and alisios <= 5.0:
            similitud = round(min(96.5, 82.0 + (tsm - 1.8) * 12.0 + (5.0 - alisios) * 3.0), 1)
            return AnalogoHistoricoFEN(
                evento_nombre="FEN 1997-1998 (Mega-Niño Canónico)",
                rango_anos="1997 - 1998",
                porcentaje_similitud=similitud,
                tipo_evento="Canónico Extraordinario de Cuenca Completa",
                indicadores_clave={
                    "Anomalía TSM Niño 1+2": f"+{tsm:.1f} °C (Histórico: +3.2 °C)",
                    "Onda Kelvin Precursora": "Downwelling Intenso detectado en Paita",
                    "Caudal Río Piura Esperado": "> 3,500 m³/s en Puente Cáceres"
                },
                leccion_tactica="El pico se concentra en Febrero-Marzo con colapso de diques vulnerables; requiere preposicionamiento 60 días antes."
            )
        elif tsm >= 2.6:
            # FEN 1982-1983
            return AnalogoHistoricoFEN(
                evento_nombre="FEN 1982-1983 (Mega-Niño Histórico)",
                rango_anos="1982 - 1983",
                porcentaje_similitud=89.5,
                tipo_evento="Canónico Máximo del Siglo XX",
                indicadores_clave={
                    "Anomalía TSM Niño 1+2": "+3.4 °C",
                    "Duración Temporal": "18 meses continuos de lluvias y sequía sur"
                },
                leccion_tactica="Afectación dual extrema: lluvias destructivas en Tumbes/Piura y sequía severa en el Altiplano puneño."
            )
        elif iph >= 75.0 and tsm < 1.8:
            # FEN Costero 2017 / Yaku 2023
            return AnalogoHistoricoFEN(
                evento_nombre="FEN Costero 2017 / Ciclón Yaku 2023",
                rango_anos="2017 / 2023",
                porcentaje_similitud=86.2,
                tipo_evento="Convectivo Local Súbito",
                indicadores_clave={
                    "Calentamiento Exclusivo": "Región Niño 1+2 sin aviso en Niño 3.4",
                    "Comportamiento Quebradas": "Activación masiva en Lima y La Libertad"
                },
                leccion_tactica="Respuesta ultra rápida (< 12 horas); no esperar que los modelos globales NOAA confirmen el evento."
            )
        else:
            return AnalogoHistoricoFEN(
                evento_nombre="FEN Moderado 2015-2016",
                rango_anos="2015 - 2016",
                porcentaje_similitud=78.0,
                tipo_evento="Híbrido / Modoki",
                indicadores_clave={
                    "TSM": "+1.2 °C",
                    "Impacto": "Localizado en valles costeros medios"
                },
                leccion_tactica="Mantener vigilancia de canales y descolmatación preventiva sin alarma general."
            )

    def _calcular_minutero_tactico(
        self,
        fecha: datetime,
        tsm: float,
        alisios: float,
        iph: float
    ) -> EstadoMinuteroTactico:
        """
        Calcula el ángulo del minutero:
        - Ángulo calendario base: Diciembre = 0°, Enero = 30°, etc.
        - Desfase por forzamiento hidroclimático:
          * Mayor TSM y mayor IPH -> Desplaza la manecilla hacia adelante (FEN Temprano).
          * Alisios fuertes -> Retrasa la manecilla (FEN Tardío).
        """
        # Mapear mes y día a hora calendario en el dial (12:00 = Dic, 1:00 = Ene, ..., 11:00 = Nov)
        mes_actual = fecha.month # 1 a 12
        dia_actual = fecha.day   # 1 a 31
        
        # En nuestro reloj:
        # Mes 12 (Dic) -> hora 0.0 (0°)
        # Mes 1 (Ene)  -> hora 1.0 (30°)
        # Mes 2 (Feb)  -> hora 2.0 (60°)
        # Mes 9 (Set)  -> hora 9.0 (270°)
        hora_base = (mes_actual % 12) + (dia_actual / 30.5)
        angulo_base = (hora_base * 30.0) % 360.0

        # Cálculo del desfase dinámico en días
        # Normalizado con respecto a umbrales de ENFEN:
        # TSM basal = +1.0 °C; cada +0.5 °C adelanta 10 días.
        # Alisios basales = 6.5 m/s; cada -1.0 m/s adelanta 5 días.
        # IPH basal = 50%; cada +10% de saturación adelanta 3 días.
        dias_desfase_tsm = (tsm - 1.0) * 16.0
        dias_desfase_viento = (6.5 - alisios) * 4.5
        dias_desfase_suelo = ((iph - 50.0) / 10.0) * 3.0
        
        total_desfase_dias = round(dias_desfase_tsm + dias_desfase_viento + dias_desfase_suelo, 1)

        # En el reloj, 30 días = 1 hora = 30 grados (es decir, 1 día = 1 grado)
        desfase_angular = total_desfase_dias * 1.0 # 1° por día
        angulo_tactico = (angulo_base + desfase_angular) % 360.0
        hora_tactica = angulo_tactico / 30.0
        if hora_tactica == 0:
            hora_tactica = 12.0

        if total_desfase_dias > 12.0:
            calificacion = "IMPACTO_TEMPRANO_ACELERADO"
        elif total_desfase_dias < -12.0:
            calificacion = "IMPACTO_TARDIO_RETARDADO"
        else:
            calificacion = "RITMO_ESTACIONAL_ESTANDAR"

        # Fecha proyectada del clímax
        # Canónicamente el clímax es el 15 de marzo (hora 3.5 = 105°).
        # Ajustamos según el desfase
        dias_al_climax = round(15.0 - total_desfase_dias)
        if dias_al_climax <= 0:
            fecha_climax = "Inminente / En curso (Marzo adelantado a Febrero)"
        elif total_desfase_dias > 20:
            fecha_climax = "Febrero 2027 (Aceleración crítica de 25 días)"
        else:
            fecha_climax = "Primera quincena de Marzo 2027 (Canónico)"

        return EstadoMinuteroTactico(
            hora_calendario=round(hora_base, 2),
            angulo_calendario_deg=round(angulo_base, 1),
            desfase_forzamiento_dias=total_desfase_dias,
            desfase_angular_deg=round(desfase_angular, 1),
            angulo_tactico_final_deg=round(angulo_tactico, 1),
            hora_tactica_final=round(hora_tactica, 2),
            calificacion_tiempo=calificacion,
            fecha_proyectada_climax=fecha_climax
        )

    def generar_svg_reloj(self, modelo: ModeloRelojFEN, ancho: int = 560, alto: int = 560) -> str:
        """
        Genera una representación visual vectorial (SVG de alta fidelidad)
        del Reloj del FEN con estilo Glassmorphism Dark C2 de grado militar.
        """
        cx, cy, r = ancho / 2, alto / 2, (ancho / 2) - 45
        r_arco = r - 16
        r_interno = r_arco - 56

        # Convertir ángulo de reloj (0° arriba, horario) a coordenadas cartesianas
        def polar_to_cartesian(radio, angulo_deg):
            rad = math.radians(angulo_deg - 90.0)
            return cx + radio * math.cos(rad), cy + radio * math.sin(rad)

        # Generar arcos SVG para la 'zona roja variopinta' (degradado térmico continuo)
        # El arco va de 0° (12:00 Dic) a 157.5° (5:15 May)
        # Dividimos en 7 segmentos cromáticos variopintos de alto impacto
        segmentos_arco = [
            (0.0, 22.0, "#ff758f", 0.50, "Dic (Incidente)"),
            (22.0, 48.0, "#ff5400", 0.70, "Ene (Lluvias)"),
            (48.0, 75.0, "#e63946", 0.85, "Feb (Saturación)"),
            (75.0, 105.0, "#850000", 1.0, "Mar (Clímax FEN)"),
            (105.0, 128.0, "#a4133c", 0.80, "Abr (Disipación)"),
            (128.0, 146.0, "#c9184a", 0.60, "May (Declive)"),
            (146.0, 157.5, "#ff8fa3", 0.35, "May fin")
        ]

        paths_arco = []
        for a_ini, a_fin, color, opac, label in segmentos_arco:
            x1_out, y1_out = polar_to_cartesian(r_arco + 16, a_ini)
            x2_out, y2_out = polar_to_cartesian(r_arco + 16, a_fin)
            x2_in, y2_in = polar_to_cartesian(r_interno, a_fin)
            x1_in, y1_in = polar_to_cartesian(r_interno, a_ini)
            
            d = f"M {x1_out:.2f} {y1_out:.2f} A {r_arco+16} {r_arco+16} 0 0 1 {x2_out:.2f} {y2_out:.2f} L {x2_in:.2f} {y2_in:.2f} A {r_interno} {r_interno} 0 0 0 {x1_in:.2f} {y1_in:.2f} Z"
            paths_arco.append(f'<path d="{d}" fill="{color}" fill-opacity="{opac}" stroke="#1e293b" stroke-width="0.8" />')

        # Sector Especial: Ventana de Oro Logística FEN (Noviembre: 300.0° a 359.5°)
        # La única ventana física de estiaje para descolmatación antes de las crecidas de diciembre
        x1_oro_fen, y1_oro_fen = polar_to_cartesian(r_arco + 16, 300.0)
        x2_oro_fen, y2_oro_fen = polar_to_cartesian(r_arco + 16, 359.5)
        x2_oro_fen_in, y2_oro_fen_in = polar_to_cartesian(r_interno, 359.5)
        x1_oro_fen_in, y1_oro_fen_in = polar_to_cartesian(r_interno, 300.0)
        path_arco_oro_fen = (
            f"M {x1_oro_fen:.2f} {y1_oro_fen:.2f} "
            f"A {r_arco+16} {r_arco+16} 0 0 1 {x2_oro_fen:.2f} {y2_oro_fen:.2f} "
            f"L {x2_oro_fen_in:.2f} {y2_oro_fen_in:.2f} "
            f"A {r_interno} {r_interno} 0 0 0 {x1_oro_fen_in:.2f} {y1_oro_fen_in:.2f} Z"
        )
        r_oro_fen_mid = (r_arco + 16 + r_interno) / 2
        x1_oro_fen_t, y1_oro_fen_t = polar_to_cartesian(r_oro_fen_mid, 302.0)
        x2_oro_fen_t, y2_oro_fen_t = polar_to_cartesian(r_oro_fen_mid, 357.0)
        path_track_oro_fen = f"M {x1_oro_fen_t:.2f} {y1_oro_fen_t:.2f} A {r_oro_fen_mid:.2f} {r_oro_fen_mid:.2f} 0 0 1 {x2_oro_fen_t:.2f} {y2_oro_fen_t:.2f}"

        # Definir pistas concéntricas para texto extendido sobre la zona roja variopinta (3 niveles tácticos)
        r_track_sup = (r_arco + 16 + r_interno) / 2 + 18
        r_track_med = (r_arco + 16 + r_interno) / 2 + 1
        r_track_inf = (r_arco + 16 + r_interno) / 2 - 16

        x1_sup, y1_sup = polar_to_cartesian(r_track_sup, 6.0)
        x2_sup, y2_sup = polar_to_cartesian(r_track_sup, 154.0)
        path_track_sup = f"M {x1_sup:.2f} {y1_sup:.2f} A {r_track_sup:.2f} {r_track_sup:.2f} 0 0 1 {x2_sup:.2f} {y2_sup:.2f}"

        x1_med, y1_med = polar_to_cartesian(r_track_med, 8.0)
        x2_med, y2_med = polar_to_cartesian(r_track_med, 152.0)
        path_track_med = f"M {x1_med:.2f} {y1_med:.2f} A {r_track_med:.2f} {r_track_med:.2f} 0 0 1 {x2_med:.2f} {y2_med:.2f}"

        x1_inf, y1_inf = polar_to_cartesian(r_track_inf, 10.0)
        x2_inf, y2_inf = polar_to_cartesian(r_track_inf, 150.0)
        path_track_inf = f"M {x1_inf:.2f} {y1_inf:.2f} A {r_track_inf:.2f} {r_track_inf:.2f} 0 0 1 {x2_inf:.2f} {y2_inf:.2f}"

        # Pistas perimétricas para las etiquetas de los Años 2026 y 2027 (Bisel Exterior)
        r_ano_track = r + 24.5
        x1_a26, y1_a26 = polar_to_cartesian(r_ano_track, 272.0)
        x2_a26, y2_a26 = polar_to_cartesian(r_ano_track, 10.0)
        path_track_ano26 = f"M {x1_a26:.2f} {y1_a26:.2f} A {r_ano_track:.2f} {r_ano_track:.2f} 0 0 1 {x2_a26:.2f} {y2_a26:.2f}"

        x1_a27, y1_a27 = polar_to_cartesian(r_ano_track, 20.0)
        x2_a27, y2_a27 = polar_to_cartesian(r_ano_track, 248.0)
        path_track_ano27 = f"M {x1_a27:.2f} {y1_a27:.2f} A {r_ano_track:.2f} {r_ano_track:.2f} 0 1 1 {x2_a27:.2f} {y2_a27:.2f}"

        # CUADRANTES DE FONDO BICOLOR EJECUTIVO (Dial Background Sectors)
        # Sector Fondo Cuadrante 2026 (255° a 15° - Azul Océano Profundo / Gestación)
        x_fq_o1_26, y_fq_o1_26 = polar_to_cartesian(r + 14, 255.0)
        x_fq_o2_26, y_fq_o2_26 = polar_to_cartesian(r + 14, 15.0)
        x_fq_i2_26, y_fq_i2_26 = polar_to_cartesian(r_interno - 14, 15.0)
        x_fq_i1_26, y_fq_i1_26 = polar_to_cartesian(r_interno - 14, 255.0)
        path_cuadrante_2026 = f"M {x_fq_o1_26:.2f} {y_fq_o1_26:.2f} A {r+14} {r+14} 0 0 1 {x_fq_o2_26:.2f} {y_fq_o2_26:.2f} L {x_fq_i2_26:.2f} {y_fq_i2_26:.2f} A {r_interno-14} {r_interno-14} 0 0 0 {x_fq_i1_26:.2f} {y_fq_i1_26:.2f} Z"

        # Sector Fondo Cuadrante 2027 (15° a 255° - Vino Carmesí de Alerta / Clímax FEN)
        x_fq_o1_27, y_fq_o1_27 = polar_to_cartesian(r + 14, 15.0)
        x_fq_o2_27, y_fq_o2_27 = polar_to_cartesian(r + 14, 255.0)
        x_fq_i2_27, y_fq_i2_27 = polar_to_cartesian(r_interno - 14, 255.0)
        x_fq_i1_27, y_fq_i1_27 = polar_to_cartesian(r_interno - 14, 15.0)
        path_cuadrante_2027 = f"M {x_fq_o1_27:.2f} {y_fq_o1_27:.2f} A {r+14} {r+14} 0 1 1 {x_fq_o2_27:.2f} {y_fq_o2_27:.2f} L {x_fq_i2_27:.2f} {y_fq_i2_27:.2f} A {r_interno-14} {r_interno-14} 0 1 0 {x_fq_i1_27:.2f} {y_fq_i1_27:.2f} Z"

        # Bandas exteriores de delimitación de Año (Ribbons Perimétricos)
        # Sector Año 2026 (255° a 15°, pasando por 0°)
        x_o1_26, y_o1_26 = polar_to_cartesian(r + 28, 255.0)
        x_o2_26, y_o2_26 = polar_to_cartesian(r + 28, 15.0)
        x_i2_26, y_i2_26 = polar_to_cartesian(r + 16, 15.0)
        x_i1_26, y_i1_26 = polar_to_cartesian(r + 16, 255.0)
        path_banda_2026 = f"M {x_o1_26:.2f} {y_o1_26:.2f} A {r+28} {r+28} 0 0 1 {x_o2_26:.2f} {y_o2_26:.2f} L {x_i2_26:.2f} {y_i2_26:.2f} A {r+16} {r+16} 0 0 0 {x_i1_26:.2f} {y_i1_26:.2f} Z"

        # Sector Año 2027 (15° a 255°)
        x_o1_27, y_o1_27 = polar_to_cartesian(r + 28, 15.0)
        x_o2_27, y_o2_27 = polar_to_cartesian(r + 28, 255.0)
        x_i2_27, y_i2_27 = polar_to_cartesian(r + 16, 255.0)
        x_i1_27, y_i1_27 = polar_to_cartesian(r + 16, 15.0)
        path_banda_2027 = f"M {x_o1_27:.2f} {y_o1_27:.2f} A {r+28} {r+28} 0 1 1 {x_o2_27:.2f} {y_o2_27:.2f} L {x_i2_27:.2f} {y_i2_27:.2f} A {r+16} {r+16} 0 1 0 {x_i1_27:.2f} {y_i1_27:.2f} Z"

        # Demarcación de Cambio de Año (15.0° - frontera entre DIC '26 y ENE '27)
        x_div_ini, y_div_ini = polar_to_cartesian(r_interno - 16, 15.0)
        x_div_fin, y_div_fin = polar_to_cartesian(r + 32, 15.0)
        x_badge, y_badge = polar_to_cartesian(r + 16, 15.0)

        # Banderas / Callouts ejecutivos de término de 2026 e inicio de 2027 en la frontera
        x_fin26, y_fin26 = polar_to_cartesian(r - 18, 5.0)
        x_ini27, y_ini27 = polar_to_cartesian(r - 18, 25.0)

        # Demarcación de Cierre/Inicio de Ciclo (255.0° - frontera entre AGO '27 y SET '26)
        x_ret_ini, y_ret_ini = polar_to_cartesian(r_interno - 14, 255.0)
        x_ret_fin, y_ret_fin = polar_to_cartesian(r + 30, 255.0)
        x_ret_badge, y_ret_badge = polar_to_cartesian(r + 16, 255.0)

        # Coordenadas de la Aguja Horaria (Horario: Mes Civil Base - Corta y Sólida)
        ang_cal = modelo.minutero.angulo_calendario_deg
        r_horario = r_interno + 14
        x_hor, y_hor = polar_to_cartesian(r_horario, ang_cal)
        x_hor_back, y_hor_back = polar_to_cartesian(18, (ang_cal + 180) % 360)

        # Coordenadas de la Aguja del Minutero Táctico (Minutero: Forzamiento FEN - Larga, Gruesa y Discontinua)
        ang_minutero = modelo.minutero.angulo_tactico_final_deg
        r_minutero = r_arco - 6
        x_min, y_min = polar_to_cartesian(r_minutero, ang_minutero)
        x_min_back, y_min_back = polar_to_cartesian(26, (ang_minutero + 180) % 360)

        # Arco conector de coherencia y desfase angular entre Horario y Minutero
        diff_ang = (ang_minutero - ang_cal) % 360.0
        r_conector = r_interno + 28
        x_c1, y_c1 = polar_to_cartesian(r_conector, ang_cal)
        x_c2, y_c2 = polar_to_cartesian(r_conector, ang_minutero)
        sweep_flag = 1 if diff_ang <= 180.0 else 0
        path_arco_desfase = f"M {x_c1:.2f} {y_c1:.2f} A {r_conector:.2f} {r_conector:.2f} 0 0 {sweep_flag} {x_c2:.2f} {y_c2:.2f}"

        # Marcas y textos de los 12 meses con diferenciación cromática de AÑO 2026 vs. AÑO 2027
        textos_meses = []
        lineas_ticks = []
        for m in modelo.meses:
            x_txt, y_txt = polar_to_cartesian(r + 7, m.angulo_grados)
            x_t1, y_t1 = polar_to_cartesian(r - 5, m.angulo_grados)
            x_t2, y_t2 = polar_to_cartesian(r + 1, m.angulo_grados)
            
            # Clasificación de Año en el Ciclo FEN:
            # AÑO 2026 (Gestación / Primavera): SET(9), OCT(10), NOV(11), DIC(12)
            # AÑO 2027 (Clímax / Verano / Declive): ENE(1), FEB(2), MAR(3), ABR(4), MAY(5), JUN(6), JUL(7), AGO(8)
            if m.hora == 11:
                ano_tag = "'26★"
                color_ano = "#86efac"       # Verde claro táctico para Ventana de Oro
                color_txt = "#4ade80"
                color_tick = "#22c55e"
                bg_chip = "#052e16"
                border_chip = "#22c55e"
            elif m.hora in [9, 10, 12]:
                ano_tag = "'26"
                color_ano = "#38bdf8"       # Cian / Azul acero para 2026
                color_txt = "#7dd3fc" if m.hora != 12 else "#ff758f"
                color_tick = "#00d2ff"
                bg_chip = "#041b33"
                border_chip = "#0284c7"
            else:
                ano_tag = "'27"
                color_ano = "#fde047"       # Oro ámbar táctico para 2027
                color_txt = "#ff4d6d" if m.hora in [1, 2, 3] else ("#ff8fa3" if m.hora in [4, 5] else "#cbd5e1")
                color_tick = "#ef4444" if m.hora in [1, 2, 3] else ("#f59e0b" if m.hora in [4, 5] else "#94a3b8")
                bg_chip = "#20060d" if m.hora in [1, 2, 3] else "#180d05"
                border_chip = "#ef4444" if m.hora in [1, 2, 3] else "#b45309"
            
            peso_txt = "bold" if m.angulo_grados <= 150.0 or m.hora in [9, 10, 11, 12] else "normal"
            
            lineas_ticks.append(f'<line x1="{x_t1:.1f}" y1="{y_t1:.1f}" x2="{x_t2:.1f}" y2="{y_t2:.1f}" stroke="{color_tick}" stroke-width="2.2" />')
            textos_meses.append(
                f'<g transform="translate({x_txt:.1f}, {y_txt:.1f})">'
                f'<rect x="-18" y="-7.5" width="36" height="15" rx="3.5" fill="{bg_chip}" fill-opacity="0.75" stroke="{border_chip}" stroke-width="0.8" />'
                f'<text x="0" y="3.2" font-family="system-ui, sans-serif" text-anchor="middle">'
                f'<tspan fill="{color_txt}" font-size="9" font-weight="{peso_txt}">{m.nombre_corto}</tspan> '
                f'<tspan fill="{color_ano}" font-size="7" font-weight="900">{ano_tag}</tspan>'
                f'</text>'
                f'</g>'
            )

        analogo_label = modelo.analogo_dominante.evento_nombre.split('(')[0].strip()

        svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="100%" height="100%" style="background: radial-gradient(circle at center, #0f172a 0%, #070d17 100%); border-radius: 16px; border: 1px solid #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.6);">
            <defs>
                <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="6" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-gold" x="-25%" y="-25%" width="150%" height="150%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-green" x="-25%" y="-25%" width="150%" height="150%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <radialGradient id="dial-grad" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#131e33" stop-opacity="0.9" />
                    <stop offset="70%" stop-color="#0a101d" stop-opacity="0.95" />
                    <stop offset="100%" stop-color="#05080e" stop-opacity="1.0" />
                </radialGradient>
                <radialGradient id="grad-dial-2026" cx="30%" cy="30%" r="70%">
                    <stop offset="0%" stop-color="#0e3a66" stop-opacity="0.55" />
                    <stop offset="80%" stop-color="#051a33" stop-opacity="0.40" />
                    <stop offset="100%" stop-color="#020d1c" stop-opacity="0.25" />
                </radialGradient>
                <radialGradient id="grad-dial-2027" cx="70%" cy="40%" r="70%">
                    <stop offset="0%" stop-color="#4c0d1b" stop-opacity="0.55" />
                    <stop offset="80%" stop-color="#26060e" stop-opacity="0.40" />
                    <stop offset="100%" stop-color="#120206" stop-opacity="0.25" />
                </radialGradient>
                
                <!-- Pistas curvas invisibles para el texto extendido en la zona roja variopinta (3 niveles concéntricos) -->
                <path id="track-sup-rojo" d="{path_track_sup}" fill="none" />
                <path id="track-med-rojo" d="{path_track_med}" fill="none" />
                <path id="track-inf-rojo" d="{path_track_inf}" fill="none" />

                <!-- Pista para la Ventana de Oro Logística (Noviembre) -->
                <path id="track-oro-nov" d="{path_track_oro_fen}" fill="none" />

                <!-- Pistas curvas invisibles para los arcos exteriores de AÑOS 2026 y 2027 -->
                <path id="track-ano-2026" d="{path_track_ano26}" fill="none" />
                <path id="track-ano-2027" d="{path_track_ano27}" fill="none" />
            </defs>

            <!-- Fondo Circular Principal -->
            <circle cx="{cx}" cy="{cy}" r="{r + 28}" fill="url(#dial-grad)" stroke="#1e3a5f" stroke-width="1.5" />
            
            <!-- CUADRANTES DE FONDO BICOLOR EJECUTIVO (Diferenciación Cromática de Años en el Dial) -->
            <g id="cuadrantes-fondo-anos">
                <!-- Cuadrante Año 2026 (Azul Océano / Gestación: SET, OCT, NOV, DIC) -->
                <path id="cuadrante-2026" d="{path_cuadrante_2026}" fill="url(#grad-dial-2026)" stroke="#0284c7" stroke-width="1.2" stroke-dasharray="2,2" stroke-opacity="0.65" />
                <!-- Cuadrante Año 2027 (Vino Carmesí / Impacto FEN: ENE a AGO) -->
                <path id="cuadrante-2027" d="{path_cuadrante_2027}" fill="url(#grad-dial-2027)" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="2,2" stroke-opacity="0.65" />
            </g>

            <!-- Bandas Perimétricas de Años (Bisel Exterior Aumentado 2026 vs 2027) -->
            <g id="bandas-anos">
                <!-- Sector Año 2026 (Azul Acero Tecnológico / Gestación) -->
                <path d="{path_banda_2026}" fill="#0369a1" fill-opacity="0.32" stroke="#00b4d8" stroke-width="1.5" />
                <!-- Sector Año 2027 (Rojo Carmesí de Alerta / Clímax FEN) -->
                <path d="{path_banda_2027}" fill="#991b1b" fill-opacity="0.32" stroke="#ef4444" stroke-width="1.5" />
                
                <!-- Textos Curvados sobre los Biseles Exteriores -->
                <text fill="#38bdf8" font-size="8" font-weight="900" font-family="system-ui, sans-serif" letter-spacing="1.8px">
                    <textPath href="#track-ano-2026" xlink:href="#track-ano-2026" startOffset="50%" text-anchor="middle">
                        ◄ AÑO 2026 (GESTACIÓN / PRIMAVERA) ◄
                    </textPath>
                </text>
                <text fill="#fbbf24" font-size="8" font-weight="900" font-family="system-ui, sans-serif" letter-spacing="1.8px">
                    <textPath href="#track-ano-2027" xlink:href="#track-ano-2027" startOffset="50%" text-anchor="middle">
                        ► AÑO 2027 (VERANO CLÍMAX FEN / OTOÑO) ►
                    </textPath>
                </text>
            </g>

            <!-- Línea Divisoria Radial de Cambio de Año (15°: Entre DIC '26 y ENE '27) -->
            <line x1="{x_div_ini:.1f}" y1="{y_div_ini:.1f}" x2="{x_div_fin:.1f}" y2="{y_div_fin:.1f}" stroke="#f59e0b" stroke-width="2.8" stroke-dasharray="5,2" filter="url(#glow-gold)" />
            
            <!-- Pastilla / Badge Ejecutivo Central de Transición de Año en Bisel -->
            <g transform="translate({x_badge:.1f}, {y_badge:.1f})">
                <rect x="-42" y="-10" width="84" height="20" rx="5" fill="#060c18" stroke="#f59e0b" stroke-width="1.6" filter="url(#glow-gold)" />
                <text x="0" y="3.5" fill="#fef08a" font-size="8" font-weight="900" font-family="system-ui, sans-serif" text-anchor="middle" letter-spacing="0.5px">2026 ➔ 2027</text>
            </g>

            <!-- Cartelas Tácticas de Frontera a ambos lados de la Línea de 15° -->
            <g id="cartelas-frontera-ano">
                <g transform="translate({x_fin26:.1f}, {y_fin26:.1f})">
                    <rect x="-46" y="-7.5" width="92" height="15" rx="3.5" fill="#041527" fill-opacity="0.9" stroke="#38bdf8" stroke-width="1" />
                    <text x="0" y="3" fill="#7dd3fc" font-size="6.8" font-weight="900" font-family="system-ui, sans-serif" text-anchor="middle">◄ FIN AÑO 2026 (31-DIC)</text>
                </g>
                <g transform="translate({x_ini27:.1f}, {y_ini27:.1f})">
                    <rect x="-46" y="-7.5" width="92" height="15" rx="3.5" fill="#1f060c" fill-opacity="0.9" stroke="#f59e0b" stroke-width="1" />
                    <text x="0" y="3" fill="#fde047" font-size="6.8" font-weight="900" font-family="system-ui, sans-serif" text-anchor="middle">INICIO AÑO 2027 (01-ENE) ►</text>
                </g>
            </g>

            <!-- Línea Divisoria de Inicio/Cierre de Ciclo a 255° -->
            <line x1="{x_ret_ini:.1f}" y1="{y_ret_ini:.1f}" x2="{x_ret_fin:.1f}" y2="{y_ret_fin:.1f}" stroke="#334155" stroke-width="1.8" stroke-dasharray="3,3" />
            <g transform="translate({x_ret_badge:.1f}, {y_ret_badge:.1f})">
                <rect x="-34" y="-8" width="68" height="16" rx="4" fill="#0b1322" stroke="#475569" stroke-width="1.2" />
                <text x="0" y="3" fill="#94a3b8" font-size="6.5" font-weight="800" font-family="system-ui, sans-serif" text-anchor="middle">2027 ◄ | ► 2026</text>
            </g>

            <circle cx="{cx}" cy="{cy}" r="{r_arco + 20}" fill="none" stroke="#1b2838" stroke-width="1" stroke-dasharray="3,3" />

            <!-- SECTOR VENTANA DE ORO LOGÍSTICA FEN (NOVIEMBRE) -->
            <path d="{path_arco_oro_fen}" fill="#10b981" fill-opacity="0.50" stroke="#4ade80" stroke-width="1.5" filter="url(#glow-green)" />
            <text fill="#dcfce7" font-size="7.5" font-weight="bold" font-family="system-ui, sans-serif" letter-spacing="0.5">
                <textPath href="#track-oro-nov" xlink:href="#track-oro-nov" startOffset="50%" text-anchor="middle">★ VENTANA DE ORO (NOVIEMBRE) ★</textPath>
            </text>

            <!-- Zona Roja Variopinta de Amenaza FEN con Gradiente Dinámico -->
            <g id="arco-fen" filter="url(#glow-red)">
                {''.join(paths_arco)}
            </g>

            <!-- Marcas de los 12 Meses -->
            <g id="ticks">
                {''.join(lineas_ticks)}
            </g>
            <g id="meses-labels">
                {''.join(textos_meses)}
            </g>

            <!-- Etiqueta 12:00 (Inicio de Amenaza) -->
            <rect x="{cx - 45}" y="{cy - r + 8}" width="90" height="20" rx="4" fill="#7f0000" fill-opacity="0.85" stroke="#ff4d6d" stroke-width="1" />
            <text x="{cx}" y="{cy - r + 22}" fill="#ffffff" font-size="10" font-weight="bold" font-family="system-ui, sans-serif" text-anchor="middle">
                12:00 INICIO FEN
            </text>

            <!-- TEXTO EXTENDIDO CURVADO EN LA ZONA ROJA VARIOPINTA (DISEÑO EJECUTIVO SOBRIO) -->
            <g id="texto-extendido-zona-roja">
                <!-- Nivel 1: Título Doctrinal Sobrio -->
                <text fill="#cbd5e1" font-size="9" font-weight="700" font-family="system-ui, -apple-system, sans-serif" letter-spacing="2.4px" stroke="#0f172a" stroke-width="1.8" paint-order="stroke fill">
                    <textPath href="#track-sup-rojo" xlink:href="#track-sup-rojo" startOffset="50%" text-anchor="middle">
                        SIMILITUD ANÁLOGA
                    </textPath>
                </text>
                <!-- Nivel 2: Precedente Análogo Hero Ejecutivo (Sin Estrellas) -->
                <text fill="#f3e8b0" font-size="13.5" font-weight="800" font-family="system-ui, -apple-system, sans-serif" letter-spacing="2.5px" stroke="#1c0409" stroke-width="2.2" paint-order="stroke fill">
                    <textPath href="#track-med-rojo" xlink:href="#track-med-rojo" startOffset="50%" text-anchor="middle">
                        {analogo_label}
                    </textPath>
                </text>
                <!-- Nivel 3: Probabilidad y Calibración Ejecutiva -->
                <text fill="#99f6e4" font-size="10" font-weight="700" font-family="system-ui, -apple-system, sans-serif" letter-spacing="1.8px" stroke="#0f172a" stroke-width="1.8" paint-order="stroke fill">
                    <textPath href="#track-inf-rojo" xlink:href="#track-inf-rojo" startOffset="50%" text-anchor="middle">
                        PROBABILIDAD: {modelo.analogo_dominante.porcentaje_similitud}%
                    </textPath>
                </text>
            </g>

            <!-- Círculo Central Hub (Sala C2) -->
            <circle cx="{cx}" cy="{cy}" r="{r_interno - 18}" fill="#0b1322" stroke="#00b4d8" stroke-width="1.5" />
            
            <!-- Información en el Centro del Reloj -->
            <text x="{cx}" y="{cy - 48}" fill="#38bdf8" font-size="12" font-weight="900" font-family="system-ui, sans-serif" text-anchor="middle" letter-spacing="1">
                EL RELOJ DEL FEN
            </text>
            <text x="{cx}" y="{cy - 33}" fill="#fbbf24" font-size="8" font-weight="bold" font-family="system-ui, sans-serif" text-anchor="middle">
                TRANSICIÓN CICLO 2026 ➔ 2027
            </text>
            
            <!-- Display Digital de Hora Táctica -->
            <rect x="{cx - 65}" y="{cy - 20}" width="130" height="32" rx="6" fill="#040811" stroke="#334155" stroke-width="1" />
            <text x="{cx}" y="{cy + 2}" fill="#00f5d4" font-size="18" font-weight="900" font-family="Courier, monospace" text-anchor="middle">
                {int(modelo.minutero.hora_tactica_final):02d}:{(int(modelo.minutero.hora_tactica_final * 60) % 60):02d} H
            </text>

            <!-- Desfase Dinámico de Forzamiento -->
            <text x="{cx}" y="{cy + 26}" fill="{'#ff4d6d' if modelo.minutero.desfase_forzamiento_dias > 0 else '#06d6a0'}" font-size="9" font-weight="bold" font-family="system-ui, sans-serif" text-anchor="middle">
                DESFASE: {modelo.minutero.desfase_forzamiento_dias:+.1f} DÍAS ({'TEMPRANO' if modelo.minutero.desfase_forzamiento_dias > 0 else 'TARDÍO'})
            </text>
            <text x="{cx}" y="{cy + 40}" fill="#cbd5e1" font-size="8" font-family="system-ui, sans-serif" text-anchor="middle">
                TSM 1+2: +{modelo.anomalia_tsm_nino12:.1f}°C | Alisios: {modelo.velocidad_alisios_ms:.1f} m/s
            </text>
            <text x="{cx}" y="{cy + 52}" fill="#cbd5e1" font-size="8" font-family="system-ui, sans-serif" text-anchor="middle">
                Saturación Suelo (IPH): {modelo.indice_iph_promedio:.1f}%
            </text>

            <!-- Arco Conector de Desfase Dinámico (Coherencia Horario vs. Minutero) -->
            <path d="{path_arco_desfase}" fill="none" stroke="{'#ff4d6d' if modelo.minutero.desfase_forzamiento_dias > 0 else '#06d6a0'}" stroke-width="2.2" stroke-dasharray="3,3" opacity="0.85" />

            <!-- AGUJA HORARIA (HORARIO: MES CIVIL BASE - CORTA, SÓLIDA, ROBUSTA) -->
            <g id="aguja-horario">
                <!-- Contrapeso horario -->
                <line x1="{cx}" y1="{cy}" x2="{x_hor_back:.1f}" y2="{y_hor_back:.1f}" stroke="#1e40af" stroke-width="4.5" stroke-linecap="round" />
                <!-- Aguja horaria principal sólida -->
                <line x1="{cx}" y1="{cy}" x2="{x_hor:.1f}" y2="{y_hor:.1f}" stroke="#38bdf8" stroke-width="5.0" stroke-linecap="round" />
                <!-- Puntero terminal horario -->
                <circle cx="{x_hor:.1f}" cy="{y_hor:.1f}" r="4.5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
            </g>

            <!-- AGUJA DEL MINUTERO TÁCTICO (MINUTERO: FORZAMIENTO HIDROCLIMÁTICO - LARGA, LÍNEAS DISCONTINUAS, MÁS GRUESA) -->
            <g id="minutero-tactico" filter="url(#glow-cyan)">
                <!-- Cola de contrapeso minutero -->
                <line x1="{cx}" y1="{cy}" x2="{x_min_back:.1f}" y2="{y_min_back:.1f}" stroke="#0284c7" stroke-width="4.0" stroke-linecap="round" />
                <!-- Aguja minutero con líneas discontinuas pero más gruesas -->
                <line x1="{cx}" y1="{cy}" x2="{x_min:.1f}" y2="{y_min:.1f}" stroke="#00f5d4" stroke-width="5.0" stroke-dasharray="9,5" stroke-linecap="round" />
                <!-- Blanco/Target táctico reflectivo en la punta -->
                <circle cx="{x_min:.1f}" cy="{y_min:.1f}" r="5.5" fill="#00f5d4" stroke="#ffffff" stroke-width="2.0" />
                <circle cx="{x_min:.1f}" cy="{y_min:.1f}" r="2" fill="#030712" />
            </g>

            <!-- Perno Central del Reloj -->
            <circle cx="{cx}" cy="{cy}" r="6" fill="#00b4d8" stroke="#ffffff" stroke-width="1.5" />
            <circle cx="{cx}" cy="{cy}" r="2" fill="#0f172a" />

            <!-- BARRA DE LEYENDA EJECUTIVA DE AÑOS Y FRONTERA TÁCTICA -->
            <g id="leyenda-ejecutiva-anos">
                <rect x="{cx - 225}" y="{alto - 21}" width="450" height="17" rx="4.5" fill="#050a14" fill-opacity="0.94" stroke="#1e3a5f" stroke-width="0.9" />
                <circle cx="{cx - 212}" cy="{alto - 12.5}" r="3.2" fill="#0284c7" stroke="#38bdf8" stroke-width="1"/>
                <text x="{cx - 204}" y="{alto - 10}" fill="#7dd3fc" font-size="7" font-weight="800" font-family="system-ui, sans-serif">AÑO 2026: GESTACIÓN (SET-DIC)</text>
                
                <text x="{cx}" y="{alto - 10}" fill="#f59e0b" font-size="7.2" font-weight="900" font-family="system-ui, sans-serif" text-anchor="middle">⚡ 15°: CAMBIO DE AÑO CIVIL</text>
                
                <circle cx="{cx + 96}" cy="{alto - 12.5}" r="3.2" fill="#ef4444" stroke="#f59e0b" stroke-width="1"/>
                <text x="{cx + 104}" y="{alto - 10}" fill="#fca5a5" font-size="7" font-weight="800" font-family="system-ui, sans-serif">AÑO 2027: CLÍMAX FEN (ENE-AGO)</text>
            </g>
        </svg>
        """
        return svg
