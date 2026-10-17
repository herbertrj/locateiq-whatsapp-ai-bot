[# Chatbot de atendimento no WhatsApp com RAG

Bot que responde no **WhatsApp** usando **IA**, mas com respostas baseadas em **documentos** (PDF, texto) para não inventar informação. Usei **RAG**, **Docker**, **LangChain** e a **Evolution API**.

Sou estudante; montei o projeto para estudar na prática integração, Docker e vector store.

---

## O que o projeto faz

Em atendimento por WhatsApp costuma faltar gente no horário de pico, a resposta atrasa e o cliente desiste. Resposta genérica não resolve; modelo que inventa detalhe de produto ou serviço é arriscado.

Aqui a ideia é responder com base em material que você indexa (PDF, texto) e manter um mínimo de contexto da conversa. Por isso o **RAG**: o sistema busca trechos relevantes antes de mandar o pedido para a OpenAI.

---

## Como funciona (passo a passo)

1. Alguém manda mensagem no WhatsApp.
2. A **Evolution API** chama o **`POST /webhook`** do serviço em Python.
3. O **FastAPI** lê o JSON e extrai o texto e o identificador do chat.
4. O **buffer** (`message_buffer.py`) junta mensagens em sequência com debounce no **Redis**; depois disso roda a chain.
5. A **chain** (LangChain) usa histórico no **Redis**, busca no **Chroma** e gera a resposta.
6. O backend chama a Evolution de novo para enviar o texto de volta.

O **Postgres** no compose existe porque a imagem da Evolution precisa de banco. O **Redis** serve à Evolution e, no bot, guarda histórico e a fila do buffer.

---

## O que tem no repositório

```
├── app.py              # Webhook FastAPI
├── chains.py           # Chain RAG conversacional
├── message_buffer.py   # Buffer + debounce no Redis
├── prompts.py          # Prompts
├── vectorstore.py      # Documentos → Chroma
├── memory.py           # Histórico por sessão (Redis)
├── evolution_api.py    # Chamadas HTTP à Evolution (texto, presença etc.)
├── config.py           # Variáveis de ambiente
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── rag_files/          # PDF/TXT para indexar
└── vectorstore_data/   # Chroma em disco (não versionar)
```

---

## Requisitos

- Docker e Docker Compose
- Conta OpenAI (API key)
- Instância na Evolution com webhook apontando para este serviço
- Arquivo `.env` na raiz (os nomes das variáveis estão no `config.py`; não incluí `.env.example` no repo)

---

## Variáveis de ambiente (resumo)

| Variável | Uso |
|----------|-----|
| `OPENAI_API_KEY` | OpenAI |
| `OPENAI_MODEL_NAME` | Modelo de chat |
| `OPENAI_MODEL_TEMPERATURE` | Temperatura |
| `AI_CONTEXTUALIZE_PROMPT` | Prompt de contextualização com histórico |
| `AI_SYSTEM_PROMPT` | Instruções do assistente; o QA precisa de `{context}` |
| `VECTOR_STORE_PATH` | Pasta do Chroma (no Docker costumo usar `/app/vectorstore`) |
| `RAG_FILES_DIRS` | Pasta dos docs (no Docker `/app/rag_files`); no código vira `RAG_FILES_DIR` |
| `EVOLUTION_API_URL` | URL base da Evolution (no compose: `http://evolution-api:8080`) |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância |
| `AUTHENTICATION_API_KEY` | Header `apikey` |
| `CACHE_REDIS_URI` | Redis (ex.: `redis://redis:6379`) |
| `BUFFER_KEY_SUFIX` | Opcional; sufixo da chave do buffer no Redis (padrão `:msgbuf`) |
| `DEBOUNCE_SECONDS` | Opcional; segundos após a última mensagem antes de processar (padrão 5; aceita `DEBALANCE_SECONDS` se estiver errado no .env) |
| `BUFFER_TTL` | Opcional; TTL da lista no Redis em segundos (padrão 600) |

Documentação da Evolution: [Evolution API v2](https://doc.evolution-api.com/).

---

## Rodar com Docker

Na raiz:

```bash
docker compose up --build
```

Portas comuns no compose:

- Evolution: `http://localhost:8080`
- Bot: `http://localhost:8000`
- Postgres: `5432`
- Redis: `6379`

A senha do Postgres no compose está simples só para desenvolvimento; em produção troque.

---

## Rodar só o bot (sem Docker)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

A Evolution precisa alcançar o webhook (mesma rede, túnel ou ngrok se estiver fora).

---

## Testar

Abra `http://localhost:8000/docs` e use o `POST /webhook`.

Exemplo de corpo (PowerShell, uma linha):

```bash
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"data\":{\"key\":{\"remoteJid\":\"5511999999999@s.whatsapp.net\"},\"message\":{\"conversation\":\"Olá, teste\"}}}"
```

Com o buffer ativo, a resposta só sai depois do tempo de debounce sem nova mensagem para aquele contato. Se algo der errado, olhe `docker compose logs -f bot`.

---

## Limitações do código

O `app.py` trata principalmente mensagens com campo `conversation`. Áudio, imagem e `extendedTextMessage` ainda não entram no fluxo.

Não há filtro `fromMe`; em alguns webhooks pode aparecer eco — vale conferir na Evolution.

---

## Segurança

Não commite o `.env`. Troque chaves se vazarem. Não exponha Postgres nem API à internet sem controle de acesso.

---

## Autor

Herbert
](https://github.com/herbertrj/ChatBot_LocateIQ)
