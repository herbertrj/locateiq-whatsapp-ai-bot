# Chatbot de atendimento no WhatsApp com RAG (LocateIQ)

Olá. Sou o Herbert, trabalho como CEO na **LocateIQ** e montei este projeto em paralelo ao dia a dia da empresa. A ideia foi dupla: resolver um problema real de **atendimento no WhatsApp** quando o volume sobe, e forçar-me a **aprender na prática** um conjunto de ferramentas que eu só tinha lido em tutorial — Docker a sério, LangChain, vector database, integração com API de WhatsApp, esse tipo de coisa.

Não é um slide de vendas. É código que eu escrevi, quebrei, voltei a escrever. Se estás a ler isto como recrutador, espero que consigas ver **o problema**, **o que usei**, **porquê** e **como podes validar** que isto até funciona.

---

## Que problema isto tenta resolver

Na LocateIQ o WhatsApp é canal importante. Quando entram muitas mensagens ao mesmo tempo, ou de madrugada, **ou respondes tarde e o cliente esfria**, ou metes uma pessoa só a apagar incêndios. Um bot burro que responde “em breve respondemos” não resolve; um modelo que **alucina** preço ou condição do serviço é pior.

O que eu queria era: **resposta automática** que ainda assim se apoiasse em **documentos que a empresa já tem** (PDF, texto), com **memória da conversa** para não parecer um robô que esquece a frase anterior. Daí o caminho **RAG** (buscar trechos relevantes antes de mandar o texto para o modelo) em vez de confiar só no conhecimento genérico da OpenAI.

---

## O fluxo em linguagem humana

1. O cliente manda mensagem no WhatsApp.
2. A **Evolution API** (que está ligada à nossa instância) dispara um evento e chama o meu **`POST /webhook`** no serviço Python.
3. O **FastAPI** recebe o JSON, tira o texto e o identificador do chat.
4. Entra a **chain do LangChain**: histórico no **Redis**, busca semântica no **Chroma** (feita com embeddings da OpenAI), depois o **modelo de chat** gera a resposta.
5. O mesmo backend chama de novo a Evolution para **enviar o texto** de volta ao número.

O **Postgres** na stack não é “porque sim”: a imagem da Evolution que uso precisa de base de dados para estado/metadados. O **Redis** serve à API e eu uso também para guardar o histórico das mensagens no LangChain.

---

## Tecnologias que usei e o porquê de cada uma

**Python 3.13** — É a versão que fixei no `Dockerfile`. Queria algo recente mas estável para não brigar com dependências do LangChain sem necessidade.

**FastAPI** — Framework leve para expor o webhook. Gosto do facto de ser nativo para async e de gerar documentação OpenAPI; para um endpoint principal mais vale simples do que carregar Framework pesado.

**Uvicorn** — Servidor ASGI que meti no comando do container. É o padrão para correr FastAPI em produção (ou quase-produção).

**Docker + Docker Compose** — Foi aqui que mais aprendi neste projeto. Queria **um comando** para subir tudo: API Evolution, Postgres, Redis e o meu bot, na **mesma rede**, com **volumes** para não perder instância do WhatsApp, base de dados, ficheiros RAG e pasta do Chroma. Sem isso eu passava a vida a dizer “na minha máquina funciona”.

**Dockerfile do bot** — Copia `requirements.txt`, instala dependências, copia o código, expõe a porta 8000 e arranca o Uvicorn. Simples de proposito.

**Evolution API (imagem evoapicloud)** — Abstrai a parte chata de estar colado ao protocolo WhatsApp. Eu recebo **HTTP** com JSON e mando **HTTP** para enviar mensagem. Por baixo usa Baileys; eu não tratei disso linha a linha porque o objetivo era outro: **orquestrar IA e dados**.

**PostgreSQL 15** — Vem no `docker-compose` porque a Evolution precisa. Ajustei `max_connections` no compose para evitar dor de cabeça quando há muitas ligações.

**Redis** — Cache e outras funções internas da Evolution; no meu código uso **Redis** também via `RedisChatMessageHistory` do LangChain para o histórico por `session_id` (no caso, ligado ao JID do WhatsApp).

**LangChain** (vários pacotes: `langchain-core`, `langchain-classic`, `langchain-openai`, `langchain-community`, `langchain-chroma`, `langchain-text-splitters`) — Usei porque já traz o padrão **history-aware retriever** + **stuff documents** + **retrieval chain** + **RunnableWithMessageHistory**. Dava para fazer à mão, mas eu queria **aprender a ferramenta que o mercado usa** e não reinventar a roda mal feita.

**OpenAI** — `ChatOpenAI` para a resposta final e `OpenAIEmbeddings` para transformar texto em vetor e pesquisar no Chroma. Uma API só para os dois papéis simplifica contas e chaves.

**Chroma** — Base vectorial em disco (`persist_directory`), integrada ao LangChain. Escolhi por ser **prática para um projeto individual**: não precisei de subir Pinecone ou Weaviate no primeiro dia. Os dados ficam na pasta `vectorstore_data` (montada no container).

**PyPDF + loaders do LangChain** — Para ingerir PDF e TXT da pasta `rag_files`. Os ficheiros processados vão para `rag_files/processed` (e essa pasta está no `.gitignore` para não ir lixo para o Git).

**Requests** — No `evolution_api.py` faço o `POST` para o endpoint `sendText` da Evolution com o `apikey` no header. Direto, fácil de debugar com logs.

**python-dotenv** — Todas as chaves e URLs vêm do ficheiro `.env`. Nunca commitar isso.

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
├── rag_files/          # Coloca aqui PDF/TXT para indexar
└── vectorstore_data/   # Onde o Chroma guarda os vetores (não vai para o Git)
```

---

## O que precisas antes de começar

- **Docker** e **Docker Compose** instalados.
- Conta **OpenAI** com API key.
- Instância configurada na **Evolution API** (QR code, webhook apontando para o teu bot).
- Ficheiro **`.env`** na raiz (cria a partir dos nomes no `config.py`; não há exemplo no repo de propósito para não vazar estrutura de secrets).

### Variáveis que o `config.py` espera (nomes para copiares)

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

Serviços expostos por defeito no compose:

- Evolution API: `http://localhost:8080`
- Bot (FastAPI): `http://localhost:8000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

**Nota:** a senha do Postgres no compose está como `postgres` só para desenvolvimento. Em ambiente real muda isso já.

### Correr só o bot no PC (sem Docker)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Tens de garantir que a Evolution consegue bater no webhook. Se a Evolution estiver noutra máquina, precisas de URL pública (ngrok, túnel, etc.) ou da mesma rede Docker.

---

## Como testar (para quem quer verificar na pele)

**1. Ver se o bot está vivo**  
Abre `http://localhost:8000/docs` — o FastAPI mostra o Swagger. O endpoint importante é `POST /webhook`.

**2. Teste “de mentira” com JSON parecido com a Evolution**  
Podes usar o Swagger ou o curl abaixo (ajusta o número e o texto). Isto simula o corpo que a Evolution manda em `messages.upsert`:

PowerShell (Windows), numa linha só:

```bash
curl -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d "{\"data\":{\"key\":{\"remoteJid\":\"5511999999999@s.whatsapp.net\"},\"message\":{\"conversation\":\"Olá, teste\"}}}"
```

No Linux/macOS o escape das aspas pode variar; o mais simples é usar o **Swagger** em `/docs` e colar o JSON lá.

Se a chain, Redis, Chroma e OpenAI estiverem bem configurados, deves ver atividade no terminal e (se a Evolution estiver ligada e o número existir) uma mensagem a chegar ao WhatsApp. Se algo falhar, o sítio certo para olhar é o log do container `bot`.

**3. Teste real**  
Com a instância WhatsApp conectada na Evolution e o webhook configurado para `http://bot:8000/webhook` (rede interna do Compose) ou o URL público equivalente, manda uma mensagem do teu telefone. O comportamento esperado é resposta automática com base nos documentos indexados.

**4. Logs**  

```bash
docker compose logs -f bot
```

**5. Alimentar o RAG**  
Mete PDF ou TXT em `rag_files/` (não dentro de `processed`). Reinicia o bot ou força o código a recarregar documentos conforme a tua lógica no `vectorstore.py`. A primeira vez demora mais (embeddings + escrita no Chroma).

---

## Limitações que eu próprio conheço

O `app.py` actual só trata bem mensagens com campo `conversation`. Áudio, imagem ou texto só em `extendedTextMessage` ainda não estão cobertos; é melhoria que tenho na lista.

Também não filtrei `fromMe` no snippet actual: em cenários estranhos podes ter eco se não tiveres cuidado na configuração do webhook. Fica como aviso honesto.

---

## Segurança

- `.env` fora do Git.  
- Rotação de chaves se alguma vez tiver ido parar ao histórico.  
- Não expor Postgres e painéis da API à internet sem firewall ou VPN.

---

## Palavra final

Fiz este projeto para **aprender fazendo**: compose, RAG, memória de conversa, integração WhatsApp. Se quiseres falar sobre decisões técnicas ou sobre como eu evoluiria isto para produção com mais gente em cima, estou disponível.

Herbert — LocateIQ
