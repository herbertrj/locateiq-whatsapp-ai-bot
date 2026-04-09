# Chatbot de atendimento no WhatsApp com RAG

Repositório de um **projeto de automação de atendimento**: responder gente no **WhatsApp** com **IA**, mas puxando resposta de **documentos** (PDF, texto) pra não ficar no vácuo inventando coisa. Stack: **RAG**, **Docker**, **LangChain**, **Evolution API**.

Sou **estudante**, curto tecnologia e montei isso pra **aprender na prática** — infra, integração, vector store — além da parte só de teoria.

Não é pitch comercial: é código que eu fui quebrando e consertando. Se você caiu aqui de paraquedas: abaixo tem **qual é o problema**, **o que usei**, **por que** e **como rodar**.

---

## Qual problema isso tenta resolver

Em **atendimento por WhatsApp** o padrão é sempre o mesmo: pico de mensagem, horário ruim, **demora pra responder** e o cliente some. Mensagem automática genérica quase não ajuda; modelo que **inventa** detalhe de produto/serviço é furada.

A ideia é **responder automático** com base em **material indexado** (PDF, texto) e ainda **lembrar o contexto** da conversa. Por isso **RAG**: antes de gerar, o sistema **busca trecho** relevante e só depois chama a OpenAI.

---

## Fluxo (sem jargão demais)

1. Cliente manda mensagem no WhatsApp.
2. **Evolution API** (instância configurada no painel) dispara evento e bate no **`POST /webhook`** do Python.
3. **FastAPI** lê o JSON, pega o texto e o id do chat.
4. Entra a **chain LangChain**: histórico no **Redis**, busca no **Chroma** (embeddings OpenAI), modelo gera a resposta.
5. O backend chama a Evolution de novo pra **devolver o texto** pro número.

**Postgres** tá no compose porque a **imagem da Evolution** precisa de banco pra estado/metadata. **Redis** a Evolution usa pra cache etc.; no bot, guarda **histórico** do LangChain.

---

## Stack (e por que não outra coisa)

**Python 3.13** — Versão do `Dockerfile`; equilíbrio entre coisa nova e LangChain não ficar no limbo.

**FastAPI** — Webhook leve, async, já nasce com doc OpenAPI.

**Uvicorn** — ASGI no container; par clássico com FastAPI.

**Docker + Compose** — Um `docker compose up` sobe Evolution, Postgres, Redis e o bot na **mesma rede**, com **volume** pra instância, banco, arquivos RAG e pasta do Chroma. Ambiente **repetível** em outra máquina.

**Dockerfile do bot** — Copia `requirements.txt`, instala deps, copia código, porta 8000, sobe Uvicorn. Sem firula.

**Evolution (evoapicloud)** — WhatsApp via HTTP JSON; por baixo Baileys. Aqui o foco é **encaixar IA + RAG + memória**, não reescrever cliente.

**PostgreSQL 15** — Evolution pede; subi `max_connections` no compose pra não sofrer com muita conexão.

**Redis** — Evolution + no bot o histórico `RedisChatMessageHistory` com `session_id` = JID.

**LangChain** (`langchain-core`, `langchain-classic`, `langchain-openai`, etc.) — History-aware retriever + stuff documents + retrieval chain + `RunnableWithMessageHistory`, padrão que aparece em tutorial e projeto real.

**OpenAI** — Chat + embeddings num lugar só; menos chave pra gerenciar.

**Chroma** — Vetor em disco (`persist_directory`), simples pra escopo desse projeto. Dados em `vectorstore_data` (montado no container).

**PyPDF + loaders** — Ingere PDF/TXT de `rag_files/`; o que for processado cai em `rag_files/processed` (`.gitignore` pra não poluir o Git).

**Requests** — `evolution_api.py` faz `POST` no `sendText` com `apikey` no header; debug é olhar status/corpo.

**python-dotenv** — Tudo sensível no `.env`. **Não commitar.**

---

## Pastas / arquivos

```
├── app.py              # FastAPI: webhook + chain + WhatsApp
├── chains.py           # RAG conversacional
├── message_buffer.py   # Buffer de mensagens (debounce no Redis) — use no webhook se quiser agrupar rajadas
├── prompts.py          # Prompts de sistema
├── vectorstore.py      # Docs → chunks → Chroma
├── memory.py           # Histórico Redis por sessão
├── evolution_api.py    # Envia texto pela Evolution
├── config.py           # Lê .env
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── rag_files/          # Joga PDF/TXT aqui pra indexar
└── vectorstore_data/   # Chroma no disco (não vai pro Git)
```

---

## Antes de rodar

- Docker + Docker Compose
- Conta OpenAI (API key)
- Instância na Evolution com webhook apontando pro bot
- `.env` na raiz (nomes das variáveis estão no `config.py`; não tem `.env.example` de propósito)

### Variáveis que o `config.py` lê

| Variável | Pra quê |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI |
| `OPENAI_MODEL_NAME` | Modelo de chat |
| `OPENAI_MODEL_TEMPERATURE` | Temperatura |
| `AI_CONTEXTUALIZE_PROMPT` | Reformula pergunta com histórico |
| `AI_SYSTEM_PROMPT` | Instruções; o QA precisa de `{context}` |
| `VECTOR_STORE_PATH` | Pasta Chroma (no Docker uso `/app/vectorstore`) |
| `RAG_FILES_DIRS` | Docs (no Docker `/app/rag_files`) — o código usa `RAG_FILES_DIR` |
| `EVOLUTION_API_URL` | Base da API (`http://evolution-api:8080` dentro do compose) |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância |
| `AUTHENTICATION_API_KEY` | Header `apikey` |
| `CACHE_REDIS_URI` | Redis (ex. `redis://redis:6379`) |
| `BUFFER_KEY_SUFIX` | (opcional) sufixo da chave do buffer; default `:msgbuf` |
| `DEBOUNCE_SECONDS` | (opcional) espera após última msg; default 3 (aceita typo `DEBALANCE_SECONDS`) |
| `BUFFER_TTL` | (opcional) TTL da lista no Redis; default 600 |

Doc Evolution: [Evolution API v2](https://doc.evolution-api.com/).

---

## Subir tudo

```bash
docker compose up --build
```

Portas usuais:

- Evolution: `http://localhost:8080`
- Bot: `http://localhost:8000`
- Postgres: `5432`
- Redis: `6379`

Senha `postgres` no compose é só dev; produção muda isso.

### Só o bot na máquina (sem Docker)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

A Evolution precisa conseguir chamar o webhook. Se não for na mesma rede/túnel, vira ngrok ou URL pública.

---

## Testar

**1.** `http://localhost:8000/docs` — Swagger; o que importa é `POST /webhook`.

**2.** JSON fake parecido com Evolution — Swagger ou PowerShell:

```bash
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"data\":{\"key\":{\"remoteJid\":\"5511999999999@s.whatsapp.net\"},\"message\":{\"conversation\":\"Olá, teste\"}}}"
```

No Linux/macOS o escape muda; na dúvida usa o `/docs`.

Se chain + Redis + Chroma + OpenAI tiverem ok, aparece coisa no terminal e (Evolution ligada) mensagem no Zap. Erro → log do container `bot`.

**3.** Teste de verdade: instância conectada, webhook tipo `http://bot:8000/webhook` no compose (ou URL pública).

**4.** Logs: `docker compose logs -f bot`

**5.** RAG: PDF/TXT em `rag_files/` (fora de `processed`), reinicia ou recarrega conforme teu `vectorstore.py`. Primeira vez demora (embedding + Chroma).

---

## Limitações

`app.py` hoje só trata `conversation` direto. Áudio, imagem, `extendedTextMessage` → ainda não.

Sem filtro `fromMe` em alguns webhooks pode dar eco; vale checar na Evolution.

---

## Segurança

`.env` fora do Git. Rotaciona chave se vazou. Não deixa Postgres/API aberto na internet sem proteção.

---

## Fechando

Projeto de **atendimento com RAG** e stack que dá pra subir de novo em outro PC. Também foi treino de compose, memória de conversa e WhatsApp. Dúvida sobre o repo, chama.

— Herbert
