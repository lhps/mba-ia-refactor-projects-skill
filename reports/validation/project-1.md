# Projeto 1 — code-smells-project: validação da Fase 3

## Boot (PORT=5055 python app.py)
```
SECRET_KEY não definida; usando chave efêmera gerada no boot.
 * Serving Flask app 'src.app'
 * Debug mode: off
2026-10-21 15:04:04,535 INFO werkzeug: [31m[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.[0m
 * Running on http://127.0.0.1:5055
```

## Smoke test ANTES da refatoração (baseline)
```
GET     /                                -> 200 {   "endpoints": {     "health": "/health",     "login": "/login",     "pedidos": "/pedidos",     "produtos": 
GET     /health                          -> 200 {   "ambiente": "producao",   "counts": {     "pedidos": 0,     "produtos": 10,     "usuarios": 3   },   "data
GET     /produtos                        -> 200 {   "dados": [     {       "ativo": 1,       "categoria": "informatica",       "criado_em": "2026-10-21 16:55:
GET     /produtos/busca?q=Mouse&preco_max=100 -> 200 {   "dados": [     {       "ativo": 1,       "categoria": "informatica",       "criado_em": "2026-10-21 16:55:
GET     /produtos/1                      -> 200 {   "dados": {     "ativo": 1,     "categoria": "informatica",     "criado_em": "2026-10-21 16:55:57",     "de
GET     /produtos/999                    -> 404 {   "erro": "Produto n\u00e3o encontrado",   "sucesso": false } 
POST    /produtos                        -> 201 {   "dados": {     "id": 11   },   "mensagem": "Produto criado",   "sucesso": true } 
POST    /produtos                        -> 400 {   "erro": "Pre\u00e7o n\u00e3o pode ser negativo" } 
PUT     /produtos/11                     -> 200 {   "mensagem": "Produto atualizado",   "sucesso": true } 
DELETE  /produtos/11                     -> 200 {   "mensagem": "Produto deletado",   "sucesso": true } 
GET     /usuarios                        -> 200 {   "dados": [     {       "criado_em": "2026-10-21 16:55:57",       "email": "admin@loja.com",       "id": 1,
GET     /usuarios/1                      -> 200 {   "dados": {     "criado_em": "2026-10-21 16:55:57",     "email": "admin@loja.com",     "id": 1,     "nome":
POST    /usuarios                        -> 201 {   "dados": {     "id": 4   },   "sucesso": true } 
POST    /login                           -> 200 {   "dados": {     "email": "joao@email.com",     "id": 2,     "nome": "Jo\u00e3o Silva",     "tipo": "cliente
POST    /login                           -> 401 {   "erro": "Email ou senha inv\u00e1lidos",   "sucesso": false } 
POST    /pedidos                         -> 201 {   "dados": {     "pedido_id": 1,     "total": 6179.79   },   "mensagem": "Pedido criado com sucesso",   "suc
POST    /pedidos                         -> 400 {   "erro": "Estoque insuficiente para Notebook Gamer",   "sucesso": false } 
GET     /pedidos                         -> 200 {   "dados": [     {       "criado_em": "2026-10-21 16:55:59",       "id": 1,       "itens": [         {      
GET     /pedidos/usuario/2               -> 200 {   "dados": [     {       "criado_em": "2026-10-21 16:55:59",       "id": 1,       "itens": [         {      
PUT     /pedidos/1/status                -> 200 {   "mensagem": "Status atualizado",   "sucesso": true } 
PUT     /pedidos/1/status                -> 400 {   "erro": "Status inv\u00e1lido" } 
GET     /relatorios/vendas               -> 200 {   "dados": {     "desconto_aplicavel": 308.99,     "faturamento_bruto": 6179.79,     "faturamento_liquido": 
```

## Smoke test DEPOIS da refatoração
```
GET     /                                -> 200 {"endpoints":{"health":"/health","login":"/login","pedidos":"/pedidos","produtos":"/produtos","relatorios":"/r
GET     /health                          -> 200 {"ambiente":"development","counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"o
GET     /produtos                        -> 200 {"dados":[{"ativo":1,"categoria":"informatica","criado_em":"2026-10-21 18:04:04","descricao":"Notebook potente
GET     /produtos/busca?q=Mouse&preco_max=100 -> 200 {"dados":[{"ativo":1,"categoria":"informatica","criado_em":"2026-10-21 18:04:04","descricao":"Mouse sem fio er
GET     /produtos/1                      -> 200 {"dados":{"ativo":1,"categoria":"informatica","criado_em":"2026-10-21 18:04:04","descricao":"Notebook potente 
GET     /produtos/999                    -> 404 {"erro":"Produto n\u00e3o encontrado","sucesso":false} 
POST    /produtos                        -> 201 {"dados":{"id":11},"mensagem":"Produto criado","sucesso":true} 
POST    /produtos                        -> 400 {"erro":"Pre\u00e7o n\u00e3o pode ser negativo","sucesso":false} 
PUT     /produtos/11                     -> 200 {"mensagem":"Produto atualizado","sucesso":true} 
DELETE  /produtos/11                     -> 200 {"mensagem":"Produto deletado","sucesso":true} 
GET     /usuarios                        -> 200 {"dados":[{"criado_em":"2026-10-21 18:04:04","email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},{"
GET     /usuarios/1                      -> 200 {"dados":{"criado_em":"2026-10-21 18:04:04","email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"},"su
POST    /usuarios                        -> 201 {"dados":{"id":4},"sucesso":true} 
POST    /login                           -> 200 {"dados":{"email":"joao@email.com","id":2,"nome":"Jo\u00e3o Silva","tipo":"cliente"},"mensagem":"Login OK","su
POST    /login                           -> 401 {"erro":"Email ou senha inv\u00e1lidos","sucesso":false} 
POST    /pedidos                         -> 201 {"dados":{"pedido_id":1,"total":6179.79},"mensagem":"Pedido criado com sucesso","sucesso":true} 
POST    /pedidos                         -> 400 {"erro":"Estoque insuficiente para Notebook Gamer","sucesso":false} 
GET     /pedidos                         -> 200 {"dados":[{"criado_em":"2026-10-21 18:04:07","id":1,"itens":[{"preco_unitario":5999.99,"produto_id":1,"produto
GET     /pedidos/usuario/2               -> 200 {"dados":[{"criado_em":"2026-10-21 18:04:07","id":1,"itens":[{"preco_unitario":5999.99,"produto_id":1,"produto
PUT     /pedidos/1/status                -> 200 {"mensagem":"Status atualizado","sucesso":true} 
PUT     /pedidos/1/status                -> 400 {"erro":"Status inv\u00e1lido","sucesso":false} 
GET     /relatorios/vendas               -> 200 {"dados":{"desconto_aplicavel":308.99,"faturamento_bruto":6179.79,"faturamento_liquido":5870.8,"pedidos_aprova
```

Resultado: 22/22 endpoints com o mesmo status code do baseline. `/admin/query` removido (404), `/admin/reset-db` sem token -> 403, SQL injection no login -> 401, `senha`/`secret_key` ausentes das respostas.
