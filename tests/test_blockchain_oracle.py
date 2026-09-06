"""
Pruebas Unitarias para el Oráculo Climático Criptográfico de AMARU-FEN.
Certamen: IEEE ClimateChain Global Hackathon 2026 (COP31).
"""

import pytest
import json
from core.climate_oracle_web3 import AmaruClimateOracle

def test_oracle_initialization_and_fingerprint():
    oracle = AmaruClimateOracle()
    assert oracle.public_key_pem is not None
    assert oracle.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert oracle.oracle_address_fingerprint.startswith("0x")
    assert len(oracle.oracle_address_fingerprint) == 42

def test_emit_and_verify_climate_attestation():
    oracle = AmaruClimateOracle()
    
    ficha_edan_mock = {
        "distrito": "Catacaos",
        "ubigeo": "200105",
        "poblacion_afectada": 12500,
        "viviendas_colapsadas": 450,
        "necesidad_carpas": 300,
        "necesidad_agua_litros": 25000
    }

    atestado = oracle.emitir_atestado_climatico(
        ubigeo="200105",
        nombre_distrito="Catacaos",
        anomalia_tsm=2.35,
        caudal_m3s=2150.0,
        nivel_alerta="ROJA",
        ficha_edan=ficha_edan_mock,
        nonce=1001
    )

    assert atestado["payload"]["ubigeo"] == "200105"
    assert atestado["payload"]["telemetria"]["caudal_rio_m3s"] == 2150.0
    assert atestado["payload"]["telemetria"]["nivel_alerta"] == "ROJA"
    assert len(atestado["payload"]["seguridad"]["edan_hash"]) == 64
    assert atestado["signature_hex"] is not None

    # Verificación matemática
    valido, mensaje = AmaruClimateOracle.verificar_atestado(atestado)
    assert valido is True
    assert "verificada con éxito" in mensaje

def test_tampered_payload_fails_verification():
    oracle = AmaruClimateOracle()
    
    atestado = oracle.emitir_atestado_climatico(
        ubigeo="200105",
        nombre_distrito="Catacaos",
        anomalia_tsm=1.8,
        caudal_m3s=1950.0,
        nivel_alerta="ROJA",
        nonce=2002
    )

    # Intento de manipulación fraudulenta de datos (cambio de caudal)
    atestado["payload"]["telemetria"]["caudal_rio_m3s"] = 500.0

    valido, mensaje = AmaruClimateOracle.verificar_atestado(atestado)
    assert valido is False
    assert "Fallo de verificación" in mensaje

def test_edan_hash_immutability():
    oracle = AmaruClimateOracle()
    
    ficha_original = {
        "ubigeo": "200105",
        "familias_damnificadas": 120,
        "raciones_alimento": 500
    }
    
    hash_1 = oracle.calcular_hash_edan(ficha_original)
    assert len(hash_1) == 64

    # Mismo contenido debe dar idéntico hash
    hash_2 = oracle.calcular_hash_edan(dict(ficha_original))
    assert hash_1 == hash_2

    # Cualquier alteración en una cifra altera el hash
    ficha_alterada = dict(ficha_original)
    ficha_alterada["familias_damnificadas"] = 999
    hash_alterado = oracle.calcular_hash_edan(ficha_alterada)
    assert hash_1 != hash_alterado
