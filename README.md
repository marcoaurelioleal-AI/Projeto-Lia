# Projeto LIA

Painel operacional para o Grupo Empresarial Lia, que reúne Lia Burguer, Lia Pizza e Lia Salgados. O projeto nasceu em Streamlit e agora passa a ter uma arquitetura profissional com React no frontend e FastAPI no backend.

## Arquitetura

- `apps/web`: frontend React + TypeScript + Vite, responsivo e otimizado para mobile.
- `apps/api`: backend FastAPI com autenticação, checklists, manuais e IA.
- `meu_assistente.py`: versão Streamlit legada, mantida temporariamente como referência.
- `alembic`: base para futuras migrações de banco.

## Funcionalidades da nova versão

- Login por usuário com token e senha com hash.
- Dashboard de operação diária.
- Checklists persistentes por data e loja.
- Observação de fechamento de turno.
- Manuais técnicos filtráveis por unidade.
- Assistente IA protegido no backend, sem expor chave Gemini ao navegador.
- Docker multi-stage servindo React + API em um único serviço.

## Rodando localmente

Crie um `.env` a partir do `.env.example` e ajuste os valores.

Backend:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Acesse `http://127.0.0.1:5173`.

Usuário inicial de desenvolvimento:

```env
LIA_ADMIN_USER="admin"
LIA_ADMIN_PASSWORD="troque-essa-senha"
```

## Validações

Backend:

```bash
python -m py_compile meu_assistente.py dados_operacionais.py apps/api/app/main.py
pytest
```

Frontend:

```bash
cd apps/web
npm run lint
npm run typecheck
npm run build
```

## Banco de dados e migrations

O projeto usa `DATABASE_URL` como configuracao central do banco. SQLite e adequado para desenvolvimento local e testes simples. Para producao, prefira PostgreSQL.

Exemplos:

```env
DATABASE_URL="sqlite:///./lia.db"
DATABASE_URL="postgresql+psycopg://usuario:senha@host:5432/banco"
```

Em desenvolvimento, `AUTO_CREATE_TABLES=true` permite manter o fluxo local simples. Em producao, use `AUTO_CREATE_TABLES=false` e aplique migrations com Alembic.

Gerar migration:

```bash
alembic revision --autogenerate -m "descricao_da_migration"
```

Aplicar migrations:

```bash
alembic upgrade head
```

## Deploy

O `Dockerfile` atual constrói o React e copia o build para a API FastAPI, que serve a SPA em produção. Isso permite manter um único Web Service no Render.

No Docker, o comando de inicializacao aplica `alembic upgrade head` antes de iniciar o Uvicorn.

O arquivo `render.yaml` deixa a configuração base pronta para Blueprint/Infrastructure as Code no Render.

Variáveis importantes no Render:

- `DATABASE_URL`
- `AUTO_CREATE_TABLES`
- `JWT_SECRET`
- `LIA_ADMIN_USER`
- `LIA_ADMIN_PASSWORD`
- `GEMINI_API_KEY`
- `MODELO_GEMINI`
- `FRONTEND_ORIGINS`

Para o serviço Docker no Render, use `DATABASE_URL=sqlite:////app/data/lia.db` apenas para teste simples. Para produção real, prefira PostgreSQL no `DATABASE_URL`, use `AUTO_CREATE_TABLES=false` e troque todos os segredos padrão.
