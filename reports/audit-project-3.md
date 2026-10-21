# Audit Report — Projeto 3: task-manager-api

> Saída das Fases 1 e 2 da skill `/refactor-arch` executada em `task-manager-api/`.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não fixada; validado com 3.13)
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1 (não usado), requests 2.31.0 (não usado), python-dotenv 1.0.0 (não usado)
Domain:        Task Manager API (tasks, usuários, categorias, relatórios de produtividade)
Architecture:  Camadas parciais — models/, routes/, services/, utils/ existem, mas regras de negócio e queries vivem nas rotas; services/ e utils/ praticamente não são usados; sem config nem error handling centralizados
Source files:  12 files analyzed (~1158 lines; + 3 empty __init__.py)
DB:            SQLite (tasks.db) via ORM Flask-SQLAlchemy
DB tables:     tasks, users, categories
Entry point:   app.py — `python seed.py && python app.py` (porta 5000)
Endpoints:     22 endpoints mapeados
================================
```

| Método | Path | Handler | Arquivo:linha |
|---|---|---|---|
| GET | /health | health | app.py:22 |
| GET | / | index | app.py:26 |
| GET | /tasks | get_tasks | routes/task_routes.py:11 |
| GET | /tasks/<id> | get_task | routes/task_routes.py:65 |
| POST | /tasks | create_task | routes/task_routes.py:85 |
| PUT | /tasks/<id> | update_task | routes/task_routes.py:156 |
| DELETE | /tasks/<id> | delete_task | routes/task_routes.py:225 |
| GET | /tasks/search | search_tasks | routes/task_routes.py:240 |
| GET | /tasks/stats | task_stats | routes/task_routes.py:273 |
| GET | /users | get_users | routes/user_routes.py:10 |
| GET | /users/<id> | get_user | routes/user_routes.py:27 |
| POST | /users | create_user | routes/user_routes.py:42 |
| PUT | /users/<id> | update_user | routes/user_routes.py:92 |
| DELETE | /users/<id> | delete_user | routes/user_routes.py:134 |
| GET | /users/<id>/tasks | get_user_tasks | routes/user_routes.py:153 |
| POST | /login | login | routes/user_routes.py:185 |
| GET | /reports/summary | summary_report | routes/report_routes.py:12 |
| GET | /reports/user/<id> | user_report | routes/report_routes.py:103 |
| GET | /categories | get_categories | routes/report_routes.py:157 |
| POST | /categories | create_category | routes/report_routes.py:167 |
| PUT | /categories/<id> | update_category | routes/report_routes.py:190 |
| DELETE | /categories/<id> | delete_category | routes/report_routes.py:211 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   12 analyzed | ~1158 lines of code
Architecture (current): Camadas parciais
```

## Summary
CRITICAL: 2 | HIGH: 4 | MEDIUM: 5 | LOW: 4

| # | Severity | Anti-pattern | File |
|---|----------|--------------|------|
| 1 | CRITICAL | AP-01 Segredos hardcoded | app.py:11-13, services/notification_service.py:7-10 |
| 2 | CRITICAL | AP-04 Senhas com MD5 sem salt | models/user.py:27-32 |
| 3 | HIGH | AP-07 Hash de senha nas respostas | models/user.py:16-25 |
| 4 | HIGH | AP-09 Token falso / escalonamento de role | routes/user_routes.py:52, 119-122, 207-211 |
| 5 | HIGH | AP-06 Regras de negócio nas rotas | routes/*.py |
| 6 | HIGH | AP-10 Debug + 0.0.0.0 + CORS aberto | app.py:15, 34 |
| 7 | MEDIUM | AP-14 APIs deprecated | 13 arquivos/38 ocorrências |
| 8 | MEDIUM | AP-11 Queries N+1 | routes/task_routes.py:41-57, routes/report_routes.py:15-68, 159-164, routes/user_routes.py:22 |
| 9 | MEDIUM | AP-12 except nu / sem handler global | routes/*.py, utils/helpers.py |
| 10 | MEDIUM | AP-13 Validação duplicada | routes/task_routes.py:92-124, 166-213, routes/user_routes.py:54-72, 102-122 |
| 11 | MEDIUM | AP-06 Recurso no módulo errado | routes/report_routes.py:157-223 |
| 12 | LOW | AP-18 Imports e dependências mortos | app.py:7, routes/*.py, utils/helpers.py:2-7, requirements.txt:4-6 |
| 13 | LOW | AP-17 Magic numbers/strings | routes/task_routes.py:110-113, 177-182, routes/user_routes.py:64, 71, 115, 120 |
| 14 | LOW | AP-19 print como log | routes/task_routes.py:149-234, routes/user_routes.py:83-147 |
| 15 | LOW | AP-18 Lógica verbosa / nomes | models/task.py:38-60, models/user.py:34-38, routes/report_routes.py:24-28 |

## Findings

### #1 [CRITICAL] SECRET_KEY e senha SMTP hardcoded
File: app.py:11-13, services/notification_service.py:7-10
Category: Security
Anti-pattern: AP-01 Credenciais hardcoded
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'`, URI do banco fixa; `NotificationService` contém `email_user='taskmanager@gmail.com'` e `email_password='senha123'`.
Impact: Segredos versionados; quem lê o repo assina tokens e usa a conta SMTP.
Recommendation: `config/settings.py` com `os.environ` (python-dotenv já é dependência) + `.env.example`; service recebe config por injeção (Playbook P-01).

### #2 [CRITICAL] Hash de senha MD5 sem salt
File: models/user.py:27-32
Category: Security
Anti-pattern: AP-04 Armazenamento inseguro de senha
Description: `hashlib.md5(pwd.encode()).hexdigest()` em `set_password`/`check_password`; política mínima de 4 caracteres (routes/user_routes.py:64).
Impact: MD5 sem salt é revertido por rainbow tables em segundos.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`, com migração transparente de hashes MD5 legados no login (Playbook P-08).

### #3 [HIGH] Hash de senha devolvido pela API
File: models/user.py:16-25
Category: Security
Anti-pattern: AP-07 Exposição de dados sensíveis
Description: `User.to_dict()` inclui `'password': self.password`, usado em GET/POST/PUT `/users` e na resposta de `/login` (routes/user_routes.py:33, 85, 129, 209).
Impact: Combinado com #2, qualquer cliente obtém as senhas de todos os usuários.
Recommendation: Remover `password` da serialização (Playbook P-08).

### #4 [HIGH] Autenticação falsa e escalonamento de privilégio
File: routes/user_routes.py:52, 119-122, 207-211
Category: Security
Anti-pattern: AP-09 Autenticação/autorização ausente ou falsa
Description: Login retorna `'token': 'fake-jwt-token-' + str(user.id)` (previsível); `role` (inclusive `admin`) é aceito do corpo em criação e update sem checagem; nenhuma rota exige token.
Impact: Qualquer cliente forja tokens e se promove a admin.
Recommendation: Token assinado com `itsdangerous` (SECRET_KEY) mantendo o campo `token`; registrar recomendação de autorização por rota (Playbook P-10).

### #5 [HIGH] Regras de negócio e acesso a dados dentro das rotas
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299, routes/user_routes.py:42-90, 153-183, routes/report_routes.py:12-155
Category: Architecture
Anti-pattern: AP-06 Regra de negócio na camada de roteamento
Description: Rotas montam dicts campo a campo, validam, consultam o ORM e calculam estatísticas. A regra "overdue" é copiada em 6 lugares (task_routes.py:30-39, 71-80, 283-287; user_routes.py:171-180; report_routes.py:33-36, 132-135) enquanto `Task.is_overdue()` (models/task.py:50-60), `process_task_data` (utils/helpers.py:57-108) e `NotificationService` existem sem uso.
Impact: Camadas existem só no nome; mudar uma regra exige editar N rotas; nada testável sem HTTP.
Recommendation: Criar `controllers/` (task, user, category, report) com a lógica; rotas viram Views finas; usar os métodos do model e helpers existentes (Playbook P-05).

### #6 [HIGH] Debug e bind público fixos; CORS irrestrito
File: app.py:15, 34
Category: Security
Anti-pattern: AP-10 Configuração insegura de execução
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` e `CORS(app)` sem origens.
Impact: Debugger do Werkzeug acessível na rede (RCE); API consumível de qualquer origem.
Recommendation: Flags via env com defaults seguros (Playbook P-01).

### #7 [MEDIUM] Uso de APIs deprecated (datetime.utcnow e Query.get)
File: models/task.py:15-16, 52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, 42, 51, 67, 72, 117, 122, 158, 188, 195, 215, 227, 285, routes/user_routes.py:29, 94, 136, 155, 172, routes/report_routes.py:35, 42, 45, 71, 105, 133, 192, 213, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Category: Deprecated API
Anti-pattern: AP-14 Uso de APIs deprecated
Description: `datetime.utcnow()` (DeprecationWarning desde Python 3.12 — emitido ao rodar `seed.py`) e `Model.query.get()` (legado no SQLAlchemy 2.x, `LegacyAPIWarning`).
Impact: Quebra em futuras versões de Python/SQLAlchemy; avisos poluem logs.
Recommendation: Helper `utcnow()` com `datetime.now(timezone.utc)` (naive para SQLite) e `db.session.get(Model, id)` (Playbook P-11).

### #8 [MEDIUM] Queries N+1 em listagens e relatórios
File: routes/task_routes.py:41-57, routes/report_routes.py:15-28, 53-68, 159-164, routes/user_routes.py:22
Category: Performance
Anti-pattern: AP-11 Queries N+1
Description: `GET /tasks` faz `User.query.get` e `Category.query.get` por task; relatório faz 1 query por usuário e 13 `COUNT` separados; `/categories` conta tasks por categoria; `/users` dispara lazy-load `len(u.tasks)` por usuário.
Impact: Número de queries cresce com o volume de dados.
Recommendation: `joinedload`, agregações `GROUP BY` (Playbook P-06).

### #9 [MEDIUM] except nu e ausência de error handler global
File: routes/task_routes.py:62, 137, 204, 236, routes/report_routes.py:186, 207, 221, routes/user_routes.py:130, 149, utils/helpers.py:46, 49, 88
Category: Reliability
Anti-pattern: AP-12 Tratamento de erros espalhado
Description: 12 `except:` nus que engolem qualquer erro (inclusive `KeyboardInterrupt`); sem `@app.errorhandler`; `update_category` quebra com 500 se o corpo não for JSON (report_routes.py:196-197).
Impact: Falhas silenciosas e respostas inconsistentes.
Recommendation: Exceções de domínio + `middlewares/error_handler.py` (Playbook P-07).

### #10 [MEDIUM] Validação duplicada entre create/update e sem checagem de tipos
File: routes/task_routes.py:92-124, 166-213, routes/user_routes.py:54-72, 102-122
Category: Maintainability
Anti-pattern: AP-13 Validação duplicada
Description: Regras de título/status/prioridade/datas/tags copiadas entre create e update; regex de email repetida (também em utils/helpers.py:21); `priority` string causa `TypeError` → 500.
Impact: Regras divergem com o tempo; entradas inválidas geram 500.
Recommendation: Validadores únicos (`validate_task_payload`, `validate_user_payload`) no controller (Playbook P-09).

### #11 [MEDIUM] CRUD de categorias registrado no blueprint de relatórios
File: routes/report_routes.py:157-223
Category: Architecture
Anti-pattern: AP-06 Regra de negócio na camada de roteamento (coesão)
Description: Endpoints `/categories` vivem em `report_routes.py`.
Impact: Baixa coesão; difícil localizar e evoluir o recurso.
Recommendation: `routes/category_routes.py` + `controllers/category_controller.py` (Playbook P-03).

### #12 [LOW] Imports e dependências não utilizados
File: app.py:7, routes/task_routes.py:7, routes/report_routes.py:7-8, routes/user_routes.py:6, utils/helpers.py:2-7, models/task.py:3, requirements.txt:4-6
Category: Maintainability
Anti-pattern: AP-18 Código morto
Description: `import os, sys, json, ...` sem uso em vários módulos; `marshmallow`, `requests` e `python-dotenv` declarados sem import.
Impact: Ruído, superfície de dependências maior.
Recommendation: Remover imports; usar `python-dotenv` na config e remover deps mortas (Playbook P-14).

### #13 [LOW] Magic numbers e listas de domínio repetidas
File: routes/task_routes.py:110-113, 177-182, routes/user_routes.py:64, 71, 115, 120
Category: Maintainability
Anti-pattern: AP-17 Magic numbers/strings
Description: Listas de status/roles e faixas `1..5`, `3..200`, `4` repetidas inline, embora `VALID_STATUSES`, `VALID_ROLES`, etc. existam em utils/helpers.py:110-116 sem uso.
Impact: Divergência de regras.
Recommendation: Constantes no model e uso único (Playbook P-13).

### #14 [LOW] print como log
File: routes/task_routes.py:149, 153, 219, 234, routes/user_routes.py:83, 89, 147, services/notification_service.py:21, 24
Category: Maintainability
Anti-pattern: AP-19 print como log
Description: Eventos e erros registrados com `print`.
Impact: Sem níveis nem destino configurável.
Recommendation: `logging` (Playbook P-14).

### #15 [LOW] Condicionais verbosas e nomes pouco descritivos
File: models/task.py:38-60, models/user.py:34-38, routes/report_routes.py:24-28
Category: Maintainability
Anti-pattern: AP-18 Nomenclatura ruim
Description: `if cond: return True else: return False`, ifs aninhados em 3 níveis em `is_overdue`; variáveis `p1..p5`.
Impact: Leitura difícil.
Recommendation: Expressões booleanas diretas; dicionário por prioridade (Playbook P-14).

## Deprecated APIs
| File:line | Deprecated API | Modern replacement |
|-----------|----------------|--------------------|
| models/*.py, routes/*.py, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74 (22 ocorrências) | `datetime.utcnow()` | `datetime.now(timezone.utc)` via helper `utcnow()` naive |
| routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 (16 ocorrências) | `Model.query.get(id)` | `db.session.get(Model, id)` |

## Refactoring Plan (Phase 3 preview)
Strategy: evolução incremental das camadas existentes (sem mover `models/`, `routes/`).
Target structure:
```
app.py                       # create_app() + entry point (seed.py continua importando app, db)
config/settings.py           # NOVO — env vars
database.py
models/                      # mantidos: sem password no to_dict, constantes, utcnow
controllers/                 # NOVO — task, user, category, report
routes/                      # Views finas: task, user, category (NOVO), report
services/                    # notification_service com config injetada; auth_service (token)
middlewares/error_handler.py # NOVO
utils/                       # helpers realmente usados (datas, validação)
```
Key transformations:
- P-01 → #1, #6 · P-08 → #2, #3 · P-10 → #4 · P-05 → #5 · P-11 → #7 · P-06 → #8
- P-07 → #9 · P-09 → #10 · P-03 → #11 · P-14 → #12, #14, #15 · P-13 → #13
API contract changes (security-driven): `password` removido das respostas de usuário; `token` do login passa a ser assinado (mesmo campo).

```
================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
