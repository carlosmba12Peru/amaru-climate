import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AgenteLegalNormativo:
    """
    Agente Legal y Normativo FEN:
    Estructura, almacena y consulta las normas legales extraordinarias dictadas por el Estado Peruano
    para enfrentar el Fenómeno El Niño (Decretos de Urgencia, Decretos Supremos de Emergencia,
    Ley de Contrataciones del Estado, Obras por Impuestos y Ley SINAGERD).
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.nombre = "Agente Legal y Normativo FEN"
        self.base_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        
        self.catalogo_normas = []
        self.distritos_emergencia = []
        self.metadata_ds_124 = {}
        self.distritos_fondes_1891 = []
        self.metadata_fondes_1891 = {}
        
        # Índices cacheados de alto rendimiento O(1)
        self._set_ds_124_emergencia = set()
        self._map_fondes_ubigeo = {}
        self._map_fondes_distrito_dep = {}
        
        self._cargar_bases_normativas()

    def _cargar_bases_normativas(self):
        # 1. Cargar catálogo de normas
        path_normas = os.path.join(self.base_dir, "catalogo_normas_legales_fen.json")
        try:
            with open(path_normas, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.catalogo_normas = data.get("normas_vigentes_fen", [])
        except Exception as e:
            logger.error(f"Error cargando catalogo_normas_legales_fen.json: {e}")
            self.catalogo_normas = []

        # 2. Cargar los 893 distritos del DS 124-2026-PCM
        path_distritos = os.path.join(self.base_dir, "distritos_emergencia_ds_124_2026_pcm.json")
        try:
            with open(path_distritos, "r", encoding="utf-8") as f:
                data_893 = json.load(f)
                self.metadata_ds_124 = data_893.get("metadata", {})
                self.distritos_emergencia = data_893.get("distritos_declarados", [])
                self._set_ds_124_emergencia = {
                    (d.get("distrito", "").upper().strip(), d.get("departamento", "").upper().strip())
                    for d in self.distritos_emergencia
                }
        except Exception as e:
            logger.error(f"Error cargando distritos_emergencia_ds_124_2026_pcm.json: {e}")
            self.distritos_emergencia = []
            self._set_ds_124_emergencia = set()

        # 3. Cargar la matriz nacional consolidada de los 1,891 distritos FONDES (DS N° 234-2025-EF)
        path_fondes = os.path.join(self.base_dir, "distritos_riesgo_nacional_1891_cenepred_mef.json")
        try:
            with open(path_fondes, "r", encoding="utf-8") as f:
                data_fondes = json.load(f)
                self.metadata_fondes_1891 = data_fondes.get("metadata", {})
                self.distritos_fondes_1891 = data_fondes.get("distritos", [])
                
                # Crear índices O(1)
                for d in self.distritos_fondes_1891:
                    ub = d.get("ubigeo")
                    if ub:
                        self._map_fondes_ubigeo[str(ub).strip()] = d
                    key_nom = (d.get("distrito", "").upper().strip(), d.get("departamento", "").upper().strip())
                    self._map_fondes_distrito_dep[key_nom] = d
        except Exception as e:
            logger.error(f"Error cargando distritos_riesgo_nacional_1891_cenepred_mef.json: {e}")
            self.distritos_fondes_1891 = []
            self._map_fondes_ubigeo = {}
            self._map_fondes_distrito_dep = {}

    def consultar_normas_vigentes(self) -> List[Dict[str, Any]]:
        """Retorna todas las normas vigentes registradas en el catálogo oficial."""
        return self.catalogo_normas

    def consultar_distrito_riesgo_fondes(self, termino_busqueda: str, departamento: str = "") -> Dict[str, Any]:
        """
        Consulta la calificación oficial de riesgo en SIGRID CENEPRED y ANA de cualquiera
        de los 1,891 distritos del Perú, bajo el marco del D.S. N° 234-2025-EF (FONDES).
        Permite buscar por código UBIGEO (6 dígitos) o nombre del distrito.
        """
        busq = termino_busqueda.strip().upper()
        dep_busq = departamento.strip().upper()
        
        coincidencias = []
        for d in self.distritos_fondes_1891:
            ubigeo = d.get("ubigeo", "")
            dist_nom = d.get("distrito", "").upper()
            dep_nom = d.get("departamento", "").upper()
            prov_nom = d.get("provincia", "").upper()
            
            # Búsqueda exacta por UBIGEO o contenida en nombre
            if busq == ubigeo or (len(busq) >= 3 and busq in dist_nom):
                if not dep_busq or dep_busq in dep_nom:
                    # Cruzar con estado de emergencia DS 124-2026-PCM mediante conjunto O(1)
                    en_ds_124 = (dist_nom, dep_nom) in self._set_ds_124_emergencia
                    
                    item = dict(d)
                    item["declarado_emergencia_ds_124_pcm"] = en_ds_124
                    item["priorizacion_fondes"] = item.get("nivel_peligro_riesgo_sigrid") in ["Muy Alto", "Alto"]
                    coincidencias.append(item)
                    
        return {
            "agente": self.nombre,
            "termino_consultado": termino_busqueda,
            "departamento_filtro": departamento or "TODOS",
            "total_coincidencias": len(coincidencias),
            "coincidencias": coincidencias,
            "marco_normativo": "Decreto Supremo N° 234-2025-EF (Reglamento FONDES)",
            "fuentes_sustento": "Oficio N° 00072-2026-CENEPRED/J y Oficios Técnicos ANA (Puntos Críticos)",
            "total_distritos_pais": len(self.distritos_fondes_1891)
        }

    def obtener_resumen_nacional_fondes(self) -> Dict[str, Any]:
        """Retorna las estadísticas consolidadas a nivel nacional del dataset FONDES."""
        return {
            "metadata": self.metadata_fondes_1891,
            "total_distritos": len(self.distritos_fondes_1891),
            "distribucion_riesgo": self.metadata_fondes_1891.get("resumen_niveles_riesgo", {})
        }

    def verificar_distrito_estado_emergencia(self, nombre_distrito: str, departamento: str = "") -> Dict[str, Any]:
        """
        Verifica si un distrito específico forma parte de los 893 distritos declarados
        en Estado de Emergencia por el Decreto Supremo Nº 124-2026-PCM (El Peruano, 01/09/2026).
        """
        nom_busq = nombre_distrito.strip().upper()
        dep_busq = departamento.strip().upper()

        coincidencias = []
        for d in self.distritos_emergencia:
            dist_nom = d.get("distrito", "").upper()
            dep_nom = d.get("departamento", "").upper()
            
            if nom_busq in dist_nom:
                if not dep_busq or dep_busq in dep_nom:
                    coincidencias.append(d)

        declarado = len(coincidencias) > 0

        return {
            "agente": self.nombre,
            "distrito_consultado": nombre_distrito,
            "declarado_estado_emergencia": declarado,
            "total_coincidencias": len(coincidencias),
            "detalle_distritos": coincidencias,
            "base_legal": "Decreto Supremo Nº 124-2026-PCM (Publicado en El Peruano el 01/09/2026)",
            "vigencia": "60 días calendario",
            "alcance_nacional": f"{len(self.distritos_emergencia)} distritos en 22 departamentos",
            "habilitacion_operativa": (
                "AUTORIZADO: La entidad está facultada para ejecutar contrataciones directas de emergencia, "
                "movilizar maquinaria pesada con cargo al Programa Presupuestal 0068 y acogerse al DU Nº 010-2026 (OxI)."
                if declarado
                else "NO DECLARADO EN ESTE DECRETO: Requiere solicitud de ampliación de declaratoria ante INDECI/PCM si las lluvias lo ameritan."
            )
        }

    def consultar_mecanismo_obras_por_impuestos_du_010(self) -> Dict[str, Any]:
        """
        Retorna el análisis y lineamientos operativos del Decreto de Urgencia Nº 010-2026
        (El Peruano, 02/09/2026) para Obras por Impuestos ante El Niño.
        """
        du = next((n for n in self.catalogo_normas if n.get("id_norma") == "DU-010-2026"), None)
        if not du:
            return {"error": "DU Nº 010-2026 no encontrado en el catálogo."}

        return {
            "agente": self.nombre,
            "norma": du.get("numero"),
            "titulo": du.get("titulo"),
            "fecha_publicacion": du.get("fecha_publicacion"),
            "url_oficial": du.get("diario_oficial_url"),
            "sustento_enfen": du.get("sustento_cientifico_invocado"),
            "beneficio_clave": du.get("beneficio_tactico"),
            "sectores_habilitados": du.get("sectores_habilitados", []),
            "pasos_para_alcalde_o_gobernador": [
                "1. Identificar la intervención prioritaria (descolmatación de río/quebrada o drenaje pluvial).",
                "2. Verificar que el distrito esté en el DS Nº 124-2026-PCM.",
                "3. Suscribir convenio expedito de Obras por Impuestos con la empresa privada aliada bajo el DU Nº 010-2026.",
                "4. Emitir los Certificados de Inversión Pública Regional y Local (CIPRL) correspondientes contra el Impuesto a la Renta."
            ]
        }

    def generar_sustento_contratacion_directa(self, entidad: str, distrito: str, tipo_intervencion: str) -> Dict[str, Any]:
        """
        Genera el informe de fundamentación legal para contrataciones directas (exoneración de licitación)
        amparado en el Art. 27 Literal b de la Ley de Contrataciones (Ley Nº 30225) y DS Nº 124-2026-PCM,
        otorgando blindaje y seguridad jurídica a la autoridad local frente a auditorías de Contraloría.
        """
        check_ds = self.verificar_distrito_estado_emergencia(distrito)
        esta_en_ds = check_ds.get("declarado_estado_emergencia", False)

        return {
            "agente": self.nombre,
            "entidad_ejecutora": entidad,
            "distrito": distrito,
            "tipo_intervencion": tipo_intervencion,
            "amparo_legal_principal": "Artículo 27, literal b de la Ley Nº 30225 (Ley de Contrataciones del Estado)",
            "causal": "Situación de Emergencia por Acontecimientos Catastróficos o Peligro Inminente",
            "respaldo_estado_emergencia": (
                f"Distrito comprendido en el Decreto Supremo Nº 124-2026-PCM (Ítem oficial verificado)."
                if esta_en_ds
                else "Emergencia local sustentada en informe técnico meteorológico de peligro inminente."
            ),
            "plazo_regularizacion_normativo": "10 días hábiles posteriores a la entrega del bien o primera prestación del servicio.",
            "dictamen_juridico_amaru": (
                f"PROCEDENTE: La {entidad} está legalmente facultada para contratar de forma directa e inmediata "
                f"'{tipo_intervencion}' en el distrito de {distrito}. La aprobación de la resolución autoritativa e "
                f"informe técnico se regulariza ex-post dentro de los 10 días hábiles, garantizando la continuidad del servicio "
                f"sin responsabilidad administrativa disciplinaria por demoras operativas."
            )
        }

    def obtener_estadisticas_distritos_emergencia(self) -> Dict[str, Any]:
        """Retorna el desglose estadístico de los 893 distritos por departamento."""
        conteo = {}
        for d in self.distritos_emergencia:
            dep = d.get("departamento", "OTROS")
            conteo[dep] = conteo.get(dep, 0) + 1

        return {
            "total_distritos_declarados": len(self.distritos_emergencia),
            "total_departamentos": len(conteo),
            "distribucion_por_departamento": dict(sorted(conteo.items(), key=lambda x: -x[1])),
            "top_departamentos": [
                {"departamento": dep, "total_distritos": c}
                for dep, c in sorted(conteo.items(), key=lambda x: -x[1])[:8]
            ]
        }

    def generar_resolucion_alcaldia_emergencia(
        self,
        entidad: str,
        alcalde: str,
        distrito: str,
        intervencion: str,
        monto_estimado_soles: float
    ) -> str:
        """
        Genera el borrador formal de la Resolución de Alcaldía / Gobernación Regional
        listo para firma y publicación en el portal de transparencia de la entidad,
        amparado en el DS Nº 124-2026-PCM, DU Nº 010-2026 y Ley Nº 30225.
        """
        check_ds = self.verificar_distrito_estado_emergencia(distrito)
        num_item = check_ds["detalle_distritos"][0]["id"] if check_ds["detalle_distritos"] else "S/N"
        
        resolucion = f"""================================================================================
RESOLUCIÓN DE ALCALDÍA Nº 084-2026-{entidad.split()[-1].upper()}
================================================================================

Distrito de {distrito}, 03 de septiembre de 2026

VISTO:
El Informe Técnico emitido por el Centro de Operaciones de Emergencia Local (COEL) y la Subgerencia 
de Gestión del Riesgo de Desastres, el Decreto Supremo Nº 124-2026-PCM, el Decreto de Urgencia 
Nº 010-2026, y el Artículo 27 literal b) del Texto Único Ordenado de la Ley Nº 30225, Ley de 
Contrataciones del Estado;

CONSIDERANDO:
Que, el Artículo 194 de la Constitución Política del Perú, modificado por la Ley de Reforma Constitucional, 
establece que las Municipalidades son órganos de gobierno local con autonomía política, económica 
y administrativa en los asuntos de su competencia;

Que, mediante Decreto Supremo Nº 124-2026-PCM, publicado en el Diario Oficial El Peruano el 01 de setiembre 
de 2026, se declaró el Estado de Emergencia en el distrito de {distrito.upper()} (Ítem Oficial Nº {num_item}) 
por peligro inminente ante intensas precipitaciones pluviales asociadas al Fenómeno El Niño 2026-2027, 
por el plazo de sesenta (60) días calendario;

Que, el Decreto de Urgencia Nº 010-2026 dicta medidas extraordinarias para la ejecución inmediata de 
intervenciones ante el Fenómeno El Niño en coordinación con los sectores competentes;

Que, el literal b) del numeral 27.1 del artículo 27 de la Ley Nº 30225, Ley de Contrataciones del Estado, 
faculta a las entidades a contratar directamente ante una 'Situación de Emergencia', permitiendo regularizar 
la documentación y resolución dentro de los diez (10) días hábiles posteriores a la entrega del bien o 
inicio de la prestación;

Que, ante el inminente desborde pluvial y la amenaza sobre la vida y la infraestructura pública, resulta 
urgente e impostergable la ejecución de: '{intervencion}', con una afectación presupuestal estimada en 
S/. {monto_estimado_soles:,.2f} Soles con cargo al Programa Presupuestal 0068 (Reducción de la Vulnerabilidad 
y Atención de Emergencias por Desastres);

SE RESUELVE:

ARTÍCULO PRIMERO.- APROBAR la CONTRATACIÓN DIRECTA POR SITUACIÓN DE EMERGENCIA para: 
'{intervencion}', por el monto estimado de S/. {monto_estimado_soles:,.2f} Soles, al amparo del literal b) 
del artículo 27 de la Ley Nº 30225 y el Decreto Supremo Nº 124-2026-PCM.

ARTÍCULO SEGUNDO.- DISPONER que la Oficina de Logística y Abastecimiento ejecute de manera inmediata 
las acciones operativas de adjudicación, contratación y despliegue en terreno, debiendo regularizar 
los actuados administrativos dentro del plazo perentorio de diez (10) días hábiles.

ARTÍCULO TERCERO.- NOTIFICAR la presente Resolución al Órgano de Control Institucional (OCI), a la 
Contraloría General de la República y al Sistema Electrónico de Contrataciones del Estado (SEACE) 
para los fines de ley.

REGÍSTRESE, COMUNÍQUESE Y CÚMPLASE.


_____________________________________________
{alcalde}
Alcalde / Autoridad Titular
{entidad}
================================================================================
"""
        return resolucion

    def consultar_marco_soberania_humana_ia(self) -> Dict[str, Any]:
        """
        Retorna el marco normativo y principios éticos que consagran la Soberanía y
        Supervisión Humana Permanente (Human-in-the-Loop) en el uso de IA para GRD.
        Conforme a la Ley Nº 31814 (Perú), DS 085-2024-PCM, UNESCO (2021), OCDE y Marco de Sendai.
        """
        return {
            "principio_rector": "SOBERANÍA HUMANA Y SUPERVISIÓN HUMANA EXCLUSIVA (HUMAN-IN-THE-LOOP)",
            "declaracion_fundamental": (
                "Ningún agente de Inteligencia Artificial en AMARU-FEN toma decisiones autónomas "
                "de carácter administrativo, financiero, de evacuación o legal. Todas las salidas, "
                "scores IRCE-FEN, borradores de contratos y fichas EDAN constituyen RECOMENDACIONES "
                "TÉCNICAS Y HERRAMIENTAS DE SOPORTE A LA DECISIÓN (DSS). La decisión final, la firma y "
                "la responsabilidad administrativa, civil y penal recaen exclusivamente en las autoridades "
                "humanas competentes (Alcaldes, Gobernadores, Ministros, Directores de COEN e INDECI)."
            ),
            "marco_normativo_nacional": {
                "ley": "Ley Nº 31814 - Ley que promueve el uso de la inteligencia artificial en favor del desarrollo económico y social del país",
                "reglamento": "Decreto Supremo Nº 085-2024-PCM (Reglamento de la Ley Nº 31814)",
                "ente_rector": "Secretaría de Gobierno y Transformación Digital (SGTD - PCM)",
                "principios_clave_peru": [
                    "Supervisión Humana Obligatoria (Human-in-the-loop y Human-over-the-loop).",
                    "Rendición de Cuentas y Responsabilidad Administrativa Indelegable.",
                    "No Discriminación, Equidad y Protección de los Derechos Fundamentales.",
                    "Transparencia y Explicabilidad Algorítmica en el Sector Público."
                ]
            },
            "marco_normativo_internacional": {
                "unesco": "Recomendación sobre la Ética de la Inteligencia Artificial (UNESCO, 2021) - Primacía de la dignidad humana y control humano.",
                "ocde": "Principios de la OCDE sobre Inteligencia Artificial Responsable (Valores centrados en el ser humano y supervisión activa).",
                "onu_sendai": "Marco de Sendai para la Reducción del Riesgo de Desastres 2015-2030 (Soberanía indelegable del Estado y sus autoridades)."
            },
            "protocolo_operativo_amaru": {
                "alertas_sismate": "La IA calcula el umbral físico; la orden de transmisión y activación de sirenas requiere autorización del Director del COEN / INDECI.",
                "contratacion_directa": "La IA redacta el borrador del acuerdo sustentado en el DS 124-2026-PCM; la firma y validez jurídica emana de la Resolución del Titular del Pliego.",
                "gasto_presupuestal": "La IA detecta el trigger paramétrico CAF/PUCP; la aprobación del desembolso PP 0068 corresponde al Gerente de Presupuesto y MEF.",
                "fichas_edan": "La IA consolida daños por OSINT y sensores; la firma y subida oficial al SINPAD corresponde al evaluador de Defensa Civil acreditado."
            },
            "sello_disclaimer_oficial": "⚠️ RECOMENDACIÓN TÉCNICA DE IA PARA DECISIÓN HUMANA EXCLUSIVA (Ley Nº 31814 - Soberanía y Supervisión Humana Permanente)"
        }

    def obtener_sello_soberania_humana(self) -> str:
        """Retorna el sello textual mandatorio para todas las salidas operativas."""
        return "⚠️ RECOMENDACIÓN TÉCNICA DE IA PARA DECISIÓN HUMANA EXCLUSIVA (Ley Nº 31814 - Human-in-the-Loop)"


