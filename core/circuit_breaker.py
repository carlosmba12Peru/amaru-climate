import time
import logging
from typing import Callable, Any

logger = logging.getLogger("AMARU.CircuitBreaker")

class LLMCircuitBreaker:
    """
    Protege el sistema contra caídas del API de Gemini, cuotas excedidas
    o latencias altas durante picos de emergencia de lluvias.
    """
    def __init__(self, failure_threshold: int = 3, recovery_time: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()
        
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_time:
                logger.info("Circuit Breaker pasando a HALF-OPEN para probar recuperación.")
                self.state = "HALF-OPEN"
            else:
                logger.warning("Circuit Breaker OPEN. Activando fallback local determinista.")
                return self._fallback_response(*args, **kwargs)

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF-OPEN":
                logger.info("Llamada exitosa. Restaurando Circuit Breaker a CLOSED.")
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            logger.error(f"Falla detectada en llamada LLM ({self.failure_count}/{self.failure_threshold}): {e}")
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.critical(f"Umbral de fallas superado. Circuit Breaker pasa a OPEN por {self.recovery_time}s.")
            return self._fallback_response(*args, **kwargs)

    def _fallback_response(self, *args, **kwargs):
        return {
            "status": "FALLBACK_OPERATIVO",
            "message": "Operación ejecutada con heurística de resiliencia local ante alta saturación de red.",
            "is_emergency": True,
            "priority": "ALTA"
        }
