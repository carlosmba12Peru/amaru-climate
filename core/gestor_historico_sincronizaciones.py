"""
Gestor de Historial y Comparativa Delta de Sincronizaciones C2.
Sistema AMARU-FEN - Sala de Mando C2.

Registra cada sincronización de indicadores de los 893 UBIGEOS,
calcula la variación (Delta) de nodos Rojos, Naranjas, Amarillos y Verdes,
y permite observar la evolución temporal de la amenaza FEN a lo largo de las actualizaciones.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("AMARU.HistoricoSincronizaciones")

PATH_HISTORICO = Path(__file__).resolve().parent.parent / "data" / "historico_sincronizaciones_c2.json"

class GestorHistoricoSincronizaciones:
    """Gestiona el archivo histórico de snapshots y el análisis comparativo delta."""

    def __init__(self, ruta_archivo: Optional[Path] = None):
        self.ruta_archivo = ruta_archivo or PATH_HISTORICO
        self.snapshots: List[Dict[str, Any]] = self._cargar_historico()

    def _cargar_historico(self) -> List[Dict[str, Any]]:
        if not self.ruta_archivo.exists():
            # Crear línea base inicial con 3 snapshots históricos sintéticos representativos
            linea_base = [
                {
                    "id_snapshot": "SYNC-001",
                    "timestamp": "2026-08-15 08:00:00",
                    "fuente": "Línea Base Inicial (Vigilancia Invernal)",
                    "motivo": "Configuración inicial de la temporada",
                    "total_ubigeos": 893,
                    "rojos": 8,
                    "naranjas": 42,
                    "amarillos": 210,
                    "verdes": 633,
                    "delta_rojos": 0,
                    "delta_naranjas": 0,
                    "delta_amarillos": 0,
                    "delta_verdes": 0,
                    "distritos_en_rojo_muestra": ["Catacaos", "Cura Mori", "Tambogrande"]
                },
                {
                    "id_snapshot": "SYNC-002",
                    "timestamp": "2026-08-26 12:30:00",
                    "fuente": "Informe Técnico ENFEN N° 15 (Alerta FEN)",
                    "motivo": "Anomalía TSM Niño 1+2 sube a +1.8 °C",
                    "total_ubigeos": 893,
                    "rojos": 24,
                    "naranjas": 98,
                    "amarillos": 320,
                    "verdes": 451,
                    "delta_rojos": 16,
                    "delta_naranjas": 56,
                    "delta_amarillos": 110,
                    "delta_verdes": -182,
                    "distritos_en_rojo_muestra": ["Catacaos", "Cura Mori", "Piura", "Castilla", "Íllimo", "Tumbes"]
                }
            ]
            self._guardar_historico(linea_base)
            return linea_base

        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("snapshots", [])
        except Exception as e:
            logger.error(f"Error al leer histórico de sincronizaciones: {e}")
            return []

    def _guardar_historico(self, snapshots: List[Dict[str, Any]]) -> None:
        try:
            self.ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump({
                    "descripcion": "Registro histórico y comparativo de sincronizaciones C2 - Sistema AMARU-FEN",
                    "ultima_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "total_snapshots": len(snapshots),
                    "snapshots": snapshots
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error al guardar histórico de sincronizaciones: {e}")

    def registrar_snapshot(
        self,
        ubigeos_data: List[Dict[str, Any]],
        fuente: str = "Ingesta Oficial Autorizada (SENAMHI / ENFEN)",
        motivo: str = "Sincronización en tiempo real"
    ) -> Dict[str, Any]:
        """
        Calcula el conteo de semáforo actual, compara contra el último snapshot
        y almacena el nuevo registro en el historial.
        """
        n_rojos = sum(1 for u in ubigeos_data if u.get("nivel_alerta") == "CRITICO_ROJO")
        n_naranjas = sum(1 for u in ubigeos_data if u.get("nivel_alerta") == "ALTO_NARANJA")
        n_amarillos = sum(1 for u in ubigeos_data if u.get("nivel_alerta") == "MEDIO_AMARILLO")
        n_verdes = sum(1 for u in ubigeos_data if u.get("nivel_alerta") == "BAJO_VERDE")

        distritos_rojos = [u.get("distrito", "") for u in ubigeos_data if u.get("nivel_alerta") == "CRITICO_ROJO"]

        # Calcular deltas con respecto al snapshot anterior
        ultimo = self.snapshots[-1] if self.snapshots else None
        if ultimo:
            d_rojos = n_rojos - ultimo.get("rojos", 0)
            d_naranjas = n_naranjas - ultimo.get("naranjas", 0)
            d_amarillos = n_amarillos - ultimo.get("amarillos", 0)
            d_verdes = n_verdes - ultimo.get("verdes", 0)
        else:
            d_rojos = d_naranjas = d_amarillos = d_verdes = 0

        nuevo_id = f"SYNC-{len(self.snapshots) + 1:03d}"
        nuevo_snapshot = {
            "id_snapshot": nuevo_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fuente": fuente,
            "motivo": motivo,
            "total_ubigeos": len(ubigeos_data),
            "rojos": n_rojos,
            "naranjas": n_naranjas,
            "amarillos": n_amarillos,
            "verdes": n_verdes,
            "delta_rojos": d_rojos,
            "delta_naranjas": d_naranjas,
            "delta_amarillos": d_amarillos,
            "delta_verdes": d_verdes,
            "distritos_en_rojo_muestra": distritos_rojos[:10]
        }

        self.snapshots.append(nuevo_snapshot)
        # Mantener un histórico suficiente para análisis de 1 día, 1 mes y 1 año (hasta 250 snapshots)
        if len(self.snapshots) > 250:
            self.snapshots = self.snapshots[-250:]

        self._guardar_historico(self.snapshots)
        return nuevo_snapshot

    def obtener_comparativa_delta_ultima(self) -> Dict[str, Any]:
        """Retorna el último snapshot y la variación respecto al previo."""
        if not self.snapshots:
            return {}
        actual = self.snapshots[-1]
        previo = self.snapshots[-2] if len(self.snapshots) >= 2 else actual

        return {
            "actual": actual,
            "previo": previo,
            "variacion": {
                "rojos": actual.get("delta_rojos", 0),
                "naranjas": actual.get("delta_naranjas", 0),
                "amarillos": actual.get("delta_amarillos", 0),
                "verdes": actual.get("delta_verdes", 0)
            },
            "tendencia_general": "EMERGENCIA_EN_AUMENTO" if actual.get("delta_rojos", 0) > 0 else (
                "EMERGENCIA_ESTABLE" if actual.get("delta_rojos", 0) == 0 else "DESESCALAMIENTO"
            )
        }

    def obtener_todos_los_snapshots(self) -> List[Dict[str, Any]]:
        """Retorna la serie temporal completa de snapshots."""
        return self.snapshots

    @staticmethod
    def _parsear_fecha(ts_str: str) -> Optional[datetime]:
        """Parsea strings de fecha en formatos estándar de AMARU-C2."""
        if not ts_str:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(str(ts_str).strip(), fmt)
            except Exception:
                pass
        return None

    def filtrar_por_periodo(self, periodo: str = "TODO") -> List[Dict[str, Any]]:
        """
        Filtra los snapshots históricos según la ventana temporal requerida:
        - "1_DIA" / "1D" / "24H": últimas 24 horas
        - "5_DIAS" / "5D": últimos 5 días
        - "7_DIAS" / "7D" / "1_SEMANA": últimos 7 días
        - "1_MES" / "30D": últimos 30 días
        - "1_ANO" / "365D": últimos 365 días (1 año)
        - "TODO" / "HISTORICO": sin filtro temporal (todo el registro)
        """
        if not self.snapshots:
            return []

        periodo_norm = str(periodo).upper().strip()
        if periodo_norm in ["TODO", "HISTORICO", "HISTORICO COMPLETO", "ALL"]:
            return self.snapshots

        # Determinar la fecha de referencia (el timestamp más reciente entre los snapshots)
        fechas = [self._parsear_fecha(s.get("timestamp", "")) for s in self.snapshots]
        fechas_validas = [f for f in fechas if f is not None]
        
        if not fechas_validas:
            return self.snapshots

        fecha_ref = max(fechas_validas)

        from datetime import timedelta
        dias_delta = None
        if periodo_norm in ["1_DIA", "1D", "24H", "1 DIA", "1 DÍA", "ULTIMAS_24H"]:
            dias_delta = timedelta(days=1)
        elif periodo_norm in ["5_DIAS", "5D", "5 DIAS", "5 DÍAS"]:
            dias_delta = timedelta(days=5)
        elif periodo_norm in ["7_DIAS", "7D", "7 DIAS", "7 DÍAS", "1_SEMANA", "1 SEMANA"]:
            dias_delta = timedelta(days=7)
        elif periodo_norm in ["1_MES", "1M", "30D", "1 MES", "30 DIAS"]:
            dias_delta = timedelta(days=30)
        elif periodo_norm in ["1_ANO", "1A", "365D", "1 AÑO", "1 ANO", "365 DIAS"]:
            dias_delta = timedelta(days=365)
        else:
            return self.snapshots

        fecha_corte = fecha_ref - dias_delta

        filtrados = []
        for s in self.snapshots:
            dt = self._parsear_fecha(s.get("timestamp", ""))
            if dt and dt >= fecha_corte:
                filtrados.append(s)

        # Si el filtro es demasiado restrictivo y no deja elementos, devolver al menos el último
        if not filtrados:
            return [self.snapshots[-1]]

        return filtrados

gestor_historico_sincronizaciones = GestorHistoricoSincronizaciones()
