"""
MOTOR CIENTÍFICO Y CARTOGRÁFICO: EL RELOJ DE LA NIÑA (AMARU-CHIRI)
===================================================================
Sistema AMARU - Sala de Mando C2 & Gestión del Riesgo Crioclimático Altoandino

Metáfora y Modelo Operativo:
- Cada hora (1:00 a 12:00) representa un mes del ciclo hidroclimático y térmico anual.
- Las 12:00 marca el solsticio de verano austral (Diciembre = 0°).
- Las 6:00 marca el solsticio de invierno austral (Junio = 180°).
- Un arco glacial de gradiente azul cian y blanco hielo representa la 'Ventana de Amenaza de Heladas y Friaje':
  * Inicia a las 4:45 (Mayo = 142.5°) con las primeras heladas meteorológicas.
  * Se intensifica al azul cian eléctrico y blanco hielo en el clímax invernal (Junio-Julio / 180°-210°).
  * Se atenúa progresivamente hacia Agosto-Septiembre (240°-262.5°) con la primavera austral.
- En el corazón del sector glacial se despliega el Evento Análogo Dominante (ej. La Niña 2007-2008)
  y su porcentaje de similitud multivariable.
- El minutero táctico avanza no solo por calendario solar, sino que se ADELANTA o RETRASA
  según el forzamiento crioclimático en vivo:
  * Anomalía negativa de TSM en el Pacífico (Niño 1+2 / Niño 3.4).
  * Hiper-intensificación de vientos alisios (> 7.0 m/s).
  * Descenso de temperatura mínima nocturna promedio (Tmin) en estaciones altoandinas (Puno, Huancavelica, Arequipa).
"""

from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import math

class MesRelojNina(BaseModel):
    hora: int
    nombre_mes: str
    nombre_corto: str
    angulo_grados: float  # 0° a 360° en sentido horario (12:00 = 0° / Diciembre)
    estacion: str
    fenomenologia_chiri: str

class SectorArcoGlacial(BaseModel):
    hora_inicio: float  # ej. 4.75 (Mayo temprano)
    hora_fin: float     # ej. 8.75 (Septiembre incipiente)
    hora_climax: float  # ej. 6.75 (Fines de Junio / Julio)
    angulo_inicio_deg: float
    angulo_fin_deg: float
    angulo_climax_deg: float
    amplitud_grados: float
    color_inicio_hex: str
    color_climax_hex: str
    color_fin_hex: str
    intensidad_pico: float  # 0.0 a 1.0

class AnalogoHistoricoNina(BaseModel):
    evento_nombre: str
    rango_anos: str
    porcentaje_similitud: float
    tipo_evento: str  # Mega-Niña Clásica, Prolongada Multianual, Niña Modoki / Débil
    indicadores_clave: Dict[str, str]
    leccion_tactica: str

class EstadoMinuteroCrioclimatico(BaseModel):
    hora_calendario: float
    angulo_calendario_deg: float
    desfase_forzamiento_dias: float  # Positivo = helada adelantada/temprana, Negativo = invierno retrasado/benigno
    desfase_angular_deg: float
    angulo_tactico_final_deg: float
    hora_tactica_final: float
    calificacion_tiempo: str  # HELADA_TEMPRANA_ACELERADA, RITMO_ESTACIONAL_ESTANDAR, INVIERNO_TARDIO_BENIGNO
    fecha_proyectada_climax: str

class ModeloRelojNina(BaseModel):
    timestamp_calculo: str
    anomalia_tsm_pacifico: float
    velocidad_alisios_ms: float
    temperatura_minima_promedio_c: float
    meses: List[MesRelojNina]
    arco_glacial: SectorArcoGlacial
    analogo_dominante: AnalogoHistoricoNina
    minutero: EstadoMinuteroCrioclimatico
    resumen_ejecutivo: str

class MotorRelojNina:
    """
    Calculador de dinámica polar y crono-inteligencia crioclimática para El Reloj de La Niña (AMARU-CHIRI).
    Completamente desacoplado del motor de El Niño (core/reloj_fen.py).
    """

    MESES_CANONICOS_NINA = [
        (12, "Diciembre", "DIC", 0.0, "Verano Austral", "Aguas costeras templadas; lluvias normales o inhibidas."),
        (1, "Enero", "ENE", 30.0, "Verano Austral", "Tiempo relativamente estable en costa; lluvias en sierra oriental."),
        (2, "Febrero", "FEB", 60.0, "Verano Austral", "Descargas fluviales moderadas en vertiente atlántica."),
        (3, "Marzo", "MAR", 90.0, "Otoño Austral", "Inicio del cese de lluvias andinas y descenso gradual de humedad."),
        (4, "Abril", "ABR", 120.0, "VENTANA DE ORO LOGÍSTICA", "Única ventana física para instalar módulos térmicos PRONIED, techar cobertizos y distribuir forraje antes del congelamiento de vías."),
        (5, "Mayo", "MAY", 150.0, "Inicio Ventana Crioclimática", "Incursión de masas de aire seco polar; Tmin cae bajo 0°C en puna."),
        (6, "Junio", "JUN", 180.0, "Solsticio de Invierno Austral", "Heladas meteorológicas severas generalizadas; riesgo de nevadas."),
        (7, "Julio", "JUL", 210.0, "Clímax Glacial Histórico", "Pico gélido anual en Puno e Imata; temperaturas de hasta -25°C."),
        (8, "Agosto", "AGO", 240.0, "Invierno Austral Avanzado", "Vientos catabáticos severos; desecación de pastos y bofedales congelados."),
        (9, "Septiembre", "SET", 270.0, "Primavera Austral", "Retiro progresivo del aire polar; heladas agronómicas tardías."),
        (10, "Octubre", "OCT", 300.0, "Primavera Austral", "Transición térmica; siembras tempranas en valles interandinos."),
        (11, "Noviembre", "NOV", 330.0, "Primavera Austral", "Aumento de cobertura nubosa y humedad previa al verano.")
    ]

    def __init__(self):
        self.meses = [
            MesRelojNina(
                hora=h,
                nombre_mes=n,
                nombre_corto=nc,
                angulo_grados=deg,
                estacion=est,
                fenomenologia_chiri=desc
            )
            for h, n, nc, deg, est, desc in self.MESES_CANONICOS_NINA
        ]

    def calcular_reloj(
        self,
        fecha_evaluacion: Optional[datetime] = None,
        anomalia_tsm: float = -1.3,
        velocidad_alisios: float = 7.8,
        tmin_promedio: float = -11.5
    ) -> ModeloRelojNina:
        """
        Calcula el estado integral del Reloj de La Niña a partir de indicadores oceanográficos y térmicos altoandinos.
        """
        if fecha_evaluacion is None:
            fecha_evaluacion = datetime.now()

        # 1. Definir el Arco Glacial de Amenaza de Heladas
        # Inicia a las 4:45 (Mayo = 142.5°) y se extiende hasta las 8:45 (Septiembre = 262.5°)
        # Clímax a las 6:45 - 7:00 (Fines de Junio / Julio = 202.5° - 210.0°)
        arco_glacial = SectorArcoGlacial(
            hora_inicio=4.75,
            hora_fin=8.75,
            hora_climax=6.75,
            angulo_inicio_deg=142.5,
            angulo_fin_deg=262.5,
            angulo_climax_deg=202.5,
            amplitud_grados=120.0,
            color_inicio_hex="#38bdf8",  # Azul cielo / escarcha suave
            color_climax_hex="#00f2fe",  # Azul cian eléctrico / hielo puro
            color_fin_hex="#1e3a8a",     # Azul noche / disipación
            intensidad_pico=min(1.0, max(0.4, abs(anomalia_tsm) / 2.0))
        )

        # 2. Determinar el Análogo Histórico Dominante de La Niña
        analogo = self._clasificar_analogo_historico(anomalia_tsm, velocidad_alisios, tmin_promedio)

        # 3. Calcular la Posición del Minutero Crioclimático
        minutero = self._calcular_minutero_crioclimatico(fecha_evaluacion, anomalia_tsm, velocidad_alisios, tmin_promedio)

        # 4. Resumen Ejecutivo
        resumen = (
            f"El Reloj de La Niña (AMARU-CHIRI) marca una posición táctica a las {minutero.hora_tactica_final:.2f} h "
            f"({minutero.calificacion_tiempo.replace('_', ' ')}). "
            f"El forzamiento oceánico frío de {anomalia_tsm:+.1f}°C y vientos de {velocidad_alisios:.1f} m/s "
            f"generan un desfase de {minutero.desfase_forzamiento_dias:+.1f} días respecto al calendario solar. "
            f"El análogo histórico dominante es {analogo.evento_nombre} con una correlación del {analogo.porcentaje_similitud:.1f}%."
        )

        return ModeloRelojNina(
            timestamp_calculo=datetime.now(timezone.utc).isoformat(),
            anomalia_tsm_pacifico=anomalia_tsm,
            velocidad_alisios_ms=velocidad_alisios,
            temperatura_minima_promedio_c=tmin_promedio,
            meses=self.meses,
            arco_glacial=arco_glacial,
            analogo_dominante=analogo,
            minutero=minutero,
            resumen_ejecutivo=resumen
        )

    def _clasificar_analogo_historico(
        self,
        tsm: float,
        alisios: float,
        tmin: float
    ) -> AnalogoHistoricoNina:
        """
        Compara la huella térmica marina y de frío altoandino con los grandes precedentes de La Niña en Perú.
        """
        # Caso 1: La Niña 2007-2008 (Ola de Frío Extremo Histórico en el Altiplano)
        if tmin <= -12.0 or (tsm <= -1.4 and alisios >= 7.5):
            similitud = round(min(96.0, 84.0 + abs(tsm + 1.0) * 8.0 + max(0.0, -10.0 - tmin) * 1.5), 1)
            return AnalogoHistoricoNina(
                evento_nombre="La Niña 2007-2008 (Ola Polar Histórica)",
                rango_anos="2007 - 2008",
                porcentaje_similitud=similitud,
                tipo_evento="Crioclima Extremo de Cuenca Completa",
                indicadores_clave={
                    "Récord Tmin Mazocruz": "-28.2 °C (Julio 2008)",
                    "Anomalía TSM Pacífico": f"{tsm:+.1f} °C",
                    "Afectación Pecuaria": "> 85,000 crías de alpaca perecidas"
                },
                leccion_tactica="Pico glacial entre el 20 de junio y 25 de julio; requiere entrega de cobertizos y pacas de heno en mayo."
            )
        # Caso 2: La Niña Prolongada Multianual 2020-2023 (Triple-Dip)
        elif tsm <= -0.8 and alisios >= 7.0:
            return AnalogoHistoricoNina(
                evento_nombre="La Niña Prolongada 2020-2023 (Triple-Dip)",
                rango_anos="2020 - 2023",
                porcentaje_similitud=88.5,
                tipo_evento="Enfriamiento Multianual Persistente",
                indicadores_clave={
                    "Duración Temporal": "36 meses consecutivos de aguas frías",
                    "Estrés Hídrico": "Déficit severo en reservorios Condoroma y Pasto Grande",
                    "Impacto Agrícola": "Pérdida de pasturas naturales por congelamiento sostenido"
                },
                leccion_tactica="Monitorear el agotamiento de bofedales y estrés forrajero acumulativo tras dos inviernos seguidos."
            )
        # Caso 3: La Niña 1988-1989 (Mega-Niña Canónica del Siglo XX)
        elif tsm <= -1.8:
            return AnalogoHistoricoNina(
                evento_nombre="La Niña 1988-1989 (Mega-Niña del Siglo XX)",
                rango_anos="1988 - 1989",
                porcentaje_similitud=91.0,
                tipo_evento="Fase Fría Canónica Máxima",
                indicadores_clave={
                    "Anomalía TSM Máxima": "-2.1 °C en Niño 3.4",
                    "Inhibición Costera": "Cero precipitaciones en costa norte",
                    "Heladas Sierra Sur": "Nevadas de más de 80 cm en pasos viales"
                },
                leccion_tactica="Bloqueo total de la Carretera Interoceánica e Imata por nevadas tempranas en junio."
            )
        # Caso 4: La Niña Débil / Modoki
        else:
            return AnalogoHistoricoNina(
                evento_nombre="La Niña Débil / Transición Fría 2011-2012",
                rango_anos="2011 - 2012",
                porcentaje_similitud=76.5,
                tipo_evento="Modoki / Frío Moderado",
                indicadores_clave={
                    "Anomalía TSM": "-0.6 °C",
                    "Comportamiento": "Heladas dentro del percentil 80 histórico"
                },
                leccion_tactica="Refuerzo veterinario preventivo sin necesidad de declaratoria de emergencia de nivel 5."
            )

    def _calcular_minutero_crioclimatico(
        self,
        fecha: datetime,
        tsm: float,
        alisios: float,
        tmin: float
    ) -> EstadoMinuteroCrioclimatico:
        """
        Calcula el ángulo del minutero táctico de La Niña:
        - Ángulo calendario base: Diciembre = 0°, Enero = 30°, Junio = 180°, etc.
        - Desfase por forzamiento crioclimático:
          * Mayor enfriamiento marino (TSM negativa) y alisios fuertes -> Adelanta la llegada del frío severo.
          * Descenso térmico bajo cero en cabeceras -> Acelera el clímax glacial hacia mayo/junio.
        """
        mes_actual = fecha.month
        dia_actual = fecha.day

        hora_base = (mes_actual % 12) + (dia_actual / 30.5)
        angulo_base = (hora_base * 30.0) % 360.0

        # Ecuaciones de forzamiento dinámico de AMARU-CHIRI:
        # 1. Forzamiento Térmico Marino: Basal = -0.5 °C. Cada -0.5 °C adicional adelanta 8 días.
        dias_desfase_tsm = max(0.0, (-0.5 - tsm) * 16.0) if tsm <= -0.5 else (-(tsm + 0.5) * 8.0)
        
        # 2. Forzamiento Eólico: Basal = 6.5 m/s. Vientos alisios fuertes (> 6.5 m/s) empujan frío.
        dias_desfase_viento = (alisios - 6.5) * 4.0

        # 3. Forzamiento Térmico Terrestre: Basal = -5.0 °C en cabeceras.
        dias_desfase_tmin = max(0.0, (-5.0 - tmin) * 1.8) if tmin <= -5.0 else 0.0

        total_desfase_dias = round(dias_desfase_tsm + dias_desfase_viento + dias_desfase_tmin, 1)

        # 1 día = 1 grado sexagesimal
        desfase_angular = total_desfase_dias * 1.0
        angulo_tactico = (angulo_base + desfase_angular) % 360.0
        hora_tactica = angulo_tactico / 30.0
        if hora_tactica == 0:
            hora_tactica = 12.0

        if total_desfase_dias > 10.0:
            calificacion = "HELADA_TEMPRANA_ACELERADA"
        elif total_desfase_dias < -10.0:
            calificacion = "INVIERNO_TARDIO_BENIGNO"
        else:
            calificacion = "RITMO_ESTACIONAL_ESTANDAR"

        # Fecha proyectada del clímax glacial (Canónicamente el 10 de julio = hora 7.33 = 220°)
        dias_al_climax = round(20.0 - total_desfase_dias)
        if total_desfase_dias > 18.0:
            fecha_climax = "Fines de Junio (Helada adelantada crítica de 20 días)"
        elif total_desfase_dias > 8.0:
            fecha_climax = "Primera quincena de Julio (Canónico adelantado)"
        else:
            fecha_climax = "Segunda quincena de Julio / Inicios de Agosto"

        return EstadoMinuteroCrioclimatico(
            hora_calendario=round(hora_base, 2),
            angulo_calendario_deg=round(angulo_base, 1),
            desfase_forzamiento_dias=total_desfase_dias,
            desfase_angular_deg=round(desfase_angular, 1),
            angulo_tactico_final_deg=round(angulo_tactico, 1),
            hora_tactica_final=round(hora_tactica, 2),
            calificacion_tiempo=calificacion,
            fecha_proyectada_climax=fecha_climax
        )

    def generar_svg_reloj(self, modelo: ModeloRelojNina, ancho: int = 560, alto: int = 560) -> str:
        """
        Genera la representación visual vectorial (SVG de alta fidelidad)
        del Reloj de La Niña con estilo Glassmorphism Dark C2 y paleta glacial crioclimática.
        """
        cx, cy, r = ancho / 2, alto / 2, (ancho / 2) - 45
        r_arco = r - 16
        r_interno = r_arco - 56

        def polar_to_cartesian(radio, angulo_deg):
            rad = math.radians(angulo_deg - 90.0)
            return cx + radio * math.cos(rad), cy + radio * math.sin(rad)

        # Generar arcos SVG para la 'zona glacial' (degradado crioclimático continuo)
        # El arco va de 142.5° (Mayo incipiente) a 262.5° (Septiembre incipiente)
        segmentos_arco = [
            (142.5, 165.0, "#38bdf8", 0.45, "May (Escarcha)"),
            (165.0, 185.0, "#00d2ff", 0.70, "Jun (Solsticio)"),
            (185.0, 215.0, "#00f2fe", 1.00, "Jul (Clímax Glacial)"),
            (215.0, 240.0, "#0284c7", 0.80, "Ago (Heladas Viento)"),
            (240.0, 262.5, "#1d4ed8", 0.40, "Set (Disipación)")
        ]

        paths_arco = []
        for a_ini, a_fin, color, opac, label in segmentos_arco:
            x1_out, y1_out = polar_to_cartesian(r_arco + 16, a_ini)
            x2_out, y2_out = polar_to_cartesian(r_arco + 16, a_fin)
            x2_in, y2_in = polar_to_cartesian(r_interno, a_fin)
            x1_in, y1_in = polar_to_cartesian(r_interno, a_ini)

            d = (
                f"M {x1_out:.2f} {y1_out:.2f} "
                f"A {r_arco+16} {r_arco+16} 0 0 1 {x2_out:.2f} {y2_out:.2f} "
                f"L {x2_in:.2f} {y2_in:.2f} "
                f"A {r_interno} {r_interno} 0 0 0 {x1_in:.2f} {y1_in:.2f} Z"
            )
            paths_arco.append(
                f'<path d="{d}" fill="{color}" fill-opacity="{opac}" stroke="#0369a1" stroke-width="0.8" />'
            )

        # Sector Especial: Ventana de Oro Logística (Abril: 105.0° a 142.5°)
        # La única ventana física para aprovisionamiento antes de la llegada del frío de mayo
        x1_oro, y1_oro = polar_to_cartesian(r_arco + 16, 105.0)
        x2_oro, y2_oro = polar_to_cartesian(r_arco + 16, 142.5)
        x2_oro_in, y2_oro_in = polar_to_cartesian(r_interno, 142.5)
        x1_oro_in, y1_oro_in = polar_to_cartesian(r_interno, 105.0)
        path_arco_oro = (
            f"M {x1_oro:.2f} {y1_oro:.2f} "
            f"A {r_arco+16} {r_arco+16} 0 0 1 {x2_oro:.2f} {y2_oro:.2f} "
            f"L {x2_oro_in:.2f} {y2_oro_in:.2f} "
            f"A {r_interno} {r_interno} 0 0 0 {x1_oro_in:.2f} {y1_oro_in:.2f} Z"
        )
        r_oro_mid = (r_arco + 16 + r_interno) / 2
        x1_oro_t, y1_oro_t = polar_to_cartesian(r_oro_mid, 107.0)
        x2_oro_t, y2_oro_t = polar_to_cartesian(r_oro_mid, 140.0)
        path_track_oro = f"M {x1_oro_t:.2f} {y1_oro_t:.2f} A {r_oro_mid:.2f} {r_oro_mid:.2f} 0 0 1 {x2_oro_t:.2f} {y2_oro_t:.2f}"

        # Pistas circulares concéntricas para texto curvo en el arco glacial
        r_track_sup = (r_arco + 16 + r_interno) / 2 + 18
        r_track_med = (r_arco + 16 + r_interno) / 2 + 1
        r_track_inf = (r_arco + 16 + r_interno) / 2 - 16

        x1_sup, y1_sup = polar_to_cartesian(r_track_sup, 148.0)
        x2_sup, y2_sup = polar_to_cartesian(r_track_sup, 258.0)
        path_track_sup = f"M {x1_sup:.2f} {y1_sup:.2f} A {r_track_sup:.2f} {r_track_sup:.2f} 0 0 1 {x2_sup:.2f} {y2_sup:.2f}"

        x1_med, y1_med = polar_to_cartesian(r_track_med, 150.0)
        x2_med, y2_med = polar_to_cartesian(r_track_med, 255.0)
        path_track_med = f"M {x1_med:.2f} {y1_med:.2f} A {r_track_med:.2f} {r_track_med:.2f} 0 0 1 {x2_med:.2f} {y2_med:.2f}"

        x1_inf, y1_inf = polar_to_cartesian(r_track_inf, 152.0)
        x2_inf, y2_inf = polar_to_cartesian(r_track_inf, 252.0)
        path_track_inf = f"M {x1_inf:.2f} {y1_inf:.2f} A {r_track_inf:.2f} {r_track_inf:.2f} 0 0 1 {x2_inf:.2f} {y2_inf:.2f}"

        # Coordenadas de la Aguja Horaria (Mes Calendario Solar)
        ang_cal = modelo.minutero.angulo_calendario_deg
        r_horario = r_interno + 14
        x_hor, y_hor = polar_to_cartesian(r_horario, ang_cal)
        x_hor_back, y_hor_back = polar_to_cartesian(18, (ang_cal + 180) % 360)

        # Coordenadas del Minutero Táctico Crioclimático (Forzamiento La Niña)
        ang_minutero = modelo.minutero.angulo_tactico_final_deg
        r_minutero = r_arco - 6
        x_min, y_min = polar_to_cartesian(r_minutero, ang_minutero)
        x_min_back, y_min_back = polar_to_cartesian(26, (ang_minutero + 180) % 360)

        # Arco conector de desfase angular entre Horario y Minutero
        diff_ang = (ang_minutero - ang_cal) % 360.0
        r_conector = r_interno + 28
        x_c1, y_c1 = polar_to_cartesian(r_conector, ang_cal)
        x_c2, y_c2 = polar_to_cartesian(r_conector, ang_minutero)
        sweep_flag = 1 if diff_ang <= 180.0 else 0
        path_arco_desfase = f"M {x_c1:.2f} {y_c1:.2f} A {r_conector:.2f} {r_conector:.2f} 0 0 {sweep_flag} {x_c2:.2f} {y_c2:.2f}"

        # Marcas y textos de los 12 meses
        textos_meses = []
        for m in modelo.meses:
            x_txt, y_txt = polar_to_cartesian(r + 8, m.angulo_grados)
            x_t1, y_t1 = polar_to_cartesian(r - 5, m.angulo_grados)
            x_t2, y_t2 = polar_to_cartesian(r + 1, m.angulo_grados)

            # Abril resaltado en Amarillo táctico (Ventana de Oro Logística)
            if m.hora == 4:
                color_txt = "#facc15"
                color_tick = "#eab308"
                weight = "bold"
            # Meses de la ventana de heladas resaltados en cian/hielo
            elif m.hora in [5, 6, 7, 8]:
                color_txt = "#00f2fe" if m.hora in [6, 7] else "#38bdf8"
                color_tick = "#00f2fe"
                weight = "bold"
            else:
                color_txt = "#94a3b8"
                color_tick = "#475569"
                weight = "normal"

            label_display = f"{m.nombre_corto}★" if m.hora == 4 else m.nombre_corto
            textos_meses.append(
                f'<line x1="{x_t1:.2f}" y1="{y_t1:.2f}" x2="{x_t2:.2f}" y2="{y_t2:.2f}" stroke="{color_tick}" stroke-width="2" />'
                f'<text x="{x_txt:.2f}" y="{y_txt:.2f}" fill="{color_txt}" font-size="11" font-weight="{weight}" '
                f'font-family="system-ui, -apple-system, sans-serif" text-anchor="middle" dominant-baseline="central">{label_display}</text>'
            )

        # Construcción integral del SVG
        svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="100%" height="100%" style="background: transparent;">
            <defs>
                <!-- Filtros Glassmorphism y Glow Crioclimático -->
                <radialGradient id="gradienteFondoGlacial" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stop-color="#082f49" stop-opacity="0.85" />
                    <stop offset="60%" stop-color="#020617" stop-opacity="0.95" />
                    <stop offset="100%" stop-color="#000000" stop-opacity="0.98" />
                </radialGradient>
                <filter id="glowGlacial" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glowAmarillo" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <!-- Pistas de texto curvo -->
                <path id="trackOroAbril" d="{path_track_oro}" fill="none" />
                <path id="trackGlacialSup" d="{path_track_sup}" fill="none" />
                <path id="trackGlacialMed" d="{path_track_med}" fill="none" />
                <path id="trackGlacialInf" d="{path_track_inf}" fill="none" />
            </defs>

            <!-- Fondo Principal del Dial -->
            <circle cx="{cx}" cy="{cy}" r="{r + 32}" fill="url(#gradienteFondoGlacial)" stroke="#0369a1" stroke-width="1.5" />
            <circle cx="{cx}" cy="{cy}" r="{r + 16}" fill="none" stroke="#0ea5e9" stroke-width="0.6" stroke-dasharray="3 3" />
            <circle cx="{cx}" cy="{cy}" r="{r_interno}" fill="#020617" stroke="#1e293b" stroke-width="1" />

            <!-- SECTOR VENTANA DE ORO LOGÍSTICA (ABRIL) EN AMARILLO -->
            <path d="{path_arco_oro}" fill="#facc15" fill-opacity="0.65" stroke="#fef08a" stroke-width="1.6" filter="url(#glowAmarillo)" />
            <text fill="#020617" font-size="8.5" font-weight="900" font-family="system-ui, sans-serif" letter-spacing="0.5">
                <textPath href="#trackOroAbril" xlink:href="#trackOroAbril" startOffset="50%" text-anchor="middle">Ventana de Oro (Abril)</textPath>
            </text>

            <!-- Segmentos del Arco Glacial -->
            <g id="arcoGlacialNina">
                {''.join(paths_arco)}
            </g>

            <!-- Textos Curvos Concéntricos sobre el Arco Glacial en Color Negro -->
            <g id="textosArcoGlacial" opacity="0.98">
                <text font-family="system-ui, sans-serif" font-size="8.5" font-weight="900" fill="#000000" letter-spacing="2px">
                    <textPath href="#trackGlacialSup" xlink:href="#trackGlacialSup" startOffset="50%" text-anchor="middle">
                        VENTANA DE HELADAS SEVERAS (AMARU-CHIRI)
                    </textPath>
                </text>
                <text font-family="system-ui, sans-serif" font-size="11.5" font-weight="900" fill="#000000">
                    <textPath href="#trackGlacialMed" xlink:href="#trackGlacialMed" startOffset="50%" text-anchor="middle">
                        {modelo.analogo_dominante.evento_nombre}
                    </textPath>
                </text>
                <text font-family="system-ui, sans-serif" font-size="9" font-weight="800" fill="#000000">
                    <textPath href="#trackGlacialInf" xlink:href="#trackGlacialInf" startOffset="50%" text-anchor="middle">
                        SIMILITUD MULTIVARIABLE: {modelo.analogo_dominante.porcentaje_similitud:.1f}% | CLÍMAX: JULIO
                    </textPath>
                </text>
            </g>

            <!-- Malla y Ticks de Meses -->
            <g id="ticksMeses">
                {''.join(textos_meses)}
            </g>

            <!-- Indicador de Solsticio de Invierno (180° - 21 de Junio) -->
            <line x1="{cx}" y1="{cy + r_interno}" x2="{cx}" y2="{cy + r_arco + 16}" stroke="#00f2fe" stroke-width="2" stroke-dasharray="4 2" />
            <circle cx="{cx}" cy="{cy + r_arco + 20}" r="3" fill="#00f2fe" filter="url(#glowGlacial)" />

            <!-- Arco de Desfase Dinámico -->
            <path d="{path_arco_desfase}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="3 3" opacity="0.75" />

            <!-- Aguja Horaria (Mes Calendario Solar) -->
            <g id="agujaCalendario">
                <line x1="{x_hor_back:.2f}" y1="{y_hor_back:.2f}" x2="{x_hor:.2f}" y2="{y_hor:.2f}" stroke="#94a3b8" stroke-width="3" stroke-linecap="round" />
                <circle cx="{x_hor:.2f}" cy="{y_hor:.2f}" r="4" fill="#cbd5e1" />
            </g>

            <!-- Minutero Táctico Crioclimático (Forzamiento La Niña) -->
            <g id="minuteroTactico" filter="url(#glowGlacial)">
                <line x1="{x_min_back:.2f}" y1="{y_min_back:.2f}" x2="{x_min:.2f}" y2="{y_min:.2f}" stroke="#00f2fe" stroke-width="4" stroke-linecap="round" />
                <polygon points="{x_min:.2f},{y_min:.2f} {x_min-5:.2f},{y_min+10:.2f} {x_min+5:.2f},{y_min+10:.2f}" fill="#00f2fe" />
            </g>

            <!-- Núcleo Central C2 con Telemetría Resumida -->
            <circle cx="{cx}" cy="{cy}" r="42" fill="#020617" stroke="#0ea5e9" stroke-width="2" />
            <circle cx="{cx}" cy="{cy}" r="36" fill="#082f49" opacity="0.6" />
            <text x="{cx}" y="{cy - 12}" fill="#38bdf8" font-size="8" font-family="system-ui" text-anchor="middle" font-weight="bold">LA NIÑA C2</text>
            <text x="{cx}" y="{cy + 2}" fill="#ffffff" font-size="13" font-family="system-ui" text-anchor="middle" font-weight="900">{modelo.anomalia_tsm_pacifico:+.1f}°C</text>
            <text x="{cx}" y="{cy + 15}" fill="#00f2fe" font-size="8" font-family="system-ui" text-anchor="middle" font-weight="600">TSM PACÍFICO</text>
            <text x="{cx}" y="{cy + 25}" fill="#94a3b8" font-size="7" font-family="system-ui" text-anchor="middle">Tmin: {modelo.temperatura_minima_promedio_c:.1f}°C</text>
        </svg>
        """
        return svg.strip()
