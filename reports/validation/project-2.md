# Projeto 2 — ecommerce-api-legacy: validação da Fase 3

## Boot (npm start)
```

> desafio-arquitetura-ia-boilerplate@1.0.0 start
> node src/app.js

[2026-10-21T18:06:25.053Z] INFO LMS API rodando na porta 3000
[2026-10-21T18:06:26.859Z] INFO Processando pagamento {"last4":"4444","amount":497}
[2026-10-21T18:06:26.916Z] INFO Processando pagamento {"last4":"4444","amount":997}
[2026-10-21T18:06:26.929Z] INFO Processando pagamento {"last4":"4111","amount":497}
[2026-10-21T18:06:26.978Z] INFO Usuário removido com dependentes {"userId":1}
```

## Smoke test ANTES da refatoração (baseline)
```
POST    /api/checkout                    -> 200 {"msg":"Sucesso","enrollment_id":2}
POST    /api/checkout                    -> 400 Pagamento recusado
POST    /api/checkout                    -> 200 {"msg":"Sucesso","enrollment_id":3}
POST    /api/checkout                    -> 404 Curso não encontrado
POST    /api/checkout                    -> 400 Bad Request
GET     /api/admin/financial-report      -> 200 [{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":994,"students":[{"s
DELETE  /api/users/1                     -> 200 Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.
```

## Smoke test DEPOIS da refatoração
```
POST    /api/checkout                    -> 200 {"msg":"Sucesso","enrollment_id":2}
POST    /api/checkout                    -> 400 Pagamento recusado
POST    /api/checkout                    -> 200 {"msg":"Sucesso","enrollment_id":3}
POST    /api/checkout                    -> 404 Curso não encontrado
POST    /api/checkout                    -> 400 Bad Request
GET     /api/admin/financial-report      -> 200 [{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":994,"students":[{"s
DELETE  /api/users/1                     -> 200 Usuário deletado
```

Resultado: 7/7 chamadas com o mesmo status code do baseline. Extras: DELETE de usuário inexistente -> 404; JSON inválido -> 400; com `ADMIN_TOKEN` definido o relatório exige `X-Admin-Token` (403 sem, 200 com); após deletar o usuário 1 o relatório não contém mais matrículas órfãs; o log mostra apenas os 4 últimos dígitos do cartão.
