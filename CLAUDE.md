# Agente de atendimento ao aluno

API em FastAPI que dá ao agente acesso seguro e normalizado aos quatro sistemas do grupo. Comece por
[docs/index.md](/docs/index.md); a [Arquitetura](/docs/architecture.md) é a referência das decisões.

## Comandos

| Comando | O que faz |
|---|---|
| `make setup` | `uv sync` com o grupo dev: cria `.venv` com Python 3.14 e instala as versões travadas no `uv.lock` |
| `uv lock` | Regera o `uv.lock` depois de mudar dependências no `pyproject.toml`; o CI barra lock desatualizado com `uv lock --check` |
| `docker compose up -d --wait api` | Sobe a API em `127.0.0.1:8000`, com o banco |
| `make check` | Formatação, lint, contratos de camada, tipos (mypy e Pyright) e testes com coverage no terminal. Exige o banco de pé |
| `make check-fast` | O mesmo, sem as varreduras marcadas `sweep` e `slow` e sem `tests/lint`, para o loop de desenvolvimento |
| `make fix` | Aplica correções automáticas e formata |

Uma tarefa só termina com `make check` verde; a saída dele é a prova. Recarregar os dados
(`docker compose down -v && docker compose up -d --wait`) apaga o volume: só com pedido do dono.

## Regras que o linter garante

- **Camadas:** bootstrap → presentation → application → domain; persistence → domain; infrastructure → domain. Application, persistence e infrastructure não se importam: falam por ports do domínio. Só `src/api/bootstrap/`, o composition root, conhece todas e monta o grafo por request.
- **Agente:** LangChain só em `src/api/application/agent/` e no bootstrap. A presentation só tem rotas HTTP.
- **Domínio:** só biblioteca padrão, sem rede nem ambiente. Dependência externa entra por `domain/ports/`, com um módulo por área.
- **Banco:** só a persistence importa SQLAlchemy, e só o `RepositoryAdapter` e a carga da sessão abrem sessão de banco.
- **Tamanho e complexidade:** os limites estão em `ruff.toml`, `.flake8` e `quality.toml`.
- **Comentários:** proibidos, inclusive `noqa` e `type: ignore`. A exceção é `# examiner: <nota>`, só para algo
  extremamente relevante aos examinadores. Docstring só nas tools do agente, em `src/api/application/agent/tools`,
  onde o modelo a lê como descrição da tool.

## Ao receber um erro do linter

Corrija o código: extraia funções, renomeie, separe responsabilidades. Nunca enfraqueça a regra. Os arquivos
`ruff.toml`, `.flake8`, `.importlinter`, `mypy.ini`, `pyrightconfig.json`, `quality.toml`, `Makefile`, `tools/quality/` e `tests/lint/` são do dono do projeto; se uma regra
parecer errada para o caso, relate com o exemplo e espere a decisão.
