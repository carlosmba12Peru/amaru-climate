"""
Registro Centralizado de Fuentes Validadas y Allowlist Soberano de Búsqueda y Extracción.
Sistema AMARU-FEN - Sala de Mando C2.

Principio de Seguridad C2:
Queda estrictamente prohibida la búsqueda abierta en la web ('Open Web Search') sin restricciones.
Toda ingesta, scraping o búsqueda de información debe provenir exclusivamente de fuentes
oficialmente auditadas y homologadas por el Equipo Técnico de AMARU-FEN.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger("AMARU.RegistroFuentesValidadas")

PATH_CATALOGO_FUENTES = Path(__file__).resolve().parent.parent / "data" / "fuentes_validadas_amaru.json"

class ViolacionSeguridadFuenteNoAutorizada(Exception):
    """Excepción de seguridad emitida cuando un agente intenta consultar una fuente no homologada."""
    pass

class RegistroFuentesValidadas:
    """
    Gestor del catálogo de fuentes autorizadas (Allowlist Soberana).
    Garantiza que la IA solo extraiga datos de entidades verificadas del Estado peruano,
    organismos internacionales acreditados y radiodifusoras regionales comunitarias validadas.
    """

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(RegistroFuentesValidadas, cls).__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self):
        if self._inicializado:
            return
        self.ruta_catalogo = PATH_CATALOGO_FUENTES
        self.catalogo: Dict[str, Any] = self._cargar_catalogo()
        self._inicializado = True

    def _cargar_catalogo(self) -> Dict[str, Any]:
        if not self.ruta_catalogo.exists():
            logger.error(f"Catálogo de fuentes no encontrado en {self.ruta_catalogo}")
            return {"fuentes_validadas": []}
        try:
            with open(self.ruta_catalogo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer catálogo de fuentes validadas: {e}")
            return {"fuentes_validadas": []}

    def listar_fuentes_activas(self, solo_tier1_y_2: bool = False) -> List[Dict[str, Any]]:
        """Retorna las fuentes autorizadas por el equipo AMARU-FEN."""
        fuentes = [f for f in self.catalogo.get("fuentes_validadas", []) if f.get("estado") == "ACTIVO_AUDITADO"]
        if solo_tier1_y_2:
            fuentes = [f for f in fuentes if f.get("tier") in ["TIER_1_OFICIAL_ESTATAL", "TIER_2_INSTITUCIONAL_INTERNACIONAL"]]
        return fuentes

    def validar_url(self, url: str) -> Dict[str, Any]:
        """
        Verifica si una URL pertenece a un dominio homologado en la Allowlist.
        Si no pertenece, levanta ViolacionSeguridadFuenteNoAutorizada.
        """
        if not url:
            raise ViolacionSeguridadFuenteNoAutorizada("URL vacía o no proporcionada.")

        parsed = urlparse(url)
        dominio = parsed.netloc.lower()

        for fuente in self.catalogo.get("fuentes_validadas", []):
            if fuente.get("estado") != "ACTIVO_AUDITADO":
                continue
            dominio_fuente = urlparse(fuente.get("dominio_autorizado", "")).netloc.lower()
            if dominio_fuente and (dominio == dominio_fuente or dominio.endswith("." + dominio_fuente)):
                return {
                    "autorizada": True,
                    "fuente_id": fuente["id"],
                    "nombre": fuente["nombre"],
                    "tier": fuente["tier"],
                    "gatilla_calculo_directo": fuente.get("gatilla_calculo_directo", False)
                }

        logger.critical(f"[ALERTA DE SEGURIDAD C2] Intento de acceso a fuente no autorizada: {url}")
        raise ViolacionSeguridadFuenteNoAutorizada(
            f"El dominio '{dominio}' no forma parte de la Allowlist Soberana de AMARU-FEN. "
            "Acceso bloqueado conforme a las políticas de seguridad de la Sala C2."
        )

    def es_fuente_autorizada(self, url: str) -> bool:
        """Verifica de forma booleana si la URL está permitida sin arrojar excepción."""
        try:
            self.validar_url(url)
            return True
        except ViolacionSeguridadFuenteNoAutorizada:
            return False

    def obtener_resumen_gobernanza(self) -> Dict[str, Any]:
        """Provee métricas para el panel de control y auditoría de la Sala de Mando C2."""
        fuentes = self.catalogo.get("fuentes_validadas", [])
        tiers = {}
        for f in fuentes:
            t = f.get("tier", "OTROS")
            tiers[t] = tiers.get(t, 0) + 1

        return {
            "total_fuentes_validadas": len(fuentes),
            "politica": self.catalogo.get("metadatos_catalogo", {}).get("politica_seguridad", "ALLOWLIST_ESTRICTO"),
            "distribucion_tiers": tiers,
            "auditado_por": self.catalogo.get("metadatos_catalogo", {}).get("auditado_por", "Equipo AMARU-FEN"),
            "fecha_auditoria": self.catalogo.get("metadatos_catalogo", {}).get("fecha_auditoria", "2026-09")
        }

registro_fuentes_amaru = RegistroFuentesValidadas()
