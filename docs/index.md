# Documentos do projeto

## Base

- [Arquitetura do agente de atendimento ao aluno](/docs/architecture.md): Decisões, desenho e restrições da API que dá ao agente acesso seguro e normalizado aos quatro sistemas do grupo educacional.
- [Ontologia do atendimento ao aluno](/docs/ontology.md): Os conceitos do agente, com definição, sistema oficial, origem, evidência e relações.

## Processo

- [Guia de autoria](/docs/authoring-guide.md): Quando e como escrever documentos OKF neste projeto, para que sejam poucos, curtos, duráveis e digam apenas o que o código não diz.
- [Pendências](/docs/pendencias.md): O que falta definir e preparar para começar a implementação, para marcar ao longo das sessões.
- [Ontologia e topologia de tools](/docs/plans/ontologia-e-tools.md): Spec da tarefa que cria a classe Ontology, as 19 tools do agente, o envelope de resposta com paginação e a correção do cálculo de dívida.
- [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md): Spec-mãe da fase que reorganiza as camadas com o bootstrap, cria o agente LangChain com skills, o histórico, a confirmação de protocolo, o chat com stream, o eval de modelos e as evidências do case.
- [Entrega e escala](/docs/plans/entrega-e-escala.md): Spec da tarefa que deixa o projeto rodável pelo examinador com um comando, troca o semáforo por rate limit por aluno em Redis, separa as imagens de desenvolvimento e produção e registra a análise de escala.

- [Insumos da entrega](/docs/insumos-da-entrega.md): Fatos marcantes do desenvolvimento, com número e fonte, para escrever o documento final e montar a apresentação do case.
- [Guia do eval](/docs/guia-do-eval.md): Como interpretar os resultados do eval do agente, onde achar cada resposta, gate e veredito, o mapa do código e a ordem para revisar.

## Referência

- [Diretrizes do case](/docs/diretrizes.md): O enunciado do case como recebido, com o desafio, os requisitos, os critérios de avaliação, os entregáveis e as tabelas dos quatro sistemas.
- [Open Knowledge Format (OKF) v0.2](/docs/okf-spec.md): The documentation format this repository is written in — frontmatter, provenance and trust fields, lifecycle status, link resolution, the actor convention, and the shape of index and log files.
- [Ontologia e evidências no NVIDIA Auto Ontology](/docs/research-auto-ontology.md): Como o Auto Ontology modela termos e devolve a procedência das respostas, e quais ideias podem servir de referência para o agente de atendimento.
- [Análise exploratória dos dados](/docs/eda.md): Como os dados recebidos estão dispostos, como os sistemas se relacionam e quais inconsistências existem, sem recomendações de solução.
- [Catálogo de perguntas do aluno](/docs/question-catalog.md): As perguntas que um aluno faria ao agente, por área do enunciado, com a intenção, os dados, a armadilha e a resposta ideal de cada uma.
