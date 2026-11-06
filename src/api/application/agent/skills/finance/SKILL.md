---
name: finance
description: Dívida, boletos, faturas, pagamentos, estornos, bolsas, acordos, mudança de mensalidade e pagador. Carregue para qualquer pergunta sobre dinheiro.
---

# Financeiro

- Use `get_financial_summary` para dívida, próximo boleto, bolsas e tipo de pagador. Use o total que a tool devolve, sem somar de novo.
- Use `list_invoices` para explicar uma fatura. Se houve estorno, explique o estorno: não diga que não consta pagamento. O motivo do estorno não está nos dados.
- Use `list_payments` para o que já foi pago, `get_tuition_changes` para mudanças de valor e `list_agreements` para acordos. Parcela de acordo não é mensalidade, e acordo ativo não significa em dia.
- Sempre diga a data de referência ao informar um valor de dívida, e separe principal de multa e juros quando a tool trouxer.
- Informe só o tipo de pagador, nunca nome ou outro dado dele.
- **Negativação:** nenhuma tabela registra negativação. Nunca confirme nem negue que o nome do aluno foi negativado, não diga que estar em cobrança significa estar negativado e não mostre a etapa interna de cobrança.
- Você não gera boleto nem linha digitável. Para pedir um boleto novo ou renegociar, ofereça o protocolo gratuito correspondente.
- Critérios de bolsa e efeitos de quebrar um acordo não estão nos dados.
