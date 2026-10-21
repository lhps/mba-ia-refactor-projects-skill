# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express — refatorada para MVC pela skill `refactor-arch` (ver `reports/audit-project-2.md` na raiz do repositório).

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000` (configure `PORT`). O banco SQLite é em memória (`DB_PATH`) e carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`. Variáveis de ambiente em `.env.example` — quando `ADMIN_TOKEN` é definido, `/api/admin/*` e `DELETE /api/users/:id` exigem o header `X-Admin-Token`.

## Estrutura

```
src/
├── app.js            # composition root (createApp) + listen
├── config/           # variáveis de ambiente, logger
├── database/         # wrapper Promise do sqlite3, transações, schema e seed
├── errors/           # AppError e subclasses
├── models/           # user, course, enrollment, payment, auditLog (SQL parametrizado)
├── services/         # pagamento, hash de senha (scrypt), cache
├── controllers/      # checkout, relatório financeiro, usuários
├── routes/           # express.Router por domínio
└── middlewares/      # asyncHandler, errorHandler, requireAdmin
```
