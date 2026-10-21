# Audit Report — Projeto 2: ecommerce-api-legacy

> Saída das Fases 1 e 2 da skill `/refactor-arch` executada em `ecommerce-api-legacy/`.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js — versão não fixada; validado com v22)
Framework:     Express ^4.18.2
Dependencies:  sqlite3 ^5.1.6
Domain:        LMS (plataforma de cursos) com fluxo de checkout — usuários, cursos, matrículas, pagamentos, auditoria
Architecture:  God Class — AppManager.js cria schema, faz seed, registra rotas e contém toda a regra de checkout/relatório
Source files:  3 files analyzed (~180 lines)
DB:            SQLite em memória (':memory:') via driver sqlite3 com callbacks, SQL manual
DB tables:     users, courses, enrollments, payments, audit_logs
Entry point:   src/app.js — `npm start` (porta 3000)
Endpoints:     3 endpoints mapeados
================================
```

| Método | Path | Handler | Arquivo:linha |
|---|---|---|---|
| POST | /api/checkout | AppManager.setupRoutes (inline) | src/AppManager.js:28-78 |
| GET | /api/admin/financial-report | AppManager.setupRoutes (inline) | src/AppManager.js:80-129 |
| DELETE | /api/users/:id | AppManager.setupRoutes (inline) | src/AppManager.js:131-137 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code
Architecture (current): God Class (AppManager)
```

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 5 | LOW: 4

| # | Severity | Anti-pattern | File |
|---|----------|--------------|------|
| 1 | CRITICAL | AP-05 God Class | src/AppManager.js:4-139 |
| 2 | CRITICAL | AP-07 Dados de cartão e chave em log | src/AppManager.js:45 |
| 3 | CRITICAL | AP-04 Hash de senha inseguro | src/AppManager.js:18, 68, src/utils.js:17-23 |
| 4 | CRITICAL | AP-01 Credenciais hardcoded | src/utils.js:1-7 |
| 5 | HIGH | AP-09 Rotas admin/destrutivas sem auth | src/AppManager.js:80, 131 |
| 6 | HIGH | AP-06 Regra de negócio no handler | src/AppManager.js:28-78 |
| 7 | HIGH | AP-08 Estado global mutável / sem DI | src/AppManager.js:5-8, src/utils.js:9-15, 25 |
| 8 | MEDIUM | AP-15 Callback hell sem transação | src/AppManager.js:37-77, 83-128 |
| 9 | MEDIUM | AP-11 Queries N+1 | src/AppManager.js:89-125 |
| 10 | MEDIUM | AP-16 Registros órfãos no DELETE | src/AppManager.js:131-136 |
| 11 | MEDIUM | AP-12 Erros ignorados/mal mapeados | src/AppManager.js:38, 57, 92-93, 104-106, 133 |
| 12 | MEDIUM | AP-13 Validação insuficiente | src/AppManager.js:35, 68 |
| 13 | LOW | AP-18 Nomes ruins | src/AppManager.js:26, 29-33, src/utils.js:17 |
| 14 | LOW | AP-18 Código morto | src/AppManager.js:2, src/utils.js:2-3, 10, 25 |
| 15 | LOW | AP-17 Magic strings | src/AppManager.js:46, 108 |
| 16 | LOW | AP-19 console.log como log | src/AppManager.js:45, src/utils.js:13 |

## Findings

### #1 [CRITICAL] God Class AppManager: banco, seed, rotas e regras no mesmo objeto
File: src/AppManager.js:4-139
Category: Architecture
Anti-pattern: AP-05 God Class
Description: `AppManager` instancia o banco (7), cria schema e seed (10-23) e registra as 3 rotas com toda a lógica de checkout, pagamento, auditoria e relatório inline (25-138).
Impact: Nenhuma parte é testável isoladamente; qualquer alteração mexe na classe inteira (viola SRP/OCP).
Recommendation: Separar em `database/`, `models/` (user, course, enrollment, payment, audit), `controllers/` (checkout, report, user), `routes/` e `services/` (Playbook P-03).

### #2 [CRITICAL] Número de cartão e chave do gateway impressos em log
File: src/AppManager.js:45
Category: Security
Anti-pattern: AP-07 Exposição de dados sensíveis
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava PAN completo e a chave `pk_live_...`.
Impact: Violação de PCI-DSS; logs passam a conter dados de cartão e segredo de produção.
Recommendation: Remover o log ou registrar apenas os 4 últimos dígitos; nunca logar chaves (Playbook P-08).

### #3 [CRITICAL] "Hash" de senha caseiro e reversível
File: src/utils.js:17-23, src/AppManager.js:18, 68
Category: Security
Anti-pattern: AP-04 Armazenamento inseguro de senha
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e trunca em 10 chars (sem salt, colisões triviais); seed grava `'123'` em claro (18); senha ausente vira `"123456"` (68).
Impact: Senhas recuperáveis/colidíveis; contas criadas no checkout ficam com senha padrão conhecida.
Recommendation: `crypto.scryptSync` com salt aleatório (stdlib); exigir senha no checkout de novo usuário (Playbook P-08).

### #4 [CRITICAL] Credenciais de produção hardcoded
File: src/utils.js:1-7
Category: Security
Anti-pattern: AP-01 Credenciais hardcoded
Description: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser` e porta fixos em `utils.js`.
Impact: Acesso ao repositório = acesso ao banco e ao gateway de pagamento de produção.
Recommendation: `src/config/index.js` lendo `process.env` + `.env.example` (Playbook P-01).

### #5 [HIGH] Relatório financeiro e exclusão de usuário sem autenticação
File: src/AppManager.js:80, 131
Category: Security
Anti-pattern: AP-09 Autenticação/autorização ausente
Description: `GET /api/admin/financial-report` expõe receita e nomes de alunos e `DELETE /api/users/:id` apaga usuários sem qualquer verificação.
Impact: Qualquer cliente lê dados financeiros e apaga contas.
Recommendation: Middleware `requireAdmin` baseado em token de config (`ADMIN_TOKEN`) aplicado às rotas admin/destrutivas, habilitável sem quebrar o contrato em dev (Playbook P-10).

### #6 [HIGH] Fluxo de checkout inteiro dentro do handler HTTP
File: src/AppManager.js:28-78
Category: Architecture
Anti-pattern: AP-06 Regra de negócio na camada de roteamento
Description: O handler valida entrada, busca curso, cria usuário, decide pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`, linha 46), matricula, registra pagamento, audita e cacheia.
Impact: Regra de pagamento presa ao Express; impossível testar ou trocar o gateway.
Recommendation: `CheckoutController.checkout()` + `PaymentService.charge()`; rota apenas mapeia `req.body` → input (Playbook P-05).

### #7 [HIGH] Estado global mutável e dependências não injetadas
File: src/AppManager.js:5-8, src/utils.js:9-15, 25
Category: Architecture
Anti-pattern: AP-08 Estado global mutável
Description: `let globalCache = {}` e `let totalRevenue = 0` exportados e mutados por `logAndCache`; a conexão `new sqlite3.Database(':memory:')` é criada dentro do construtor da classe de rotas.
Impact: Cache cresce sem limite e é compartilhado por todo o processo; impossível substituir banco/cache em testes.
Recommendation: `CacheService` e `Database` instanciados no composition root e injetados nos controllers (Playbook P-04).

### #8 [MEDIUM] Callback hell sem transação no checkout e no relatório
File: src/AppManager.js:37-77, 83-128
Category: Reliability
Anti-pattern: AP-15 Callback hell
Description: 5 níveis de callbacks (`get` → `get` → `run` → `run` → `run`) com `self = this`; o relatório usa contadores manuais `coursesPending--/enrPending--`. Matrícula, pagamento e auditoria são gravados sem `BEGIN/COMMIT`.
Impact: Falha no INSERT de pagamento deixa matrícula sem pagamento; erros se perdem em callbacks.
Recommendation: Wrapper Promise sobre sqlite3, `async/await` e `db.transaction()` (Playbook P-12).

### #9 [MEDIUM] Relatório financeiro com N+1 queries
File: src/AppManager.js:89-125
Category: Performance
Anti-pattern: AP-11 Queries N+1
Description: Para cada curso, 1 query de matrículas; para cada matrícula, 1 query de usuário e 1 de pagamento.
Impact: 1 + C + 2·M queries por requisição; degrada linearmente.
Recommendation: Uma query com `LEFT JOIN` courses × enrollments × users × payments agrupada em memória (Playbook P-06).

### #10 [MEDIUM] DELETE de usuário deixa matrículas e pagamentos órfãos
File: src/AppManager.js:131-136
Category: Reliability
Anti-pattern: AP-16 Integridade de dados
Description: Apaga apenas `users`; a própria resposta admite "as matrículas e pagamentos ficaram sujos no banco". Usuário inexistente também retorna 200.
Impact: Relatórios contam receita de usuários inexistentes ("Unknown").
Recommendation: Excluir payments → enrollments → user em transação; 404 se não existir (Playbook P-12).

### #11 [MEDIUM] Erros de banco ignorados ou mal mapeados
File: src/AppManager.js:38, 57, 92-93, 104-106, 133
Category: Reliability
Anti-pattern: AP-12 Tratamento de erros espalhado
Description: Erro de DB vira 404 "Curso não encontrado" (38); `err` ignorado no audit log (57), no relatório (`enrollments.length` com `enrollments` indefinido quebra o processo, 92-93) e no DELETE (133).
Impact: Crash do servidor em falha de banco; respostas enganosas.
Recommendation: `asyncHandler` + middleware de erro Express com `AppError` (Playbook P-07).

### #12 [MEDIUM] Validação de entrada insuficiente
File: src/AppManager.js:35, 68
Category: Maintainability
Anti-pattern: AP-13 Validação ausente
Description: Só verifica presença de `usr`, `eml`, `c_id`, `card`; não valida formato de email/cartão; senha opcional com fallback fixo.
Impact: Dados inválidos persistidos; contas com senha conhecida.
Recommendation: `validateCheckoutInput()` no controller (Playbook P-09).

### #13 [LOW] Nomes de variáveis sem significado
File: src/AppManager.js:26, 29-33, src/utils.js:17
Category: Maintainability
Anti-pattern: AP-18 Nomenclatura ruim
Description: `u`, `e`, `p`, `cid`, `cc`, `self = this`, função `badCrypto`, config em arquivo `utils.js`.
Impact: Leitura difícil; intenção oculta.
Recommendation: Mapear o body (contrato mantido) para `{ name, email, password, courseId, card }` (Playbook P-14).

### #14 [LOW] Código e configuração mortos
File: src/AppManager.js:2, src/utils.js:2-3, 10, 25
Category: Maintainability
Anti-pattern: AP-18 Código morto
Description: `totalRevenue` exportado/importado e nunca usado; `dbUser`/`dbPass` nunca lidos (banco é em memória).
Impact: Ruído e falsa impressão de funcionalidade.
Recommendation: Remover (Playbook P-14).

### #15 [LOW] Magic strings de regra de pagamento
File: src/AppManager.js:46, 108
Category: Maintainability
Anti-pattern: AP-17 Magic numbers/strings
Description: Prefixo `"4"` decide aprovação; status `'PAID'`/`'DENIED'` literais repetidos.
Impact: Regra de aprovação escondida no handler.
Recommendation: `PAYMENT_STATUS` e `APPROVED_CARD_PREFIX` no `PaymentService` (Playbook P-13).

### #16 [LOW] console.log como log
File: src/AppManager.js:45, src/utils.js:13
Category: Maintainability
Anti-pattern: AP-19 print como log
Description: Logs sem nível em fluxo de negócio.
Impact: Sem controle de verbosidade; facilita vazamento (ver #2).
Recommendation: Logger mínimo com níveis em `src/config/logger.js` (Playbook P-14).

## Deprecated APIs
| File:line | Deprecated API | Modern replacement |
|-----------|----------------|--------------------|
| — | Nenhuma API formalmente deprecated detectada (Express 4 usado com `express.json()`, `Buffer.from`; boot sem avisos `[DEP0xxx]`). O uso de callbacks do `sqlite3` é tratado como AP-15 com recomendação de wrapper Promise/async-await. | — |

## Refactoring Plan (Phase 3 preview)
Strategy: God Class → MVC completo em `src/` (mantém `npm start` → `node src/app.js`).
Target structure:
```
src/
├── app.js                      # composition root + listen
├── config/index.js             # env vars
├── database/connection.js      # wrapper Promise + transaction + schema/seed
├── errors/AppError.js
├── models/                     # user, course, enrollment, payment, auditLog
├── services/                   # payment, password, cache
├── controllers/                # checkout, report, user
├── routes/                     # checkout, admin, user (express.Router)
└── middlewares/                # errorHandler, asyncHandler, requireAdmin
```
Key transformations:
- P-03 → #1 · P-08 → #2, #3 · P-01 → #4 · P-10 → #5 · P-05 → #6 · P-04 → #7
- P-12 → #8, #10 · P-06 → #9 · P-07 → #11 · P-09 → #12 · P-13 → #15 · P-14 → #13, #14, #16
API contract changes (security-driven): rotas admin/destrutivas exigem `X-Admin-Token` **apenas quando `ADMIN_TOKEN` estiver configurado** (dev mantém comportamento); DELETE de usuário agora remove dependentes e retorna 404 para id inexistente; checkout de novo usuário sem `pwd` gera senha aleatória em vez de `"123456"`.

```
================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
