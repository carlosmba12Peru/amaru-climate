import re
import os

class FileSanitizer:
    """
    Limpia y valida archivos multimedia (fotos de quebradas, audios SOS)
    subidos por la ciudadanía para prevenir inyecciones o exploits.
    """
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".m4a"}
    MAX_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
        return clean.strip('._')

    @classmethod
    def validate_file(cls, filename: str, file_size: int) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False
        if file_size > cls.MAX_SIZE_BYTES:
            return False
        return True
