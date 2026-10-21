# task-manager-api

API de Task Manager em Python/Flask — evoluída para MVC pela skill `refactor-arch` (ver `reports/audit-project-3.md` na raiz do repositório). A organização em camadas existente (`models/`, `routes/`, `services/`, `utils/`) foi mantida e completada com `config/`, `controllers/` e `middlewares/`.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configure `PORT`; no macOS a 5000 pode estar ocupada pelo AirPlay). O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**.

## Estrutura

```
app.py                 # composition root (create_app) + entry point
config/settings.py     # configuração via variáveis de ambiente / .env
database.py            # instância SQLAlchemy
errors.py              # exceções de domínio
models/                # entidades ORM, constantes de domínio, serialização segura
controllers/           # regras de negócio: tasks, usuários, categorias, relatórios
routes/                # Views: Blueprints finos (tasks, users, categories, reports)
services/              # notificações (SMTP via config) e tokens assinados
middlewares/           # error handler centralizado
utils/                 # helpers de data e validadores
```

## Notas de segurança

- Senhas com `werkzeug.security` (hashes MD5 legados são migrados no primeiro login); o hash nunca é retornado pela API.
- `POST /login` retorna um token assinado com `SECRET_KEY` (`itsdangerous`), válido por `TOKEN_MAX_AGE_SECONDS`.
- Novas senhas exigem no mínimo 8 caracteres.
