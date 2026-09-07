# test_telegram.py
import os
import sys

# Ensure stdout can handle UTF-8 on Windows (prevents UnicodeEncodeError)
sys.stdout.reconfigure(encoding='utf-8')

from core.telegram_notifier import TelegramNotifier

# ---------- Amaru‑Fen ----------
tn_fen = TelegramNotifier(
    token=os.getenv('TELEGRAM_BOT_TOKEN_FEN'),
    chat_id=os.getenv('TELEGRAM_CHAT_ID_FEN')
)
print('Fen →', tn_fen.enviar_mensaje_telegram('🚀 *Prueba* – Bot **Amaru‑Fen IA ‑ Alertas** activo.'))

# ---------- Amaru‑Chiri ----------
tn_chiri = TelegramNotifier(
    token=os.getenv('TELEGRAM_BOT_TOKEN_CHIRI'),
    chat_id=os.getenv('TELEGRAM_CHAT_ID_CHIRI')
)
print('Chiri →', tn_chiri.enviar_mensaje_telegram('🚀 *Prueba* – Bot **Amaru‑Chiri IA ‑ Alertas** activo.'))
