---
name: refactor-arch
description: Analisa, audita e refatora uma codebase backend para o padrão MVC (Models, Views/Routes, Controllers), de forma agnóstica de tecnologia. Executa 3 fases — (1) análise da stack e arquitetura, (2) auditoria contra um catálogo de anti-patterns com relatório por severidade e arquivo:linha, pausando para confirmação, (3) refatoração para MVC com validação de boot e endpoints. Use quando o usuário pedir /refactor-arch, auditoria arquitetural, "refatorar para MVC", ou revisão de code smells/segurança de um projeto legado.
disable-model-invocation: true
argument-hint: "[caminho-do-projeto (opcional, padrão: diretório atual)]"
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior executando uma refatoração **segura, incremental e verificável** de um projeto legado. O projeto-alvo é o diretório atual (ou `$ARGUMENTS`, se informado).

A skill tem **3 fases sequenciais**. Nunca pule uma fase e nunca altere arquivos antes da confirmação explícita do usuário ao final da Fase 2.

## Arquivos de referência (carregue sob demanda)

| Arquivo | Quando ler | Conteúdo |
|---|---|---|
| `references/project-analysis.md` | Início da Fase 1 | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| `references/anti-patterns-catalog.md` | Início da Fase 2 | Catálogo de anti-patterns (sinais de detecção + severidade), incluindo APIs deprecated |
| `references/report-template.md` | Ao montar o relatório da Fase 2 | Formato obrigatório do relatório de auditoria |
| `references/mvc-guidelines.md` | Início da Fase 3 | Regras da arquitetura MVC alvo, responsabilidades e layout por stack |
| `references/refactoring-playbook.md` | Durante a Fase 3 | Transformações concretas (antes/depois) para cada anti-pattern |

Os caminhos acima são relativos ao diretório desta skill (`.claude/skills/refactor-arch/`).

## Regras invioláveis

1. **Fases 1 e 2 são somente leitura.** Use apenas leitura de arquivos e buscas (Read, Grep, Glob, `ls`, `wc`). Não crie, edite, mova ou apague nada; não instale dependências.
2. **Pausa obrigatória** ao fim da Fase 2: pergunte `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e **pare a resposta**. Só continue com um "sim" explícito (y, yes, s, sim, prossiga). Qualquer outra resposta encerra a skill sem modificações.
3. **Evidência exata.** Todo finding cita `arquivo:linha` ou `arquivo:linhaInicial-linhaFinal` conferidos na leitura real do arquivo. Nunca invente números de linha; se em dúvida, releia o trecho.
4. **Preservar o contrato da API.** Mesmos métodos HTTP, paths, nomes de campos de request/response e status codes de sucesso. Mudanças de contrato só são permitidas para eliminar uma falha de segurança (ex.: remover senha da resposta, remover endpoint que executa SQL arbitrário) e devem ser listadas explicitamente no resumo da Fase 3.
5. **Preservar o comando de execução** documentado (ex.: `python app.py`, `npm start`). O entry point pode virar um *composition root* fino, mas deve continuar existindo.
6. **Sem dependências novas** a menos que imprescindível; prefira a stdlib e o que o framework já traz (ex.: `werkzeug.security` no Flask, `crypto` no Node). Se adicionar, atualize o manifesto (requirements.txt / package.json).
7. Adapte-se ao contexto: um monolito de poucos arquivos e um projeto já parcialmente em camadas exigem transformações diferentes (ver `mvc-guidelines.md` § Estratégia por ponto de partida).

---

## FASE 1 — Análise do Projeto

Objetivo: entender stack, domínio e arquitetura atual antes de julgar qualquer coisa.

1. Leia `references/project-analysis.md`.
2. Liste os arquivos-fonte ignorando `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `.git/`, `.claude/`, `dist/`, `build/`, lockfiles e bancos (`*.db`).
3. Leia manifestos (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, …) e o README do projeto para detectar linguagem, framework + versão, dependências e comando de execução.
4. Leia **todos** os arquivos-fonte (são a base da auditoria). Conte as linhas com `wc -l`.
5. Mapeie:
   - **Domínio** (substantivos das rotas/tabelas → ex.: "E-commerce", "LMS", "Task Manager");
   - **Banco** (driver/ORM, tabelas/modelos, onde o schema é criado, onde há seed);
   - **Inventário de endpoints** (método + path + handler + arquivo:linha) — será usado na validação da Fase 3;
   - **Arquitetura atual** (classifique com a tabela de `project-analysis.md`: monolito de arquivo único, monolito multi-arquivo "pseudo-camadas", camadas parciais, MVC/camadas completo).
6. Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se detectável>
Framework:     <framework + versão>
Dependencies:  <deps relevantes, separadas por vírgula>
Domain:        <descrição curta do domínio (entidades principais)>
Architecture:  <classificação — justificativa em uma linha>
Source files:  <N> files analyzed (~<L> lines)
DB:            <engine + acesso (driver cru / ORM)>
DB tables:     <tabelas ou modelos>
Entry point:   <arquivo + comando de execução>
Endpoints:     <N> endpoints mapeados
================================
```

Em seguida, imprima a tabela do inventário de endpoints (Método | Path | Handler | Arquivo:linha).

---

## FASE 2 — Auditoria Arquitetural

Objetivo: cruzar o código contra o catálogo e produzir um relatório priorizado.

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Para **cada** anti-pattern do catálogo, procure os sinais de detecção (use Grep com os padrões sugeridos **e** a leitura feita na Fase 1). Registre cada ocorrência com arquivo e linha(s) exatos.
3. Verifique explicitamente **APIs deprecated** (seção AP-14 do catálogo) para a stack detectada, incluindo avisos que a própria execução emitiria (ex.: `DeprecationWarning`, `LegacyAPIWarning`).
4. Agrupe ocorrências do mesmo anti-pattern no mesmo arquivo em um único finding (listando todas as linhas); ocorrências em arquivos distintos podem virar findings distintos quando o impacto difere.
5. Classifique a severidade usando a definição do catálogo (CRITICAL / HIGH / MEDIUM / LOW). Em caso de dúvida entre duas severidades, escolha a maior e justifique no campo Impact.
6. Ordene os findings: CRITICAL → HIGH → MEDIUM → LOW (dentro da mesma severidade, por arquivo).
7. Imprima o relatório **exatamente** no formato de `report-template.md`, incluindo o plano de refatoração proposto (estrutura alvo + mapeamento finding → padrão do playbook).
8. Mínimos de qualidade: ≥ 5 findings e ≥ 1 CRITICAL ou HIGH. Se não atingir, releia o código procurando pelas categorias ainda não verificadas antes de concluir que o projeto está limpo.
9. Termine com a linha abaixo e **pare** aguardando o usuário:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## FASE 3 — Refatoração para MVC

Só execute após confirmação explícita. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.

### 3.1 Baseline (antes de tocar em qualquer arquivo)
1. Prepare o ambiente de execução (venv/`npm install`) **fora** do controle de versão ou em diretórios já ignorados pelo `.gitignore`.
2. Suba a aplicação **original** em uma porta livre (atenção: no macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver e responde 403 — prefira outra porta, ex. 5055/3055, sem editar o código: use variável de ambiente ou um wrapper de linha de comando).
3. Execute um smoke test que chama **todos** os endpoints do inventário (casos de sucesso e ao menos um de erro de validação/404 por recurso). Guarde status code e formato do corpo como baseline. Rode seeds se o README exigir.
4. Pare a aplicação e apague bancos/arquivos gerados pelo baseline.

### 3.2 Plano e execução
1. Crie uma lista de tarefas (TodoWrite/TaskCreate, se disponível) com uma tarefa por grupo de transformação.
2. Siga a ordem recomendada em `mvc-guidelines.md` § Ordem de execução: config → infraestrutura de banco → models → controllers → views/routes → middlewares/error handling → composition root → limpeza.
3. Para cada finding, aplique o padrão de transformação correspondente do playbook. Não deixe finding CRITICAL/HIGH sem tratamento; MEDIUM/LOW tratados sempre que tocarem arquivos já reescritos.
4. Remova os arquivos legados que foram totalmente substituídos (use `git mv` quando um arquivo apenas muda de lugar, para preservar histórico). Não deixe código morto nem imports não utilizados.
5. Crie `.env.example` documentando todas as variáveis de configuração (sem valores secretos reais) e atualize o README do projeto se o modo de execução/configuração mudou.

### 3.3 Validação (obrigatória)
1. **Boot:** suba a aplicação refatorada com o comando de execução preservado (porta livre via env var). Ela deve iniciar sem exceções nem warnings de deprecação novos.
2. **Endpoints:** rode o mesmo smoke test do baseline e compare: cada endpoint deve retornar o mesmo status code e o mesmo formato de corpo, exceto as mudanças de contrato justificadas por segurança.
3. **Re-scan:** rode novamente os padrões de grep do catálogo nos novos arquivos; nenhum CRITICAL/HIGH pode permanecer.
4. Se algo falhar, corrija e repita a validação (máx. 3 ciclos). Se ainda falhar, reporte com honestidade o que não passou — nunca marque ✓ sem ter executado.
5. Pare a aplicação e remova bancos/artefatos gerados pelos testes.

### 3.4 Resumo final
Imprima:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios final, anotando a camada MVC de cada pasta>

## Findings addressed
<tabela: finding → transformação aplicada → arquivo(s) novos>

## API contract changes (security-driven)
<lista, ou "None">

## Validation
  ✓|✗ Application boots without errors (<comando usado>)
  ✓|✗ All endpoints respond correctly (<N>/<N> matched baseline)
  ✓|✗ Zero CRITICAL/HIGH anti-patterns remaining
================================
```
