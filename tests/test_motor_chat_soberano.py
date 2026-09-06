"""
Pruebas Unitarias para el Motor de Chat Soberano (AMARU-FEN).
Verifica que las respuestas provengan exclusivamente de fuentes homologadas,
que los cálculos y citas sean exactos, y que se aplique el filtro Dura Lex ante temas ajenos.
"""

import pytest
from core.motor_chat_soberano import MotorChatSoberano

@pytest.fixture
def motor():
    return MotorChatSoberano()

def test_consulta_ubigeo_ciudadano_catacaos(motor):
    # Consulta como vecino / ciudadano de Catacaos
    res = motor.procesar_consulta("Soy de Catacaos, qué información tienes para mí", rol="ciudadano")
    assert res["categoria"] == "UBIGEO_HISTORICO"
    assert res["ubigeo_detectado"] == "200105"
    assert res["rol_aplicado"] == "ciudadano"
    assert "INFORMACIÓN VITAL PARA VECINOS" in res["respuesta"]
    assert "Cura Mori" in res["respuesta"]
    assert "Mochila de Emergencia" in res["respuesta"]
    assert "116" in res["respuesta"] # Bomberos

def test_consulta_ubigeo_alcalde_catacaos(motor):
    # Consulta como autoridad / alcalde
    res = motor.procesar_consulta("Como alcalde de Catacaos, qué acciones tácticas debo ejecutar y qué maquinaria contrato", rol="alcalde")
    assert res["categoria"] == "UBIGEO_HISTORICO"
    assert res["ubigeo_detectado"] == "200105"
    assert res["rol_aplicado"] == "alcalde"
    assert "DESPACHO TÁCTICO PARA EL ALCALDE" in res["respuesta"]
    assert "124-2026-PCM" in res["respuesta"]
    assert "PP 0068" in res["respuesta"]
    assert "Contraloría" in res["respuesta"]

def test_consulta_ubigeo_tecnico_catacaos(motor):
    # Consulta como técnico / científico
    res = motor.procesar_consulta("Dame el análisis hidrológico y la consistencia matemática de Saaty para Catacaos", rol="tecnico")
    assert res["categoria"] == "UBIGEO_HISTORICO"
    assert res["ubigeo_detectado"] == "200105"
    assert res["rol_aplicado"] == "tecnico"
    assert "DOSSIER MATEMÁTICO" in res["respuesta"]
    assert "Saaty AHP" in res["respuesta"]
    assert "0.0113" in res["respuesta"]

def test_consulta_ubigeo_periodista_catacaos(motor):
    # Consulta como periodista / prensa
    res = motor.procesar_consulta("Para nota de prensa sobre Catacaos, qué información oficial verificada se tiene", rol="periodista")
    assert res["categoria"] == "UBIGEO_HISTORICO"
    assert res["ubigeo_detectado"] == "200105"
    assert res["rol_aplicado"] == "periodista"
    assert "REPORTE VERIFICADO PARA PRENSA" in res["respuesta"]
    assert "Fake News" in res["respuesta"]
    assert "D.S. Nº 124-2026-PCM" in res["respuesta"]

def test_consulta_ubigeo_por_nombre_distrito(motor):
    # Consulta por nombre en lenguaje natural para Punta Hermosa
    res = motor.procesar_consulta("Cuál fue el impacto del Ciclón Yaku en Punta Hermosa y qué holgura táctica se obtuvo", rol="ciudadano")
    assert res["categoria"] == "UBIGEO_HISTORICO"
    assert res["ubigeo_detectado"] == "150126"
    assert "PUNTA HERMOSA" in res["respuesta"]

def test_consulta_sustento_iph_histeresis(motor):
    # Consulta doctrinal sobre el IPH y la memoria del suelo
    res = motor.procesar_consulta("Por qué AMARU-FEN usa un IPH en lugar de solo mirar la lluvia de hoy y qué es la histéresis")
    assert res["categoria"] == "SUSTENTO_IPH_HISTÉRESIS"
    assert "IPH-FEN" in res["respuesta"]
    assert "histéresis" in res["respuesta"].lower() or "histeresis" in res["respuesta"].lower()
    assert "7 Huaicos de San Ildefonso" in res["respuesta"]
    assert "alpha" in res["respuesta"] or "\\alpha" in res["respuesta"]
    assert len(res["fuentes_citadas"]) >= 1

def test_consulta_formulas_irce_saaty_ahp(motor):
    # Consulta sobre el cálculo y los pesos de Saaty
    res = motor.procesar_consulta("Explícame la fórmula del IRCE-FEN y por qué la matriz Saaty tiene consistencia CR menor a 0.10")
    assert res["categoria"] == "FORMULAS_IRCE_SAATY"
    assert "IRCE-FEN" in res["respuesta"]
    assert "0.467" in res["respuesta"]  # Peso del Peligro
    assert "0.0113" in res["respuesta"] # CR
    assert "Dura Lex" in res["respuesta"] or "CONSISTENCIA AXIOMÁTICA" in res["respuesta"]

def test_consulta_marco_legal_ds124_y_soberania(motor):
    # Consulta sobre la base legal y Contraloría
    res = motor.procesar_consulta("Qué dice el D.S. 124-2026-PCM sobre compras directas y cómo se protege al alcalde ante Contraloría")
    assert res["categoria"] == "MARCO_LEGAL_DS124"
    assert "124-2026-PCM" in res["respuesta"]
    assert "PP 0068" in res["respuesta"]
    assert "Ley Nº 31814" in res["respuesta"]
    assert "SHA-256" in res["respuesta"]

def test_consulta_resumen_backtesting_probabilidad_exito(motor):
    # Consulta sobre la probabilidad de éxito global y las métricas
    res = motor.procesar_consulta("Por qué la probabilidad de éxito en el backtesting va del 94.2 al 98.4 y qué significa el 96.2")
    assert res["categoria"] == "BACKTESTING_GLOBAL"
    assert "96.2%" in res["respuesta"]
    assert "100.0%" in res["respuesta"] # Recall
    assert "+8.1 horas útiles" in res["respuesta"]

def test_consulta_quebradas_criticas(motor):
    # Consulta de catálogo de quebradas
    res = motor.procesar_consulta("Cuáles son las quebradas críticas de mayor riesgo y qué umbrales tienen")
    assert res["categoria"] == "QUEBRADAS_Y_TERRITORIO"
    assert "quebradas críticas reincidentes" in res["respuesta"]
    assert len(res["fuentes_citadas"]) >= 1

def test_consulta_fuentes_allowlist_tiers(motor):
    # Consulta sobre la política de Allowlist
    res = motor.procesar_consulta("Cuáles son las fuentes autorizadas y qué significa el Tier 1 en AMARU-FEN")
    assert res["categoria"] == "ALLOWLIST_SEGURIDAD"
    assert "TIER 1" in res["respuesta"]
    assert "SENAMHI" in res["respuesta"]
    assert "ENFEN" in res["respuesta"]

def test_rechazo_dura_lex_pregunta_no_homologada(motor):
    # Consulta ajena a la gestión de riesgo FEN
    res = motor.procesar_consulta("Quién ganó el partido de fútbol de ayer en la liga española")
    assert res["categoria"] == "RECHAZO_DURA_LEX"
    assert "FILTRO DURA LEX" in res["respuesta"]
    assert "terminantemente restringida" in res["respuesta"]
    assert "Temas autorizados para consulta" in res["respuesta"]

def test_consulta_ficha_edan_sinpad(motor):
    # Consulta sobre Ficha EDAN y bloques de información
    res = motor.procesar_consulta("Qué es la Ficha EDAN y cómo están configurados los bloques de información en SINPAD?")
    assert res["categoria"] == "FICHA_EDAN_SINPAD"
    assert "SINAGERD (Ley Nº 29664)" in res["respuesta"]
    assert "Bloque I: Información General" in res["respuesta"]
    assert "Bloque VIII: Sellado Criptográfico" in res["respuesta"]
    assert "modelo_practico_ficha_edan_digital_amaru_fen.pdf" in str(res["fuentes_citadas"])

def test_consulta_modulo_satelite_comite_cgr(motor):
    # Consulta sobre el módulo satélite externo y aprobación de comité CGR
    res = motor.procesar_consulta("Podemos hacer un módulo satélite externo para precarga de fichas EDAN con aprobación de comité según Contraloría?")
    assert res["categoria"] == "MODULO_SATELITE_COMITE_CGR"
    assert "MÓDULO SATÉLITE EXTERNO" in res["respuesta"]
    assert "Comité de Validación y Cumplimiento CGR" in res["respuesta"]
    assert "Memoria Cap. 5" in res["respuesta"]
    assert "Achoma" in res["respuesta"]
    assert "modulo_satelite_precarga_edan_y_gobernanza_comite_cgr.pdf" in str(res["fuentes_citadas"])

def test_consulta_reloj_del_fen(motor):
    # Consulta sobre el Reloj del FEN
    res = motor.procesar_consulta("Explícame el reloj del FEN, cómo funciona el arco rojo, el análogo de 1997-1998 y el minutero?")
    assert res["categoria"] == "RELOJ_DEL_FEN_TACTICO"
    assert "EL RELOJ DEL FEN" in res["respuesta"]
    assert "12:00" in res["respuesta"]
    assert "1997-1998" in res["respuesta"]
    assert "reloj_del_fen_modelo_matematico_y_analogos.pdf" in str(res["fuentes_citadas"])

def test_consulta_disparidad_enfen_wmo(motor):
    # Consulta sobre disparidad en probabilidades entre ENFEN, WMO y AMARU-FEN
    res = motor.procesar_consulta("Por qué hay diferencias entre las probabilidades de un Niño en un porcentaje menor en ENFEN respecto a AMARU-FEN y WMO?")
    assert res["categoria"] == "DISPARIDAD_PROBABILIDADES_ENFEN_WMO"
    assert "SUSTENTO DOCTRINAL DE DISPARIDAD" in res["respuesta"]
    assert "43%" in res["respuesta"]
    assert "83%" in res["respuesta"]
    assert "WMO" in res["respuesta"]
    assert "analisis_comparativo_probabilidades_amaru_vs_enfen_wmo.pdf" in str(res["fuentes_citadas"])



