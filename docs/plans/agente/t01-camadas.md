---
type: Plan
title: T1 · Reorganização em camadas
description: Tarefa da fase do agente que cria o bootstrap como composition root, move as tools para a application, cria a infrastructure e prepara settings, dependências e marcadores para as ondas seguintes.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T1 · Reorganização em camadas

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 0, sem dependências. Modelo sugerido:
> Opus, porque todas as tarefas seguintes partem daqui.

## Objetivo

Levar o código ao desenho da arquitetura (B36 a B39) **sem mudar comportamento**, e deixar prontos os pontos de extensão
que as ondas 1 e 2 usam sem editar os mesmos arquivos.

## O que fazer

1. **Bootstrap:** `src/api/main.py` e `src/api/settings.py` passam a `src/api/bootstrap/app.py` e `bootstrap/settings.py`.
   O conteúdo de `src/api/composition/` vira `bootstrap/student_providers.py` (carga da sessão, adapter, repositórios e
   services por aluno) e some. O `StudentRepositories` deixa de existir como tipo: o provider passa cada repositório ao
   service que o usa.
2. **Singletons:** `bootstrap/singletons.py` reúne o que nasce uma vez: `Settings`, `Database`, relógio. As tarefas seguintes
   acrescentam os seus campos por módulos próprios, não neste arquivo; se não couber, T1 já declara os campos com valor
   ausente.
3. **Infrastructure:** `ReferenceClock` sai de `settings.py` para `infrastructure/clock.py`, implementando o port `Clock`.
4. **Sessão:** port `StudentSessionLoader` em `domain/ports/`; `StudentSessionRepository` passa a implementá-lo.
5. **Tools:** `presentation/tools/` vai para `application/agent/tools/`, com `registry.py`. `StudentTools` vai para
   `application/agent/student_tools.py`.
6. **Settings da fase inteira**, todos opcionais ou com padrão, para que nenhuma tarefa precise editar o arquivo:
   modelo (`gpt-6-luna`), effort, chave da OpenAI lida de `OPENAI_API_KEY`, limites de chamadas, timeout e concorrência do
   agente, janela do histórico (20), segredo e validade do JWT, `dev_login`, segredo e validade da proposta (15 minutos),
   chaves e URL do Langfuse lidas de `LANGFUSE_*`.
7. **Dependências** com versão exata, conferidas na instalação: `pyjwt` e `langfuse` nas dependências; `pyyaml` e `locust` no
   grupo `dev`.
8. **Marcador `live`** no `pyproject.toml` e opção `--live` em `tests/conftest.py`: sem a opção, testes `live` são pulados.
9. **Entradas:** `Dockerfile` e `compose.yaml` passam a `api.bootstrap.app:ApiFactory.create`. `.env.example` ganha as
   variáveis novas, sem valores secretos. O serviço `db` do Compose passa a receber `API_DB_PASSWORD`, que o script de role
   de T2 lê; a URL da API troca para a role em T2. T1 é a única tarefa da onda 0 que edita `compose.yaml` e
   `.env.example`.
10. **Pastas por área (D17 do spec-mãe):** cada camada ganha subpastas por área, e o prefixo da área sai do nome do arquivo
    (`domain/finance_agreement.py` vira `domain/finance/agreement.py`). Alvo:
    - `domain/`: `academic/`, `finance/`, `lms/`, `protocol/`, `identity/` (sessão), `shared/` (marca, dinheiro), mais
      `ontology/` e `ports/`, que já existem.
    - `application/`: `academic/`, `finance/`, `lms/`, `protocol/`, `overview/`, `health/` e `shared/` (página, filtro de
      período, busca por nome, `ToolResult`), cada área com o seu `dto/`; mais `agent/`.
    - `persistence/`: `core/` (base, database, adapter, guard, ownership e registro, `dialect_lookup`, `brasilia`),
      `identity/` (carga da sessão e consultas de identidade e pagador), mais `sag/`, `finance/`, `lms/` e `secretary/`.
    - `tests/unit/<área>/` e `tests/integration/<área>/`, com os helpers compartilhados em `support/`.
    O nome final de cada arquivo é escolha do implementador, desde que diga o que o arquivo contém sem repetir a pasta.
    `docs/ontology.md` é gerado: se o caminho do gerador mudar, o teste de sincronia continua passando.
11. **Testes:** mudam de pasta e de import. Nenhuma asserção muda.

## Não tocar

Semântica das tools, services, domínio e persistence; arquivos do dono.

## Arquivos do dono

Antes de T1, o dono aplica o patch de transição: o `quality.toml` aceita os caminhos novos de `database.py`,
`repository_adapter.py` e `student_session_repository.py` junto dos antigos. Se outra regra do dono citar caminho movido,
o implementador para e relata, sem contornar.

Ao fim da arrumação (T1, T1b e T2), o condutor entrega um patch final que tira do `quality.toml` os caminhos antigos e
`src/api/presentation/tools/**`, as camadas opcionais `(api.main)` e `(api.settings)` do `.importlinter` e `api/main.py` e
`api/settings.py` de `LAYER_MODULES` em `tests/lint/test_import_contracts.py`.

## Pronto quando

- `make check` verde com os mesmos testes de antes (609 ou mais).
- `lint-imports` com os 6 contratos mantidos, e `grep -r "api.composition\|api.main\|api.settings" src tests` vazio.
- `docker compose up -d --wait api` sobe, e `GET /health` responde 200.

## Oráculo

API real no Compose: `/health` 200 e o log de subida sem erro. Suíte completa verde.
