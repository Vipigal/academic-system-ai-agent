---
type: Backlog
title: Pendências
description: O que falta definir e preparar para começar a implementação, para marcar ao longo das sessões.
tags: [backlog, planejamento]
status: stable
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T02:53:00Z }
---

# Pendências

Lista viva. Marcar um item não cria regra; o que for durável vira documento, conforme o
[Guia de autoria](/docs/authoring-guide.md). Decisões já tomadas estão em [Arquitetura](/docs/architecture.md).

## Preparo para os agentes

- [x] Revisar e verificar o [Guia de autoria](/docs/authoring-guide.md).
- [x] Criar o `CLAUDE.md`: comandos, regras essenciais e ponto de entrada em `docs/index.md`.
- [x] Preencher o `.gitignore`, que está vazio: no mínimo `.env`, ambiente virtual e caches.
- [x] Transformar o briefing em [análise exploratória](/docs/eda.md), sem recomendações.
- [ ] Decidir se os comentários de `db/init/01_load.sh` e `compose.yaml` ficam, segundo a regra de comentários.
- [x] Definir como o agente prova que terminou uma tarefa: comandos de teste e reset do banco.

## Definições do agente

Nesta ordem, porque cada uma depende da anterior:

- [x] **Catálogo de perguntas:** 40 a 60 perguntas por área do enunciado, incluindo as que cruzam sistemas, sem resposta e recusadas, com intenção, dados e armadilha.
- [x] **Ontologia:** dicionário de dados e glossário de termos, decidindo onde cada um fica. Referência: [pesquisa do Auto Ontology](/docs/research-auto-ontology.md).
- [x] **Topologia de tools:** uma tool por intenção, com filtros tipados e sem SQL livre, validada contra o catálogo.
- [x] **Contrato de resposta:** envelope comum para distinguir vazio, zero e não registrado, paginar com total e próximo offset, indicar período coberto, tratar erros e devolver evidências.

## Stack e ferramentas

- [x] Modelos, considerando o provedor da chave de LLM do avaliador. O framework do agente é o LangChain; versão e API são conferidas no spec do agente.
- [x] Formato das skills e como são carregadas.
- [x] Base do projeto: gerenciador de pacotes, versão do Python, lint, tipos, testes e teste de importação entre camadas.
- [ ] Produção: log estruturado, JWT e ferramenta de teste de carga.
- [x] Eval: ferramenta e formato do golden set, com gabarito em SQL independente.
- [x] Tecnologia da página mínima de chat, necessária para a aprovação com um clique.
- [x] RAG: decidido não usar. A base não tem texto de conhecimento para indexar.

## Dúvida externa

- [x] Decidido não perguntar ao recrutador sobre base de regulamentos. O agente diz que não tem a informação, como o enunciado pede.

## Implementação

- [x] Dividir o trabalho em planos por ondas e definir quais rodam de forma autônoma.
- [x] `02_constraints.sql`: PKs e FKs, com `NOT VALID` nas 5 FKs violadas.
- [x] `03_indexes.sql`: índices derivados das consultas reais.
- [x] `04_agent_schema.sql`: conversas, mensagens, chamadas de tool e sequências.
- [x] `05_roles.sh`: role restrita da API.

## Reta final

Nesta ordem. O bug e as decisões estão em [T14 · Protocolo robusto](/docs/plans/agente/t14-protocolo-robusto.md), e o caso do eval em
[T10 · Runner de eval](/docs/plans/agente/t10-runner-eval.md).

**Eval e baseline:**

- [ ] Limpar o banco com `docker compose down -v`, para remover o protocolo `20260025164` do teste no front.
- [ ] Terminar o runner: revisar o que foi escrito, runner, CLI, juiz, relatório e testes dos graders.
- [ ] Acrescentar os itens `TR`, `SV` e `ES`, o `ProposalGrader` e a regra de itens críticos.
- [ ] Rodar e salvar o baseline com o bug aparecendo, antes de qualquer correção.

**Correção do protocolo:**

- [ ] Catálogo de ações no domínio, com efeito e limite de cada serviço, e falha fechada.
- [ ] `propose_protocol(action, enrollment, subject)`, sem `message`, com as recusas de disciplina e de situação da matrícula.
- [ ] Nome em português e efeito nos DTOs de serviço; nome em português dos 8 cursos.
- [ ] Skill e ontologias explicando que trancamento é do curso inteiro e a confusão com "matrícula em disciplina", sem oferecê-la como opção.
- [ ] Prompt `v2`, com a regra de escopo: receita de bolo e código Python são recusados.
- [ ] Confirmação com a mensagem escrita pelo aluno e a palavra digitada, exigidas pelo servidor.
- [ ] Evento de confirmação no histórico, com o papel novo `system_event`.
- [ ] Card novo no front, e tirar `181722` dos atalhos de login.
- [ ] Verificar o card no navegador, com o Chromium do WSL.

**Relógio:**

- [ ] Produção com a data de hoje, sem variável no `.env`; testes e eval injetam 31/10/2026.
- [ ] Corrigir A16 em `docs/architecture.md` e declarar nas evidências o efeito da foto dos dados com a data real.

**Fechamento:**

- [ ] Rodada final em banco limpo e comparação com o baseline.
- [ ] Evidências e `README` (T13), com o case do protocolo.

**Em sessão separada ou como atenção:**

- [ ] Bugs visuais do front e verificação em 390 px. O dono passa a lista.
- [ ] Ponto de atenção: muitos testes "unitários" sobem banco e varrem os dados, o que os deixa lentos e não escalaria num projeto real. Não reescrever agora; declarar nas evidências, e teste novo usa fake para regra.
