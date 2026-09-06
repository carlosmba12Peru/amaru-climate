import pytest
from core.edan_normalizer import FichaEDAN, EvaluacionDanosInfraestructura

def test_ficha_edan_creation():
    ficha = FichaEDAN(
        id_ficha="EDAN-TEST-001",
        departamento="Piura",
        provincia="Piura",
        distrito="Catacaos",
        localidad_o_sector="Sector Pedregal Grande",
        tipo_evento="Inundacion",
        nivel_severidad="CRITICA",
        origen_reporte="VOZ_VAPI",
        personas_atrapadas=5,
        danos_infraestructura=EvaluacionDanosInfraestructura(
            viviendas_colapsadas=12,
            puentes_destruidos=1
        ),
        necesidades_urgentes=["Botes de rescate", "Agua potable"],
        entidades_notificadas=["COEN", "PNP_RESCATE", "EJERCITO"]
    )
    assert ficha.departamento == "Piura"
    assert ficha.personas_atrapadas == 5
    assert ficha.danos_infraestructura.viviendas_colapsadas == 12
    assert "COEN" in ficha.entidades_notificadas
    assert ficha.estado_gestion == "REGISTRADO"
