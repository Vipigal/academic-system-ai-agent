# Agente de atendimento ao aluno

[![check](https://github.com/Vipigal/academic-system-ai-agent/actions/workflows/check.yml/badge.svg)](https://github.com/Vipigal/academic-system-ai-agent/actions/workflows/check.yml)
[![Coverage badge](https://raw.githubusercontent.com/Vipigal/academic-system-ai-agent/python-coverage-comment-action-data/badge.svg)](https://github.com/Vipigal/academic-system-ai-agent/tree/python-coverage-comment-action-data)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Checked with Pyright](https://img.shields.io/badge/types-Pyright-blue)](https://github.com/microsoft/pyright)

[![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1.4.9-1C3C3C?logo=langchain&logoColor=white)](https://python.langchain.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.1.8-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

## Propósito

Um agente de IA que atende alunos de um grupo educacional com 5 marcas, consultando quatro sistemas independentes: acadêmico
(SAG), ambiente virtual (LMS), secretaria e financeiro. Ele responde sobre curso, notas, frequência, mensalidades, protocolos e
provas, e abre protocolos com a confirmação do aluno. A garantia central é de arquitetura, não de prompt: a identidade vem só
da sessão, e nenhuma consulta alcança dados de outro aluno ou dados corporativos, seja qual for o texto da conversa. O
enunciado está em [Diretrizes do case](/docs/diretrizes.md).

## Como rodar

Requisito: Docker com Compose v2.24.0 ou mais novo (o `env_file` opcional do `compose.yaml` exige essa versão).

**Para avaliar**

```bash
cp .env.example .env          # preencha só a OPENAI_API_KEY
docker compose up -d --wait
```

Abra http://localhost:5173 e escolha um aluno no login simulado (sem senha). Sobem:

| Serviço | Endereço | Papel |
|---|---|---|
| `db` | `127.0.0.1:5432` | Postgres 18; na primeira subida, carrega os CSVs dos quatro sistemas e cria a role restrita da API |
| `redis` | `127.0.0.1:6379` | Contador do rate limit, sem persistência |
| `api` | `127.0.0.1:8000` | FastAPI; `/health/live` e `/health/ready` |
| `web` | `127.0.0.1:5173` | Front em React servido por nginx |

Langfuse é opcional: para ver os traces, descomente e preencha as chaves `LANGFUSE_*` no `.env`. Sem elas, nada muda.

**Modo produção**

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d --wait --build
```

O overlay troca a imagem de desenvolvimento (`local.dockerfile`, com reload e o código montado) pela de produção
(`Dockerfile` multi-stage com uv, usuário 10001, só a venv no estágio final) e roda a API com sistema de arquivos só de
leitura, `/tmp` em memória, sem capabilities e com `no-new-privileges`. Os dois modos usam o mesmo nome de imagem, por isso o
`--build` ao trocar de um para o outro; para voltar ao desenvolvimento, `docker compose up -d --wait --build`.

**Desenvolvimento** (exige o [uv](https://docs.astral.sh/uv/))

| Comando | O que faz |
|---|---|
| `make setup` | `uv sync` com o grupo dev: cria `.venv` com Python 3.14 e as versões travadas no `uv.lock` |
| `docker compose up -d --wait db` | Sobe só o banco, que os testes exigem |
| `make check` | Formatação, lint, contratos de camada, tipos (mypy e Pyright) e testes com coverage |
| `make check-fast` | O mesmo, sem as varreduras longas, para o loop de desenvolvimento |

## Arquitetura em alto nível

```text
Aluno ── navegador ──► web (React, nginx) ──► api (FastAPI)
                                                │
   JWT ──► sessão do aluno, carregada do banco a cada request
                                                │
   rate limit por aluno ◄──────────────────────►│◄────► Redis (contador de 1 hora)
                                                │
   agente LangChain, tools sem parâmetro de identidade ◄────► OpenAI
                                                │
   services da application (composição entre sistemas)
                                                │
   adapter de repositório: AND de ownership em toda consulta
                                                │
   Postgres, role `api` com menor privilégio: sag · lms · secretary · finance · agent

   traces do turno, das tools e do modelo ─────────────────► Langfuse (opcional)
```

O código fica em seis camadas: `bootstrap` (composition root, monta o grafo por request), `presentation` (só rotas HTTP),
`application` (services, o agente e as tools), `domain` (regras e ports, só biblioteca padrão), `persistence` (o único lugar
que importa SQLAlchemy) e `infrastructure` (JWT, relógio, Langfuse, log e Redis). As dependências apontam para o domínio, e o
import-linter quebra o build se uma camada importar o que não pode. As decisões e os trade-offs estão na
[Arquitetura](/docs/architecture.md).

## Como foi feito

**Stack.** Python 3.14, FastAPI, SQLAlchemy assíncrono com asyncpg, LangChain com modelo da OpenAI, Postgres, Redis,
Langfuse e uv. Front em React com Vite.

**Segurança por arquitetura, não por prompt.**

- A identidade vem só da sessão, montada a partir do JWT; o texto da conversa nunca define quem é o aluno.
- Nenhuma tool recebe identidade como parâmetro: cada uma é uma closure sobre services que já carregam a sessão.
- O adapter de repositório acrescenta o `AND` de ownership em toda consulta, e um teste chama todas as tools com todos os
  argumentos para provar que nenhuma linha de outro aluno volta.
- A API conecta ao banco com uma role de menor privilégio: lê só as tabelas mapeadas e escreve só nas de protocolo e de
  conversa.
- O agente não escreve sozinho: ele propõe a abertura de protocolo num token assinado, e a escrita só acontece quando o aluno
  confirma no front, numa rota fora do LLM.

**Escala.** A API é stateless: a sessão nasce e morre no request, o histórico está no Postgres e a proposta de protocolo é um
token assinado. Um processo uvicorn por container, escalando por réplicas. O custo é contido por um rate limit por aluno em
Redis (60 mensagens do chat por hora por padrão, `APP_CHAT_RATE_LIMIT_PER_HOUR`), que responde 429 com `Retry-After` e
deixa passar se o Redis estiver fora do ar. O pool do banco é configurável (`APP_DB_POOL_SIZE`, `APP_DB_MAX_OVERFLOW`,
`APP_DB_POOL_TIMEOUT_SECONDS`). A análise de escala completa vai no documento de entrega.

**Eval.** Um conjunto de perguntas de referência, de red team e de abertura de protocolo, com os fatos da referência
conferidos por SQL independente das tools; os itens críticos precisam acertar em todas as repetições (pass^k), e um juiz
LLM, calibrado com respostas corretas e adulteradas, avalia cada critério da rubrica. Como ler os resultados está no
[Guia do eval](/docs/guia-do-eval.md).

**Desenvolvimento assistido por IA, com gates.** O código foi escrito com um agente de código a partir de specs em
[`docs/plans`](/docs/plans). Nenhuma tarefa fecha sem `make check` verde: ruff, flake8 com limites de tamanho e
complexidade, contratos de camada no import-linter, mypy em modo estrito, Pyright e a suíte de testes. O CI roda o mesmo gate,
confere o `uv.lock` e publica a cobertura.

## Evidências

Em preparação. Esta seção vai trazer:

- exemplos de conversa;
- tentativas de ataque e o resultado de cada uma;
- medição de latência;
- avaliação da qualidade das respostas;
- traces públicos do Langfuse.

## Documentos

- [Índice dos documentos](/docs/index.md)
- [Arquitetura](/docs/architecture.md)
- [Diretrizes do case](/docs/diretrizes.md)
- [Guia do eval](/docs/guia-do-eval.md)
