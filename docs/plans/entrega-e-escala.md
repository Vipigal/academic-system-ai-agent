---
type: Plan
title: Entrega e escala
description: Spec da tarefa que deixa o projeto rodável pelo examinador com um comando, troca o semáforo por rate limit por aluno em Redis, separa as imagens de desenvolvimento e produção e registra a análise de escala.
tags: [plano, entrega, escala, docker, rate-limit, ops]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-09T15:00:00Z }
sources:
  - id: diretrizes
    resource: /README.md
    title: Enunciado do case, que vira /docs/diretrizes.md na T5
  - id: arquitetura
    resource: /docs/architecture.md
    title: Arquitetura do agente de atendimento ao aluno
  - id: pesquisa-docker
    resource: vault do Obsidian, pasta docker-fastapi-producao
    title: Dockerfile de produção para FastAPI, pesquisa de 2026-11-09
---

# Entrega e escala

> **Status:** aprovado para implementação · **Data:** 2026-11-09
> **Spec vivo:** este arquivo é a fonte única da tarefa. Mudanças são editadas aqui e anotadas em
> "Mudança no spec" na seção Registro; leia o Registro junto do restante.
> **Repos:** só este. O dono do projeto liberou, para esta tarefa, mudanças em `Makefile`, `.importlinter`, `pyproject.toml` e
> `.github/workflows/check.yml`, nos pontos descritos aqui; `ruff.toml`, `.flake8`, `mypy.ini`, `pyrightconfig.json`, `quality.toml`, `tools/quality/` e
> `tests/lint/` seguem intocáveis.

## Para o humano

- **TL;DR:** o examinador passa a rodar tudo (banco, Redis, API e front) com `cp .env.example .env`, a chave da OpenAI e `docker compose up`. O semáforo de
  8 chamadas por processo sai; no lugar entra um rate limit de 60 mensagens por hora por aluno, em Redis, que falha aberto. Nascem um `local.dockerfile` de
  desenvolvimento e um `Dockerfile` de produção multi-stage com uv. O README vira `docs/diretrizes.md`, e um README novo explica o projeto, com badges de CI e
  coverage e as evidências reservadas.
- **Revise com atenção:** o desenho do rate limit (§6.2), o Dockerfile de produção e o overlay de produção (§6.4) e a análise de escala (§6.6), que vai
  depois para o documento de entrega.
- **Para o aluno:** acima de 60 mensagens numa hora, o chat responde 429 e diz quando volta. Nada muda abaixo disso.

## 1. Contexto e problema

1. **O examinador não consegue rodar.** O `README.md` é o enunciado do case. Com `APP_JWT_SECRET` vazio, o `JwtCodec` levanta erro na subida
   (`src/api/infrastructure/token_codec.py:12`); o `APP_PROPOSAL_SECRET` vazio faz o mesmo no `ProposalJwtSigner`
   (`src/api/bootstrap/protocol_providers.py:22`); com `APP_DEV_LOGIN=false`, a rota de login nem é montada (`src/api/bootstrap/identity_providers.py:30`). O
   front só roda com Node na máquina.
2. **O semáforo limita a escala sem proteger o custo.** `asyncio.Semaphore(8)` por processo (`src/api/application/agent/agent_runtime.py:35`, usado em
   `src/api/application/agent/provider_gate.py:24`) segura no máximo 8 chamadas ao modelo ao mesmo tempo por réplica, sem 429 e sem relação com o limite da
   conta no provedor. Um aluno sozinho ainda pode disparar mensagens sem limite, e cada uma faz até 8 chamadas ao modelo.
3. **A imagem não é de produção.** Um estágio, `pip install .` sem lock, `USER nobody`, CMD sem flags de produção, e o Compose sobe a API com `--reload`.
4. **Não há medida de cobertura** nem badge, e o `/health` único consulta o banco, o que, usado como liveness, reiniciaria todas as réplicas numa queda do
   Postgres.

## 2. Princípios

- **O examinador roda com um comando.** Docker e a chave da OpenAI bastam; o resto vem pronto no `.env.example`.
- **Limite onde está o custo.** O que custa é o LLM; o limite conta mensagens do `/chat`, por pessoa, não por token nem por IP.
- **O limite não derruba o atendimento.** Ele protege custo, não isolamento: Redis fora do ar deixa passar e registra.
- **Opcional de verdade.** Langfuse e Redis ausentes não quebram nenhum fluxo; Redis ausente só desliga o limite.
- **Produção mostrada, desenvolvimento intacto.** O `docker compose up` de sempre continua sendo o modo de desenvolvimento; a produção é um overlay
  explícito.
- **Camadas e lint da casa valem para o código novo:** porta no domínio, adaptador em infrastructure, montagem no bootstrap, HTTP na presentation.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| E1 | `compose.yaml` é o modo de desenvolvimento: constrói o `local.dockerfile` com reload e o código montado | O fluxo do dono e do harness não muda |
| E2 | Produção sobe com `docker compose -f compose.yaml -f compose.prod.yaml up`, um overlay que troca o build para o `Dockerfile` e roda com `read_only`, `tmpfs /tmp`, `cap_drop: ALL` e `no-new-privileges` | A imagem de produção é exercitada, endurecida, sem mudar o comando de dev |
| E3 | O banco passa a `postgres:18` com tag exata; saem a imagem e a menção ao pgvector | O RAG foi descartado; a imagem pgvector levantava pergunta sem resposta |
| E4 | Serviço `redis` no Compose, sem persistência em disco | Contadores de uma hora não precisam sobreviver a reinício |
| E5 | Serviço `web` no Compose: build do front em Node e arquivos estáticos num nginx sem root, publicado em `127.0.0.1:5173` | O examinador não precisa de Node |
| E6 | uv em tudo: `uv.lock` no repo, `make setup` com `uv sync`, `uv lock --check` no CI, uv no estágio de build do Dockerfile | Trava as dependências transitivas de ponta a ponta |
| E7 | `Dockerfile` de produção multi-stage: `uv sync --locked --no-editable`, só a venv no estágio final, base `python:3.14.10-slim-trixie` com tag exata e sem digest, UID/GID 10001, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED` e `PYTHONFAULTHANDLER`, exec form | Padrão do guia do uv e da doc do FastAPI; o digest congelaria patches de segurança sem um bot |
| E8 | Um processo uvicorn por container, com `--timeout-keep-alive 65`, `--timeout-graceful-shutdown 70`, `--no-server-header` e `--no-access-log`; sem `--workers` no CMD, e `WEB_CONCURRENCY` fica disponível pelo próprio uvicorn | Escala por réplicas; keep-alive acima dos 60 s típicos de load balancer; graceful cobre o turno de até 60 s; o `RequestLog` já registra cada request |
| E9 | Sem `--proxy-headers` nem `--forwarded-allow-ips` explícitos no CMD | O uvicorn já trata os headers de proxy e confia só em `127.0.0.1` e `::1` por padrão; quem implanta atrás de um LB define `FORWARDED_ALLOW_IPS`, sem risco na máquina do examinador |
| E10 | `.dockerignore` segue como lista de permitidos, com o `uv.lock` acrescentado; labels `org.opencontainers.image.*` com versão, commit e data por `ARG` | O formato atual (`*` e exceções) já é o mais restrito |
| E11 | O semáforo sai inteiro: `ProviderGate`, `AgentLimits.max_concurrency`, `AgentRuntime.gate`, `agent_max_concurrency` e `APP_AGENT_MAX_CONCURRENCY`. O eval ganha uma concorrência padrão própria | O limite certo é por aluno e no provedor, não por processo |
| E12 | O rate limit conta só as mensagens do `POST /chat` | O custo está no LLM; criar conversa e confirmar protocolo não chamam o modelo |
| E13 | A chave é o menor `person_id` da `StudentSession`: `ratelimit:chat:<person_id>` | 1.015 `person_id` para 1.000 CPFs: com o `sub` do JWT, a mesma pessoa logada por duas matrículas teria duas cotas. A sessão já é carregada no `/chat` |
| E14 | Janela fixa que começa na primeira mensagem: INCR e EXPIRE NX numa transação (MULTI), sem script Lua; 60 por hora por padrão, em `APP_CHAT_RATE_LIMIT_PER_HOUR` | Sem pico coletivo na virada da hora; 60 cobre um examinador testando; sem Lua, o cliente em memória dos testes reproduz o comportamento |
| E15 | Estourou: 429 antes de abrir o stream, com `Retry-After` (tempo restante da chave) e `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`; as respostas aceitas também levam os `RateLimit-*` | O front e qualquer cliente sabem quando voltar |
| E16 | Redis fora do ar ou lento (timeout curto, cerca de 100 ms): fail-open, a mensagem passa e a API registra log de erro | O limite é proteção de custo; o isolamento entre alunos não depende dele |
| E17 | Redis opcional: `APP_REDIS_URL` vazio desliga o limite, com aviso no log da subida. Os testes usam um cliente Redis em memória, escrito no projeto, que implementa as operações usadas; o CI não sobe Redis | Decisão do dono: Redis opcional e testado com cliente em memória |
| E18 | Coverage com `pytest-cov` no `make test`, publicada pela action `py-cov-action/python-coverage-comment-action` (só `GITHUB_TOKEN`, badge numa branch de dados do repo, comentário nos PRs); README com badges de CI e coverage | Repositório público, sem conta externa |
| E19 | `/health/live` sem dependências e `/health/ready` com o banco; o `/health` sai. O healthcheck do Compose usa o ready; o `HEALTHCHECK` do Dockerfile usa o live | Readiness checa backends; liveness que depende do banco causa reinício em cascata |
| E20 | Pool do banco configurável: `APP_DB_POOL_SIZE`, `APP_DB_MAX_OVERFLOW`, `APP_DB_POOL_TIMEOUT_SECONDS`, com `pool_pre_ping` | O pool padrão (5 + 10) é o primeiro gargalo sob carga, antes do LLM |
| E21 | Contrato novo no `.importlinter`: `redis` só em `api.infrastructure` e `api.bootstrap` | Mesmo padrão do SQLAlchemy: o cliente não vaza para as regras |
| E22 | O `README.md` atual vira `docs/diretrizes.md` com `git mv`; o README novo traz propósito, como foi feito, como rodar, arquitetura em alto nível, badges e a seção de evidências reservada, onde entrarão os traces públicos do Langfuse | Entregável 1 do enunciado; as evidências ficam para o fim, por decisão do dono |
| E23 | `.env.example` roda sem edição além da chave da OpenAI: `APP_JWT_SECRET` e `APP_PROPOSAL_SECRET` de exemplo (32 bytes ou mais, com aviso de trocar), `APP_DEV_LOGIN=true`, CORS com `localhost` e `127.0.0.1` na 5173 | Hoje segredo vazio derruba a subida e sem dev-login não há como entrar |
| E24 | Ficam só descritos no documento de entrega: scan com Trivy, SBOM, hadolint, digest com Dependabot, `QueueHandler` no log e workers múltiplos por padrão | Decisão do dono: CI e imagem sem esses itens agora |

### 3.2 Pendentes (confirmar na revisão)

Nenhuma.

## 4. Escopo

### Dentro

- `.env.example`, settings, pool do banco, `pyproject.toml`, `uv.lock`, `Makefile`, CI, `CLAUDE.md`.
- Remoção do semáforo e o padrão próprio de concorrência do eval.
- Rate limit por aluno: porta, decisão, serviço, adaptador Redis, adaptador sem limite, cliente em memória, 429, contrato de import.
- Health live e ready.
- `Dockerfile`, `local.dockerfile`, `compose.yaml`, `compose.prod.yaml`, `.dockerignore`, imagem e configuração do front.
- `docs/diretrizes.md`, `README.md` novo, `docs/index.md`.

### Fora

| Item | Volta quando |
|---|---|
| Documento de evidências e traces públicos do Langfuse | Na última etapa, depois dos ajustes que o dono ainda quer fazer |
| Scan, SBOM e hadolint no CI | O dono pedir; o documento de entrega descreve o job |
| Digest da base e Dependabot | O dono pedir; exige o bot para não congelar patches |
| `QueueHandler` no log | Teste de carga mostrar o stdout como gargalo |
| Teste de carga com Locust | Tarefa própria, junto das evidências |
| Limite global por réplica ou fila para o provedor | O volume real chegar perto do limite de tokens por minuto da conta |
| Manifestos de Kubernetes | Fora do case; o documento descreve as probes e os tempos |

## 5. Terreno: como a codebase faz hoje

- **Montagem:** `ApiFactory.create` monta `Singletons` e `StudentRoutes` (`src/api/bootstrap/app.py:21`). Os `Singletons` têm `settings`, `database`, `clock` e
  `agent` (`src/api/bootstrap/singletons.py:13`); o `dispose` fecha o banco no lifespan.
- **Chat:** `ChatRouter.build(chat_service)` (`src/api/presentation/http/chat.py:53`) recebe um provider que já depende da sessão do aluno
  (`src/api/bootstrap/chat_providers.py:24`, que usa `IdentityProviders.session_dependency`, `src/api/bootstrap/identity_providers.py:33`). O `POST /chat`
  chama `service.begin` e devolve `StreamingResponse` (`src/api/presentation/http/chat.py:64`).
- **Sessão:** `StudentSession.person_ids` é um `frozenset` com todos os `person_id` da pessoa (`src/api/domain/identity/session.py`).
- **Semáforo:** `AgentLimits.max_concurrency` (`src/api/application/agent/agent_runtime.py:17`), `gate` (`:25`, `:35`), `ProviderGate`
  (`src/api/application/agent/provider_gate.py`), ligado em `src/api/application/agent/agent_graph.py:47`; settings em `src/api/bootstrap/settings.py:18` e
  `src/api/bootstrap/agent_providers.py:30`; `.env.example:33`. Testes: `tests/unit/agent/agent_support.py:17` e `:60`,
  `tests/unit/agent/test_model_resilience.py:45`, `tests/integration/chat/test_provider_gate_release.py`. O eval usa `agent_max_concurrency` como concorrência
  padrão (`src/evals/student_driver.py:23`, lido em `src/evals/run_session.py:41`).
- **Banco:** `Database` cria o engine sem configurar o pool (`src/api/persistence/core/database.py:10`).
- **Health:** `HealthRouter` expõe `GET /health` e devolve 503 sem banco (`src/api/presentation/http/health.py:13`); `RequestLog` silencia `/health`
  (`src/api/bootstrap/request_log.py:11`); testes em `tests/integration/health/test_endpoint.py` e `tests/unit/core/test_request_log.py`.
- **Langfuse:** sem chaves, `Tracing` não cria cliente e `handler()` devolve `None` (`src/api/infrastructure/tracing.py:57` e `:70`); os `@observe` de
  `src/api/application/chat/service.py:38`, `src/api/application/protocol/confirmation.py:29` e `src/api/application/health/service.py:11` continuam ativos.
- **Front:** `API_URL` vem de `VITE_API_URL` no build, com padrão `http://127.0.0.1:8000` (`src/app/src/api.ts:4`); o Vite serve em `localhost:5173`
  (`src/app/vite.config.ts`); o CORS libera `http://localhost:5173` (`src/api/bootstrap/settings.py`).
- **Docker:** `Dockerfile` de um estágio; `.dockerignore` em lista de permitidos (`*`, `!pyproject.toml`, `!src/api`, `**/__pycache__`); `compose.yaml` com
  `pgvector/pgvector:0.8.7-pg18-trixie`, API com `--reload` e `./src/api` montado, `pgweb` no profile `tools`.
- **Camadas:** `.importlinter` já tem contratos de `sqlalchemy`, `fastapi` e `langchain`; nenhum de `redis`.
- **Testes:** a regra da casa para teste novo é fake para regra e banco só na fronteira real; o `make check` exige o Postgres de pé.

## 6. Desenho

### 6.1 Configuração e execução do examinador

- Settings novos: `redis_url: SecretStr | None`, `chat_rate_limit_per_hour: int = 60`, `db_pool_size: int`, `db_max_overflow: int`,
  `db_pool_timeout_seconds: float`. Os valores padrão do pool saem da conta de §6.6 (sugestão: 20, 10 e 5 s). `agent_max_concurrency` sai.
- `.env.example`, na ordem de quem lê: chave da OpenAI primeiro, com a instrução de preencher; segredos de exemplo com comentário de troca; `APP_DEV_LOGIN=true`;
  `APP_REDIS_URL` vazio fora do Docker (o Compose preenche); pool; Langfuse comentado como opcional.
- Comando do examinador: `cp .env.example .env`, preencher `OPENAI_API_KEY`, `docker compose up -d --wait`, abrir `http://localhost:5173`.

### 6.2 Rate limit por aluno

```text
POST /chat → JWT → StudentSession → ChatRateLimit.admit(session)
   ├─ negado  → 429, Retry-After e RateLimit-*; sem stream e sem LLM
   └─ aceito  → ChatService.begin → StreamingResponse com RateLimit-*
```

- **Domínio:** porta `RateLimiter` em `domain/ports/` (um módulo novo da área), com `consume(key) -> RateLimitDecision`. `RateLimitDecision` é um valor
  imutável: `allowed`, `limit`, `remaining`, `reset_after_seconds`. A regra da chave (menor `person_id` da sessão, prefixo `ratelimit:chat:`) mora num
  lugar só, com teste.
- **Application:** um serviço do chat que recebe a sessão e a porta e devolve a decisão. Testado com um `RateLimiter` falso.
- **Infrastructure:** `RedisRateLimiter` sobre um protocolo mínimo de cliente (o subconjunto usado: pipeline transacional com `incr`, `expire` com `nx`, `ttl`
  e `execute`), para que o cliente em memória satisfaça mypy e Pyright. Fail-open em erro de Redis ou timeout: decisão `allowed` e log de erro com o motivo.
  `UnlimitedRateLimiter` quando não há URL.
- **Cliente em memória:** implementa o mesmo protocolo, com relógio controlável, nos testes. Prova: contagem, expiração, TTL devolvido no 429, chave nova
  recebendo EXPIRE e chave existente mantendo o TTL.
- **Bootstrap:** cria o cliente Redis uma vez (`redis.asyncio`, timeouts de conexão e socket curtos), monta o limitador nos `Singletons` e fecha o cliente no
  lifespan. Sem URL, avisa no log da subida.
- **Presentation:** o `ChatRouter` recebe o provider de decisão; com `allowed` falso levanta 429 com os headers; com `allowed` verdadeiro acrescenta os
  `RateLimit-*` ao `StreamingResponse`. A contagem acontece antes de `service.begin`; um `conversation_id` inexistente gasta cota (custo aceito, porque a
  conversa é checada dentro do serviço).
- **Pontos debatidos e fechados:** chave por pessoa (E13), janela da primeira mensagem (E14), fail-open (E16), Redis opcional e cliente em memória (E17).

### 6.3 Health

- `GET /health/live`: 200 sem tocar em banco, Redis ou LLM.
- `GET /health/ready`: o comportamento do `/health` atual, com 503 sem banco. O Redis não entra, porque o limite falha aberto.
- `RequestLog` silencia os dois caminhos.

### 6.4 Imagens e Compose

- **`Dockerfile` (produção):** estágio `builder` com a imagem do uv em versão fixa copiando o binário, `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`,
  `UV_PYTHON_DOWNLOADS=0`, dependências por `uv sync --locked --no-install-project --no-dev` com cache mount e depois o projeto por `uv sync --locked --no-dev
  --no-editable`. Estágio `runtime` na mesma base: usuário e grupo 10001, só a venv copiada com dono 10001, variáveis `PYTHON*`, labels OCI por `ARG`,
  `EXPOSE 8000`, `HEALTHCHECK` com Python (`urllib`) em `/health/live`, `USER 10001:10001` e o CMD de E8.
- **`local.dockerfile`:** mesma base e uv, dependências sem dev, CMD com `--reload --reload-dir src/api` e `--app-dir src`, para o código montado vencer o
  instalado, como o Compose faz hoje.
- **`compose.yaml` (dev):** `db` em `postgres:18` com tag exata; `redis` com tag exata, sem persistência (`--save ""`, `--appendonly no`) e healthcheck
  `redis-cli ping`; `api` construída do `local.dockerfile`, com `APP_REDIS_URL` apontando para o serviço, `depends_on` com `db` e `redis` saudáveis e
  healthcheck em `/health/ready`; `web` construído de `src/app`, publicado em `127.0.0.1:5173`, `depends_on` com `api` saudável; `pgweb` segue no profile.
- **`compose.prod.yaml` (overlay):** na `api`, build do `Dockerfile`, sem volume e sem o `command` de dev (o CMD da imagem vale), `read_only: true`,
  `tmpfs: /tmp`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`.
- **Front (`src/app/Dockerfile`, `src/app/.dockerignore` e a configuração do nginx):** estágio Node com tag exata e `npm ci`, `VITE_API_URL` por `ARG` com
  padrão `http://localhost:8000`; estágio final em imagem nginx sem root, servindo `dist` com fallback para `index.html`.
- **CORS:** `APP_CORS_ORIGINS` no `.env.example` com `http://localhost:5173` e `http://127.0.0.1:5173`.

### 6.5 README e documentos

- `git mv README.md docs/diretrizes.md`, com frontmatter OKF de `type: Reference` e o link em `docs/index.md`.
- README novo, curto: badges (CI e coverage); propósito; como rodar (examinador, desenvolvimento e produção); como foi feito (stack, camadas, garantias de
  segurança por arquitetura, eval, desenvolvimento assistido por IA com gates); arquitetura em alto nível com um diagrama em texto e o link para
  `docs/architecture.md`; seção **Evidências** reservada, dizendo o que vai entrar (conversas, ataques, latência, avaliação, traces públicos do Langfuse).
- `CLAUDE.md`: a tabela de comandos reflete `uv` e o overlay de produção.

### 6.6 Análise de escala e de bloqueio

Esta seção alimenta o documento de entrega.

**Modelo de processo.** A API é stateless: a sessão nasce e morre no request, o histórico está no Postgres, a proposta de protocolo é um token assinado e o
contador do rate limit está no Redis, compartilhado entre réplicas. Um processo asyncio atende muitas requisições presas em I/O ao mesmo tempo; o turno do
agente passa quase todo o tempo esperando o provedor. Por isso, um uvicorn por container e escala por réplicas atrás de um balanceador (E8), como a doc do
FastAPI recomenda com orquestrador.

**Escala horizontal.** N réplicas iguais atrás de um load balancer; o limite por aluno continua global porque o contador está no Redis. O teto vem dos
recursos compartilhados: conexões do Postgres (`réplicas × (pool_size + max_overflow)` abaixo do `max_connections`, 100 no padrão do Postgres, ou um
PgBouncer na frente) e o limite de tokens por minuto da conta no provedor. Na rodada final do eval, um turno consumiu em média cerca de 13,5 mil tokens de
entrada (2.102.226 em 156 execuções); esse número, vezes os turnos por minuto, dá a cota de TPM necessária.

**Escala vertical.** Mais CPU ajuda pouco um processo só, que usa um núcleo; serve quando o custo de CPU por request (serialização do SSE, JSON das tools)
crescer. Num servidor único, sem orquestrador, `WEB_CONCURRENCY` sobe workers no mesmo container, cada um com o próprio pool (a conta do banco multiplica).

**Gargalos, na ordem esperada.** (1) Tokens por minuto do provedor; (2) conexões do banco; (3) CPU do event loop. O rate limit por aluno corta o pior caso
de custo; o pool configurável e a conta acima tratam o segundo.

**Varredura de operações bloqueantes no caminho do request** (2026-11-09):

| Ponto | Situação |
|---|---|
| Leitura do prompt e das skills (`read_text`) | Só na subida, por `cached_property` no runtime |
| Banco | `asyncpg` assíncrono, uma sessão curta por chamada de repositório, nunca presa durante o LLM |
| LLM | `ChatOpenAI` assíncrono, cliente único por processo |
| JWT e HMAC | CPU de microssegundos |
| Log | `StreamHandler` síncrono no stdout dentro do loop: risco baixo no volume atual; correção (`QueueHandler` e `QueueListener`) registrada em E24 |
| Langfuse | O handler do LangChain e o `@observe` exportam em thread de fundo do SDK; `flush()` síncrono só no eval (`src/evals/student_driver.py:47`). A T1 confere que nenhum handler roda bloqueando o loop |
| Redis | Cliente `redis.asyncio`, timeout curto e fail-open |

**Desligamento.** O graceful de 70 s cobre o turno de até 60 s; num orquestrador, o grace period do pod precisa ser maior que o preStop somado ao graceful.

**Proxy.** Atrás de um balanceador, `FORWARDED_ALLOW_IPS` com a rede dele faz o log e a auditoria verem o IP real; `*` só quando o proxy reescreve os
headers.

## 7. Consequências

- **Melhora:** o examinador roda com um comando; o custo por aluno tem teto; a imagem de produção é endurecida e reprodutível; o health não causa cascata;
  a cobertura aparece no README.
- **Piora ou encarece:** uma ferramenta nova (uv) e um lock grande no repo; um serviço novo (Redis) no Compose; um 429 possível para o aluno acima de 60
  mensagens por hora; o CI fica um pouco mais lento com coverage.
- **Riscos e mitigação:** Redis fora do ar deixa o custo sem trava por alguns minutos (log de erro, E16); um lock desatualizado quebra o build (`uv lock
  --check` no CI); `read_only` pode quebrar algo que escreve em disco (o oráculo da T4 sobe a produção e completa um turno).
- **Não pode mudar:** identidade só da sessão; nenhuma tool recebe identidade; isolamento sem depender do limite; Langfuse ausente não quebra nada; o
  comando `docker compose up -d --wait api` segue subindo o modo de desenvolvimento.

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos | Fronteira de teste | Pronto quando | Oráculo de verificação |
|---|---|---|---|---|---|---|
| T0 | **Fundação de configuração:** settings novos (sem remover `agent_max_concurrency`), pool no `Database` e nos `Singletons`, `.env.example` (E23 e §6.1), deps `redis` e `pytest-cov`, `uv.lock`, `Makefile` (`setup` com uv, `test` com coverage), `[tool.coverage]`, CI (setup do uv, `uv lock --check`, action de coverage), `CLAUDE.md`; no `compose.yaml`, só a troca do `db` para `postgres:18` e o serviço `redis` | — | `src/api/bootstrap/settings.py`, `src/api/bootstrap/singletons.py`, `src/api/persistence/core/database.py`, `.env.example`, `pyproject.toml`, `uv.lock`, `Makefile`, `.github/workflows/check.yml`, `CLAUDE.md`, `compose.yaml` | Unitário do pool configurado; `make check` | `make setup` com uv recria a venv; `make check` verde com coverage no terminal | `docker compose down` sem `-v` e `up -d --wait db redis`, com o volume do banco preservado; `redis-cli ping` responde |
| T1 | **Remover o semáforo:** `ProviderGate`, `max_concurrency`, `gate`, `agent_max_concurrency`, a linha do `.env.example`; padrão de concorrência próprio no eval; testes ajustados; conferir que o handler do Langfuse não bloqueia o loop | T0 | `src/api/application/agent/{provider_gate,agent_runtime,agent_graph}.py`, `src/api/bootstrap/{agent_providers,settings}.py`, `.env.example`, `src/evals/student_driver.py`, `src/evals/run_session.py`, `tests/unit/agent/*`, `tests/integration/chat/test_provider_gate_release.py` | Unitário e integração do chat | Nenhuma referência a `max_concurrency` ou `ProviderGate` em `src/` e `tests/`; `make check` verde | Com o modelo `fake`, 20 turnos simultâneos pela API terminam sem fila de 8 em 8 (tempos sobrepostos no log) |
| T2 | **Rate limit por aluno** (§6.2): porta, decisão, regra da chave, serviço, `RedisRateLimiter`, `UnlimitedRateLimiter`, cliente em memória, montagem e fechamento no bootstrap, 429 e headers no `ChatRouter`, contrato do `.importlinter` | T0 | `src/api/domain/` (porta e valor novos), `src/api/application/chat/` (serviço novo), `src/api/infrastructure/` (adaptadores novos), `src/api/bootstrap/{singletons,chat_providers,student_routes,app}.py`, `src/api/presentation/http/chat.py`, `.importlinter`, testes novos | Unitário com o cliente em memória e com fake da porta; integração HTTP do 429 com um limitador de limite 1 | `make check` verde; nenhum import de `redis` fora de infrastructure e bootstrap | Com o Compose e `APP_CHAT_RATE_LIMIT_PER_HOUR=2`: 3 mensagens seguidas dão 200, 200 e 429 com `Retry-After`; `redis-cli TTL ratelimit:chat:<id>` perto de 3600; com o `redis` parado, a mensagem passa e o log mostra o erro |
| T3 | **Health live e ready** (§6.3) | T0 | `src/api/application/health/*`, `src/api/presentation/http/health.py`, `src/api/bootstrap/request_log.py`, `tests/integration/health/*`, `tests/unit/core/test_request_log.py` | Integração HTTP | `/health` não existe; `make check` verde | `curl` em `/health/live` dá 200 com o banco parado; `/health/ready` dá 503 com o banco parado e 200 com ele de pé |
| T4 | **Imagens e Compose** (§6.4): `Dockerfile`, `local.dockerfile`, `compose.yaml` (api, web, healthchecks), `compose.prod.yaml`, `.dockerignore`, imagem e nginx do front | T0, T3 | `Dockerfile`, `local.dockerfile`, `compose.yaml`, `compose.prod.yaml`, `.dockerignore`, `src/app/Dockerfile`, `src/app/.dockerignore`, `src/app/nginx.conf` | e2e manual pelo Compose | Os dois modos sobem com `--wait` e completam um turno | Dev: `docker compose up -d --wait`, login no front em `localhost:5173`, um turno com resposta; editar um arquivo de `src/api` recarrega. Produção: o overlay sobe, `docker compose exec api id -u` dá 10001, escrita fora de `/tmp` falha, um turno completa e `docker compose stop api` durante um turno termina sem corte antes de 70 s |
| T5 | **README e documentos** (§6.5) | T0, T2, T4 | `README.md`, `docs/diretrizes.md`, `docs/index.md` | Revisão pelo dono | O dono aprovou o README | Clone limpo, `cp .env.example .env`, só a `OPENAI_API_KEY` preenchida, sem chaves do Langfuse: `docker compose up -d --wait` sobe tudo, o login e um turno funcionam e a abertura de protocolo é confirmada no front |

### Ondas e paralelismo

- **Onda 0 — fundação:** T0. Settings, `.env.example`, `pyproject.toml`, `uv.lock` e a parte do `compose.yaml` com o banco e o Redis são tocados por várias
  tarefas; ficam aqui para as seguintes não disputarem os arquivos.
- **Onda 1:** T1, T2 e T3, em paralelo. Arquivos disjuntos: T1 é o pacote do agente, o eval e `settings.py`; T2 é código novo, `singletons.py`,
  `chat_providers.py`, `student_routes.py`, `app.py`, `chat.py` e `.importlinter`; T3 é o health e o `request_log.py`.
- **Onda 2:** T4, porque o healthcheck usa o `/health/ready` da T3 e o build usa o `uv.lock` da T0.
- **Onda 3:** T5, porque o README descreve os comandos da T4 e o comportamento do limite da T2.
- **Caminho crítico:** T0 → T3 → T4 → T5.

## 9. Para o agente executor

- **Comece por:** T0.
- **Leia antes:** `CLAUDE.md`, `docs/architecture.md` (§5.1, §5.8 e §5.9), este arquivo inteiro com o Registro e a síntese da pesquisa (§Fontes).
- **Não toque:** `ruff.toml`, `.flake8`, `mypy.ini`, `pyrightconfig.json`, `quality.toml`, `tools/quality/`, `tests/lint/`, `.env`, o volume do banco
  (`docker compose down -v` só com pedido do dono), `docs/architecture.md` além de corrigir o que ficar errado, `src/evals/results/`.
- **Gates:** `make check` verde é a prova de cada tarefa; comentários proibidos no código, inclusive `noqa` e `type: ignore`; erro de lint se corrige no
  código, nunca na regra; decisão nova é confirmada com o dono, editada aqui e anotada em "Mudança no spec" antes de virar código.
- **Versões:** toda imagem e dependência nova com versão exata, conferida no registro na hora (PyPI, Docker Hub, GHCR); nada de memória.
- **Iteração:** dúvidas ao dono em lote, numeradas, com a recomendação em cada uma.

## Notas de implementação

## Fontes

[^1]: Vault do Obsidian, `docker-fastapi-producao/`: índice, notas de imagem e build e de runtime, e a síntese aplicada ao case, de 2026-11-09. Sustenta
    E7, E8, E9, E10 e E19.
[^2]: `src/evals/results/rodada-final-t14/report.md`: tokens de entrada e execuções da rodada final, base da conta de §6.6.

## Execução

### Execução de 2026-11-09

#### Registro de decisões

Repo: este, na branch `feat/entrega-e-escala`, nascida de `main`.
Escopo desta execução, na ordem: fundação de configuração; remover o semáforo, rate limit por aluno e health live e ready, em paralelo; imagens e
Compose; README e documentos.
As três tarefas do meio dependem da fundação. As imagens dependem da fundação e do health. O README depende da fundação, do rate limit e das imagens.

| Decisão | Por quê | Quem decidiu | Tipo | Se mudar, afeta | Commit |
|---|---|---|---|---|---|
| Pré-voo e preflight pulados | as decisões tinham acabado de ser fechadas em quatro rodadas, e o ambiente passou na checagem rápida | você | detalhe | nada | — |
| `Database` aceita a configuração do pool como argumento opcional, com o padrão atual quando ausente | oito pontos de teste constroem `Database(url)` direto; o pool configurável não pode obrigar a mexer neles | o dono | detalhe | a fundação | 9b188da |
| Pool padrão de 20 conexões, 10 extras e 5 s de espera, com `pool_pre_ping` | é a sugestão do desenho; a conta réplicas × pool fica no documento de escala | o dono | detalhe | um valor em settings | 9b188da |
| As mudanças do `Makefile` (setup com uv e coverage no `make test`), do CI (uv, checagem do lock e a action de coverage) e o contrato do `.importlinter` para o Redis ficam prontos no scratchpad, sem aplicar | o `.claude/settings.json` do projeto nega a edição desses três arquivos; contornar seria burlar a proteção que você mesmo pôs | você, copiando as três versões | pilar | o setup com uv, o badge de coverage e o contrato de camadas do Redis | ver o commit das três cópias |
| Os testes de rate limit e de remoção do semáforo provam o comportamento numa API local em outra porta, com o modelo falso, sem reiniciar a API do Compose | duas tarefas rodam ao mesmo tempo e a API do Compose é uma instância só | o dono | detalhe | os oráculos da onda 1 | — |
| O `/health/live` responde `{"status": "alive"}` direto na rota, sem DTO nem serviço | o desenho não define o corpo; a liveness não pode depender de nada | o dono | detalhe | a rota de health | 3ecd058 |
| O eval usa 8 como concorrência padrão, numa constante ao lado do runner | era o valor que ele herdava do semáforo; a opção `--concurrency` continua mandando | o dono | detalhe | o tempo de uma rodada do eval | dc0f72a |
| O teste de turnos simultâneos prova só o pico de 20 chamadas ao modelo ao mesmo tempo, sem medir o tempo total | o pico já prova o fim da fila de 8 em 8; a medição de tempo tinha meio segundo de folga e falharia à toa no CI | o dono | detalhe | um teste de integração do chat | dc0f72a |
| A cota do chat é consumida no handler, depois da validação do corpo, e não numa dependência | o FastAPI resolve dependências antes de validar o corpo; contar ali gastaria cota num pedido inválido (422) | o dono | detalhe | a rota do chat | 6c9b3a2 |
| Sem Redis ou no fail-open, a resposta não leva `RateLimit-*` | sem medição, os números seriam inventados | o dono | detalhe | os headers do chat | 6c9b3a2 |
| O cliente Redis não tenta de novo (`retries=0`) | o padrão do redis-py tenta 10 vezes com espera crescente e anularia o timeout de 100 ms | o dono | detalhe | o tempo de resposta com o Redis fora do ar | 6c9b3a2 |
| O CORS expõe `Retry-After` e os três `RateLimit-*` ao front | sem isso o front vê o 429, mas não consegue ler quando volta | o dono | detalhe | a configuração do CORS em `app.py` | 6c9b3a2 |
| O router recebe o limitador já preso à sessão e consome a cota no handler, em vez de receber a decisão pronta como o desenho dizia | é o mesmo efeito, sem gastar cota num pedido inválido | o dono | detalhe | a rota do chat | 6c9b3a2 |
| `APP_CHAT_RATE_LIMIT_PER_HOUR` precisa ser maior que zero | com zero, toda mensagem seria recusada sem os headers do limite | o dono | detalhe | um setting | 6c9b3a2 |
| O corpo do 429 é a frase padrão `Too Many Requests`, como o 404 do chat | o spec não define texto; o front decide a mensagem ao aluno | o dono | detalhe | a resposta do chat | 6c9b3a2 |
| O `pyproject.toml` declara os prompts e as skills do agente como dados do pacote | a imagem de produção instala o pacote sem o código-fonte, e o wheel só levava os `.py`: o turno falhava com arquivo não encontrado. O Dockerfile antigo só funcionava por acaso, lendo o fonte por `--app-dir` | o dono | detalhe | o empacotamento da API | cfb1e6f |
| O CMD de dev mora no `local.dockerfile`, e o overlay de produção dá 75 s para o container parar | sem o tempo de parada, o Docker mata o processo em 10 s e o desligamento ordenado de 70 s nunca acontece | o dono | detalhe | os dois arquivos do Compose | cfb1e6f |
| O front é servido por um nginx sem root, alpine, na 5173 fixa | imagem só de estáticos; o CORS está amarrado a essa porta | o dono | detalhe | o serviço do front | cfb1e6f |
| O handler do Langfuse fica como está | lido no código das bibliotecas: o LangChain manda handlers síncronos para o pool de threads num run assíncrono, e o Langfuse exporta numa thread de fundo; o loop não bloqueia. Sob carga alta com Langfuse ligado, o handler disputa as poucas threads do executor padrão | o dono | detalhe | a análise de escala | — |

#### Plano de review

Resumo: as seis tarefas ficaram prontas. O examinador sobe banco, Redis, API e front com `cp .env.example .env`, a chave da OpenAI e `docker compose
up -d --wait`, provado num clone limpo em 27 s. O semáforo saiu, o chat tem limite de 60 mensagens por hora por aluno em Redis, a imagem de produção é
multi-stage e endurecida, o health separa liveness e readiness, e o README novo explica o projeto. O gate completo passou: 1634 testes, lint, contratos e
tipos.

**Precisa da sua decisão**

1. Aplicar as três mudanças que as permissões do projeto bloquearam?
   O `.claude/settings.json` nega a edição do `Makefile`, do CI e do `.importlinter`. Sem elas, o `make setup` segue com pip, o CI não confere o lock nem
   publica a cobertura (o badge do README fica quebrado) e o Redis não tem contrato de camada. As três versões estão prontas e testadas no scratchpad.
   Recomendo: copiar as três. Estado atual: o código não depende delas; só o README descreve o estado final.

2. Commitar o spec desta tarefa?
   O índice dos documentos já aponta para ele, mas o arquivo está fora dos commits, como manda o processo.
   Recomendo: commitar junto das três cópias acima.

**Onde olhar**

Rate limit por aluno
- `src/api/infrastructure/rate_limiter.py`: a transação INCR, EXPIRE NX e TTL, e o fail-open em erro ou timeout do Redis.
- `src/api/presentation/http/chat.py`: a cota é consumida no handler, depois da validação do corpo, para um pedido inválido não gastar cota.
- Verificado: 429 com `Retry-After` na terceira mensagem com limite 2; TTL de cerca de 3600 no Redis; com o Redis parado, a mensagem passa e o log mostra o
  erro; revisão de código sem bloqueante.

Imagens e Compose
- `Dockerfile` e `compose.prod.yaml`: o CMD de produção, o usuário 10001 e os 75 s de parada.
- `pyproject.toml`: os prompts e as skills do agente agora são dados do pacote; sem isso, a imagem de produção falhava no primeiro turno.
- Verificado: os dois modos completam um turno; a parada durante um turno de 26 s esperou o fim e saiu com código 0.

README
- `README.md`: os comandos de produção levam `--build`, porque os dois modos usam o mesmo nome de imagem.

**Pode pular**
Settings e `.env.example`, a remoção do semáforo, o health e as fontes dos documentos que apontavam para o README antigo.

Para consulta: registro de decisões acima e checkpoints no `## Registro`; commits 9b188da (fundação), 3ecd058 (health), dc0f72a (semáforo), cfb1e6f
(imagens), 6c9b3a2 (rate limit), 43d8a16 (README).

## Registro

**Checkpoint de implementação** · 2026-11-09 · T0

- **Feito:** settings do pool, do Redis e do limite; `PoolConfig` no `Database`, montado pelos `Singletons`; `.env.example` rodável só com a chave da
  OpenAI; `redis==8.1.0` e `pytest-cov==7.1.0`; `uv.lock` com 128 pacotes; `[tool.coverage.run]`; `postgres:18.6-trixie` e `redis:8.10.3-trixie` no
  Compose; `CLAUDE.md` com os comandos do uv. Evidência: `uv sync` recriou a venv; lint, contratos, mypy e Pyright limpos; 1603 testes passaram com 98% de
  cobertura; `uv lock --check` ok; banco com 1037 matrículas antes e depois da troca de imagem; `redis-cli ping` responde.
- **Divergiu do spec:** `Makefile` e CI não aplicados, porque a edição é negada pelo `.claude/settings.json`; as versões propostas estão no scratchpad da
  sessão (`proposta/Makefile` e `proposta/.github/workflows/check.yml`).
- **Próximo:** remover o semáforo, rate limit por aluno e health live e ready, em paralelo.

**Checkpoint de implementação** · 2026-11-09 · T3

- **Feito:** `/health/live` (200 sem dependência) e `/health/ready` (503 sem banco); `/health` removido; `RequestLog` silencia os dois; healthcheck do
  Compose em `/health/ready`. Evidência: 18 testes de health, log e observabilidade verdes; lint limpo; na API do Compose, live 200, ready 200 e `/health`
  404; com o banco parado, live 200 e ready 503.
- **Divergiu do spec:** nada. O container da API aparece unhealthy até ser recriado com o healthcheck novo, o que acontece na tarefa das imagens.
- **Próximo:** imagens e Compose, assim que o rate limit fechar a onda.

**Checkpoint de implementação** · 2026-11-09 · T1

- **Feito:** saíram `ProviderGate`, `max_concurrency`, `gate`, `agent_max_concurrency` e a linha do `.env.example`; o eval tem concorrência padrão própria;
  teste novo com 20 turnos simultâneos e um modelo lento chega a 20 chamadas ao modelo ao mesmo tempo. Evidência: grep sem nenhuma referência ao
  semáforo; lint, mypy e Pyright limpos; 283 testes do agente e do teste novo verdes.
- **Divergiu do spec:** nada. O teste antigo de liberação do semáforo depois de uma desconexão foi apagado, porque o objeto que ele testava não existe mais.
- **Próximo:** fechar a onda com o rate limit.

**Checkpoint de implementação** · 2026-11-09 · T4

- **Feito:** `Dockerfile` de produção multi-stage com uv, só a venv no estágio final, UID 10001 e o CMD decidido; `local.dockerfile` com reload;
  `compose.yaml` de dev com Redis na API e o serviço `web`; overlay `compose.prod.yaml` endurecido; front em nginx sem root; prompts e skills declarados
  como dados do pacote. Evidência: os dois modos sobem saudáveis e completam um turno; front 200 com fallback de rota e CORS liberado; reload no log; em
  produção, UID 10001, escrita fora de `/tmp` negada, sem capabilities e sem header `Server`; `docker compose stop` durante um turno de 26 s esperou o
  turno terminar e saiu com código 0; labels OCI preenchidas por `--build-arg`.
- **Divergiu do spec:** o `pyproject.toml` ganhou os dados do pacote, porque o wheel não levava prompts e skills e a produção falhava (registro de
  decisões). O Compose não passa commit e data às labels; quem preenche é o CI ou um `--build-arg`.
- **Próximo:** README e documentos, depois do aceite do rate limit.

**Checkpoint de implementação** · 2026-11-09 · T2

- **Feito:** porta e decisão no domínio, chave pela pessoa da sessão, serviço do chat, `RedisRateLimiter` com INCR e EXPIRE NX numa transação e fail-open,
  `UnlimitedRateLimiter` com URL vazia, cliente em memória, 429 com `Retry-After` e `RateLimit-*`, CORS expondo esses headers, limite maior que zero.
  Evidência: 171 testes do chat, da infra e de core verdes; mutações quebram os testes certos; numa API local com limite 2, 200, 200 e 429; com o Redis
  parado, a mensagem passa e o log registra o erro; revisão de código sem bloqueante; o contrato de camada proposto passa no lint-imports.
- **Divergiu do spec:** o router recebe o limitador preso à sessão em vez da decisão pronta (registro de decisões); o contrato do `.importlinter` não foi
  aplicado, porque a edição é negada.
- **Próximo:** README e documentos.

**Checkpoint de implementação** · 2026-11-09 · T5

- **Feito:** enunciado movido para `docs/diretrizes.md` com frontmatter; README novo com badges, propósito, como rodar, arquitetura em alto nível, como
  foi feito e evidências reservadas; `docs/index.md` com os links novos; `docs/architecture.md` corrigido onde esta execução o deixou errado; fontes de
  três documentos apontando para as diretrizes. Evidência: clone limpo com `.env.example` copiado e sem Langfuse subiu os quatro serviços em 27 s, com 1037
  matrículas, login, conversa, turno em stream e headers do limite expostos, sem aviso nem erro no log; o gate completo passou com 1634 testes.
- **Divergiu do spec:** o clone rodou com o modelo falso, porque a chave da OpenAI do dono não pode ser lida; a resposta real do modelo foi provada nos dois
  modos na tarefa das imagens. A confirmação de protocolo pelo front não foi exercitada nesta execução.
- **Próximo:** as decisões do plano de review; depois, o documento de evidências.

**Checkpoint de implementação** · 2026-11-09 · T0 e T2, arquivos do dono

- **Feito:** o dono copiou o `Makefile`, o CI e o `.importlinter` propostos. Evidência: `make setup` recriou a venv pelo `uv sync`; `lint-imports` com 7
  contratos mantidos, incluindo "Apenas a infrastructure e o bootstrap importam o Redis"; `make check` literal com 1634 testes e 98% de cobertura.
- **Divergiu do spec:** nada.
- **Próximo:** o documento de evidências.
