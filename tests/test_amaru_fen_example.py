import pytest
from agents.agente_legal_normativo import AgenteLegalNormativo


def test_agente_legal_normativo_loads_data():
    """Verify that the AgenteLegalNormativo loads its data files without error.

    The test checks that the catalogue of norms and the FONDES district list are
    populated (or at least initialized) after the agent is instantiated.
    """
    agente = AgenteLegalNormativo()
    # The internal structures should be lists/dicts even if the underlying JSON
    # files are empty – the loading logic defaults to empty collections on error.
    assert isinstance(agente.catalogo_normas, list), "catalogo_normas should be a list"
    assert isinstance(agente.distritos_fondes_1891, list), "distritos_fondes_1891 should be a list"
    # The public method should return the same list reference.
    normas = agente.consultar_normas_vigentes()
    assert normas is agente.catalogo_normas


def test_consultar_distrito_riesgo_fondes_basic_query():
    """Run a simple query against the FONDES district lookup.

    We use a very short, generic term that will match at least one district if
    the dataset is present. The expected return structure must contain the keys
    defined in the agent implementation.
    """
    agente = AgenteLegalNormativo()
    result = agente.consultar_distrito_riesgo_fondes("LIMA")
    # Ensure the result dictionary contains the expected top‑level keys.
    expected_keys = {
        "agente",
        "termino_consultado",
        "departamento_filtro",
        "total_coincidencias",
        "coincidencias",
        "marco_normativo",
        "fuentes_sustento",
        "total_distritos_pais",
    }
    assert expected_keys.issubset(result.keys())
    # total_coincidencias should be an int and coincidencias a list.
    assert isinstance(result["total_coincidencias"], int)
    assert isinstance(result["coincidencias"], list)
