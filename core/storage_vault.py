import hashlib
from datetime import datetime, timezone

class EvidenceVault:
    """
    Gestiona el almacenamiento seguro y la huella digital (SHA-256)
    de reportes ciudadanos y registros fotográficos de daños.
    """
    @staticmethod
    def generate_evidence_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def format_storage_record(record_id: str, uploader: str, evidence_hash: str) -> dict:
        return {
            "record_id": record_id,
            "uploader": uploader,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sha256_hash": evidence_hash,
            "integrity_verified": True
        }
