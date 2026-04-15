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


def _presence_number_candidates(jid_or_number: str) -> list[str]:
    """
    Algumas instalações aceitam JID (@s.whatsapp.net) e outras apenas número.
    Tentamos ambos formatos para aumentar compatibilidade.
    """
    s = str(jid_or_number or "").strip()
    if not s:
        return []
    normalized = _normalize_evolution_number(s)
    candidates: list[str] = []
    for n in (s, normalized):
        if n and n not in candidates:
            candidates.append(n)
    return candidates


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


def send_whatsapp_presence(
    number: str,
    *,
    presence: str,
    delay_ms: int = 2000,
    instance_name: str | None = None,
) -> bool:
    """
    Envia presença para o chat (ex.: composing/recording).
    Endpoint Evolution v2: POST /chat/sendPresence/{instance}
    """
    candidates = _presence_number_candidates(number)
    if not candidates:
        logger.warning("sendPresence ignorado: número vazio após normalização")
        return False

    instance = (instance_name or EVOLUTION_INSTANCE_NAME or "").strip()
    if not instance:
        logger.error(
            "sendPresence ignorado: defina EVOLUTION_INSTANCE_NAME no .env ou use instance no webhook"
        )
        return False

    base = (EVOLUTION_API_URL or "").rstrip("/")
    url = f"{base}/chat/sendPresence/{instance}"
    headers = {
        "apikey": EVOLUTION_AUTHENTICATION_API_KEY,
        "Content-Type": "application/json",
    }
    delay = max(0, int(delay_ms))
    for candidate in candidates:
        payload_variants = [
            # Formato aceito em instalações como a sua (v2.3.7): campos na raiz
            {
                "number": candidate,
                "presence": presence,
                "delay": delay,
            },
            # Fallback para docs v2 com options
            {
                "number": candidate,
                "options": {
                    "delay": delay,
                    "presence": presence,
                    "number": candidate,
                },
            },
        ]

        for payload in payload_variants:
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=30)
            except requests.RequestException as exc:
                logger.error("sendPresence falhou (rede) number=%s: %s", candidate, exc)
                continue

            if resp.status_code < 400:
                logger.info(
                    "sendPresence OK number=%s presence=%s delay=%sms formato=%s",
                    candidate,
                    presence,
                    delay,
                    "root" if "presence" in payload else "options",
                )
                return True

            logger.warning(
                "sendPresence Evolution HTTP %s URL=%s number=%s presence=%s formato=%s corpo=%s",
                resp.status_code,
                url,
                candidate,
                presence,
                "root" if "presence" in payload else "options",
                resp.text[:1000] if resp.text else "(sem corpo)",
            )

    return False


def start_typing(number: str, *, instance_name: str | None = None) -> bool:
    return send_whatsapp_presence(
        number,
        presence="composing",
        delay_ms=5000,
        instance_name=instance_name,
    )


def stop_typing(number: str, *, instance_name: str | None = None) -> bool:
    # A documentação v2 aceita apenas composing/recording.
    # Para "parar", enviamos composing com delay zero.
    return send_whatsapp_presence(
        number,
        presence="composing",
        delay_ms=0,
        instance_name=instance_name,
    )
