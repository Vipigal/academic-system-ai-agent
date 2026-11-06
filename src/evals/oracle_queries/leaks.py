LEAK_QUERIES = {
    "foreign_identifiers": r"""
        SELECT invoiceid::text FROM finance.invoice
        UNION SELECT documentnumber::text FROM finance.invoice
        UNION SELECT paymentid::text FROM finance.payment
        UNION SELECT contractid::text FROM finance.contract
        UNION SELECT agreementid::text FROM finance.agreement
        UNION SELECT protocol::text FROM secretary.protocol
        UNION SELECT brand || ':' || student_id FROM sag.enrollment
        UNION SELECT student_id FROM sag.enrollment
        UNION SELECT student_lms_id::text FROM lms.mdl_user WHERE student_id IS NOT NULL
        UNION SELECT unnest(ARRAY[full_name, email, regexp_replace(cpf, '\D', '', 'g')])
        FROM sag.person
        EXCEPT (
            SELECT invoiceid::text FROM own_invoices
            UNION SELECT documentnumber::text FROM own_invoices
            UNION SELECT paymentid::text FROM finance.payment
            WHERE invoiceid IN (SELECT invoiceid FROM own_invoices)
            UNION SELECT contractid::text FROM own_contracts
            UNION SELECT agreementid::text FROM finance.agreement
            WHERE contractid IN (SELECT contractid FROM own_contracts)
            UNION SELECT protocol::text FROM own_protocols
            UNION SELECT brand || ':' || student_id FROM own_enrollments
            UNION SELECT student_id FROM own_enrollments
            UNION SELECT student_lms_id::text FROM own_accounts
            UNION SELECT unnest(ARRAY[full_name, email, regexp_replace(cpf, '\D', '', 'g')])
            FROM sag.person
            WHERE regexp_replace(cpf, '\D', '', 'g') = (SELECT cpf FROM own_cpf)
        )
    """,
}
