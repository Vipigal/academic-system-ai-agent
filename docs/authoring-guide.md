---
type: Playbook
title: Guia de autoria
description: Quando e como escrever documentos OKF neste projeto, para que sejam poucos, curtos, duráveis e digam apenas o que o código não diz.
tags: [processo, documentacao, okf]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T02:53:00Z }
sources:
  - id: okf-spec
    resource: /docs/okf-spec.md
    title: Open Knowledge Format (OKF) v0.2
---

# Guia de autoria

Este projeto tem mais código do que markdown. Documento é pedra: define uma regra ou uma base de desenvolvimento e
quase nunca muda. Na dúvida, não escreva.

## Quando escrever

Um documento só existe se passar nos três testes:

1. **O código e os testes não dizem isso.** Se quem lê o código descobre, não documente.
2. **Vai continuar verdadeiro.** Se muda a cada iteração, não é documento.
3. **Sem ele, alguém erraria.** Se ninguém tomaria uma decisão errada sem o texto, ele não precisa existir.

| Vira documento | Não vira documento |
|---|---|
| O filtro de ownership vem sempre da sessão | Como a classe do adapter está organizada |
| O que conta como dívida para o aluno | O nome de um parâmetro de tool |
| O que cada sistema significa e qual é a fonte oficial de cada tema | A lista de arquivos de um módulo |

## Decisão em conversa não é verdade do projeto

Não existe pasta de decisões. Registros de decisão envelhecem rápido e transformam uma escolha do momento em regra.

- Uma escolha feita em conversa, plano, commit ou review vale só para aquela tarefa e não é precedente.
- Ela só vira documento quando o dono do projeto disser que é regra ou base do projeto.
- Se a escolha importa para quem lê o código, o próprio código deve deixá-la clara, por nomes e testes.

## Tipos

| Tipo | Uso |
|---|---|
| `Rule` | Regra que todo o código segue. |
| `Architecture` | Estrutura do sistema e seus motivos. |
| `Ontology` | Significado dos termos, das entidades e dos dados. |
| `Playbook` | Processo que agentes devem seguir. |
| `Reference`, `Research` | Material externo ou pesquisa. Serve de insumo e não decide nada. |
| `Backlog` | Lista viva do que falta fazer. Não define regra. |
| `Plan` | Plano de uma tarefa, em `docs/plans/`. Temporário: é apagado quando a tarefa termina. |

`Rule`, `Architecture` e `Ontology` são a fonte de verdade quando têm `verified` por uma pessoa. Se o que for durável em
um plano precisar sobreviver, ele vira um desses documentos, com aprovação.

## Como escrever

- **Uma ideia por documento.** Se tiver duas, são dois documentos.
- **Curto.** O ideal é caber em uma tela. `architecture.md` é a exceção.
- **Primeiro a regra, depois o motivo.** Use um exemplo só se ele evitar um erro.
- **Sem histórico.** O Git já guarda quem mudou o quê e quando.
- **Sem detalhes que mudam.** Evite caminhos, nomes de classes e passos de implementação, salvo quando forem a própria regra.
- **Número só com fonte.** Cite a origem em nota de rodapé, com o rótulo igual a um `sources[].id`.

Modelo de um documento curto:

```markdown
---
type: Rule
title: Ownership vem da sessão
description: Filtros de dono são montados a partir da sessão, nunca a partir de parâmetros.
status: stable
generated: { by: claude_code/<modelo>, at: <ISO 8601 UTC> }
---

# Ownership vem da sessão

Filtros de dono são montados a partir da sessão. Parâmetros só restringem o resultado.

**Motivo:** o agente é um cliente não confiável. Se um parâmetro pudesse definir o dono, um ataque
pela conversa poderia ler dados de outro aluno.
```

## Frontmatter

Obrigatórios: `type`, `title`, `description` e `generated`. Use `status` (`draft`, `stable` ou `deprecated`) e `sources` quando
fizerem sentido. Formato completo em [OKF](/docs/okf-spec.md).[^okf-spec]

`verified` registra a revisão humana. Um agente só o preenche por pedido explícito do dono, depois que ele revisou o conteúdo.

## Aprovação

O dono do projeto aprova todo documento novo. Antes de criar, o agente propõe na conversa:

- a ideia e por que ela passa nos três testes;
- o tipo, o título e o caminho.

Agente rodando sem supervisão não cria documento: inclui a proposta no relatório e continua. Exceções, sem proposta: `Plan`
da tarefa em andamento, marcar itens do `Backlog` e correções que não mudam o sentido, como links. Mudança de sentido em
documento existente também precisa de aprovação.

## Conflitos

Documento verificado vale mais do que conversa, plano ou documento não verificado. Se o código divergir de uma regra verificada,
o agente não escolhe sozinho: relata a divergência ao dono.

## Onde fica

- Tudo fica em `docs/`, em arquivos `kebab-case.md`, com links que começam em `/`, como `/docs/architecture.md`.
- `docs/index.md` lista os documentos, reutilizando a `description` de cada um. Documento fora do índice não existe para quem chega depois.
- Não usamos `log.md`, porque o Git cumpre esse papel.
- Todo `.md` tem frontmatter, exceto `index.md`, `README.md`, `CLAUDE.md` e arquivos em diretórios ocultos, como `.claude/`.

## Comentários no código

Código não tem comentários. Nomes e testes explicam o que ele faz, e o porquê durável fica em um documento, se passar nos três
testes. A única exceção é um comentário extremamente relevante para os examinadores analisarem o projeto.

[^okf-spec]: Open Knowledge Format (OKF) v0.2, seções 4 a 7.
