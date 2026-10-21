# refactor-arch — Refatoração Arquitetural Automatizada com Skills

Solução do desafio **"Criação de Skills — Refatoração Arquitetural Automatizada"**: uma Skill do Claude Code (`/refactor-arch`) que analisa, audita e refatora projetos backend legados para o padrão **MVC**, de forma agnóstica de tecnologia, validada em 3 projetos (2× Python/Flask, 1× Node.js/Express).

```
mba-ia-refactor-projects-skill/
├── README.md                        # este documento
├── code-smells-project/             # Projeto 1 — Flask (E-commerce), refatorado para src/ MVC
│   └── .claude/skills/refactor-arch/
├── ecommerce-api-legacy/            # Projeto 2 — Express (LMS + checkout), refatorado para src/ MVC
│   └── .claude/skills/refactor-arch/
├── task-manager-api/                # Projeto 3 — Flask (Task Manager), evolução incremental para MVC
│   └── .claude/skills/refactor-arch/
└── reports/
    ├── audit-project-{1,2,3}.md     # saída das Fases 1 e 2 de cada projeto
    └── validation/project-{1,2,3}.md # logs de boot + smoke test antes/depois (Fase 3)
```

A skill (idêntica nos 3 projetos):

```
.claude/skills/refactor-arch/
├── SKILL.md                              # prompt: 3 fases, regras invioláveis, formatos de saída
└── references/
    ├── project-analysis.md               # Análise de projeto (linguagem, framework, banco, domínio, arquitetura)
    ├── anti-patterns-catalog.md          # Catálogo: 19 anti-patterns com sinais de detecção e severidade
    ├── report-template.md                # Template do relatório de auditoria
    ├── mvc-guidelines.md                 # Guidelines da arquitetura MVC alvo
    └── refactoring-playbook.md           # Playbook: 14 transformações com código antes/depois
```

---

## A) Análise Manual

Feita lendo integralmente o código dos 3 projetos antes de escrever a skill. Severidades segundo a escala do desafio (CRITICAL / HIGH / MEDIUM / LOW). A lista completa, com todas as linhas, está nos relatórios em `reports/`.

### Projeto 1 — code-smells-project (Python/Flask, E-commerce)

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection em praticamente todas as queries (concatenação de strings) | `models.py:28, 47-50, 110, 291…` | `email = "' OR 1=1 --"` no `/login` autentica como admin; a busca permite ler/alterar qualquer tabela. |
| 2 | CRITICAL | Endpoint `POST /admin/query` executa SQL arbitrário e `/admin/reset-db` apaga o banco, ambos sem autenticação | `app.py:47-78` | Qualquer cliente anônimo tem controle total do banco. |
| 3 | CRITICAL | `SECRET_KEY` hardcoded e devolvida no `/health` | `app.py:7`, `controllers.py:289` | Segredo versionado e exposto publicamente. |
| 4 | CRITICAL | Senhas em texto puro (seed, cadastro e login por `WHERE senha = ...`) | `database.py:75-83`, `models.py:105-131` | Vazamento do banco revela senhas reais. |
| 5 | CRITICAL | God File: `models.py` com SQL + regras de 4 domínios | `models.py:1-314` | Nada testável em isolamento; mudanças afetam tudo. |
| 6 | HIGH | Conexão SQLite global mutável com `check_same_thread=False` | `database.py:4-11` | Estado global compartilhado entre threads, sem injeção. |
| 7 | HIGH | `GET /usuarios` devolve o campo `senha` | `models.py:83, 99` | Exposição de credenciais de todos os usuários. |
| 8 | MEDIUM | Queries N+1 nas listagens de pedidos (cursor por pedido e por item) | `models.py:171-233` | Latência cresce com pedidos × itens. |
| 9 | MEDIUM | Validação duplicada entre criar/atualizar produto; quantidade negativa aceita no pedido | `controllers.py:28-54, 72-90, 195-201` | Regras divergentes; pedido com quantidade negativa *aumenta* o estoque. |
| 10 | LOW | Magic numbers no desconto (`10000/0.1`, `5000/0.05`, `1000/0.02`) | `models.py:256-262` | Regra de negócio invisível. |
| 11 | LOW | `print` como log, inclusive com e-mails de usuários | `controllers.py:8-250` | Sem níveis, vaza PII. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | God Class `AppManager`: cria banco, seed, rotas e toda a regra de checkout/relatório | `src/AppManager.js:4-139` | Viola SRP; impossível testar ou evoluir partes isoladas. |
| 2 | CRITICAL | Credenciais de produção hardcoded (`dbPass`, `pk_live_...`) | `src/utils.js:1-7` | Acesso ao repo = acesso ao gateway de pagamento. |
| 3 | CRITICAL | Número do cartão e chave do gateway impressos em log | `src/AppManager.js:45` | Violação de PCI-DSS. |
| 4 | CRITICAL | "Hash" de senha caseiro (`badCrypto`) e senha padrão `"123456"` | `src/utils.js:17-23`, `src/AppManager.js:68` | Senhas triviais de reverter/colidir. |
| 5 | HIGH | Estado global mutável (`globalCache`, `totalRevenue`) exportado | `src/utils.js:9-15, 25` | Memória cresce sem limite; sem injeção de dependência. |
| 6 | MEDIUM | Callback hell (5 níveis) sem transação entre matrícula, pagamento e auditoria | `src/AppManager.js:37-77` | Falha parcial deixa dados inconsistentes; erros se perdem. |
| 7 | MEDIUM | N+1 no relatório financeiro (query por curso, por matrícula, por usuário, por pagamento) | `src/AppManager.js:89-125` | 1 + C + 2·M queries por requisição. |
| 8 | MEDIUM | `DELETE /api/users/:id` deixa matrículas e pagamentos órfãos | `src/AppManager.js:131-136` | Relatórios com dados de usuários inexistentes. |
| 9 | LOW | Nomes sem significado (`u`, `e`, `p`, `cid`, `cc`, `self = this`) | `src/AppManager.js:26-33` | Leitura difícil. |
| 10 | LOW | Código morto (`totalRevenue`, `dbUser`/`dbPass` nunca usados) | `src/utils.js:2-3, 10, 25` | Ruído e falsa impressão de funcionalidade. |

### Projeto 3 — task-manager-api (Python/Flask, Task Manager)

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Senhas com MD5 sem salt | `models/user.py:27-32` | Reversível por rainbow tables. |
| 2 | CRITICAL | `SECRET_KEY` e senha SMTP hardcoded | `app.py:13`, `services/notification_service.py:7-10` | Segredos versionados. |
| 3 | HIGH | `User.to_dict()` devolve o hash da senha em todas as respostas (inclusive login) | `models/user.py:16-25` | Com MD5, equivale a expor a senha. |
| 4 | HIGH | Token falso `'fake-jwt-token-' + id` e `role` aceito do corpo | `routes/user_routes.py:52, 210` | Qualquer cliente forja identidade e vira admin. |
| 5 | HIGH | Regras de negócio nas rotas; cálculo de "overdue" copiado em 6 lugares enquanto `Task.is_overdue()` e `utils/helpers.process_task_data` existem sem uso | `routes/*.py` | Camadas só no nome. |
| 6 | MEDIUM | APIs deprecated: `datetime.utcnow()` (22×) e `Model.query.get()` (16×) | vários | Quebram em futuras versões; o `seed.py` já emite `DeprecationWarning`. |
| 7 | MEDIUM | N+1 em `GET /tasks`, `/reports/summary`, `/categories`, `/users` | `routes/task_routes.py:41-57`, `routes/report_routes.py:53-68, 159-164` | Queries proporcionais ao volume. |
| 8 | MEDIUM | 12 `except:` nus, sem error handler global; `priority` string gera 500 | `routes/*.py`, `utils/helpers.py` | Falhas silenciosas e inconsistentes. |
| 9 | LOW | Imports e dependências não usados (`os, sys, json, time`, `marshmallow`, `requests`) | `app.py:7`, `routes/task_routes.py:7`, `requirements.txt` | Ruído e superfície de dependências. |
| 10 | LOW | Magic numbers/listas repetidas (status, roles, faixas 1–5), com constantes definidas e ignoradas em `utils/helpers.py:110-116` | `routes/task_routes.py:110-113` | Regras divergentes. |

---

## B) Construção da Skill

### Decisões de design

- **SKILL.md como orquestrador, referências como conhecimento.** O `SKILL.md` (≈140 linhas) define só o *processo*: 3 fases, regras invioláveis, formatos exatos de saída e quando ler cada referência. O conhecimento de domínio fica em 5 arquivos em `references/`, carregados sob demanda (*progressive disclosure*), economizando contexto nas fases que não precisam deles.
- **`disable-model-invocation: true`.** A skill altera muitos arquivos; ela só roda quando o usuário digita `/refactor-arch`, nunca por iniciativa do modelo.
- **Gate de segurança explícito.** Fases 1 e 2 são somente leitura (regra nº 1) e a Fase 2 termina com `Proceed with refactoring (Phase 3)? [y/n]`, instruindo o agente a *parar a resposta*; só um "sim" explícito libera a Fase 3.
- **Evidência verificável.** Todo finding exige `arquivo:linha` conferido na leitura real; o template proíbe findings vagos e traz exemplo bom e ruim.
- **Contrato da API como invariante.** A Fase 3 começa capturando um *baseline* (sobe o app original e chama todos os endpoints do inventário da Fase 1) e termina comparando status codes e formatos. Mudanças de contrato só por segurança, e sempre listadas.
- **Estratégia adaptativa.** `mvc-guidelines.md` traz uma tabela "estratégia por ponto de partida": God Class e monolito multi-arquivo → criar `src/` com todas as camadas; camadas parciais → evolução incremental (manter `models/`/`routes/`, adicionar `controllers/`, `config/`, `middlewares/`).
- **Ordem de execução fixa** (config → banco → erros → models → services → controllers → views → middlewares → composition root → limpeza → validação), evitando estados intermediários quebrados.

### Catálogo de anti-patterns (19)

| Severidade padrão | Anti-patterns |
|---|---|
| CRITICAL | AP-01 Credenciais hardcoded · AP-02 SQL Injection · AP-03 Endpoint perigoso/admin sem auth · AP-04 Senha insegura · AP-05 God Class/File |
| HIGH | AP-06 Regra de negócio na rota/Fat Controller · AP-07 Exposição de dados sensíveis · AP-08 Estado global/sem DI · AP-09 Auth falsa/ausente · AP-10 Debug/CORS/bind inseguros |
| MEDIUM | AP-11 N+1 · AP-12 Erros espalhados/`except` genérico · AP-13 Validação duplicada/ausente · **AP-14 APIs deprecated** · AP-15 Callback hell/sem transação · AP-16 Integridade de dados/side effects |
| LOW | AP-17 Magic numbers · AP-18 Nomes ruins/código morto · AP-19 `print` como log |

Por que esses: são exatamente as famílias encontradas na análise manual, generalizadas. Cada entrada tem **sinais de detecção concretos** (regex de grep por stack, ex.: `execute\(.*\+`, `` `SELECT .*\$\{ ``, `forEach` contendo `db.get(`), justificativa e o padrão de correção correspondente no playbook. A AP-14 traz uma tabela de APIs obsoletas → substitutas para Python, SQLAlchemy, Flask/Werkzeug, Node e Express, e instrui a procurar `DeprecationWarning`/`LegacyAPIWarning`/`[DEP0xxx]` na execução.

### Playbook (14 padrões, todos com antes/depois)

P-01 config por env · P-02 queries parametrizadas · P-03 quebrar God Class por domínio · P-04 estado global → injeção/escopo por request · P-05 rota fina → controller → model (+ side effects em service) · P-06 N+1 → JOIN/eager/GROUP BY · P-07 exceções de domínio + error handler · P-08 hash forte + serialização segura · P-09 validador único · P-10 remover/proteger endpoints perigosos, token assinado · P-11 deprecated → moderno · P-12 callback hell → async/await + transação · P-13 constantes nomeadas · P-14 nomes, código morto e logging.

### Como garanti que é agnóstica de tecnologia

- Heurísticas de detecção em tabelas multi-stack (Python, Node/TS, Go, Java/Kotlin, PHP, Ruby, C#) e padrões de grep de endpoints para Flask, Django, FastAPI, Express e Spring.
- Responsabilidades MVC definidas em termos de *o que cada camada faz/não faz* e uma tabela de dependências permitidas — independentes de framework — com layouts de referência para Flask e Express.
- Exemplos de playbook em Python **e** JavaScript.
- Validação definida em termos de comportamento (boot + smoke test vs. baseline), não de ferramenta de teste específica.
- Prova prática: a mesma pasta da skill, sem nenhuma alteração, foi usada nos 3 projetos.

### Desafios encontrados e como resolvi

| Desafio | Solução |
|---|---|
| No macOS a porta 5000 é do AirPlay Receiver e responde **403** a tudo — o primeiro baseline parecia "tudo quebrado". | Regra explícita no `SKILL.md` (3.1) para usar porta livre via env/wrapper; a config refatorada lê `PORT`. |
| Trocar `datetime.utcnow()` por `datetime.now(timezone.utc)` gera datetimes *aware* que quebram comparações com colunas *naive* do SQLite (`TypeError`). | Helper `utcnow()` que remove o tzinfo; documentado no playbook P-11 como armadilha. |
| Hash de senha forte invalidaria usuários existentes com MD5. | `check_password` aceita o hash legado uma vez e regrava com scrypt (migração transparente) — testado. |
| `sqlite3` do Node usa uma única conexão; `BEGIN` concorrente falha ("cannot start a transaction within a transaction"). | Wrapper `Database.transaction()` que enfileira transações. |
| Corrigir segurança sem quebrar "endpoints originais respondem". | Baseline + diff automático de status codes; mudanças de contrato só por segurança e documentadas (ex.: `/admin/query` removido; rotas admin do projeto 2 exigem token apenas se `ADMIN_TOKEN` estiver definido). |
| Projeto 3 "já organizado" poderia levar a skill a reportar pouco. | Seção "Procedimento de varredura" no catálogo manda procurar problemas *entre* camadas: services/helpers não usados, regra duplicada nas rotas, recurso no blueprint errado. |
| Garantir números de linha exatos. | Regra inviolável nº 3 + greps de confirmação; contagens de arquivos/linhas via `wc -l`. |

---

## C) Resultados

A skill foi executada pelo Claude Code seguindo o `SKILL.md` em cada projeto: Fases 1 e 2 (somente leitura) nos 3, pausa para confirmação do usuário, e então Fase 3 com validação.

### Findings por projeto

| Projeto | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated |
|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python + Flask 3.1.1 | 5 | 4 | 4 | 3 | **16** | nenhuma detectada |
| 2 — ecommerce-api-legacy | Node.js + Express ^4.18.2 | 4 | 3 | 5 | 4 | **16** | nenhuma formal (callbacks → AP-15) |
| 3 — task-manager-api | Python + Flask 3.0.0 / SQLAlchemy | 2 | 4 | 5 | 4 | **15** | `datetime.utcnow` (22×), `Query.get` (16×) |

### Antes / depois

**Projeto 1 — monolito multi-arquivo → MVC em `src/`**
```
ANTES                         DEPOIS
app.py        (88 linhas)     app.py                       # entry point (python app.py)
controllers.py (292)          .env.example
models.py     (314)           src/
database.py    (86)           ├── app.py                   # composition root: create_app()
                              ├── config/settings.py
                              ├── database.py              # conexão por request (flask.g), schema, seed com hash
                              ├── errors.py
                              ├── models/      produto_model, usuario_model, pedido_model
                              ├── controllers/ produto, usuario, pedido, relatorio, admin
                              ├── views/       produto, usuario, pedido, relatorio, main (Blueprints)
                              ├── services/    notification_service
                              └── middlewares/ error_handler, admin_auth
```

**Projeto 2 — God Class → MVC em `src/`**
```
ANTES                          DEPOIS
src/app.js        (14)         src/app.js            # composition root: createApp() + listen
src/AppManager.js (141)        src/config/           index.js, logger.js
src/utils.js      (25)         src/database/         connection.js (Promise + transação), schema.js
                               src/errors/           AppError.js
                               src/models/           user, course, enrollment, payment, auditLog
                               src/services/         payment, password (scrypt), cache
                               src/controllers/      checkout, report, user
                               src/routes/           checkout, admin, user (express.Router)
                               src/middlewares/      asyncHandler, errorHandler, requireAdmin
```

**Projeto 3 — camadas parciais → evolução incremental**
```
ANTES                               DEPOIS
app.py  (config hardcoded)          app.py              # create_app() + entry point
database.py                         config/settings.py  # NOVO
models/  task, user, category       errors.py           # NOVO
routes/  task, user, report(+cat.)  models/             # sem password no to_dict, constantes, utcnow
services/ notification (não usado)  controllers/        # NOVO: task, user, category, report
utils/   helpers (não usado)        routes/             # Views finas: task, user, category (NOVO), report
                                    services/           # notification (config injetada), auth (token assinado)
                                    middlewares/        # NOVO: error_handler
                                    utils/              # helpers de data + validators
```

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ | ✅ | ✅ |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express ^4.18.2 | ✅ Flask 3.0.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS + checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 / 780 linhas | ✅ 3 / 180 linhas | ✅ 12 (+3 `__init__` vazios) / 1158 linhas |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 16 | ✅ 16 | ✅ 15 |
| APIs deprecated (se aplicável) | ✅ seção presente (nenhuma) | ✅ seção presente (nenhuma formal) | ✅ 38 ocorrências |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura segue MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ `src/config/settings.py` | ✅ `src/config/index.js` | ✅ `config/settings.py` |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ `src/views/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `python app.py` | ✅ `npm start` | ✅ `python app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ (sem DeprecationWarning) |
| Endpoints originais respondem corretamente | ✅ 22/22 | ✅ 7/7 | ✅ 28/28 |

### Logs da aplicação rodando após a refatoração

Logs completos (boot + smoke test **antes** e **depois**, lado a lado) em `reports/validation/project-{1,2,3}.md`. Trechos:

```
# Projeto 1 — PORT=5055 python app.py
 * Serving Flask app 'src.app'
 * Debug mode: off
 * Running on http://127.0.0.1:5055
GET     /produtos                        -> 200 {"dados":[{"ativo":1,"categoria":"informatica",...
POST    /pedidos                         -> 201 {"dados":{"pedido_id":1,"total":6179.79},...
POST    /admin/query                     -> 404   (removido: executava SQL arbitrário)
POST    /login  email="' OR 1=1 --"      -> 401   (antes: SQL injection)

# Projeto 2 — npm start
[2026-10-21T18:06:25.053Z] INFO LMS API rodando na porta 3000
[2026-10-21T18:06:26.859Z] INFO Processando pagamento {"last4":"4444","amount":497}
POST    /api/checkout                    -> 200 {"msg":"Sucesso","enrollment_id":2}
GET     /api/admin/financial-report      -> 200 [{"course":"Clean Architecture","revenue":997,...
DELETE  /api/users/1                     -> 200 Usuário deletado

# Projeto 3 — python seed.py && PORT=5056 python app.py
Seed concluído com sucesso!  (3 usuários, 4 categorias, 10 tasks)
 * Running on http://127.0.0.1:5056
GET     /tasks/stats                     -> 200 {"cancelled":1,"completion_rate":10.0,"done":1,...
POST    /login                           -> 200 {"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxLCJyb2xl...
```

### Mudanças de contrato (todas por segurança)

- **P1:** `POST /admin/query` removido; `POST /admin/reset-db` exige `X-Admin-Token` (= `ADMIN_TOKEN`); `senha` fora das respostas de usuário; `/health` sem `secret_key`/`db_path`/`debug`; erros passam a incluir `"sucesso": false`; e-mail duplicado → 409.
- **P2:** com `ADMIN_TOKEN` definido, relatório e DELETE exigem `X-Admin-Token`; DELETE remove matrículas/pagamentos e retorna 404 para id inexistente; checkout sem `pwd` gera senha aleatória.
- **P3:** `password` fora das respostas; `token` do login passa a ser assinado; novas senhas com mínimo de 8 caracteres.

### Observações sobre stacks diferentes

- **Monolito Python (P1):** a skill escolheu "monolito multi-arquivo (pseudo-camadas)" — os arquivos já se chamavam `models.py`/`controllers.py`, mas sem fronteiras reais. A transformação dividiu o antigo `controllers.py` em *views* (parte HTTP) e *controllers* (fluxo), conforme a tabela de estratégia.
- **Node (P2):** os maiores ganhos vieram de AP-15 (callbacks → `async/await` + transação) e AP-11 (relatório com 1 JOIN). Como o driver `sqlite3` não tem API Promise, o playbook previu o wrapper em vez de trocar dependência (regra "sem dependências novas"). Respostas de erro em texto puro foram preservadas pelo error handler.
- **Flask já organizado (P3):** a skill não "jogou fora" a estrutura: manteve `models/` e `routes/`, criou as camadas que faltavam e deu uso real ao que estava morto (`Task.is_overdue`, `NotificationService`). Foi o único projeto com APIs deprecated relevantes, confirmadas pelos warnings emitidos pelo próprio `seed.py`.
- Nos três casos o baseline capturado antes da refatoração foi essencial para provar que nada quebrou.

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`).
- Python 3.10+ (projetos 1 e 3) e Node.js 18+ (projeto 2) para a validação da Fase 3.
- Recomendado: um virtualenv por projeto Python.

### Executar a skill

A skill fica em `.claude/skills/refactor-arch/` de cada projeto e é invocada pelo nome:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Fluxo: a skill imprime **PHASE 1: PROJECT ANALYSIS**, depois o **ARCHITECTURE AUDIT REPORT** e para em `Proceed with refactoring (Phase 3)? [y/n]`. Revise o relatório (salve-o em `reports/audit-project-N.md`) e responda `y` para refatorar. Ordem sugerida: projeto 1 → 2 → 3 (do mais desestruturado ao mais organizado). Para reaplicar em um projeto já refatorado, use `git checkout <commit-anterior> -- <pasta>` antes.

### Validar que a refatoração funcionou

```bash
# Projeto 1 (porta alternativa por causa do AirPlay no macOS)
cd code-smells-project && pip install -r requirements.txt
PORT=5055 python app.py
curl -s localhost:5055/produtos | head -c 200
curl -s -X POST localhost:5055/login -H 'Content-Type: application/json' \
     -d '{"email":"joao@email.com","senha":"123456"}'

# Projeto 2
cd ecommerce-api-legacy && npm install && npm start
# use as requisições de api.http, ex.:
curl -s -X POST localhost:3000/api/checkout -H 'Content-Type: application/json' \
     -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'

# Projeto 3
cd task-manager-api && pip install -r requirements.txt
python seed.py && PORT=5056 python app.py
curl -s localhost:5056/tasks/stats
```

Os comandos completos do smoke test (todas as rotas, sucesso e erro) e as saídas esperadas estão em `reports/validation/project-{1,2,3}.md`.
