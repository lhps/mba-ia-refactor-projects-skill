# Audit Report — Projeto 1: code-smells-project

> Saída das Fases 1 e 2 da skill `/refactor-arch` executada em `code-smells-project/`.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não fixada; validado com 3.13)
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, usuários, pedidos, relatórios de vendas)
Architecture:  Monolito multi-arquivo (pseudo-camadas) — models.py concentra SQL + regras de 4 domínios; controllers.py lê request e acessa o banco
Source files:  4 files analyzed (~780 lines)
DB:            SQLite (loja.db) via driver sqlite3 cru, SQL manual
DB tables:     produtos, usuarios, pedidos, itens_pedido
Entry point:   app.py — `python app.py` (porta 5000)
Endpoints:     19 endpoints mapeados
================================
```

| Método | Path | Handler | Arquivo:linha |
|---|---|---|---|
| GET | /produtos | controllers.listar_produtos | app.py:11 |
| GET | /produtos/busca | controllers.buscar_produtos | app.py:12 |
| GET | /produtos/<id> | controllers.buscar_produto | app.py:13 |
| POST | /produtos | controllers.criar_produto | app.py:14 |
| PUT | /produtos/<id> | controllers.atualizar_produto | app.py:15 |
| DELETE | /produtos/<id> | controllers.deletar_produto | app.py:16 |
| GET | /usuarios | controllers.listar_usuarios | app.py:18 |
| GET | /usuarios/<id> | controllers.buscar_usuario | app.py:19 |
| POST | /usuarios | controllers.criar_usuario | app.py:20 |
| POST | /login | controllers.login | app.py:21 |
| POST | /pedidos | controllers.criar_pedido | app.py:23 |
| GET | /pedidos | controllers.listar_todos_pedidos | app.py:24 |
| GET | /pedidos/usuario/<usuario_id> | controllers.listar_pedidos_usuario | app.py:25 |
| PUT | /pedidos/<pedido_id>/status | controllers.atualizar_status_pedido | app.py:26 |
| GET | /relatorios/vendas | controllers.relatorio_vendas | app.py:28 |
| GET | /health | controllers.health_check | app.py:30 |
| GET | / | index | app.py:32-45 |
| POST | /admin/reset-db | reset_database | app.py:47-57 |
| POST | /admin/query | executar_query | app.py:59-78 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Architecture (current): Monolito multi-arquivo (pseudo-camadas)
```

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 4 | LOW: 3

| # | Severity | Anti-pattern | File |
|---|----------|--------------|------|
| 1 | CRITICAL | AP-03 Endpoint perigoso | app.py:47-78 |
| 2 | CRITICAL | AP-01 Credenciais hardcoded | app.py:7, controllers.py:289 |
| 3 | CRITICAL | AP-04 Senha em texto puro | database.py:75-83, models.py:105-131 |
| 4 | CRITICAL | AP-02 SQL Injection | models.py:28-297 |
| 5 | CRITICAL | AP-05 God File | models.py:1-314 |
| 6 | HIGH | AP-10 Debug/host/CORS inseguros | app.py:8-9, 88 |
| 7 | HIGH | AP-06 Controller acoplado a HTTP + regras + side effects | controllers.py:24-62, 188-255 |
| 8 | HIGH | AP-07 Exposição de dados sensíveis | controllers.py:264-290, models.py:72-103 |
| 9 | HIGH | AP-08 Estado global mutável | database.py:4-11 |
| 10 | MEDIUM | AP-12 Tratamento de erro espalhado | controllers.py (16 blocos) |
| 11 | MEDIUM | AP-13 Validação duplicada/ausente | controllers.py:28-54, 72-90, 146-201 |
| 12 | MEDIUM | AP-11 Queries N+1 | models.py:133-233, 239-254 |
| 13 | MEDIUM | AP-16 Integridade/efeitos colaterais | controllers.py:245-250, models.py:275-283 |
| 14 | LOW | AP-17 Magic numbers/strings | controllers.py:47-52, 242, models.py:256-262 |
| 15 | LOW | AP-19 print como log | controllers.py:8-250, app.py:56, 83-86 |
| 16 | LOW | AP-18 Código duplicado/morto e nomes | models.py:2, 12-21, 31-40, 304-313, database.py:2 |

## Findings

### #1 [CRITICAL] Endpoints administrativos executam SQL arbitrário sem autenticação
File: app.py:47-78
Category: Security
Anti-pattern: AP-03 Endpoint perigoso / execução arbitrária
Description: `POST /admin/query` (app.py:59-78) executa `cursor.execute(query)` com o SQL recebido no corpo; `POST /admin/reset-db` (app.py:47-57) apaga todas as tabelas. Nenhum dos dois verifica identidade.
Impact: Qualquer cliente anônimo lê, altera ou destrói todo o banco (inclusive senhas).
Recommendation: Remover `/admin/query`; proteger `/admin/reset-db` com token administrativo vindo de config e comparado em tempo constante (Playbook P-10).

### #2 [CRITICAL] SECRET_KEY hardcoded e exposta pela API
File: app.py:7, controllers.py:289
Category: Security
Anti-pattern: AP-01 Credenciais hardcoded
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` versionado; o mesmo valor é devolvido no JSON de `/health` (controllers.py:289).
Impact: Permite forjar sessões/assinaturas; segredo público para qualquer cliente que chame `/health`.
Recommendation: Ler `SECRET_KEY` de variável de ambiente em `config/settings.py` (chave efêmera se ausente) e nunca serializá-la (Playbook P-01, P-08).

### #3 [CRITICAL] Senhas armazenadas e comparadas em texto puro
File: database.py:75-83, models.py:105-131
Category: Security
Anti-pattern: AP-04 Armazenamento inseguro de senha
Description: Seeds gravam `"admin123"`, `"123456"`, `"senha123"` em claro; `criar_usuario` grava a senha recebida; `login_usuario` compara `WHERE email = ... AND senha = ...`.
Impact: Vazamento do banco revela todas as senhas; o login depende da senha em texto puro.
Recommendation: `werkzeug.security.generate_password_hash`/`check_password_hash`; seed com hashes; buscar por email e verificar o hash no código (Playbook P-08).

### #4 [CRITICAL] SQL Injection por concatenação de strings
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, 289-297
Category: Security
Anti-pattern: AP-02 SQL Injection
Description: Praticamente todas as queries concatenam valores do usuário, ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:110) e `LIKE '%" + termo + "%'` (models.py:291).
Impact: `email = "' OR 1=1 --"` autentica como admin; busca permite exfiltrar/alterar qualquer tabela.
Recommendation: Placeholders `?` com tupla de parâmetros em todas as queries; WHERE dinâmico montado com lista de cláusulas fixas + params (Playbook P-02).

### #5 [CRITICAL] God File: models.py concentra 4 domínios, SQL e regras de negócio
File: models.py:1-314
Category: Architecture
Anti-pattern: AP-05 God Class / God File
Description: Um único módulo contém acesso a dados e regras de produtos, usuários, pedidos e relatórios (incl. cálculo de desconto em models.py:256-262 e baixa de estoque em 163-166), com serialização row→dict repetida.
Impact: Impossível testar um domínio isoladamente; qualquer mudança arrisca todos os fluxos.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`; regras de relatório/pedido em controllers (Playbook P-03).

### #6 [HIGH] Debug ligado, bind em 0.0.0.0 e CORS aberto fixos no código
File: app.py:8-9, 88
Category: Security
Anti-pattern: AP-10 Configuração insegura de execução
Description: `app.config["DEBUG"] = True`, `CORS(app)` sem restrição de origem e `app.run(host="0.0.0.0", port=5000, debug=True)`.
Impact: Debugger do Werkzeug exposto na rede permite execução remota de código; qualquer origem consome a API.
Recommendation: `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS` vindos de env com defaults seguros (debug off, 127.0.0.1) (Playbook P-01).

### #7 [HIGH] "Controllers" misturam HTTP, validação, regras e notificações
File: controllers.py:24-62, 188-255
Category: Architecture
Anti-pattern: AP-06 Regra de negócio na camada de roteamento / Fat Controller
Description: Cada função lê `request.get_json()`, valida, chama o banco e monta `jsonify`; `criar_pedido` dispara "EMAIL/SMS/PUSH" via print (208-210) e `atualizar_status_pedido` decide notificações (247-250). `health_check` executa SQL direto (264-274).
Impact: Regras presas ao Flask; impossível reutilizar ou testar sem subir servidor; side effects não desligáveis.
Recommendation: Separar Views (Blueprints finos) de Controllers (sem `request`/`jsonify`) e mover notificações para `services/notification_service.py` injetado (Playbook P-05).

### #8 [HIGH] Senhas e configuração interna expostas nas respostas
File: controllers.py:264-290, models.py:72-103
Category: Security
Anti-pattern: AP-07 Exposição de dados sensíveis
Description: `GET /usuarios` e `GET /usuarios/<id>` retornam o campo `senha` (models.py:83, 99); `/health` devolve `db_path`, `debug` e `secret_key` (controllers.py:285-289).
Impact: Qualquer cliente coleta credenciais de todos os usuários e detalhes de infraestrutura.
Recommendation: Serializador de usuário sem `senha`; health apenas com status e contagens (Playbook P-08).

### #9 [HIGH] Conexão global mutável compartilhada entre threads
File: database.py:4-11
Category: Architecture
Anti-pattern: AP-08 Estado global mutável
Description: `global db_connection` com `sqlite3.connect(..., check_same_thread=False)` reutilizada por todas as requisições; schema e seed criados como efeito colateral do primeiro `get_db()`.
Impact: Condições de corrida em requisições concorrentes; impossível injetar banco de teste.
Recommendation: Conexão por request em `flask.g` fechada no `teardown_appcontext`; `init_db()` explícito no composition root; caminho do banco via config (Playbook P-04).

### #10 [MEDIUM] try/except genérico repetido devolvendo str(e)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Category: Reliability
Anti-pattern: AP-12 Tratamento de erros espalhado
Description: 16 blocos `except Exception as e: return jsonify({"erro": str(e)}), 500`; `login` (169-171) e `atualizar_status_pedido` (239-240) quebram com 500 se o corpo não for JSON.
Impact: Mensagens internas vazam ao cliente; comportamento de erro inconsistente.
Recommendation: Exceções de domínio + `@app.errorhandler` centralizado em `middlewares/error_handler.py` (Playbook P-07).

### #11 [MEDIUM] Validação duplicada e incompleta
File: controllers.py:28-54, 72-90, 146-201
Category: Maintainability
Anti-pattern: AP-13 Validação ausente/duplicada
Description: Regras de produto copiadas entre criar (28-54) e atualizar (72-90), mas o update não valida tamanho do nome nem categoria; `criar_usuario` não valida email; `criar_pedido` não valida `quantidade` (aceita negativa, aumentando o estoque).
Impact: Dados inválidos no banco; correções precisam ser feitas em vários lugares.
Recommendation: `validar_produto()`, `validar_usuario()`, `validar_itens_pedido()` únicos chamados pelos controllers (Playbook P-09).

### #12 [MEDIUM] Queries N+1 e consultas redundantes
File: models.py:133-169, 171-201, 203-233, 239-254
Category: Performance
Anti-pattern: AP-11 Queries N+1
Description: Listagens de pedidos fazem 1 query por pedido para itens e 1 por item para o nome do produto (cursor2/cursor3); `criar_pedido` busca cada produto duas vezes; o relatório executa 5 queries COUNT/SUM separadas.
Impact: Latência cresce linearmente com pedidos × itens.
Recommendation: JOIN `itens_pedido` × `produtos` com `IN (...)`; agregação `GROUP BY status` (Playbook P-06).

### #13 [MEDIUM] Atualização de status sem regras de integridade
File: controllers.py:245-250, models.py:275-283
Category: Reliability
Anti-pattern: AP-16 Integridade de dados / efeitos colaterais acoplados
Description: Cancelar pedido apenas imprime "Devolver estoque" sem devolver; o UPDATE não verifica se o pedido existe (retorna 200 para id inexistente).
Impact: Estoque inconsistente; clientes recebem sucesso para operações que não ocorreram.
Recommendation: Controller verifica existência (404), devolve estoque em transação ao cancelar e delega notificação a service (Playbook P-05, P-12).

### #14 [LOW] Magic numbers e listas de domínio inline
File: controllers.py:47-52, 242, models.py:256-262
Category: Maintainability
Anti-pattern: AP-17 Magic numbers/strings
Description: Faixas de desconto `10000/0.1`, `5000/0.05`, `1000/0.02`; limites `2`/`200` do nome; listas de categorias e status literais.
Impact: Regras de negócio invisíveis e fáceis de divergir.
Recommendation: Constantes nomeadas no model (`FAIXAS_DESCONTO`, `CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`) (Playbook P-13).

### #15 [LOW] print usado como log
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, 83-86
Category: Maintainability
Anti-pattern: AP-19 print como log
Description: Eventos de negócio, erros e emails de usuários registrados com `print`.
Impact: Sem níveis nem destino configurável; vaza PII em stdout.
Recommendation: `logging.getLogger(__name__)` com níveis (Playbook P-14).

### #16 [LOW] Serialização duplicada, imports mortos e nomes ruins
File: models.py:2, 12-21, 31-40, 304-313, database.py:2
Category: Maintainability
Anti-pattern: AP-18 Nomenclatura ruim e código morto
Description: Mapeamento row→dict de produto copiado 3 vezes; `import sqlite3` (models.py:2) e `import os` (database.py:2) sem uso; parâmetro `id` sombreia builtin.
Impact: Ruído e risco de divergência ao alterar campos.
Recommendation: Função única `_row_to_produto()`; remover imports; renomear `id` → `produto_id` (Playbook P-14).

## Deprecated APIs
| File:line | Deprecated API | Modern replacement |
|-----------|----------------|--------------------|
| — | Nenhuma API deprecated detectada (Flask 3.1 / sqlite3 usados com APIs atuais; boot não emite DeprecationWarning) | — |

## Refactoring Plan (Phase 3 preview)
Strategy: monolito multi-arquivo → MVC completo em `src/`, mantendo `app.py` na raiz como entry point.
Target structure:
```
app.py                          # entry point (python app.py)
src/
├── app.py                      # composition root: create_app()
├── config/settings.py          # Config (env vars)
├── database.py                 # conexão por request + schema + seed (hash)
├── errors.py                   # AppError, NotFoundError, ValidationError...
├── models/                     # produto_model, usuario_model, pedido_model
├── controllers/                # produto, usuario, pedido, relatorio, health
├── views/                      # Blueprints por domínio
├── services/notification_service.py
└── middlewares/                # error_handler, admin_auth
```
Key transformations:
- P-01 → #2, #6 · P-02 → #4 · P-03 → #5 · P-04 → #9 · P-05 → #7, #13 · P-06 → #12
- P-07 → #10 · P-08 → #3, #8 · P-09 → #11 · P-10 → #1 · P-13 → #14 · P-14 → #15, #16
API contract changes (security-driven): remover `POST /admin/query`; `POST /admin/reset-db` exige header `X-Admin-Token`; respostas de usuário sem `senha`; `/health` sem `secret_key`/`db_path`/`debug`.

```
================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
