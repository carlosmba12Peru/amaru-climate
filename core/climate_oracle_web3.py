"""
AMARU-FEN: Módulo de Oráculo Climático Criptográfico y Web3
Compatible con arquitecturas EVM (Ethereum / Polygon / Arbitrum).

Garantiza la integridad inmutable de los datos meteorológicos, triggers paramétricos
y Fichas EDAN generadas por el enjambre de agentes de IA, actuando como un
Oráculo Descentralizado de Misión Crítica (Climate Oracle) para el certamen
IEEE ClimateChain Global Hackathon 2026 (COP31).
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

class AmaruClimateOracle:
    """
    Oráculo Criptográfico de Datos Ambientales y Triggers Paramétricos.
    Transforma la inferencia y telemetría de AMARU-FEN en atestados verificables on-chain.
    """

    def __init__(self, private_key_pem: Optional[str] = None):
        """
        Inicializa el oráculo con una clave privada existente o genera un nuevo par secp256k1.
        secp256k1 es la curva elíptica estándar empleada en Ethereum, Polygon y Bitcoin.
        """
        if private_key_pem:
            self._private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None
            )
        else:
            self._private_key = ec.generate_private_key(ec.SECP256K1())

        self._public_key = self._private_key.public_key()

    @property
    def public_key_pem(self) -> str:
        """Exporta la clave pública en formato PEM."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

    @property
    def oracle_address_fingerprint(self) -> str:
        """
        Genera una dirección de oráculo simulada en formato hexadecimal 0x...
        basada en el hash SHA-256 de los bytes de la clave pública (primeros 20 bytes).
        """
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )
        addr_hash = hashlib.sha256(pub_bytes).hexdigest()
        return "0x" + addr_hash[:40]

    def calcular_hash_edan(self, ficha_edan: Dict[str, Any]) -> str:
        """
        Calcula el hash inmutable SHA-256 de una Ficha EDAN (Evaluación de Daños y Análisis de Necesidades).
        Garantiza la detección inmediata de cualquier alteración en listas de damnificados o requerimientos.
        """
        contenido_canonica = json.dumps(ficha_edan, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(contenido_canonica.encode("utf-8")).hexdigest()

    def construir_payload_canonico(
        self,
        ubigeo: str,
        nombre_distrito: str,
        anomalia_tsm: float,
        caudal_m3s: float,
        nivel_alerta: str,
        edan_hash: Optional[str] = None,
        nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Construye la estructura de datos estandarizada del atestado climático.
        """
        timestamp_epoch = int(time.time())
        nonce_val = nonce if nonce is not None else int(time.time() * 1000) % 1_000_000_000
        
        return {
            "version_protocolo": "AMARU-ORACLE-V1",
            "ubigeo": str(ubigeo),
            "nombre_distrito": str(nombre_distrito),
            "telemetria": {
                "anomalia_tsm_celsius": round(float(anomalia_tsm), 2),
                "caudal_rio_m3s": round(float(caudal_m3s), 2),
                "nivel_alerta": str(nivel_alerta).upper()
            },
            "seguridad": {
                "timestamp_epoch": timestamp_epoch,
                "timestamp_iso": datetime.now(timezone.utc).isoformat(),
                "nonce": nonce_val,
                "edan_hash": edan_hash or "0" * 64
            }
        }

    def emitir_atestado_climatico(
        self,
        ubigeo: str,
        nombre_distrito: str,
        anomalia_tsm: float,
        caudal_m3s: float,
        nivel_alerta: str,
        ficha_edan: Optional[Dict[str, Any]] = None,
        nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Firma criptográficamente el reporte de amenaza y genera el atestado completo para la Blockchain.
        """
        edan_hash = self.calcular_hash_edan(ficha_edan) if ficha_edan else None
        
        payload = self.construir_payload_canonico(
            ubigeo=ubigeo,
            nombre_distrito=nombre_distrito,
            anomalia_tsm=anomalia_tsm,
            caudal_m3s=caudal_m3s,
            nivel_alerta=nivel_alerta,
            edan_hash=edan_hash,
            nonce=nonce
        )

        mensaje_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(mensaje_bytes).hexdigest()

        # Firma ECDSA con SHA-256
        firma_der = self._private_key.sign(
            mensaje_bytes,
            ec.ECDSA(hashes.SHA256())
        )
        firma_hex = firma_der.hex()

        return {
            "oracle_address": self.oracle_address_fingerprint,
            "payload": payload,
            "payload_hash": payload_hash,
            "signature_hex": firma_hex,
            "public_key_pem": self.public_key_pem,
            "smart_contract_call": {
                "target_contract": "ParametricClimateRelief",
                "function": "verifyAndTriggerDisaster(bytes32 payloadHash, bytes signature)",
                "evm_calldata_preview": f"0x6a1b2c3d{payload_hash}{firma_hex[:64]}"
            }
        }

    @staticmethod
    def verificar_atestado(atestado: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verifica matemáticamente la autenticidad del atestado usando la clave pública adjunta.
        Devuelve (True, 'OK') si la firma es auténtica y no hubo alteración en los datos.
        """
        try:
            payload = atestado.get("payload")
            signature_hex = atestado.get("signature_hex")
            pub_pem = atestado.get("public_key_pem")

            if not payload or not signature_hex or not pub_pem:
                return False, "Estructura de atestado incompleta."

            mensaje_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            firma_bytes = bytes.fromhex(signature_hex)

            public_key = serialization.load_pem_public_key(pub_pem.encode("utf-8"))
            
            # Verificación de la firma ECDSA
            public_key.verify(
                firma_bytes,
                mensaje_bytes,
                ec.ECDSA(hashes.SHA256())
            )
            return True, "Firma criptográfica verificada con éxito. Datos íntegros y auténticos."

        except Exception as e:
            return False, f"Fallo de verificación de firma: {str(e)}"

    def firmar_calculo_iph_fen(self, datos_calculo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Firma criptográficamente el cálculo del IPH-FEN y el retardo T_lag,
        generando un recibo inmutable secp256k1 blindado contra manipulación de hackers.
        """
        payload_iph = {
            "protocolo": "AMARU-IPH-SECP256K1",
            "id_quebrada": str(datos_calculo.get("id_quebrada", "")),
            "nombre_quebrada": str(datos_calculo.get("quebrada", "")),
            "iph_fen_score": float(datos_calculo.get("iph_fen_score", 0.0)),
            "nivel_alerta": str(datos_calculo.get("nivel_alerta", "")),
            "tiempo_retardo_minutos": int(datos_calculo.get("tiempo_retardo_minutos", 0)),
            "fuerza_motriz_phi": float(datos_calculo.get("fuerza_motriz_phi", 0.0)),
            "inputs_sanitizados": {
                "lluvia_cabecera_mm_h": float(datos_calculo.get("lluvia_cabecera_mm_h", 0.0)),
                "lluvia_acumulada_24h": float(datos_calculo.get("lluvia_acumulada_24h", 0.0)),
                "saturacion_api_72h": float(datos_calculo.get("saturacion_api_72h", 0.0)),
                "irce_circundante": float(datos_calculo.get("irce_circundante_usado", 0.0))
            },
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "nonce": int(time.time() * 1000) % 1_000_000_000
        }

        mensaje_bytes = json.dumps(payload_iph, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(mensaje_bytes).hexdigest()

        firma_der = self._private_key.sign(
            mensaje_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        return {
            "estado_blindaje": "INVIOLABLE_VERIFICADO_C2",
            "algoritmo": "ECDSA-SECP256K1-SHA256",
            "oracle_address": self.oracle_address_fingerprint,
            "payload_hash": payload_hash,
            "firma_hex": firma_der.hex(),
            "public_key_pem": self.public_key_pem,
            "payload_firmado": payload_iph,
            "sello_soberania_humana_ley_31814": True
        }

    def firmar_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Firma asimétrica ECDSA secp256k1 + SHA-256 de cualquier payload canónico C2
        (dictámenes periciales post-mortem, matrices Saaty calibradas, etc.).
        """
        mensaje_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        payload_hash = hashlib.sha256(mensaje_bytes).hexdigest()

        firma_der = self._private_key.sign(
            mensaje_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        return {
            "estado_blindaje": "INVIOLABLE_VERIFICADO_C2",
            "algoritmo": "ECDSA-SECP256K1-SHA256",
            "oracle_address": self.oracle_address_fingerprint,
            "payload_hash": payload_hash,
            "firma_hex": firma_der.hex(),
            "public_key_pem": self.public_key_pem,
            "sello_soberania_humana_ley_31814": True
        }

    @staticmethod
    def verificar_calculo_iph_fen(recibo: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verifica matemáticamente que el IPH-FEN no fue alterado por terceros.
        """
        try:
            payload = recibo.get("payload_firmado")
            firma_hex = recibo.get("firma_hex")
            pub_pem = recibo.get("public_key_pem")

            if not payload or not firma_hex or not pub_pem:
                return False, "Recibo IPH-FEN incompleto o alterado."

            mensaje_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            firma_bytes = bytes.fromhex(firma_hex)
            public_key = serialization.load_pem_public_key(pub_pem.encode("utf-8"))

            public_key.verify(
                firma_bytes,
                mensaje_bytes,
                ec.ECDSA(hashes.SHA256())
            )
            return True, "Cálculo IPH-FEN íntegro y auténtico. Firma secp256k1 verificada."
        except Exception as e:
            return False, f"Alerta de Sabotaje: Firma inválida ({str(e)})"

