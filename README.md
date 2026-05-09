# Projeto LIA

Central operacional para o **Grupo Empresarial Lia**, reunindo processos internos da Lia Burguer, Lia Pizza e Lia Salgados em uma plataforma web com login, dashboard, checklists, manuais técnicos e a assistente operacional **Lia**.

O projeto nasceu como uma aplicação Streamlit e está em migração para uma arquitetura mais profissional com **React + TypeScript** no frontend e **FastAPI** no backend.

## Visão Geral

O objetivo da Central LIA é ajudar a operação diária das lojas a manter padrão, organização e rastreabilidade.

Principais recursos:

- Login interno com usuário, senha com hash e token JWT.
- Dashboard operacional.
- Checklists persistentes por data e loja.
- Observação de fechamento de turno.
- Manuais técnicos por unidade.
- Chatbot **Lia**, com respostas baseadas nos manuais internos.
- Histórico resumido das conversas da Lia.
- Painel administrativo inicial para gestão.
- Gestão administrativa básica de usuários e lojas.
- Ocorrências operacionais com status e severidade.
- Upload protegido de fotos como evidências de checklist.
- Relatórios semanais/mensais de checklists, pendências, ocorrências e evidências.
- Backend preparado para SQLite em desenvolvimento e PostgreSQL em produção.
- Migrations com Alembic.
- Deploy Docker com React e FastAPI no mesmo serviço.

## Arquitetura

```text
PROJETO_LIA/
├── apps/
│   ├── api/
│   │   └── app/
│   │       ├── routers/
│   │       ├── services/
│   │       ├── repositories/
│   │       ├── config.py
│   │       ├── database.py
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── security.py
│   │       └── seed.py
│   └── web/
│       └── src/
├── alembic/
├── assets/
├── Dockerfile
├── render.yaml
├── requirements.txt
└── meu_assistente.py
```

### Backend

O backend fica em `apps/api` e usa:

- FastAPI para API HTTP.
- SQLAlchemy para ORM.
- Alembic para migrations.
- PyJWT para autenticação.
- Gemini via `google-genai` para a Lia.
- Repository/Service em checklists, ocorrências, evidências, relatórios e admin para separar responsabilidades.

Camadas principais:

- `routers`: endpoints e injeção de dependências.
- `services`: regras de negócio.
- `repositories`: consultas e persistência no banco.
- `models.py`: modelos SQLAlchemy.
- `schemas.py`: contratos Pydantic.

### Frontend

O frontend fica em `apps/web` e usa:

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- TanStack Query.
- React Router.
- Lucide React.

### Legado

`meu_assistente.py` mantém a versão Streamlit original como referência temporária. A evolução principal do produto deve acontecer em `apps/web` e `apps/api`.

## Requisitos

- Python 3.11+ recomendado para produção.
- Node.js compatível com o projeto Vite.
- npm.
- Git.

No ambiente atual de desenvolvimento, o projeto também foi validado com Python instalado localmente no Windows.

## Configuração Local

Crie um arquivo `.env` a partir do exemplo:

```powershell
copy .env.example .env
```

Edite o `.env` com seus valores locais.

Exemplo mínimo para desenvolvimento:

```env
DATABASE_URL="sqlite:///./lia.db"
AUTO_CREATE_TABLES="true"
JWT_SECRET="troque-esse-segredo"
ACCESS_TOKEN_MINUTES="480"
FRONTEND_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:8062"

LIA_ADMIN_USER="admin"
LIA_ADMIN_PASSWORD="troque-essa-senha"

GEMINI_API_KEY="sua_chave_gemini"
MODELO_GEMINI="gemini-2.5-flash"
UPLOAD_DIR="data/uploads/checklist-evidences"
MAX_UPLOAD_BYTES="5242880"
```

Não commite `.env`. Ele deve ficar apenas na máquina local ou nas variáveis do Render.

## Rodando Localmente

### Backend

```powershell
cd E:\PROJETO_LIA
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn apps.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

API local:

```text
http://127.0.0.1:8000
```

Healthcheck:

```text
http://127.0.0.1:8000/health
```

### Frontend

Em outro terminal:

```powershell
cd E:\PROJETO_LIA\apps\web
npm install
npm run dev
```

Frontend local:

```text
http://127.0.0.1:5173
```

### Rodando o Build Integrado

Quando o frontend já foi buildado, o FastAPI pode servir a SPA diretamente:

```powershell
cd E:\PROJETO_LIA
npm --prefix apps/web run build
.\.venv\Scripts\python.exe -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8062
```

Acesse:

```text
http://127.0.0.1:8062
```

Esse endereço só funciona enquanto o `uvicorn` estiver rodando.

## Banco de Dados

O projeto usa `DATABASE_URL` como configuração central.

### SQLite

Recomendado apenas para desenvolvimento local e testes simples:

```env
DATABASE_URL="sqlite:///./lia.db"
AUTO_CREATE_TABLES="true"
```

### PostgreSQL

Recomendado para produção:

```env
DATABASE_URL="postgresql+psycopg://usuario:senha@host:5432/banco"
AUTO_CREATE_TABLES="false"
```

O backend também normaliza URLs `postgres://` e `postgresql://` para o driver `postgresql+psycopg://`.

## Migrations com Alembic

Aplicar migrations:

```powershell
alembic upgrade head
```

Ver migration atual:

```powershell
alembic current
```

Gerar nova migration:

```powershell
alembic revision --autogenerate -m "descricao_da_migration"
```

Em produção, não dependa de `Base.metadata.create_all`. Use migrations com `AUTO_CREATE_TABLES=false`.

## Variáveis de Ambiente

### Backend

| Variável | Uso |
| --- | --- |
| `DATABASE_URL` | URL do banco SQLite ou PostgreSQL. |
| `AUTO_CREATE_TABLES` | Controla criação automática de tabelas no startup. Use `false` em produção. |
| `JWT_SECRET` | Segredo para assinar tokens JWT. |
| `ACCESS_TOKEN_MINUTES` | Duração da sessão. |
| `FRONTEND_ORIGINS` | Origens permitidas no CORS. |
| `LIA_ADMIN_USER` | Usuário admin inicial. |
| `LIA_ADMIN_PASSWORD` | Senha admin inicial. |
| `GEMINI_API_KEY` | Chave da API Gemini usada pela Lia. |
| `MODELO_GEMINI` | Modelo Gemini. Padrão recomendado: `gemini-2.5-flash`. |
| `UPLOAD_DIR` | Pasta local para evidências em desenvolvimento. |
| `MAX_UPLOAD_BYTES` | Tamanho máximo de upload. Padrão: `5242880` (5MB). |

### Frontend

| Variável | Uso |
| --- | --- |
| `VITE_API_URL` | URL da API quando frontend e backend rodam separados. |

Quando o FastAPI serve o build React no mesmo domínio, `VITE_API_URL` pode ficar vazio.

## IA: Chatbot Lia

A Lia é a assistente operacional da Central LIA.

Na versão atual, ela:

- responde dúvidas operacionais;
- usa RAG operacional simples para recuperar trechos relevantes dos manuais internos;
- aceita modos de resposta: `rapido`, `detalhado` e `treinamento`;
- mostra fontes usadas;
- salva histórico resumido;
- registra interações auditáveis com pergunta, resposta, modo, fontes e latência;
- pede confirmação da gestão quando a base não é suficiente;
- não executa ações no sistema.

Camada de conhecimento:

```text
apps/api/app/services/rag_service.py
apps/api/app/services/ai_service.py
apps/api/app/repositories/manual_repository.py
apps/api/app/repositories/ai_repository.py
```

A primeira versão usa busca textual por relevância, sem vector database. A arquitetura ficou preparada para trocar o recuperador por embeddings/vector store futuramente sem reescrever a rota `/ai/chat`.

## Endpoints Principais

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Healthcheck da API. |
| `POST` | `/auth/login` | Login. |
| `GET` | `/auth/me` | Usuário autenticado. |
| `GET` | `/manuals` | Lista manuais técnicos. |
| `GET` | `/checklists` | Lista checklists por data e loja. |
| `PATCH` | `/checklists/{run_id}/items` | Atualiza item de checklist. |
| `PATCH` | `/checklists/{run_id}/closing-note` | Atualiza observação de fechamento. |
| `POST` | `/ai/chat` | Conversa com a Lia. |
| `GET` | `/ai/history` | Histórico resumido da Lia. |
| `GET` | `/ai/interactions` | Histórico auditável das interações da IA para administradores. |
| `GET` | `/ai/status` | Diagnóstico seguro da configuração de IA. |
| `GET` | `/admin/users` | Lista usuários para administradores. |
| `POST` | `/admin/users` | Cria usuário. |
| `PATCH` | `/admin/users/{user_id}` | Atualiza nome, papel ou status do usuário. |
| `DELETE` | `/admin/users/{user_id}` | Desativa usuário sem remover histórico. |
| `GET` | `/admin/stores` | Lista lojas derivadas dos dados atuais. |
| `POST` | `/admin/stores` | Cria loja. |
| `PATCH` | `/admin/stores/{store_id}` | Atualiza nome ou status da loja. |
| `DELETE` | `/admin/stores/{store_id}` | Desativa loja sem remover histórico. |
| `GET` | `/admin/checklist-templates` | Lista templates de checklist. |
| `POST` | `/admin/checklist-templates` | Cria template de checklist. |
| `PATCH` | `/admin/checklist-templates/{template_id}` | Atualiza template de checklist. |
| `DELETE` | `/admin/checklist-templates/{template_id}` | Desativa template sem remover histórico. |
| `POST` | `/admin/checklist-templates/{template_id}/items` | Cria item em um template. |
| `PATCH` | `/admin/checklist-template-items/{item_id}` | Atualiza item de template. |
| `DELETE` | `/admin/checklist-template-items/{item_id}` | Desativa item sem remover histórico. |
| `GET` | `/admin/manuals` | Lista manuais para administradores. |
| `POST` | `/admin/manuals` | Cria manual operacional. |
| `PATCH` | `/admin/manuals/{manual_id}` | Atualiza manual operacional. |
| `DELETE` | `/admin/manuals/{manual_id}` | Desativa manual sem remover histórico. |
| `POST` | `/admin/manuals/{manual_id}/sections` | Cria seção em um manual. |
| `PATCH` | `/admin/manual-sections/{section_id}` | Atualiza seção de manual. |
| `DELETE` | `/admin/manual-sections/{section_id}` | Desativa seção de manual. |
| `POST` | `/admin/manual-sections/{section_id}/steps` | Cria passo em uma seção. |
| `PATCH` | `/admin/manual-steps/{step_id}` | Atualiza passo de manual. |
| `DELETE` | `/admin/manual-steps/{step_id}` | Desativa passo de manual. |
| `GET` | `/incidents` | Lista ocorrências operacionais. |
| `POST` | `/incidents` | Cria ocorrência operacional. |
| `GET` | `/incidents/{incident_id}` | Consulta uma ocorrência. |
| `PATCH` | `/incidents/{incident_id}` | Atualiza status/dados de uma ocorrência. |
| `POST` | `/checklists/items/{item_id}/evidences` | Envia foto de evidência para item de checklist. |
| `GET` | `/checklists/items/{item_id}/evidences` | Lista evidências de um item. |
| `GET` | `/checklists/{run_id}/evidences` | Lista evidências de um checklist. |
| `GET` | `/evidences` | Auditoria de evidências para administradores. |
| `GET` | `/reports/summary` | Resumo operacional por período. |

## Novas Áreas Operacionais

- `/admin`: painel administrativo com criação/edição/desativação de usuários, lojas, templates de checklist, itens, manuais, seções e passos, além de ocorrências, relatórios e auditoria de evidências.
- `/incidents`: registro e acompanhamento de ocorrências reais do turno.
- `/reports`: resumo semanal ou mensal para gestão.
- Checklists: cada item agora aceita foto como evidência, com storage local protegido por autenticação.

Para produção, troque o storage local por um provider externo como S3, Cloudinary ou Supabase Storage antes de depender das fotos como arquivo permanente.

## Validações

Backend:

```powershell
python -m py_compile apps/api/app/main.py apps/api/app/config.py apps/api/app/database.py apps/api/app/routers/checklists.py apps/api/app/services/checklist_service.py apps/api/app/repositories/checklist_repository.py
pytest
alembic current
alembic upgrade head
```

Frontend:

```powershell
cd apps/web
npm run lint
npm run typecheck
npm run build
```

## Deploy no Render

O projeto possui `Dockerfile` multi-stage:

1. builda o React;
2. instala dependências Python;
3. copia o build do frontend para a API;
4. roda `alembic upgrade head`;
5. inicia o Uvicorn.

Comando final do container:

```sh
alembic upgrade head && uvicorn apps.api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Variáveis recomendadas no Render:

```env
DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/banco
AUTO_CREATE_TABLES=false
JWT_SECRET=um_segredo_forte
LIA_ADMIN_USER=admin
LIA_ADMIN_PASSWORD=senha_forte
GEMINI_API_KEY=sua_chave_gemini
MODELO_GEMINI=gemini-2.5-flash
FRONTEND_ORIGINS=https://seu-dominio.onrender.com
UPLOAD_DIR=/app/data/uploads/checklist-evidences
MAX_UPLOAD_BYTES=5242880
```

Para teste simples no plano gratuito, SQLite funciona:

```env
DATABASE_URL=sqlite:////app/data/lia.db
```

Para produção real, use PostgreSQL. SQLite em serviço cloud gratuito pode perder dados dependendo da configuração de disco.

## Git e Versionamento

Fluxo básico:

```powershell
git status
git add .
git commit -m "Descricao objetiva da mudanca"
git push origin main
```

Antes de commitar:

- confirme que `.env` não aparece no `git status`;
- rode testes quando houver mudança de backend;
- rode `npm run build` quando houver mudança de frontend.

## Segurança

Boas práticas atuais:

- Chaves Gemini ficam apenas no backend.
- Senhas são armazenadas com hash.
- Tokens JWT são assinados com `JWT_SECRET`.
- `.env` não deve ser versionado.

Pontos importantes para produção:

- trocar todos os segredos padrão;
- usar PostgreSQL;
- usar domínio HTTPS;
- evitar plano gratuito com cold start para entrega final;
- revisar política de usuários e permissões antes de uso amplo.

## Status do Produto

Este projeto está em evolução ativa. A base atual já permite demonstração e acompanhamento pelo cliente, mas para entrega final recomenda-se:

- Render pago ou infraestrutura sem cold start;
- PostgreSQL;
- domínio próprio;
- rotina de backup;
- revisão de segurança e permissões;
- documentação operacional para a equipe das lojas.
