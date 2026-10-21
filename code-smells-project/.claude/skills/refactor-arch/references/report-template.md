# Template do Relatório de Auditoria (Fase 2)

O relatório é impresso no terminal (e pode ser salvo pelo usuário em Markdown). Siga **exatamente** a estrutura abaixo — seções, ordem e rótulos. Textos entre `<...>` são preenchidos; não deixe placeholders.

## Regras de preenchimento

1. **Ordenação:** CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade, ordem alfabética de arquivo.
2. **Numeração:** findings numerados sequencialmente (`#1`, `#2`, …) na ordem final.
3. **File:** sempre `caminho/relativo:linha`, `caminho:inicio-fim` ou lista separada por vírgula (`routes/task_routes.py:30-39, 71-80`). Caminhos relativos à raiz do projeto.
4. **Category:** `Security`, `Architecture`, `Performance`, `Maintainability`, `Deprecated API` ou `Reliability`.
5. **Anti-pattern:** ID e nome do catálogo (ex.: `AP-02 SQL Injection`).
6. **Description:** o que está errado neste código (cite o trecho/valor concreto em uma linha).
7. **Impact:** consequência concreta (segurança, manutenção, performance, dados).
8. **Recommendation:** ação específica + padrão do playbook (`P-xx`).
9. **Summary** deve bater com a contagem real de findings listados.
10. Inclua a seção **Deprecated APIs** mesmo que vazia (escreva "Nenhuma API deprecated detectada" se for o caso).
11. Termine com o **Refactoring Plan** (estrutura alvo) e a pergunta de confirmação.

## Template

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-da-pasta>
Stack:   <Linguagem> + <Framework versão>
Files:   <N> analyzed | ~<L> lines of code
Architecture (current): <classificação da Fase 1>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

| # | Severity | Anti-pattern | File |
|---|----------|--------------|------|
| 1 | CRITICAL | AP-xx <nome> | <arquivo:linhas> |
| … | … | … | … |

## Findings

### #1 [CRITICAL] <Título curto>
File: <arquivo:linhas>
Category: <categoria>
Anti-pattern: <AP-xx Nome>
Description: <o que está errado, com o trecho/valor concreto>
Impact: <consequência>
Recommendation: <ação concreta> (Playbook P-xx)

### #2 [HIGH] <Título>
...

## Deprecated APIs
| File:line | Deprecated API | Modern replacement |
|-----------|----------------|--------------------|
| <arquivo:linha> | <api> | <substituta> |

## Refactoring Plan (Phase 3 preview)
Strategy: <"monolito → MVC completo em src/" | "evolução incremental das camadas existentes">
Target structure:
```
<árvore alvo anotada com a camada de cada pasta>
```
Key transformations:
- <P-xx> → findings #a, #b
- ...
API contract changes (security-driven): <lista ou "None">

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Exemplo de finding bem escrito

```markdown
### #2 [CRITICAL] SQL Injection no login
File: models.py:109-111
Category: Security
Anti-pattern: AP-02 SQL Injection
Description: `login_usuario` concatena email e senha: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`.
Impact: `email = "' OR 1=1 --"` autentica como o primeiro usuário (admin) sem senha.
Recommendation: Usar placeholders `?` com tupla de parâmetros e verificar a senha via hash no código (Playbook P-02, P-08).
```

## Exemplo de finding ruim (não faça)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código tem problemas de qualidade.
```
Falta linha, anti-pattern, impacto e recomendação acionável.
