# Playbook de Refatoração (Fase 3)

Cada padrão mapeia um ou mais anti-patterns do catálogo (`AP-xx`) para uma transformação concreta, com exemplos **antes/depois** em Python/Flask e Node.js/Express. Adapte a sintaxe para outras stacks mantendo a ideia.

| Padrão | Resolve | Resumo |
|---|---|---|
| P-01 | AP-01, AP-10 | Config por variáveis de ambiente com defaults seguros |
| P-02 | AP-02 | Queries parametrizadas |
| P-03 | AP-05 | Quebrar God Class/File em Model + Controller + View por domínio |
| P-04 | AP-08 | Estado global → dependência injetada / escopo por request |
| P-05 | AP-06, AP-16 | Rota fina → Controller → Model; side effects em Service |
| P-06 | AP-11 | N+1 → JOIN / eager loading / agregação |
| P-07 | AP-12, AP-07 | Exceções de domínio + error handler centralizado |
| P-08 | AP-04, AP-07 | Hash de senha forte + serialização sem dados sensíveis |
| P-09 | AP-13 | Validador único por entidade |
| P-10 | AP-03, AP-09 | Remover/proteger endpoints perigosos; token assinado |
| P-11 | AP-14 | API deprecated → equivalente moderno |
| P-12 | AP-15, AP-16 | Callback hell → async/await + transação |
| P-13 | AP-17 | Magic numbers/strings → constantes nomeadas |
| P-14 | AP-18, AP-19 | Nomes claros, remover código morto, logging estruturado |

---

## P-01 — Extrair configuração para variáveis de ambiente

**Antes (Flask):**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
CORS(app)
...
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Depois:**
```python
# config/settings.py
import os, secrets, logging

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

if not os.environ.get("SECRET_KEY"):
    logging.getLogger(__name__).warning("SECRET_KEY não definida; usando chave efêmera.")

# app.py (composition root)
def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=config.CORS_ORIGINS)
    return app
```

**Antes (Node):**
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", port: 3000 };
```

**Depois:**
```js
// src/config/index.js
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  smtpUser: process.env.SMTP_USER || '',
});
```
Crie `.env.example` listando cada variável sem valor real.

---

## P-02 — Queries parametrizadas

**Antes:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")
query += " AND (nome LIKE '%" + termo + "%')"
```

**Depois:**
```python
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", params)
```
Só fragmentos **fixos** (nomes de colunas escolhidos pelo código) podem ser interpolados; valores vindos do usuário sempre via `?` / `%s` / `$1`.

**Node:**
```js
// Antes
db.all(`SELECT * FROM users WHERE email = '${email}'`);
// Depois
db.all('SELECT * FROM users WHERE email = ?', [email]);
```

---

## P-03 — Quebrar God Class / God File por domínio

**Antes (Node — tudo em `AppManager`):**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { /* CREATE TABLE..., INSERT seeds */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* validação + SQL + pagamento + log */ });
    app.get('/api/admin/financial-report', (req, res) => { /* SQL em loop */ });
  }
}
```

**Depois:**
```js
// src/models/course.model.js
class CourseModel {
  constructor(db) { this.db = db; }
  findActiveById(id) { return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]); }
}
// src/controllers/checkout.controller.js
class CheckoutController {
  constructor({ courseModel, userModel, enrollmentModel, paymentService }) { Object.assign(this, { courseModel, userModel, enrollmentModel, paymentService }); }
  async checkout({ name, email, password, courseId, card }) { /* fluxo do caso de uso */ }
}
// src/routes/checkout.routes.js
router.post('/api/checkout', asyncHandler(async (req, res) => {
  const result = await checkoutController.checkout(mapCheckoutBody(req.body));
  res.status(200).json(result);
}));
```

**Antes (Python — `models.py` com 4 domínios, `controllers.py` lendo `request`):** dividir em
`models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`, `controllers/<dominio>_controller.py` (sem `request`) e `views/<dominio>_routes.py` (Blueprints). Cada função antiga é movida para **uma** camada; nada fica duplicado.

---

## P-04 — Estado global mutável → injeção / escopo por request

**Antes:**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

**Depois (conexão por request, fechada no teardown):**
```python
from flask import g, current_app

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

**Antes (Node):**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
module.exports = { globalCache, logAndCache };
```

**Depois:**
```js
// src/services/cache.service.js
class CacheService {
  constructor() { this.store = new Map(); }
  set(key, value) { this.store.set(key, value); }
  get(key) { return this.store.get(key); }
}
// composition root
const cache = new CacheService();
const checkoutController = new CheckoutController({ ..., cache });
```

---

## P-05 — Rota fina → Controller → Model; side effects em Service

**Antes:**
```python
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for t in tasks:
        task_data = {...}
        if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled'):
            task_data['overdue'] = True
        user = User.query.get(t.user_id)  # N+1
        ...
    return jsonify(result), 200
```

**Depois:**
```python
# models/task.py
def is_overdue(self, now=None):
    now = now or utcnow()
    return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

# controllers/task_controller.py
def list_tasks():
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    return [t.to_dict(include_overdue=True, include_relations=True) for t in tasks]

# routes/task_routes.py (View)
@task_bp.get('/tasks')
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200
```

**Side effects:**
```python
# Antes (no handler)
print("ENVIANDO EMAIL: Pedido " + str(pedido_id) + " criado")
# Depois (controller chama service injetado)
self.notifier.order_created(order_id=pedido_id, user_id=usuario_id)
```

---

## P-06 — Eliminar N+1

**Antes (SQL cru):**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois:**
```python
rows = db.execute("""
    SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(p.nome, 'Desconhecido') AS produto_nome
    FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id
    WHERE i.pedido_id IN ({})""".format(",".join("?" * len(ids))), ids).fetchall()
itens_por_pedido = defaultdict(list)
for r in rows:
    itens_por_pedido[r["pedido_id"]].append(dict(r))
```

**ORM (SQLAlchemy):**
```python
# Antes: len(u.tasks) por usuário / Task.query.filter_by(category_id=c.id).count() em loop
# Depois: uma agregação
counts = dict(db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all())
```

**Contagens múltiplas → GROUP BY:**
```python
# Antes: 4 queries COUNT(*) WHERE status = ...
# Depois:
by_status = dict(db.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
```

**Node (relatório):**
```js
const rows = await db.all(`
  SELECT c.id AS course_id, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id, e.id`);
// agrupar em memória por course_id
```

---

## P-07 — Exceções de domínio + error handler centralizado

**Antes:**
```python
def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

**Depois:**
```python
# errors.py
class AppError(Exception):
    status_code = 400
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

class ValidationError(AppError): status_code = 400
class UnauthorizedError(AppError): status_code = 401
class NotFoundError(AppError): status_code = 404
class ConflictError(AppError): status_code = 409

# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return jsonify({"erro": err.description, "sucesso": False}), err.code
        app.logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500

# controller
def obter_produto(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto

# view
@produtos_bp.get("/produtos/<int:produto_id>")
def buscar_produto(produto_id):
    return jsonify({"dados": produto_controller.obter_produto(produto_id), "sucesso": True}), 200
```

**Node:**
```js
// src/errors/AppError.js
class AppError extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.status).send(err.message);
  console.error(err);
  res.status(500).send('Erro interno');
};
// rotas async: const asyncHandler = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
```
Preserve o **formato** de erro original da API (`{"erro"}`, `{"error"}` ou texto puro).

---

## P-08 — Hash de senha forte + serialização segura

**Antes:**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
def to_dict(self): return {..., 'password': self.password}
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    return check_password_hash(self.password, raw)

def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}  # sem password
```
Se houver hashes legados (MD5) no banco, aceite-os uma vez em `check_password` e regrave com o novo algoritmo (migração transparente).

**Node (sem dependências novas):**
```js
// Antes
function badCrypto(pwd) { let h = ""; for (let i = 0; i < 10000; i++) h += Buffer.from(pwd).toString('base64').substring(0, 2); return h.substring(0, 10); }
// Depois — src/services/password.service.js
const crypto = require('crypto');
function hashPassword(pwd) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(pwd, salt, 64).toString('hex');
  return `scrypt$${salt}$${hash}`;
}
function verifyPassword(pwd, stored) {
  const [, salt, hash] = stored.split('$');
  return crypto.timingSafeEqual(Buffer.from(hash, 'hex'), crypto.scryptSync(pwd, salt, 64));
}
```
Não registre em log senha, número de cartão ou chave de API: `console.log(\`Processando cartão ${cc}...\`)` → `logger.info('Processando pagamento', { last4: card.slice(-4) })`.

---

## P-09 — Validador único por entidade

**Antes (duplicado em create e update):**
```python
if "nome" not in dados: return jsonify({"erro": "Nome é obrigatório"}), 400
if "preco" not in dados: return jsonify({"erro": "Preço é obrigatório"}), 400
if preco < 0: return jsonify({"erro": "Preço não pode ser negativo"}), 400
```

**Depois:**
```python
# controllers/validators.py (ou models/produto_model.py)
def validar_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, label in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if campo not in dados:
            raise ValidationError(f"{label} é obrigatório")
    if dados["preco"] < 0:
        raise ValidationError("Preço não pode ser negativo")
    ...
    return {"nome": dados["nome"], "preco": dados["preco"], ...}

# controller
def criar_produto(dados):
    produto = validar_produto(dados)
    return produto_model.criar(**produto)
```
Mantenha as mesmas mensagens de erro para preservar o contrato. Valide tipos (`isinstance(p, int)`) antes de comparar.

---

## P-10 — Remover/proteger endpoints perigosos; autenticação real

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json().get("sql"))   # SQL arbitrário
```

**Depois:** remover o endpoint (não existe uso legítimo de SQL arbitrário via HTTP). Para operações administrativas legítimas (ex.: reset de banco em dev), proteger:
```python
def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        given = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(given, expected):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)
    return wrapper
```

**Token falso → token assinado (mesmo campo de resposta):**
```python
# Antes
'token': 'fake-jwt-token-' + str(user.id)
# Depois (itsdangerous já vem com Flask)
from itsdangerous import URLSafeTimedSerializer
serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth")
'token': serializer.dumps({"user_id": user.id})
```

---

## P-11 — APIs deprecated → equivalentes modernos

```python
# Antes
from datetime import datetime
created_at = db.Column(db.DateTime, default=datetime.utcnow)
task = Task.query.get(task_id)

# Depois
from datetime import datetime, timezone
def utcnow():
    """UTC naive — compatível com colunas DateTime sem timezone (SQLite)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

created_at = db.Column(db.DateTime, default=utcnow)
task = db.session.get(Task, task_id)
```
Atenção: não misture datetimes *aware* e *naive* em comparações (`TypeError`). Se o banco grava naive, o helper deve devolver naive.

```js
// Antes
const b = new Buffer(str);                 // DEP0005
const { query } = url.parse(req.url, true);
app.use(bodyParser.json());
// Depois
const b = Buffer.from(str);
const { searchParams } = new URL(req.url, 'http://localhost');
app.use(express.json());
```

---

## P-12 — Callback hell → async/await + transação

**Antes:**
```js
this.db.get("SELECT * FROM courses ...", [cid], (err, course) => {
  this.db.get("SELECT id FROM users ...", [e], (err, user) => {
    this.db.run("INSERT INTO enrollments ...", [userId, cid], function (err) {
      self.db.run("INSERT INTO payments ...", [this.lastID, ...], function (err) {
        self.db.run("INSERT INTO audit_logs ...", [...], (err) => res.json(...));
      });
    });
  });
});
```

**Depois:**
```js
// src/database/connection.js — wrapper Promise sobre sqlite3
run(sql, params = []) {
  return new Promise((resolve, reject) =>
    this.db.run(sql, params, function (err) { err ? reject(err) : resolve({ lastID: this.lastID, changes: this.changes }); }));
}
async transaction(work) {
  await this.run('BEGIN');
  try { const r = await work(); await this.run('COMMIT'); return r; }
  catch (e) { await this.run('ROLLBACK'); throw e; }
}

// controller
async checkout(input) {
  const course = await this.courses.findActiveById(input.courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');
  return this.db.transaction(async () => {
    const userId = await this.findOrCreateUser(input);
    const enrollmentId = await this.enrollments.create(userId, course.id);
    await this.payments.create(enrollmentId, course.price, 'PAID');
    await this.audit.log(`Checkout curso ${course.id} por ${userId}`);
    return { msg: 'Sucesso', enrollment_id: enrollmentId };
  });
}
```
Deleções com dependentes também dentro de transação (apagar `payments` → `enrollments` → `users`), eliminando registros órfãos.

---

## P-13 — Magic numbers/strings → constantes nomeadas

**Antes:**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
if status not in ['pending', 'in_progress', 'done', 'cancelled']: ...
```

**Depois:**
```python
# models/pedido_model.py
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))  # (faturamento mínimo, taxa)
STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0

# models/task.py
VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
CLOSED_STATUSES = ("done", "cancelled")
MIN_PRIORITY, MAX_PRIORITY = 1, 5
```

---

## P-14 — Nomes claros, código morto e logging

**Antes:**
```js
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;
```
```python
import os, sys, json, datetime   # só datetime é usado
print("Produto criado com ID: " + str(id))
def is_admin(self):
    if self.role == 'admin':
        return True
    else:
        return False
```

**Depois:**
```js
// mapeia o contrato externo (mantido) para nomes internos claros
const toCheckoutInput = (body) => ({ name: body.usr, email: body.eml, password: body.pwd, courseId: body.c_id, card: body.card });
```
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Produto criado com ID %s", produto_id)

def is_admin(self):
    return self.role == "admin"
```
Remova imports, exports (`totalRevenue`), funções e dependências de manifesto que não são usados após a refatoração.
