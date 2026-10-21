# Catálogo de Anti-Patterns (Fase 2)

## Escala de severidade

| Severidade | Definição | Exemplos típicos |
|---|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: impede funcionamento correto, expõe dados sensíveis ou viola completamente a separação de responsabilidades | Credenciais hardcoded, SQL Injection, execução de SQL arbitrário via API, senha em texto puro/hash quebrado, God Class com DB + regras + rotas |
| **HIGH** | Violação forte de MVC/SOLID que dificulta muito manutenção e testes | Regra de negócio pesada em rota/controller, acoplamento sem injeção de dependência, estado global mutável, dados sensíveis em respostas, autenticação falsa, debug ligado em produção |
| **MEDIUM** | Padronização, duplicação, performance moderada | Queries N+1, validação ausente/duplicada, tratamento de erro espalhado/`except` genérico, callback hell, APIs deprecated, falta de transação |
| **LOW** | Legibilidade e higiene | Magic numbers/strings, nomes ruins, imports/dependências não usados, `print` como log, código morto |

Regra de desempate: quando um mesmo problema atinge segurança **e** arquitetura, use a maior severidade aplicável. Ajuste a severidade ao contexto (ex.: segredo de *teste* em arquivo de exemplo pode ser LOW; segredo `pk_live_` é CRITICAL).

Cada entrada abaixo traz: **sinais de detecção** (o que procurar — com padrões de grep por stack), **severidade padrão**, **por que importa** e o **padrão de correção** em `refactoring-playbook.md`.

---

## AP-01 — Credenciais e segredos hardcoded
- **Severidade:** CRITICAL
- **Sinais:**
  - Atribuições literais a chaves sensíveis: `SECRET_KEY\s*=\s*['"]`, `config\[['"]SECRET_KEY['"]\]\s*=\s*['"]`, `(password|passwd|pass|pwd|senha)\w*\s*[:=]\s*['"][^'"]+['"]`, `(api|gateway|secret|private)_?key\s*[:=]\s*['"]`, prefixos `pk_live_`, `sk_live_`, `AKIA`.
  - Objetos `config = { dbPass: "...", ... }` em arquivos versionados.
  - Strings de conexão com usuário/senha (`postgres://user:pass@`).
  - Segredos devolvidos em respostas HTTP (ex.: health check retornando `secret_key`) → também AP-07.
- **Por que importa:** qualquer pessoa com acesso ao repositório obtém acesso a produção; rotação exige deploy.
- **Correção:** Playbook **P-01** (config por variáveis de ambiente).

## AP-02 — SQL Injection / queries por concatenação
- **Severidade:** CRITICAL
- **Sinais:**
  - Python: `execute\(\s*f?["'].*(\+|%|\{)`, `"... WHERE id = " + str(`, `.format(` dentro de SQL.
  - Node: template literal ou `+` dentro de `db.(run|get|all|query)\(`: `` `SELECT .*\$\{ ``.
  - `LIKE '%" + termo + "%'`.
- **Por que importa:** permite ler/alterar/apagar qualquer dado (ex.: `' OR '1'='1` no login).
- **Correção:** **P-02** (queries parametrizadas).

## AP-03 — Endpoint perigoso / execução arbitrária / admin sem autenticação
- **Severidade:** CRITICAL
- **Sinais:** rota que recebe SQL/código do cliente (`cursor.execute(query)` com `query = request...`), `eval(`, `exec(`, `child_process.exec(` com input; rotas `/admin/*`, `/debug`, `reset-db` sem nenhuma verificação de identidade; `DELETE` de recurso sem auth.
- **Por que importa:** controle total do banco/servidor por qualquer cliente anônimo.
- **Correção:** **P-10** (remover ou proteger endpoints perigosos).

## AP-04 — Armazenamento inseguro de senha
- **Severidade:** CRITICAL
- **Sinais:** coluna `senha`/`password`/`pass` gravada direto do request; `hashlib.md5(`, `hashlib.sha1(` para senha; "hash" caseiro (`base64`, loops de concatenação — ex.: `badCrypto`); comparação `WHERE email = ? AND senha = ?`; senha padrão (`pwd || "123456"`).
- **Por que importa:** vazamento do banco revela senhas reais (reutilizadas em outros serviços); MD5/SHA1 sem salt são quebrados por rainbow tables em segundos.
- **Correção:** **P-08** (KDF forte: `werkzeug.security`, `bcrypt`, `crypto.scrypt`).

## AP-05 — God Class / God File
- **Severidade:** CRITICAL (quando mistura DB + regras + rotas/HTTP) · HIGH (quando mistura vários domínios numa só camada)
- **Sinais:**
  - Uma classe/arquivo com criação de schema, seed, SQL, regras de negócio e registro de rotas (ex.: `class AppManager { initDb(); setupRoutes(app) }`).
  - Arquivo com funções de 3+ domínios (produtos, usuários, pedidos, relatórios) — ex.: `models.py` com >300 linhas e todas as entidades.
  - Funções > ~50 linhas ou com > 3 níveis de aninhamento.
- **Por que importa:** impossível testar em isolamento; qualquer mudança arrisca tudo (viola SRP).
- **Correção:** **P-03** (separar em Model/Controller/View por domínio).

## AP-06 — Regra de negócio na camada de roteamento / "Fat Controller"
- **Severidade:** HIGH
- **Sinais:**
  - Handlers HTTP com cálculos, decisões de domínio, loops sobre entidades, montagem manual de dicts campo a campo, validações extensas, envio de notificações.
  - Handler que acessa banco diretamente (`Model.query`, `db.session`, `cursor.execute`, `db.run`) **e** lê `request`.
  - Mesma regra repetida em vários handlers (ex.: cálculo de "overdue" copiado em 5 lugares).
  - Funções utilitárias/serviços que existem mas não são usados enquanto a rota reimplementa a lógica.
- **Por que importa:** regra de negócio presa ao framework HTTP não é reutilizável nem testável sem subir servidor.
- **Correção:** **P-05** (rota fina → controller → model).

## AP-07 — Exposição de dados sensíveis em respostas/logs
- **Severidade:** HIGH (CRITICAL se expõe segredo de infraestrutura ou dado de cartão)
- **Sinais:** `to_dict()`/serializadores que incluem `password`/`senha`/hash; listagens `SELECT *` de usuários devolvidas cruas; health/debug retornando `secret_key`, `db_path`, flags de debug; logs com número de cartão, token, senha (`console.log(\`...${card}...\`)`); `str(e)` de exceções internas devolvido ao cliente.
- **Por que importa:** vazamento de credenciais/PII e violação de PCI-DSS/LGPD.
- **Correção:** **P-08** (serialização segura) e **P-07** (erros centralizados sem detalhes internos).

## AP-08 — Estado global mutável / acoplamento sem injeção de dependência
- **Severidade:** HIGH
- **Sinais:** `global db_connection`; conexão única compartilhada com `check_same_thread=False`; objetos módulo-level mutáveis (`let globalCache = {}`, `let totalRevenue = 0`) exportados; serviços instanciados dentro de funções/handlers; `new Database()` dentro do construtor de uma classe de rotas; `import` direto de singletons em todo lugar.
- **Por que importa:** condições de corrida, vazamento de memória, impossível substituir por mocks em teste.
- **Correção:** **P-04** (dependências injetadas / escopo por request).

## AP-09 — Autenticação/autorização ausente ou falsa
- **Severidade:** HIGH
- **Sinais:** token previsível (`'fake-jwt-token-' + id`), login que só devolve o usuário, rotas administrativas/destrutivas sem verificação, `role` aceito do corpo da requisição sem checagem de permissão.
- **Por que importa:** qualquer cliente se passa por qualquer usuário.
- **Correção:** **P-10** (token assinado / proteção de rotas). Quando a correção completa exigir mudar o contrato, gere um token assinado mantendo o campo de resposta e registre a recomendação de autorização por rota.

## AP-10 — Configuração insegura de execução
- **Severidade:** HIGH
- **Sinais:** `debug=True` / `DEBUG = True` fixo; `app.run(host='0.0.0.0', debug=True)`; `CORS(app)` / `cors()` sem origem restrita; porta fixa no código.
- **Por que importa:** o debugger do Werkzeug permite execução remota de código; CORS aberto expõe a API a qualquer origem.
- **Correção:** **P-01** (config por ambiente com defaults seguros).

## AP-11 — Queries N+1 / consultas em loop
- **Severidade:** MEDIUM
- **Sinais:**
  - Query dentro de `for`/`forEach`/`map`: `for row in rows: cursor.execute(...)`, `Model.query.get(x.id)` em loop, `db.get(` dentro de `forEach`.
  - Acesso a relacionamento lazy em loop (`len(u.tasks)` para cada usuário).
  - Várias queries `COUNT(*)` separadas que poderiam ser um `GROUP BY`.
- **Por que importa:** latência cresce linearmente com o volume de dados.
- **Correção:** **P-06** (JOIN / eager loading / agregação).

## AP-12 — Tratamento de erros espalhado e genérico
- **Severidade:** MEDIUM
- **Sinais:** `try/except Exception as e: return jsonify({"erro": str(e)}), 500` em cada handler; `except:` nu; erros de banco ignorados em callbacks (`(err) => { res.send(...) }` sem checar `err`); mesmo erro tratado de formas diferentes; ausência de handler global (`@app.errorhandler`, middleware `(err, req, res, next)`).
- **Por que importa:** comportamento inconsistente, falhas silenciosas, vazamento de stack/mensagens internas.
- **Correção:** **P-07** (exceções de domínio + middleware de erro).

## AP-13 — Validação ausente, duplicada ou inconsistente
- **Severidade:** MEDIUM
- **Sinais:** blocos `if "campo" not in dados` copiados entre create/update; regras diferentes para o mesmo campo em rotas distintas; helpers de validação definidos e nunca chamados; `request.get_json()` usado sem checar `None`; tipos não validados (`priority < 1` quebra se vier string).
- **Por que importa:** dados inválidos chegam ao banco; correções precisam ser feitas em N lugares.
- **Correção:** **P-09** (validador único por entidade, chamado pelo controller).

## AP-14 — Uso de APIs deprecated
- **Severidade:** MEDIUM (LOW se a API apenas emite aviso sem data de remoção)
- **Sinais por stack (procure e recomende o equivalente moderno):**

| Stack | API obsoleta (grep) | Equivalente moderno |
|---|---|---|
| Python ≥ 3.12 | `datetime.utcnow()`, `datetime.utcfromtimestamp(` | `datetime.now(timezone.utc)` (ou helper `utcnow()` que remove tzinfo se o banco grava datetime *naive*) |
| SQLAlchemy 2.x / Flask-SQLAlchemy 3.x | `Model.query.get(id)`, `session.query(M).get(id)` (`LegacyAPIWarning`) | `db.session.get(Model, id)` ou `db.get_or_404(Model, id)` |
| SQLAlchemy 2.x | `engine.execute(`, `session.execute("SQL texto")` sem `text()` | `with engine.connect()` + `text()` |
| Flask ≥ 2.3 | `@app.before_first_request`, `flask.json.JSONEncoder`, `app.json_encoder`, `FLASK_ENV` | lógica em `create_app()`, `app.json` provider, `--debug` / `FLASK_DEBUG` |
| Werkzeug | `werkzeug.contrib.*`, `safe_str_cmp` | módulos dedicados, `hmac.compare_digest` |
| Python | `imp`, `distutils`, `asyncio.get_event_loop()` fora de loop | `importlib`, `setuptools`, `asyncio.run` |
| Node.js | `new Buffer(`, `Buffer(` sem `new` | `Buffer.from(` / `Buffer.alloc(` |
| Node.js | `url.parse(`, `querystring` | `new URL(` / `URLSearchParams` |
| Node.js | `crypto.createCipher(`, `crypto.createDecipher(` | `crypto.createCipheriv(` |
| Node.js | `fs.exists(`, `util.isArray(` etc. | `fs.existsSync`/`fs.access`, `Array.isArray` |
| Express 4→5 | `req.param(`, `res.send(status)`, `res.json(status, body)`, `res.sendfile(`, `app.del(` | `req.params`/`req.query`, `res.status(s).send()`, `res.sendFile`, `app.delete` |
| Express | `body-parser` só para JSON/urlencoded | `express.json()` / `express.urlencoded()` (Express ≥ 4.16) |
| Node APIs de banco | callbacks aninhados em drivers que já oferecem Promises (`mysql2`, `pg`) | API Promise / `async/await` (para `sqlite3`, envolver com `util.promisify` ou wrapper) |

  - Rode a aplicação (ou leia a saída de execução já disponível) procurando `DeprecationWarning`, `LegacyAPIWarning`, `[DEP0xxx]`.
- **Por que importa:** a próxima atualização do runtime/biblioteca quebra a aplicação.
- **Correção:** **P-11** (substituição por API moderna).

## AP-15 — Callback hell / fluxo assíncrono aninhado
- **Severidade:** MEDIUM
- **Sinais:** ≥ 3 níveis de callbacks aninhados; contadores manuais de pendências (`pending--; if (pending === 0) res.json(...)`); `self = this` para acessar contexto dentro de `function(){}`; operações multi-etapa sem transação (INSERT matrícula → INSERT pagamento → INSERT log sem `BEGIN/COMMIT`).
- **Por que importa:** erros se perdem, respostas duplicadas/nunca enviadas, inconsistência de dados em falhas parciais.
- **Correção:** **P-12** (async/await + transação).

## AP-16 — Integridade de dados / efeitos colaterais acoplados
- **Severidade:** MEDIUM
- **Sinais:** DELETE que deixa registros órfãos ("matrículas e pagamentos ficaram sujos"); operações multi-tabela sem transação; notificações (`print("ENVIANDO EMAIL")`, `smtplib`) disparadas inline no handler; status que deveria repor estoque e não repõe.
- **Por que importa:** dados inconsistentes e side effects impossíveis de testar/desligar.
- **Correção:** **P-12** (transação) e **P-05** (side effects em service injetado).

## AP-17 — Magic numbers e strings literais de domínio
- **Severidade:** LOW
- **Sinais:** limites e faixas soltas (`if faturamento > 10000: desconto = faturamento * 0.1`, `priority < 1 or priority > 5`, `len(nome) < 2`); listas de status/roles/categorias repetidas inline (`['pending', 'in_progress', 'done', 'cancelled']` em vários arquivos); constantes definidas mas não usadas.
- **Por que importa:** regras de negócio invisíveis e divergentes entre arquivos.
- **Correção:** **P-13** (constantes/enums nomeados no model/config).

## AP-18 — Nomenclatura ruim e código morto
- **Severidade:** LOW
- **Sinais:** variáveis de 1–3 letras com significado de domínio (`u`, `e`, `p`, `cid`, `cc`, `p1..p5`); nomes enganosos (`badCrypto`, `utils.js` contendo config); imports não utilizados (`import os, sys, json, time` sem uso); dependências declaradas e não importadas; funções/exports nunca chamados; `if x: return True else: return False`.
- **Por que importa:** custo de leitura e manutenção; ruído esconde problemas reais.
- **Correção:** **P-14** (renomear, remover, simplificar).

## AP-19 — `print`/`console.log` como mecanismo de log
- **Severidade:** LOW
- **Sinais:** `print(` / `console.log(` em handlers para eventos de negócio ou erros; logs sem nível nem contexto.
- **Por que importa:** sem níveis, sem destino configurável, frequentemente vaza dados.
- **Correção:** **P-14** (módulo `logging` / logger com níveis).

---

## Procedimento de varredura sugerido

1. Para cada AP acima, rode os greps da stack detectada no diretório do projeto (exclua dependências).
2. Confirme cada match lendo o trecho — descarte falsos positivos (ex.: `password` em mensagem de erro).
3. Registre `arquivo:linha` exatos; para blocos, use `inicio-fim`.
4. Cubra **todas** as categorias: segurança (AP-01..04, 07, 09, 10), arquitetura (05, 06, 08), qualidade/performance (11..16), legibilidade (17..19).
5. Em projetos já parcialmente organizados, procure problemas **entre** camadas: regra de negócio nas rotas, services não utilizados, utils com constantes ignoradas, recursos de um domínio registrados no blueprint de outro (ex.: CRUD de categorias dentro de `report_routes`).
