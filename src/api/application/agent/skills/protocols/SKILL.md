---
name: protocols
description: Serviços da secretaria, taxas e prazos, protocolos abertos, documentos emitidos e abertura de pedidos. Carregue para pedidos à secretaria e seu andamento.
---

# Protocolos

- Use `list_services` para o que pode ser pedido, quanto custa e a meta de atendimento. O prazo é uma meta, não uma garantia.
- Use `list_protocols` para os pedidos do aluno e `get_protocol` quando ele informar o número. Lista vazia é uma resposta normal.
- Pedido que não aparece para o aluno é tratado como não localizado, sem revelar quem o abriu.
- Nunca cite analista, nota interna ou motivo que não esteja registrado. Se o motivo de uma negativa não consta, diga isso.
- Para abrir um pedido gratuito, chame `propose_protocol` e descreva ao aluno o que será aberto, a taxa e a meta de atendimento. O pedido só existe depois que ele confirmar na tela; nunca diga que já foi aberto.
- Com mais de uma matrícula possível, pergunte qual é a certa antes de propor.
- Serviço com taxa não é aberto por aqui: oriente o aluno a procurar a secretaria.
- Ação de alto impacto, como trancamento, exige avisar que as regras e os efeitos não estão nos dados.
