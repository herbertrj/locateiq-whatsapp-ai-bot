# Chatbot de atendimento no WhatsApp com RAG

Este repositório é um **projeto de automação de atendimento**: a ideia é responder quem escreve no **WhatsApp** com ajuda de **IA**, mas puxando respostas de **documentos** (PDF, texto) em vez de deixar o modelo inventar tudo. Usei **RAG**, **Docker**, **LangChain** e a **Evolution API** para ligar o canal ao backend.

Sou **estudante**, gosto de tecnologia e fiz isso para **aprender na prática** — infraestrutura, integrações, vector store — além do que aparece só na teoria.

Não é apresentação comercial: é código que foi escrito, testado e corrigido várias vezes. Se você está avaliando o repositório, aqui está **que problema isso resolve**, **a stack**, **por quê** e **como testar**.

---

## Que problema isso tenta resolver

Em **atendimento por WhatsApp** o padrão se repete: picos de mensagens, horários em que ninguém está disponível, **atraso na resposta** e quem está do outro lado desiste. Respostas fixas do tipo “já vamos responder” pouco ajudam; um modelo que **inventa** dados sobre produto ou serviço é perigoso.

O objetivo deste projeto é **automatizar respostas** com base em **material de apoio indexado** (PDF, texto), mantendo **contexto da conversa**. Daí o **RAG**: antes de gerar texto, o sistema **recupera trechos** relevantes e só depois manda o pedido ao modelo da OpenAI.

---

## O fluxo em linguagem humana

1. O cliente manda mensagem no WhatsApp.
2. A **Evolution API** (instância WhatsApp configurada no painel) dispara um evento e chama o **`POST /webhook`** do serviço Python.
3. O **FastAPI** recebe o JSON, extrai o texto e o identificador do chat.
4. Entra a **chain do LangChain**: histórico no **Redis**, busca semântica no **Chroma** (feita com embeddings da OpenAI), depois o **modelo de chat** gera a resposta.
5. O mesmo backend chama de novo a Evolution para **enviar o texto** de volta ao número.

O **Postgres** na stack existe porque a **imagem da Evolution** precisa de banco de dados para estado e metadados. O **Redis** serve à Evolution e, no bot, guarda o **histórico de mensagens** do LangChain.

---

## Tecnologias que usei e o porquê de cada uma

**Python 3.13** — Versão definida no `Dockerfile`, equilíbrio entre recursos recentes e compatibilidade com o ecossistema LangChain.

**FastAPI** — Framework leve para o webhook, com suporte async e documentação OpenAPI gerada automaticamente.

**Uvicorn** — Servidor ASGI no `Dockerfile` / comando do container; uso habitual com FastAPI.

**Docker + Docker Compose** — **Um comando** para subir Evolution API, Postgres, Redis e o serviço do bot na **mesma rede**, com **volumes** para instância WhatsApp, banco de dados, arquivos RAG e pasta do Chroma. Assim o ambiente fica **reproduzível** entre máquinas.

**Dockerfile do bot** — Copia `requirements.txt`, instala dependências, copia o código, expõe a porta 8000 e sobe o Uvicorn. Simples de propósito.

**Evolution API (imagem evoapicloud)** — Abstrai a ligação ao protocolo WhatsApp: entra **HTTP** com JSON e sai **HTTP** para enviar mensagem. Por baixo usa Baileys; o foco do projeto é **orquestrar IA, RAG e histórico**, não reimplementar o cliente WhatsApp.

**PostgreSQL 15** — Vem no `docker-compose` porque a Evolution precisa. Ajustei `max_connections` no compose para evitar dor de cabeça quando há muitas conexões.

**Redis** — Cache e outras funções internas da Evolution; no bot, **Redis** guarda o histórico via `RedisChatMessageHistory` do LangChain, com `session_id` alinhado ao JID do WhatsApp.

**LangChain** (vários pacotes: `langchain-core`, `langchain-classic`, `langchain-openai`, `langchain-community`, `langchain-chroma`, `langchain-text-splitters`) — Agrega o fluxo **history-aware retriever** + **stuff documents** + **retrieval chain** + **RunnableWithMessageHistory**, padrão comum em tutoriais e projetos reais de RAG conversacional.

**OpenAI** — `ChatOpenAI` para a resposta final e `OpenAIEmbeddings` para transformar texto em vetor e pesquisar no Chroma. Uma API só para os dois papéis simplifica contas e chaves.

**Chroma** — Base vetorial em disco (`persist_directory`), integrada ao LangChain. É **simples de operar** num projeto desta escala, sem serviço vetorial externo desde o primeiro dia. Os dados ficam em `vectorstore_data` (montada no container).

**PyPDF + loaders do LangChain** — Para ingerir PDF e TXT da pasta `rag_files`. Os arquivos processados vão para `rag_files/processed` (e essa pasta está no `.gitignore` para não ir lixo para o Git).

**Requests** — No `evolution_api.py`, `POST` ao endpoint `sendText` da Evolution com `apikey` no header; fácil de inspecionar em caso de erro.

**python-dotenv** — Todas as chaves e URLs vêm do arquivo `.env`. Nunca faça commit disso.

---

## Organização do repositório

```
├── app.py              # FastAPI: webhook + chamada à chain + envio WhatsApp
├── chains.py           # Montagem da cadeia RAG conversacional
├── prompts.py          # Templates de sistema (contextualização e resposta)
├── vectorstore.py      # Carregar docs, partir em chunks, Chroma + embeddings
├── memory.py           # Histórico Redis por sessão
├── evolution_api.py    # Cliente HTTP para enviar texto pela Evolution
├── config.py           # Leitura das variáveis de ambiente
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── rag_files/          # Coloque aqui PDF/TXT para indexar
└── vectorstore_data/   # Onde o Chroma guarda os vetores (não vai para o Git)
```

---

## O que você precisa antes de começar

- **Docker** e **Docker Compose** instalados.
- Conta **OpenAI** com API key.
- Instância configurada na **Evolution API** (QR code, webhook apontando para o seu bot).
- Arquivo **`.env`** na raiz (crie a partir dos nomes no `config.py`; não há exemplo no repositório de propósito para não vazar estrutura de secrets).

### Variáveis que o `config.py` espera (nomes para copiar)

| Variável | Para quê |
|----------|----------|
| `OPENAI_API_KEY` | Chamadas à OpenAI |
| `OPENAI_MODEL_NAME` | Modelo de chat |
| `OPENAI_MODEL_TEMPERATURE` | Temperatura (número) |
| `AI_CONTEXTUALIZE_PROMPT` | Prompt que reformula pergunta com histórico |
| `AI_SYSTEM_PROMPT` | Instruções do assistente; o template de QA precisa de `{context}` para o RAG |
| `VECTOR_STORE_PATH` | Pasta do Chroma (no Docker costumo usar `/app/vectorstore`) |
| `RAG_FILES_DIRS` | Pasta dos documentos (no Docker `/app/rag_files`) — sim, o nome no env é esse, o código guarda em `RAG_FILES_DIR` |
| `EVOLUTION_API_URL` | URL base da API (dentro do Docker: `http://evolution-api:8080`) |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância na Evolution |
| `AUTHENTICATION_API_KEY` | Mesma lógica da documentação da Evolution (header `apikey`) |
| `CACHE_REDIS_URI` | URI do Redis (ex.: `redis://redis:6379`) para Evolution + histórico |

Documentação oficial útil: [Evolution API v2](https://doc.evolution-api.com/).

---

## Como subir tudo

Na raiz do projeto:

```bash
docker compose up --build
```

Serviços expostos por padrão no compose:

- Evolution API: `http://localhost:8080`
- Bot (FastAPI): `http://localhost:8000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

**Nota:** a senha do Postgres no compose está como `postgres` só para desenvolvimento. Em ambiente real, mude isso já.

### Rodar só o bot no PC (sem Docker)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Você precisa garantir que a Evolution consegue bater no webhook. Se a Evolution estiver em outra máquina, precisa de URL pública (ngrok, túnel, etc.) ou da mesma rede Docker.

---

## Como testar (para quem quer verificar na prática)

**1. Ver se o bot está vivo**  
Abra `http://localhost:8000/docs` — o FastAPI mostra o Swagger. O endpoint importante é `POST /webhook`.

**2. Teste “de mentira” com JSON parecido com a Evolution**  
Você pode usar o Swagger ou o curl abaixo (ajuste o número e o texto). Isso simula o corpo que a Evolution manda em `messages.upsert`:

PowerShell (Windows), numa linha só:

```bash
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"data\":{\"key\":{\"remoteJid\":\"5511999999999@s.whatsapp.net\"},\"message\":{\"conversation\":\"Olá, teste\"}}}"
```

No Linux/macOS o escape das aspas pode variar; o mais simples é usar o **Swagger** em `/docs` e colar o JSON lá.

Se a chain, Redis, Chroma e OpenAI estiverem bem configurados, você deve ver atividade no terminal e (se a Evolution estiver ligada e o número existir) uma mensagem chegando ao WhatsApp. Se algo falhar, o lugar certo para olhar é o log do container `bot`.

**3. Teste real**  
Com a instância WhatsApp conectada na Evolution e o webhook configurado para `http://bot:8000/webhook` (rede interna do Compose) ou o URL público equivalente, mande uma mensagem do seu telefone. O comportamento esperado é resposta automática com base nos documentos indexados.

**4. Logs**

```bash
docker compose logs -f bot
```

**5. Alimentar o RAG**  
Coloque PDF ou TXT em `rag_files/` (não dentro de `processed`). Reinicie o bot ou force o código a recarregar documentos conforme a sua lógica no `vectorstore.py`. A primeira vez demora mais (embeddings + escrita no Chroma).

---

## Limitações conhecidas

O `app.py` atual só trata bem mensagens com campo `conversation`. Áudio, imagem ou texto só em `extendedTextMessage` ainda não estão cobertos.

Não há filtro `fromMe`: em certas configurações de webhook pode haver eco; convém validar no painel da Evolution.

---

## Segurança

- `.env` fora do Git.
- Rotação de chaves se alguma vez tiver ido parar ao histórico.
- Não exponha Postgres e painéis da API à internet sem firewall ou VPN.

---

## Palavra final

Projeto focado em **atendimento automatizado** com **RAG** e stack reproduzível em Docker. Foi também exercício de **aprendizado** (compose, memória de conversa, integração WhatsApp). Dúvidas técnicas sobre o repositório, estou disponível para conversar.

— Herbert
