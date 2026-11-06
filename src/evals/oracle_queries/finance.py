FINANCE_QUERIES = {
    "debt_total": "SELECT sum(principal_cents + late_cents) FROM own_debt",
    "debt_principal": "SELECT sum(principal_cents) FROM own_debt",
    "debt_late": "SELECT sum(late_cents) FROM own_debt",
    "debt_invoices": "SELECT count(*) FROM own_debt",
    "debt_balance_of_competence": """
        SELECT principal_cents FROM own_debt WHERE competence = :competence
    """,
    "debt_total_of_invoice": """
        SELECT principal_cents + late_cents FROM own_debt WHERE invoiceid = :invoice
    """,
    "debt_due_of_kind": "SELECT duedate FROM own_debt WHERE invoicetype = :kind",
    "debt_principal_of_kind": "SELECT principal_cents FROM own_debt WHERE invoicetype = :kind",
    "debt_total_of_kind": """
        SELECT principal_cents + late_cents FROM own_debt WHERE invoicetype = :kind
    """,
    "debt_max_days": """
        SELECT max(charge.dayslate::int) FROM finance.late_charge charge
        JOIN own_debt USING (invoiceid)
        WHERE charge.referencedate = '2026-10-31'
    """,
    "debt_matches_snapshot": """
        SELECT (SELECT coalesce(sum(principal_cents + late_cents), 0) FROM own_debt)
               = coalesce(sum(snapshot.totaldebtcents::int), 0)
        FROM finance.receivable_snapshot snapshot
        WHERE snapshot.snapshotdate = '2026-10-31'
          AND snapshot.contractid IN (SELECT contractid FROM own_contracts)
    """,
    "collection_stage": """
        SELECT snapshot.collectionstage FROM finance.receivable_snapshot snapshot
        JOIN own_contracts USING (contractid)
        WHERE snapshot.snapshotdate = '2026-10-31'
    """,
    "contract_status": "SELECT status FROM own_contracts",
    "latest_contract_status": """
        SELECT status FROM own_contracts ORDER BY signedat DESC LIMIT 1
    """,
    "invoices_of_discount_contract": """
        SELECT count(invoice.invoiceid) FROM own_contracts
        JOIN finance.discount USING (contractid)
        LEFT JOIN finance.invoice USING (contractid)
        WHERE discount.discounttype = :type
    """,
    "active_discount_count": """
        SELECT count(*) FROM finance.discount
        JOIN own_contracts USING (contractid)
        WHERE discount.validfrom <= '2026-10-31'
          AND (discount.validto IS NULL OR discount.validto >= '2026-10-31')
    """,
    "next_invoice_due": """
        SELECT min(duedate) FROM own_invoices
        WHERE status IN ('OPEN', 'PARTIAL') AND duedate > '2026-10-31'
    """,
    "next_invoice_amount": """
        SELECT netamountcents FROM own_invoices
        WHERE status IN ('OPEN', 'PARTIAL') AND duedate > '2026-10-31'
        ORDER BY duedate LIMIT 1
    """,
    "next_invoice_kind": """
        SELECT invoicetype FROM own_invoices
        WHERE status IN ('OPEN', 'PARTIAL') AND duedate > '2026-10-31'
        ORDER BY duedate LIMIT 1
    """,
    "open_invoice_due": """
        SELECT min(duedate) FROM own_invoices
        WHERE status = 'OPEN' AND invoicetype = :kind AND duedate > '2026-10-31'
    """,
    "open_invoice_amount": """
        SELECT netamountcents FROM own_invoices
        WHERE status = 'OPEN' AND invoicetype = :kind AND duedate > '2026-10-31'
        ORDER BY duedate LIMIT 1
    """,
    "open_tuition_invoices": """
        SELECT count(*) FROM own_invoices WHERE status = 'OPEN' AND invoicetype = 'TUITION'
    """,
    "invoice_status": "SELECT status FROM own_invoices WHERE invoiceid = :invoice",
    "invoice_competence": "SELECT competence FROM own_invoices WHERE invoiceid = :invoice",
    "invoice_payment_amount": """
        SELECT payment.amountcents FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.invoiceid = :invoice AND payment.status = :status
    """,
    "invoice_payment_method": """
        SELECT payment.method FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.invoiceid = :invoice AND payment.status = :status
    """,
    "invoice_payment_date": """
        SELECT ((payment.paidat::timestamptz) AT TIME ZONE 'America/Sao_Paulo')::date
        FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.invoiceid = :invoice AND payment.status = :status
    """,
    "invoice_of_protocol": "SELECT invoiceid FROM own_invoices WHERE protocolref = :protocol",
    "payments_count_of_year": """
        SELECT count(*) FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.status = 'CONFIRMED'
          AND to_char(payment.paidat::timestamptz AT TIME ZONE 'America/Sao_Paulo', 'YYYY') = :year
    """,
    "payments_total_of_year": """
        SELECT sum(payment.amountcents::int) FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.status = 'CONFIRMED'
          AND to_char(payment.paidat::timestamptz AT TIME ZONE 'America/Sao_Paulo', 'YYYY') = :year
    """,
    "payments_late_of_year": """
        SELECT sum(payment.finecents::int + payment.interestcents::int) FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.status = 'CONFIRMED'
          AND to_char(payment.paidat::timestamptz AT TIME ZONE 'America/Sao_Paulo', 'YYYY') = :year
    """,
    "payments_reversed_of_year": """
        SELECT sum(payment.amountcents::int) FROM finance.payment
        JOIN own_invoices USING (invoiceid)
        WHERE payment.status = 'REVERSED'
          AND to_char(payment.paidat::timestamptz AT TIME ZONE 'America/Sao_Paulo', 'YYYY') = :year
    """,
    "payer_type": """
        SELECT CASE
            WHEN customer.taxid = (SELECT cpf FROM own_cpf) THEN 'self'
            WHEN customer.customertype = 'COMPANY' THEN 'company'
            ELSE 'other_person'
        END
        FROM own_contracts JOIN finance.customer USING (customerid)
    """,
    "payer_name": "SELECT name FROM own_contracts JOIN finance.customer USING (customerid)",
    "payer_tax_id": "SELECT taxid FROM own_contracts JOIN finance.customer USING (customerid)",
    "payer_email": "SELECT email FROM own_contracts JOIN finance.customer USING (customerid)",
    "payer_phone": "SELECT phone FROM own_contracts JOIN finance.customer USING (customerid)",
    "co_paid_student": """
        SELECT min(other.studentname) FROM finance.contract other
        WHERE other.customerid = (SELECT customerid FROM own_contracts)
          AND other.contractid NOT IN (SELECT contractid FROM own_contracts)
    """,
    "discount_rate": """
        SELECT round(discount.rate::numeric * 100, 2)::float8 FROM finance.discount
        JOIN own_contracts USING (contractid)
        WHERE discount.discounttype = :type
    """,
    "discount_start": """
        SELECT discount.validfrom FROM finance.discount
        JOIN own_contracts USING (contractid)
        WHERE discount.discounttype = :type
    """,
    "discount_end": """
        SELECT coalesce(discount.validto, 'none') FROM finance.discount
        JOIN own_contracts USING (contractid)
        WHERE discount.discounttype = :type
    """,
    "tuition_gross_of_competence": """
        SELECT grossamountcents FROM own_invoices
        WHERE invoicetype = 'TUITION' AND competence = :competence
    """,
    "tuition_net_of_competence": """
        SELECT netamountcents FROM own_invoices
        WHERE invoicetype = 'TUITION' AND competence = :competence
    """,
    "last_tuition_due": """
        SELECT max(duedate) FROM own_invoices WHERE invoicetype = 'TUITION'
    """,
    "last_tuition_status": """
        SELECT status FROM own_invoices WHERE invoicetype = 'TUITION'
        ORDER BY duedate DESC LIMIT 1
    """,
    "active_agreement": """
        SELECT agreement.agreementid FROM finance.agreement
        JOIN own_contracts USING (contractid)
        WHERE agreement.status = 'ACTIVE'
    """,
    "agreement_status": """
        SELECT agreement.status FROM finance.agreement
        JOIN own_contracts USING (contractid)
        WHERE agreementid = :agreement
    """,
    "agreement_installments": """
        SELECT installments FROM finance.agreement
        JOIN own_contracts USING (contractid)
        WHERE agreementid = :agreement
    """,
    "agreement_agreed": """
        SELECT agreedamountcents FROM finance.agreement
        JOIN own_contracts USING (contractid)
        WHERE agreementid = :agreement
    """,
    "agreement_waived": """
        SELECT waivedcents FROM finance.agreement
        JOIN own_contracts USING (contractid)
        WHERE agreementid = :agreement
    """,
    "agreement_paid_installments": """
        SELECT count(*) FROM own_invoices
        WHERE agreementid = :agreement AND invoicetype = 'AGREEMENT_INSTALLMENT'
          AND status = 'PAID'
    """,
    "agreement_overdue_installments": """
        SELECT count(*) FROM own_debt
        JOIN own_invoices USING (invoiceid)
        WHERE own_invoices.agreementid = :agreement
    """,
    "agreement_remaining_installments": """
        SELECT count(*) FROM own_invoices
        WHERE agreementid = :agreement AND invoicetype = 'AGREEMENT_INSTALLMENT'
          AND status <> 'PAID'
    """,
    "agreement_remaining_amount": """
        SELECT sum(netamountcents::int) FROM own_invoices
        WHERE agreementid = :agreement AND invoicetype = 'AGREEMENT_INSTALLMENT'
          AND status <> 'PAID'
    """,
    "agreement_remaining_due": """
        SELECT duedate FROM own_invoices
        WHERE agreementid = :agreement AND invoicetype = 'AGREEMENT_INSTALLMENT'
          AND status <> 'PAID'
        ORDER BY duedate OFFSET :position::text::int LIMIT 1
    """,
    "agreement_remaining_installment": """
        SELECT netamountcents FROM own_invoices
        WHERE agreementid = :agreement AND invoicetype = 'AGREEMENT_INSTALLMENT'
          AND status <> 'PAID'
        ORDER BY duedate OFFSET :position::text::int LIMIT 1
    """,
}
