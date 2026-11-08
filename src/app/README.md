# Front de chat

Página mínima de chat do agente de atendimento (React, Vite, TypeScript e AI SDK `useChat`).

## Rodar

```
npm ci
npm run dev
```

Abre em `http://localhost:5173`. A porta é fixa (`strictPort`) porque a API só libera essa origem no CORS.

A API vem de `VITE_API_URL`, com padrão `http://127.0.0.1:8000`:

```
VITE_API_URL=http://127.0.0.1:8000 npm run dev
```

Suba a API antes, na raiz do repo: `docker compose up -d --wait api`.

## Scripts

| Comando | O que faz |
|---|---|
| `npm run dev` | Servidor de desenvolvimento |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run build` | Typecheck e build de produção em `dist/` |

## Fluxo

O login é uma tela de teste: escolhe a unidade (marca) e a modalidade, depois o aluno, e chama `POST /auth/dev-login` com
`marca:RA`, guardando o token só na memória da página. A lista de alunos ainda vem de uma amostra fixa
(`src/devStudentsSample.ts`), no formato da rota dev-only `GET /auth/dev-students` que vai substituí-la. Em produção essa tela
não existe: o aluno chega pelo login institucional. Cada conversa nasce em
`POST /conversations`, e o `id` vai ao `useChat`, que fala com `POST /chat`. A proposta de protocolo aparece como card, e o
botão "Confirmar" chama `POST /protocols/proposals/confirm`.
