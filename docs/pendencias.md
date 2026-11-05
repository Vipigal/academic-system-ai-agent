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

- [ ] Revisar e verificar o [Guia de autoria](/docs/authoring-guide.md).
- [x] Criar o `CLAUDE.md`: comandos, regras essenciais e ponto de entrada em `docs/index.md`.
- [x] Preencher o `.gitignore`, que está vazio: no mínimo `.env`, ambiente virtual e caches.
- [x] Transformar o briefing em [análise exploratória](/docs/eda.md), sem recomendações.
- [ ] Decidir se os comentários de `db/init/01_load.sh` e `compose.yaml` ficam, segundo a regra de comentários.
- [x] Definir como o agente prova que terminou uma tarefa: comandos de teste e reset do banco.

## Definições do agente

Nesta ordem, porque cada uma depende da anterior:

- [x] **Catálogo de perguntas:** 40 a 60 perguntas por área do enunciado, incluindo as que cruzam sistemas, sem resposta e recusadas, com intenção, dados e armadilha.
- [ ] **Ontologia:** dicionário de dados e glossário de termos, decidindo onde cada um fica. Referência: [pesquisa do Auto Ontology](/docs/research-auto-ontology.md).
- [ ] **Topologia de tools:** uma tool por intenção, com filtros tipados e sem SQL livre, validada contra o catálogo.
- [ ] **Contrato de resposta:** envelope comum para distinguir vazio, zero e não registrado, indicar truncamento e período coberto, tratar erros e devolver evidências.

## Stack e ferramentas

- [ ] Framework do agente e modelos, considerando o provedor da chave de LLM do avaliador.
- [ ] Formato das skills e como são carregadas.
- [x] Base do projeto: gerenciador de pacotes, versão do Python, lint, tipos, testes e teste de importação entre camadas.
- [ ] Produção: log estruturado, JWT e ferramenta de teste de carga.
- [ ] Eval: ferramenta e formato do golden set, com gabarito em SQL independente.
- [ ] Tecnologia da página mínima de chat, necessária para a aprovação com um clique.
- [ ] RAG: medir se a busca do catálogo precisa de vetores ou se sinônimos bastam.

## Dúvida externa

- [ ] Confirmar com o recrutador se existe base de regulamentos fora do zip. Sem essa base, o agente diz que não tem a informação, como o enunciado pede.

## Implementação

- [ ] Dividir o trabalho em planos por ondas e definir quais rodam de forma autônoma.
- [ ] `02_constraints.sql`: PKs e FKs, com `NOT VALID` nas 5 FKs violadas.
- [ ] `03_indexes.sql`: índices derivados das consultas reais.
- [ ] `04_agent_schema.sql`: conversas, logs, auditoria, rascunhos e sequências.
- [ ] `05_roles.sql`: role restrita da API.
