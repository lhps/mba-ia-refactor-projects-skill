# code-smells-project

API de E-commerce em Python/Flask — refatorada para MVC pela skill `refactor-arch` (ver `reports/audit-project-1.md` na raiz do repositório).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: exporte as variáveis desejadas
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configure `PORT`; no macOS a 5000 pode estar ocupada pelo AirPlay). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

## Estrutura

```
app.py                     # entry point
src/
├── app.py                 # composition root (create_app)
├── config/settings.py     # configuração via variáveis de ambiente
├── database.py            # conexão por request, schema e seed
├── errors.py              # exceções de domínio
├── models/                # acesso a dados (SQL parametrizado)
├── controllers/           # regras de negócio e fluxo
├── views/                 # Blueprints (rotas HTTP)
├── services/              # notificações
└── middlewares/           # error handler, autenticação admin
```

## Variáveis de ambiente

Ver `.env.example`. `POST /admin/reset-db` exige o header `X-Admin-Token` igual a `ADMIN_TOKEN` (desabilitado se vazio). O antigo `POST /admin/query` (SQL arbitrário) foi removido por segurança.
