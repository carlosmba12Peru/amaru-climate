import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class AmaruSettings(BaseSettings):
    APP_NAME: str = "AMARU-FEN"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = "gemini-2.5-flash"
    FAST_MODEL: str = "gemini-2.5-flash"
    
    # Vapi AI
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_ASSISTANT_ID: str = os.getenv("VAPI_ASSISTANT_ID", "")
    
    # Despachos
    WEBHOOK_COEN: str = os.getenv("WEBHOOK_COEN_INDECI", "https://httpbin.org/post")
    WEBHOOK_PNP: str = os.getenv("WEBHOOK_PNP_RESCATE", "https://httpbin.org/post")
    WEBHOOK_EJERCITO: str = os.getenv("WEBHOOK_EJERCITO_PERUANO", "https://httpbin.org/post")
    
    # Umbrales Meteorológicos Críticos (mm/24h)
    UMBRAL_LLUVIA_AMARILLO: float = 20.0
    UMBRAL_LLUVIA_NARANJA: float = 40.0
    UMBRAL_LLUVIA_ROJO: float = 70.0

settings = AmaruSettings()
