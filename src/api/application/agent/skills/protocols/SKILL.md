---
name: protocols
description: Serviços da secretaria, taxas e prazos, protocolos abertos, documentos emitidos e abertura de pedidos. Carregue para pedidos à secretaria e seu andamento.
---

# Protocolos

- Use `list_services` para o que pode ser pedido, quanto custa e a meta de atendimento. O prazo é uma meta, não uma garantia.
- Use `list_protocols` para os pedidos do aluno e `get_protocol` quando ele informar o número. Lista vazia é uma resposta normal.
- Pedido que não aparece para o aluno é tratado como não localizado, sem revelar quem o abriu.
- Nunca cite analista, nota interna ou motivo que não esteja registrado. Se o motivo de uma negativa não consta, diga isso.

## Abrir um pedido

- Para abrir um pedido gratuito, chame `propose_protocol` com a `action` da tabela abaixo e a matrícula em `enrollment`, tirada de `list_enrollments`. Em `subject`, informe a disciplina que o aluno citou, mesmo de passagem; deixe vazio só se ele não citou nenhuma.
- Com mais de uma matrícula possível, pergunte qual é a certa antes de propor.
- Serviço com taxa não é aberto por aqui: oriente o aluno a procurar a secretaria.
- Descreva ao aluno o que será aberto, em qual curso, e a meta de atendimento.
- O card mostra o texto da ação. Nos serviços em que o aluno escreve a mensagem, ele a digita no card, e você não escreve nem sugere esse texto.
- Nas ações de alto impacto, o aluno digita no card uma palavra de confirmação. Avise que as regras e os efeitos sobre cobranças não estão nos dados.
- O pedido só existe depois que o aluno confirma no card; antes disso, nunca diga que foi aberto. Quando o histórico trouxer o evento de confirmação, o pedido está aberto, com o número e o prazo que o evento informa.

**Trancamento é sempre do curso inteiro.** O aluno pode dizer "matrícula" também para uma disciplina: "trancar minha matrícula em Direito Empresarial" fala da disciplina, não do curso. Não é possível abrir pedido para trancar uma disciplina. Nesse caso, não chame `propose_protocol`: explique isso e pergunte se ele quer trancar o curso inteiro. A mesma regra vale para cancelamento.

- Antes de perguntar o que trancar ou cancelar, consulte `list_enrollments`. Matrícula já trancada não recebe novo trancamento: diga desde quando ela está trancada e ofereça a reativação (`reativar_matricula`).
- Se ele já disse que é só uma disciplina, ou não quer o curso inteiro, diga que não existe pedido para uma disciplina, oriente-o a procurar a secretaria e ofereça abrir um pedido de informações gerais (`informacoes_gerais`), sem prometer solução.
- Se `propose_protocol` recusar com `subject_not_supported`, siga a mesma regra.
