# LocateIQ — automação de atendimento via WhatsApp

Repositório interno da **LocateIQ** para automatizar o atendimento inicial no **WhatsApp**, reduzindo perda de contato com clientes em períodos de alta demanda operacional.

## Objetivo

Integrar o WhatsApp por API (Evolution API), com backend próprio para webhooks e regras de atendimento, com evolução gradual até ambiente de produção.

## Componentes

| Componente | Descrição |
|------------|-----------|
| Evolution API | Integração WhatsApp; porta `8080`. |
| PostgreSQL | Persistência utilizada pela Evolution API. |
| Redis | Cache/fila conforme configuração da Evolution API. |
| FastAPI (`app.py`) | Webhook HTTP em desenvolvimento. |

O serviço **bot** em `docker-compose.yml` permanece comentado até alinhar imagem e comando com o código.

## Requisitos

- Docker e Docker Compose (`docker compose`)
- Python 3.12+ (execução local de `app.py`, opcional)

## Infraestrutura (Docker)

```bash
docker compose up -d
```

Configure **`.env`** na raiz (não versionado). Variáveis conforme documentação da imagem `evoapicloud/evolution-api`.

**Postgres (este compose):** credenciais padrão da imagem; substituir por valores seguros antes de produção e ajustar a URL usada pela Evolution API.

## API FastAPI (local)

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Endpoint atual de teste: `POST /weebook` (recebe JSON, resposta mínima para validar integração).

## Estrutura

```
├── app.py
├── requirements.txt
├── docker-compose.yml
├── DockerFile
└── .gitignore
```

## Segurança

- Não versionar `.env` nem chaves.
- Credenciais expostas em histórico remoto devem ser revogadas e substituídas.

## Uso

Projeto de uso interno LocateIQ.
