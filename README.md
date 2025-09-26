# Grupo Ofertas API Platform

Plataforma web configurável para gerar anúncios afiliados (Amazon, Mercado Livre e AWIN) sem depender do bot do Telegram. O projeto inclui:

- API FastAPI com módulos de integrações, templates e geração de ofertas.
- Interface web (Jinja + HTMX) para configurar credenciais, personalizar textos e gerar prévias.
- Banco relacional (PostgreSQL por padrão) para armazenar configurações e templates.
- Containers Docker para API e banco de dados.

## Estrutura

```
grupo_ofertas_api/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── static/
│   │   └── templates/
│   ├── tests/
│   └── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Desenvolvimento

1. Configure as variáveis de ambiente (ver `.env.example`).
2. Crie um virtualenv e instale as dependências:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```
3. Execute o servidor FastAPI localmente:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Acesse `http://localhost:8000` para a interface administrativa.

## Docker

1. Copie `.env.example` para `.env` e ajuste as credenciais desejadas.
2. Suba os containers:
   ```bash
   docker compose up --build
   ```
3. A API ficará disponível em `http://localhost:8000`.

## Testes

```bash
pytest backend/tests
```

## Próximos passos

- Implementar autenticação multiusuário.
- Adicionar logs e métricas.
- Publicar imagens em registry privado para distribuição.

## API endpoints principais

- GET /api/integrations — lista integrações configuradas.
- PUT /api/integrations/{provider} — atualiza credenciais (amazon, mercadolivre, awin).
- GET /api/templates / POST /api/templates — gerencia templates Jinja.
- GET /api/rules — regras dinâmicas de transformação.
- POST /api/offers/preview — gera prévia textual a partir de uma URL.
- GET / — painel web com formulários para administrar o produto.
