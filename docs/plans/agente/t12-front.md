---
type: Plan
title: T12 · Front de chat
description: Tarefa da fase do agente que cria a página de chat em React com AI SDK useChat, escolha de aluno simulada e o card de confirmação de protocolo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T12 · Front de chat

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 4, depende de T11. Modelo sugerido: Sonnet.

## Objetivo

A página mínima de chat que o enunciado e B26 pedem, sem gastar tempo com UI (D8).

## O que fazer

1. `src/app/`: React com Vite e TypeScript, `ai` e `@ai-sdk/react` em versões exatas. Componentes prontos do assistant-ui
   são opcionais; se derem atrito, `useChat` com poucos componentes próprios.
2. Escolha do aluno: campo `marca:RA` e alguns alunos do golden set como atalho; chama `dev-login` e guarda o token na memória
   da página.
3. Chat com `useChat` e `DefaultChatTransport` apontando para `/chat`, com o Bearer no header e o `id` devolvido por
   `POST /conversations` (D25).
4. Parte `tool-propose_protocol` renderizada como card: serviço, matrícula, mensagem e o botão "Confirmar", que chama a rota
   de confirmação com o token de `client_only` (D26). Mostra o número do protocolo ou o erro.
5. Estados: carregando, erro da API, conversa vazia.
6. Instruções de rodar no `README` de `src/app/`, com `npm` e a URL da API.

## Pronto quando

O fluxo roda no navegador contra a API do Compose.

## Oráculo

Pelo Chrome DevTools MCP: escolher `UniAraucaria_EAD:013161`, perguntar FI-01 e ver o stream; pedir um protocolo, ver o card,
confirmar e ver o número; derrubar a API e ver o estado de erro; largura de celular sem rolagem lateral.

## Identidade visual e login por unidade

Desenho aprovado pelo dono em 2026-11-06, depois da exploração do site e do login do aluno (SSO) da instituição pelo Chrome
DevTools MCP. A página segue a identidade visual dela, mas sem logo, sem nome do grupo e sem marca registrada: o projeto fica
público como agente acadêmico do dono.

### Decisões

| # | Decisão | Por quê |
|---|---|---|
| V1 | Só a identidade visual: paleta, fonte e forma dos botões. Sem logo, sem o nome do grupo; a marca é um ícone neutro com "Atendimento ao aluno" e o subtítulo "Agente acadêmico". | O repositório é público e é projeto do dono; a referência à instituição não pode ficar explícita. |
| V2 | Fundo azul em gradiente em toda a tela, com login e chat num card branco central. | Pedido do dono; é o arranjo do header do site e do login do aluno. |
| V3 | Login em dois passos: unidade (marca) e modalidade, depois o aluno, com busca por nome ou RA. Um clique no aluno faz o `dev-login`. | Substitui o campo `marca:RA` e os atalhos; ninguém precisa conhecer RA para testar. |
| V4 | Aviso abaixo do card nas duas telas de login: tela de teste para desenvolvimento, sem senha; em produção ela não existe e o aluno chega pelo login institucional (SSO). | O avaliador precisa ler que o login sem senha é deliberado e restrito ao desenvolvimento. |
| V5 | Conversa vazia com saudação pelo primeiro nome e quatro sugestões clicáveis, uma por área do enunciado (README §1): notas e frequência, mensalidades em aberto, andamento dos protocolos e provas no ambiente virtual. | Mostra o que o agente sabe fazer e acelera a demonstração. Trancamento de disciplina saiu: não há serviço de protocolo para ele. |
| V6 | O card de protocolo não ganha botão "Agora não" nesta tarefa. | Decisão do dono. |
| V7 | Uma rota `GET /auth/dev-students`, montada só com `dev_login` ligado, devolve todos os alunos de uma vez; o front agrupa. | Cerca de 1.040 matrículas (uns 60 KB); duas rotas custam mais sem ganho nesse volume. |
| V8 | Resposta do assistente em markdown, com `react-markdown` e `remark-gfm` em versão exata. | Listas e tabelas do modelo ficam legíveis; a lib monta elementos React, sem HTML injetado. |
| V9 | Cada tool vira um item expansível: o título traz um rótulo em português por tool (`toolLabels.ts`), e o painel aberto mostra o nome técnico, o input e o output em JSON. | O avaliador vê o que foi chamado e o que voltou ao modelo. |
| V10 | O painel omite `client_only` do output e diz que omitiu. | O modelo não recebe esse campo (`src/api/application/shared/tool_result.py:90`); mostrar seria falsear o que ele viu. |
| V11 | Avatar do assistente com ícone de robô. | Pedido do dono. |

### Tokens

Medidos nos estilos computados do site e do login do aluno.

| Token | Valor | Uso |
|---|---|---|
| Azul do fundo | `#003B71`, gradiente de `#0B4279` a `#022C55` | Fundo da página |
| Azul de título | `#03386D` | Títulos e texto sobre o dourado |
| Azul de ação | `#0B4279` | Botão principal, bolha do aluno, avatar |
| Azul de borda | `#2A65A1` | Borda do botão secundário |
| Dourado | `#FBAE17`, com texto `#03386D` | Botão "Enviar", selo "Ambiente de teste", borda da proposta |
| Superfície suave | `#EEF3F7` | Bolha do assistente, hover da lista |
| Fonte | Work Sans 400, 500, 600 e 700 | Toda a página, pelo Google Fonts no `index.html` |
| Raio | 999px nos botões e campos; 16px nos cards; 12px no card de protocolo e na lista | |

### Contrato da rota

`GET /auth/dev-students` → `200` com `[{brand, student_id, full_name, status}]`, uma linha por matrícula (`sag.enrollment` com
`sag.person`), ordenada por `full_name`. `status` é o `enrollment_status` do banco (`ACTIVE`, `LOCKED`, `DROPOUT`…). Sem token: a
rota só existe com `APP_DEV_LOGIN` ligado, pelo mesmo `AuthRouter` que o `dev-login` usa (`src/api/bootstrap/identity_providers.py:31`).
A leitura entra por um método novo no port `PersonDirectory` (`src/api/domain/ports/identity.py:10`), implementado no
`StudentSessionRepository`.

O front separa a modalidade pelo sufixo `_EAD` da marca (`UniSaoPaulo` e `UniSaoPaulo_EAD` viram a linha "UniSaoPaulo", com as
pílulas Presencial e EAD) e mostra a contagem de cada uma.

### Ordem

1. Front: tokens, telas de login e chat, e a lista de alunos vinda de uma amostra fixa em `api.ts`, com o mesmo formato da rota.
2. Depois do aviso do baseline da T10 commitado: a rota na API, com teste, e a troca da amostra pela chamada.

Até o baseline, nenhum protocolo é confirmado no navegador, e `UniSaoPaulo:181722` (item TR-01) não é usado.

### Oráculo

Pelo Chrome DevTools MCP, em 1440 px e 390 px sem rolagem lateral: escolher UniMontanhas Presencial, buscar e entrar com
`UniMontanhas:070114`; ver a saudação com as sugestões; clicar numa sugestão e ver o stream; derrubar a API e ver o erro na lista
de alunos e no chat; sair e voltar ao passo da unidade.
