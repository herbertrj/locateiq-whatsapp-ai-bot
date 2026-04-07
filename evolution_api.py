import logging

import requests

from config import (
    EVOLUTION_API_URL,
    EVOLUTION_INSTANCE_NAME,
    EVOLUTION_AUTHENTICATION_API_KEY,
)

logger = logging.getLogger(__name__)


def _normalize_evolution_number(jid_or_number: str) -> str:
    """Evolution sendText espera o número local"""
    if not jid_or_number or not str(jid_or_number).strip():
        return ""
    s = str(jid_or_number).strip()
    if "@" in s:
        return s.split("@", 1)[0]
    return s


def send_whatsapp_message(
    number: str,
    text: str,
    *,
    instance_name: str | None = None,
) -> bool:
    number = _normalize_evolution_number(number)
    if not number:
        logger.warning("sendText ignorado: número vazio após normalização")
        return False

    instance = (instance_name or EVOLUTION_INSTANCE_NAME or "").strip()
    if not instance:
        logger.error(
            "sendText ignorado: defina EVOLUTION_INSTANCE_NAME no .env ou use instance no webhook"
        )
        return False

    base = (EVOLUTION_API_URL or "").rstrip("/")
    url = f"{base}/message/sendText/{instance}"
    headers = {
        "apikey": EVOLUTION_AUTHENTICATION_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "number": number,
        "text": text,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
    except requests.RequestException as exc:
        logger.error("sendText falhou (rede): %s", exc)
        return False

    if resp.status_code >= 400:
        logger.error(
            "sendText Evolution HTTP %s URL=%s corpo=%s",
            resp.status_code,
            url,
            resp.text[:2000] if resp.text else "(sem corpo)",
        )
        return False

    return True
