import logging

from fastapi import FastAPI, Request

from evolution_api import send_whatapp_message

logging.basicConfig(level=logging.INFO)

app = FastAPI()


def _extract_incoming_text(message: dict) -> str | None:
    if not message:
        return None
    if message.get("conversation"):
        return message["conversation"]
    ext = message.get("extendedTextMessage") or {}
    if ext.get("text"):
        return ext["text"]
    return None


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    inner = data.get("data") or {}
    key = inner.get("key") or {}

    if key.get("fromMe"):
        return {"status": "ok"}

    chat_id = key.get("remoteJid")
    if chat_id and str(chat_id).endswith("@lid"):
        chat_id = key.get("remoteJidAlt") or chat_id

    message = _extract_incoming_text(inner.get("message") or {})

    if chat_id and message and "@g.us" not in str(chat_id):
        send_whatapp_message(
            number=chat_id,
            text=(
                "Estamos implementando I.A em nosso atendimento,\n"
                " pedimos um pouco de compreensão:\n"
                f" Voce me enviou {message}"
            ),
            instance_name=data.get("instance"),
        )

    return {"status": "ok"}
