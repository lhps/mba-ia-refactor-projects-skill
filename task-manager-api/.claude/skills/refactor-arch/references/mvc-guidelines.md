# Guidelines de Arquitetura — MVC alvo (Fase 3)

Em uma API backend não há templates HTML: a **View** é a camada de apresentação HTTP — rotas que traduzem requisições em chamadas ao controller e serializam a resposta. O alvo é um MVC em camadas com dependências apontando **sempre para dentro**:

```
HTTP ─▶ View/Routes ─▶ Controller ─▶ Model ─▶ Banco
                  │            └─▶ Service (integrações: e-mail, pagamento, cache)
                  └─ erros sobem como exceções ─▶ Middleware de erro ─▶ HTTP
Config ─▶ injetada no composition root (app factory / app.js)
```

## Responsabilidades por camada

### Config (`config/`)
- **Faz:** lê variáveis de ambiente (com `.env` opcional), define defaults **seguros** para desenvolvimento, centraliza constantes de infraestrutura (porta, URL do banco, CORS, debug).
- **Não faz:** lógica de negócio; não contém segredos reais versionados.
- Segredos sem valor definido: gere um valor efêmero em dev (ex.: `secrets.token_hex(32)`/`crypto.randomBytes`) e emita warning — nunca um literal fixo.

### Models (`models/`)
- **Faz:** representa entidades e o acesso a dados (SQL parametrizado ou ORM), criação de schema/seed, serialização para dict/JSON **sem campos sensíveis**, constantes do domínio (status válidos, faixas de prioridade), regras intrínsecas da entidade (ex.: `task.is_overdue()`).
- **Não faz:** ler `request`, montar respostas HTTP, chamar serviços externos, conhecer o framework web.
- Um arquivo por agregado/entidade (`produto_model.py`, `user.py`, `course.model.js`).

### Controllers (`controllers/`)
- **Faz:** orquestra o caso de uso: valida a entrada (com validators), aplica regras de negócio, chama models, dispara services (notificação, pagamento), controla transações. Recebe **dados simples** (dict/objeto) e retorna **dados simples**; sinaliza falhas lançando exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`).
- **Não faz:** importar `request`/`req`/`res`/`jsonify`; escrever SQL; formatar status HTTP.
- Um controller por domínio (`produto_controller.py`, `checkout.controller.js`).

### Views / Routes (`views/` ou `routes/`)
- **Faz:** declara método + path, extrai parâmetros (path, query, body), chama **um** método do controller, serializa a resposta (`jsonify`, `res.json`) com o status code correto.
- **Não faz:** regras de negócio, loops sobre entidades, acesso ao banco, try/except genérico.
- Handlers idealmente com ≤ 10 linhas. Um módulo de rotas por domínio (Blueprint / `express.Router`).

### Services (`services/`) — opcional
- Integrações e efeitos colaterais: e-mail, SMS, gateway de pagamento, cache, geração de token. Recebem config por injeção. São chamados pelos controllers.

### Middlewares (`middlewares/`)
- **Error handler centralizado** (obrigatório): converte exceções de domínio em respostas HTTP com o mesmo formato de erro que a API já usava (ex.: `{"erro": "..."}` ou `{"error": "..."}`); exceções inesperadas → 500 com mensagem genérica e log do stack trace (nunca `str(e)` para o cliente).
- Opcional: autenticação, logging de requisições.

### Composition root (`app.py` / `app.js` / `server.js`)
- Cria a aplicação (app factory `create_app(config)` / função `createApp(deps)`), carrega config, inicializa banco, instancia models/services/controllers, registra rotas e middlewares. É o **único** lugar que conhece todas as camadas.
- O entry point executável (`python app.py`, `npm start`) apenas chama a factory e sobe o servidor.

## Regras de dependência (verifique no re-scan)

| Camada | Pode importar | Não pode importar |
|---|---|---|
| config | stdlib | qualquer outra camada |
| models | config, db | controllers, views, framework HTTP (`request`, `jsonify`, `req/res`) |
| services | config | views, models (preferencialmente) |
| controllers | models, services, validators, errors | views, `request`/`jsonify`/`req`/`res` |
| views/routes | controllers, framework HTTP | models, db, SQL |
| middlewares | errors, framework HTTP | models |

## Estratégia por ponto de partida

| Arquitetura atual (Fase 1) | Estratégia |
|---|---|
| **God Class / arquivo único** | Criar `src/` com todas as camadas; extrair schema/seed para `models/` ou `database/`; cada rota vira view + método de controller; classe original é removida. |
| **Monolito multi-arquivo (pseudo-camadas)** | Criar `src/` com as camadas; quebrar o `models.py` gigante em um model por entidade; o `controllers.py` atual (que lê `request`) é dividido em **views** (parte HTTP) + **controllers** (fluxo); manter `app.py` na raiz como entry point fino. |
| **Camadas parciais** | **Evolução incremental, sem mover o que já está no lugar certo**: manter `models/` e transformar `routes/` em views finas; criar `controllers/` com a lógica extraída das rotas; criar `config/`, `middlewares/`; dar uso real aos `services/` e `utils/` existentes (ou removê-los se mortos); separar recursos registrados no módulo errado (ex.: categorias dentro de relatórios). |
| **MVC completo** | Focar nos findings pontuais (segurança, performance, deprecated) sem reestruturar. |

## Layouts de referência

### Python / Flask — partindo de monolito
```
<projeto>/
├── app.py                      # entry point: from src.app import create_app
├── requirements.txt
├── .env.example
└── src/
    ├── __init__.py
    ├── app.py                  # composition root: create_app()
    ├── config/settings.py      # Config via os.environ
    ├── database.py             # conexão por request (flask.g) + schema + seed
    ├── models/                 # <entidade>_model.py — SQL parametrizado
    ├── controllers/            # <dominio>_controller.py — regras e fluxo
    ├── views/                  # <dominio>_routes.py — Blueprints finos
    ├── services/               # notification_service.py etc.
    ├── middlewares/error_handler.py
    └── errors.py               # AppError, NotFoundError, ValidationError
```

### Python / Flask — camadas parciais (evolução)
```
<projeto>/
├── app.py                      # create_app() + entry point (mantém `from app import app`)
├── config/settings.py
├── database.py
├── models/                     # mantidos; sem senha no to_dict; constantes de domínio
├── controllers/                # NOVO: task_controller.py, user_controller.py, ...
├── routes/                     # mantidos como Views: apenas HTTP
├── services/                   # integrados via injeção (ou removidos se mortos)
├── middlewares/error_handler.py
└── utils/                      # apenas helpers realmente usados
```

### Node.js / Express
```
<projeto>/
├── package.json                # "start" continua funcionando
├── .env.example
└── src/
    ├── app.js                  # composition root + listen
    ├── config/index.js         # process.env com defaults seguros
    ├── database/connection.js  # wrapper Promise + schema + seed
    ├── models/                 # <entidade>.model.js — SQL parametrizado
    ├── controllers/            # <dominio>.controller.js — async/await
    ├── routes/                 # <dominio>.routes.js — express.Router
    ├── services/               # payment.service.js, cache.service.js, password.service.js
    ├── middlewares/errorHandler.js
    └── errors/AppError.js
```

## Ordem de execução recomendada

1. **Config** — extrair segredos e flags para `config/` + `.env.example`.
2. **Infra de banco** — conexão com escopo correto (por request ou injetada), schema e seed preservados.
3. **Erros de domínio** — `AppError` e subclasses (base para controllers e middleware).
4. **Models** — um por entidade, SQL parametrizado, serialização segura, constantes de domínio.
5. **Services** — notificações, pagamento, hashing, cache.
6. **Controllers** — mover regras de negócio das rotas/God Class; validação centralizada.
7. **Views/Routes** — handlers finos chamando controllers.
8. **Middleware de erro** — registrar no composition root.
9. **Composition root** — app factory, registro de rotas, entry point preservado.
10. **Limpeza** — remover arquivos legados, imports/deps não usados, atualizar README/manifesto.
11. **Validação** — boot + smoke test vs. baseline + re-scan.

## Contrato da API — o que preservar

- Paths, métodos, nomes de campos do body (mesmo que mal nomeados, ex.: `usr`, `eml` — renomeie só internamente), formato do envelope de resposta (`{"dados": ..., "sucesso": true}`), status codes.
- Mensagens de erro podem ser mantidas iguais; o error handler deve reproduzir o formato.
- Mudanças permitidas apenas por segurança: remover campos sensíveis (senha/hash, secret), remover/proteger endpoints de execução arbitrária, trocar token falso por token assinado mantendo o campo. Liste todas no resumo final.
