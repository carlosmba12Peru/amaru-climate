import pytest
import json
import os
import hashlib

CATALOGO_PATH = os.path.join("data", "catalogo_distritos_heladas_nina.json")
FEN_QUEBRADAS_PATH = os.path.join("data", "catalogo_quebradas_criticas.json")

def test_catalogo_heladas_existe_y_estructura_valida():
    assert os.path.exists(CATALOGO_PATH), f"No se encontró el archivo {CATALOGO_PATH}"
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "metadata" in data
    assert "distritos" in data
    assert len(data["distritos"]) == 27
    
    metadata = data["metadata"]
    assert "hash_integridad_sha256" in metadata
    assert metadata["total_distritos_priorizados"] == 27
    assert set(metadata["regiones_priorizadas"]) == {
        "PUNO", "HUANCAVELICA", "AREQUIPA", "CUSCO", "TACNA", "LIMA", "PASCO", "HUANUCO"
    }

def test_distritos_campos_requeridos_y_coherencia_geografica():
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    distritos = data["distritos"]
    ubigeos_vistos = set()
    
    for d in distritos:
        # 1. Identificadores oficiales
        assert len(d["ubigeo"]) == 6, f"UBIGEO inválido: {d['ubigeo']}"
        assert d["ubigeo"] not in ubigeos_vistos, f"UBIGEO duplicado: {d['ubigeo']}"
        ubigeos_vistos.add(d["ubigeo"])
        assert d["departamento"] in {
            "PUNO", "HUANCAVELICA", "AREQUIPA", "CUSCO", "TACNA", "LIMA", "PASCO", "HUANUCO"
        }
        
        # 2. Coordenadas y altitud válida
        assert -18.5 <= d["lat"] <= -9.0, f"Latitud fuera de rango andino: {d['lat']}"
        assert -77.5 <= d["lng"] <= -68.5, f"Longitud fuera de rango andino: {d['lng']}"
        assert d["altitud_msnm"] >= 3000, f"Altitud inferior a umbral de heladas: {d['altitud_msnm']} m"
        assert d["cota_maxima_msnm"] > d["altitud_msnm"]
        
        # 3. Umbrales crioclimáticos SENAMHI
        assert d["umbral_helada_moderada_c"] == 0.0
        assert d["umbral_helada_severa_c"] <= -4.0
        assert d["umbral_helada_extrema_c"] <= -9.0
        assert d["record_historico_tmin_c"] <= d["umbral_helada_extrema_c"]
        assert "Estación" in d["estacion_senamhi_referencia"]
        
        # 4. Vulnerabilidad y censo pecuario y escolar
        assert d["poblacion_total_estimada"] > 0
        assert d["poblacion_vulnerable_ninos_ancianos"] > 0
        assert d["censo_camelidos_alpacas"] > 0
        assert d.get("colegios_vulnerables_sin_aislamiento", 0) > 0
        assert d.get("escolares_en_riesgo", 0) > 0
        
        # 5. Código táctico
        assert d["codigo_tactico_c2"].startswith("CHIRI-")

def test_aislamiento_total_frente_a_fen_quebradas():
    """Garantiza que el catálogo de heladas no altera ni contamina los datos del FEN"""
    assert os.path.exists(FEN_QUEBRADAS_PATH)
    with open(FEN_QUEBRADAS_PATH, "r", encoding="utf-8") as f:
        fen_data = json.load(f)
    
    assert len(fen_data) == 46, "El catálogo de quebradas FEN fue alterado"
    # Verificar que ninguna quebrada tiene códigos del módulo de heladas
    for q in fen_data:
        assert not str(q.get("id_quebrada", "")).startswith("CHIRI")
