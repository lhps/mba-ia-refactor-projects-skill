# Análise de Projeto — Heurísticas (Fase 1)

Objetivo: descobrir **o que** o projeto é (stack, domínio, dados) e **como** está organizado, sem executar nem modificar nada.

## 1. Detecção de linguagem

Decida pela combinação de manifesto + extensão dominante (conte arquivos por extensão, ignorando dependências vendorizadas).

| Sinal (manifesto / arquivo) | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`, `*.py` | Python |
| `package.json` + `*.js` / `*.mjs` / `*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` + `*.ts` | TypeScript (Node.js) |
| `go.mod`, `*.go` | Go |
| `pom.xml`, `build.gradle`, `*.java` / `*.kt` | Java / Kotlin |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `*.csproj`, `*.cs` | C# |

Versão da linguagem: `.python-version`, `.tool-versions`, `.nvmrc`, `engines` no `package.json`, `python_requires`, `go` em `go.mod`. Se não houver, escreva "versão não fixada".

## 2. Detecção de framework

| Linguagem | Sinal no manifesto | Sinal no código | Framework |
|---|---|---|---|
| Python | `flask` | `Flask(__name__)`, `@app.route`, `Blueprint(` | Flask |
| Python | `django` | `settings.py`, `urls.py`, `INSTALLED_APPS` | Django |
| Python | `fastapi` | `FastAPI()`, `@app.get` | FastAPI |
| Node | `express` | `require('express')`, `app.get(`, `express.Router()` | Express |
| Node | `@nestjs/core` | `@Controller()`, `@Module()` | NestJS |
| Node | `fastify` / `koa` / `hapi` | `fastify()`, `new Koa()` | Fastify / Koa / Hapi |
| Go | `gin-gonic/gin`, `labstack/echo`, `gofiber` | `gin.Default()`, `echo.New()` | Gin / Echo / Fiber |
| Java | `spring-boot-starter-web` | `@RestController`, `@SpringBootApplication` | Spring Boot |
| PHP | `laravel/framework` | `routes/web.php`, `artisan` | Laravel |
| Ruby | `rails` | `config/routes.rb` | Rails |

Versão: leia do manifesto (`flask==3.1.1`, `"express": "^4.18.2"`). Para ranges (`^4.18.2`) informe o range e, se houver lockfile, a versão resolvida.

Extensões relevantes a reportar em *Dependencies*: CORS, ORM, validação (marshmallow, pydantic, joi, zod), auth (jwt, passport), clientes HTTP, drivers de banco. Marque dependências **declaradas mas não importadas** em nenhum arquivo (candidatas a finding LOW).

## 3. Detecção de banco de dados

| Sinal | Engine / Acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite, driver cru (SQL manual) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite, driver cru (callbacks) |
| `':memory:'` | Banco em memória — dados somem a cada boot |
| `flask_sqlalchemy`, `db.Model`, `SQLAlchemy()` | ORM SQLAlchemy |
| `SQLALCHEMY_DATABASE_URI`, `DATABASE_URL` | String de conexão (verifique se está hardcoded) |
| `psycopg2`, `pg`, `mysql`, `mysql2`, `pymysql` | PostgreSQL / MySQL |
| `mongoose`, `pymongo`, `mongodb` | MongoDB |
| `prisma`, `sequelize`, `typeorm`, `knex` | ORMs/Query builders Node |

Mapeie as **tabelas/modelos**: procure `CREATE TABLE`, classes `db.Model`, `__tablename__`, `mongoose.model(`, `@Entity`. Anote onde o schema é criado e onde existe seed (dados iniciais), pois a Fase 3 deve preservar ambos.

## 4. Inventário de endpoints

Padrões de busca:

| Stack | Grep |
|---|---|
| Flask | `@\w+\.route\(`, `add_url_rule\(`, `Blueprint\(` |
| Django | `path\(`, `re_path\(` em `urls.py` |
| FastAPI | `@\w+\.(get|post|put|patch|delete)\(` |
| Express | `\b(app|router)\.(get|post|put|patch|delete|use)\(` |
| Spring | `@(Get|Post|Put|Delete|Request)Mapping` |

Para cada endpoint registre: método, path, handler, arquivo:linha. Inclua endpoints "escondidos" (admin, debug, health). Verifique `.http`, coleções Postman ou README com exemplos de requisição — eles servem de base para o smoke test da Fase 3.

## 5. Detecção de domínio

1. Extraia os substantivos dos paths (`/produtos`, `/pedidos`, `/courses`, `/tasks`) e das tabelas.
2. Agrupe-os em um domínio conhecido: produtos+pedidos+usuários → **E-commerce**; cursos+matrículas+pagamentos → **LMS / plataforma de cursos com checkout**; tasks+categorias+usuários → **Task Manager**; etc.
3. Use também README, nome do pacote e mensagens de log.

## 6. Classificação da arquitetura atual

| Classificação | Sinais |
|---|---|
| **Monolito de arquivo único / God Class** | Um arquivo ou classe concentra rotas + SQL + regras + config (ex.: classe `*Manager` com `initDb()` e `setupRoutes()`) |
| **Monolito multi-arquivo (pseudo-camadas)** | Arquivos com nomes de camada (`models.py`, `controllers.py`) mas sem fronteiras reais: "controllers" leem `request` e acessam o banco; "models" concentram todos os domínios e regras de negócio |
| **Camadas parciais** | Pastas `models/`, `routes/`, `services/`, `utils/` existem, mas regras de negócio vivem nas rotas, serviços estão desconectados, faltam config e error handling centralizados |
| **MVC / camadas completo** | Config isolada, models só com dados, controllers com fluxo, rotas finas, middleware de erros, composition root |

Justifique a classificação em uma linha citando arquivos concretos (ex.: "AppManager.js contém DB, rotas e regras de checkout").

## 7. Métricas

- **Source files**: arquivos de código do próprio projeto (exclua `__init__.py` vazios apenas se estiverem vazios — mas conte-os se tiverem conteúdo).
- **Lines**: `wc -l` somado dos arquivos-fonte.
- Anote os **maiores arquivos** (candidatos a God Class) e o **entry point** (`if __name__ == "__main__"`, `"main"`/`"start"` do package.json, `app.listen(`).

## 8. Checklist de saída da Fase 1

- [ ] Linguagem e versão
- [ ] Framework e versão
- [ ] Dependências relevantes (e não utilizadas)
- [ ] Domínio com entidades principais
- [ ] Banco, tabelas/modelos, onde nasce o schema e o seed
- [ ] Inventário completo de endpoints
- [ ] Classificação da arquitetura com justificativa
- [ ] Contagem de arquivos e linhas
- [ ] Entry point e comando de execução
