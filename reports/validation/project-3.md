# Projeto 3 — task-manager-api: validação da Fase 3

## Seed + boot (`python -W error::DeprecationWarning seed.py` e `PORT=5056 python -W error::DeprecationWarning app.py`)
```
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
SECRET_KEY não definida; usando chave efêmera gerada no boot.
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5056
```

Antes da refatoração, o mesmo `seed.py` emitia 5 `DeprecationWarning` de `datetime.utcnow()`; depois, executado com warnings promovidos a erro, roda limpo.

## Smoke test ANTES da refatoração (baseline)
```
GET     /                                  -> 200 {"message":"Task Manager API","version":"1.0"} 
GET     /health                            -> 200 {"status":"ok","timestamp":"2026-10-21 13:56:19.902138"} 
GET     /tasks                             -> 200 [{"category_id":1,"category_name":"Backend","created_at":"2026-10-21 16:56:17.658179","description":"Adicionar autentica
GET     /tasks/1                           -> 200 {"category_id":1,"created_at":"2026-10-21 16:56:17.658179","description":"Adicionar autentica\u00e7\u00e3o real com JWT"
GET     /tasks/999                         -> 404 {"error":"Task n\u00e3o encontrada"} 
GET     /tasks/search?q=login&status=in_progress -> 200 [{"category_id":2,"created_at":"2026-10-21 16:56:17.658181","description":"Tela de login responsiva","due_date":"2026-10
GET     /tasks/stats                       -> 200 {"cancelled":1,"completion_rate":10.0,"done":1,"in_progress":2,"overdue":2,"pending":6,"total":10} 
POST    /tasks                             -> 201 {"category_id":1,"created_at":"2026-10-21 16:56:20.032481","description":"","due_date":"2030-01-01 00:00:00","id":11,"pr
POST    /tasks                             -> 400 {"error":"T\u00edtulo muito curto"} 
POST    /tasks                             -> 400 {"error":"Prioridade deve ser entre 1 e 5"} 
PUT     /tasks/11                          -> 200 {"category_id":1,"created_at":"2026-10-21 16:56:20.032481","description":"","due_date":"2030-01-01 00:00:00","id":11,"pr
PUT     /tasks/11                          -> 400 {"error":"Status inv\u00e1lido"} 
DELETE  /tasks/11                          -> 200 {"message":"Task deletada com sucesso"} 
GET     /users                             -> 200 [{"active":true,"created_at":"2026-10-21 16:56:17.655173","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role
GET     /users/1                           -> 200 {"active":true,"created_at":"2026-10-21 16:56:17.655173","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","passw
POST    /users                             -> 201 {"active":true,"created_at":"2026-10-21 16:56:20.140972","email":"ana@email.com","id":4,"name":"Ana","password":"571fd41
POST    /users                             -> 409 {"error":"Email j\u00e1 cadastrado"} 
PUT     /users/4                           -> 200 {"active":true,"created_at":"2026-10-21 16:56:20.140972","email":"ana@email.com","id":4,"name":"Ana Maria","password":"5
GET     /users/1/tasks                     -> 200 [{"created_at":"2026-10-21 16:56:17.658179","description":"Adicionar autentica\u00e7\u00e3o real com JWT","due_date":"20
POST    /login                             -> 200 {"message":"Login realizado com sucesso","token":"fake-jwt-token-1","user":{"active":true,"created_at":"2026-10-21 16:56
POST    /login                             -> 401 {"error":"Credenciais inv\u00e1lidas"} 
DELETE  /users/4                           -> 200 {"message":"Usu\u00e1rio deletado com sucesso"} 
GET     /reports/summary                   -> 200 {"generated_at":"2026-10-21 16:56:20.240822","overdue":{"count":2,"tasks":[{"days_overdue":3,"due_date":"2026-10-18 16:5
GET     /reports/user/1                    -> 200 {"statistics":{"cancelled":0,"completion_rate":0.0,"done":0,"high_priority":2,"in_progress":0,"overdue":2,"pending":4,"t
GET     /categories                        -> 200 [{"color":"#3498db","created_at":"2026-10-21 16:56:17.655942","description":"Tarefas de backend","id":1,"name":"Backend"
POST    /categories                        -> 201 {"color":"#123456","created_at":"2026-10-21 16:56:20.281602","description":"","id":5,"name":"QA"} 
PUT     /categories/5                      -> 200 {"color":"#123456","created_at":"2026-10-21 16:56:20.281602","description":"Qualidade","id":5,"name":"QA"} 
DELETE  /categories/5                      -> 200 {"message":"Categoria deletada"} 
```

## Smoke test DEPOIS da refatoração
```
GET     /                                  -> 200 {"message":"Task Manager API","version":"1.0"} 
GET     /health                            -> 200 {"status":"ok","timestamp":"2026-10-21 15:09:08.371927"} 
GET     /tasks                             -> 200 [{"category_id":1,"category_name":"Backend","created_at":"2026-10-21 18:09:05.741754","description":"Adicionar autentica
GET     /tasks/1                           -> 200 {"category_id":1,"created_at":"2026-10-21 18:09:05.741754","description":"Adicionar autentica\u00e7\u00e3o real com JWT"
GET     /tasks/999                         -> 404 {"error":"Task n\u00e3o encontrada"} 
GET     /tasks/search?q=login&status=in_progress -> 200 [{"category_id":2,"created_at":"2026-10-21 18:09:05.741756","description":"Tela de login responsiva","due_date":"2026-10
GET     /tasks/stats                       -> 200 {"cancelled":1,"completion_rate":10.0,"done":1,"in_progress":2,"overdue":2,"pending":6,"total":10} 
POST    /tasks                             -> 201 {"category_id":1,"created_at":"2026-10-21 18:09:08.451874","description":"","due_date":"2030-01-01 00:00:00","id":11,"pr
POST    /tasks                             -> 400 {"error":"T\u00edtulo muito curto"} 
POST    /tasks                             -> 400 {"error":"Prioridade deve ser entre 1 e 5"} 
PUT     /tasks/11                          -> 200 {"category_id":1,"created_at":"2026-10-21 18:09:08.451874","description":"","due_date":"2030-01-01 00:00:00","id":11,"pr
PUT     /tasks/11                          -> 400 {"error":"Status inv\u00e1lido"} 
DELETE  /tasks/11                          -> 200 {"message":"Task deletada com sucesso"} 
GET     /users                             -> 200 [{"active":true,"created_at":"2026-10-21 18:09:05.738281","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role
GET     /users/1                           -> 200 {"active":true,"created_at":"2026-10-21 18:09:05.738281","email":"joao@email.com","id":1,"name":"Jo\u00e3o Silva","role"
POST    /users                             -> 201 {"active":true,"created_at":"2026-10-21 18:09:08.586376","email":"ana@email.com","id":4,"name":"Ana","role":"user"} 
POST    /users                             -> 409 {"error":"Email j\u00e1 cadastrado"} 
PUT     /users/4                           -> 200 {"active":true,"created_at":"2026-10-21 18:09:08.586376","email":"ana@email.com","id":4,"name":"Ana Maria","role":"manag
GET     /users/1/tasks                     -> 200 [{"created_at":"2026-10-21 18:09:05.741754","description":"Adicionar autentica\u00e7\u00e3o real com JWT","due_date":"20
POST    /login                             -> 200 {"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4ifQ.atj_xA.T3wpvL-bBHmYThhNCz2LXa5F
POST    /login                             -> 401 {"error":"Credenciais inv\u00e1lidas"} 
DELETE  /users/4                           -> 200 {"message":"Usu\u00e1rio deletado com sucesso"} 
GET     /reports/summary                   -> 200 {"generated_at":"2026-10-21 18:09:08.776562","overdue":{"count":2,"tasks":[{"days_overdue":3,"due_date":"2026-10-18 18:0
GET     /reports/user/1                    -> 200 {"statistics":{"cancelled":0,"completion_rate":0.0,"done":0,"high_priority":2,"in_progress":0,"overdue":2,"pending":4,"t
GET     /categories                        -> 200 [{"color":"#3498db","created_at":"2026-10-21 18:09:05.739392","description":"Tarefas de backend","id":1,"name":"Backend"
POST    /categories                        -> 201 {"color":"#123456","created_at":"2026-10-21 18:09:08.812216","description":"","id":5,"name":"QA"} 
PUT     /categories/5                      -> 200 {"color":"#123456","created_at":"2026-10-21 18:09:08.812216","description":"Qualidade","id":5,"name":"QA"} 
DELETE  /categories/5                      -> 200 {"message":"Categoria deletada"} 
```

Resultado: 28/28 chamadas com o mesmo status code do baseline. Extras: `priority` string -> 400 (antes 500); PUT categoria sem corpo -> 400 (antes 500); `password` ausente das respostas; token assinado (itsdangerous); login com hash MD5 legado -> 200 e hash migrado para scrypt.
