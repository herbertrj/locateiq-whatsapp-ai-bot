# LocateIQ — chatbot com IA para WhatsApp (Evolution API)

Repositório interno da **LocateIQ** para automatizar o atendimento no **WhatsApp** com respostas assistidas por IA, reduzindo perda de contato com clientes em períodos de alta demanda operacional.

## Sobre o projeto

Este projeto é um **chatbot para WhatsApp** que utiliza:

- **Evolution API** — integração com o WhatsApp
- **FastAPI** — API de backend e webhooks
- **LangChain** — orquestração da conversa com IA
- **OpenAI** — modelos de linguagem
- **Docker** e **Docker Compose** — implantação da infraestrutura

A Evolution API expõe a instância do WhatsApp; o backend FastAPI recebe eventos, aplica a lógica de conversa (LangChain + modelo OpenAI) e devolve mensagens pela mesma API. A integração completa da camada de IA no repositório evolui junto com o serviço do bot.

## Objetivo

Integrar WhatsApp, webhooks e fluxo de mensagens de forma confiável, com evolução gradual até ambiente de produção.

## Componentes na infraestrutura

| Componente | Descrição |
|------------|-----------|
| Evolution API | Integração WhatsApp; porta `8080`. |
| PostgreSQL | Persistência utilizada pela Evolution API. |
| Redis | Cache/fila conforme configuração da Evolution API. |
| FastAPI (`app.py`) | Webhook HTTP e ponto de extensão para LangChain/OpenAI. |

O serviço **bot** em `docker-compose.yml` permanece comentado até alinhar imagem e comando com o código.

## Requisitos

- Docker e Docker Compose (`docker compose`)
- Python 3.12+ (execução local de `app.py`, opcional)

## Infraestrutura (Docker)

```bash
docker compose up -d
```

Configure **`.env`** na raiz (não versionado). Variáveis conforme documentação da imagem `evoapicloud/evolution-api` e, quando aplicável, chaves da OpenAI e demais segredos do bot.

**Postgres (este compose):** credenciais padrão da imagem; substituir por valores seguros antes de produção e ajustar a URL usada pela Evolution API.

## API FastAPI (local)

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Endpoint atual de teste: `POST /weebook` (recebe JSON, resposta mínima para validar integração com a Evolution API).

## Estrutura

```
├── app.py
├── requirements.txt
├── docker-compose.yml
├── DockerFile
└── .gitignore
```

## Segurança

- Não versionar `.env` nem chaves (incluindo tokens OpenAI e Evolution API).
- Credenciais expostas em histórico remoto devem ser revogadas e substituídas.

## Uso

Projeto de uso interno LocateIQ.
