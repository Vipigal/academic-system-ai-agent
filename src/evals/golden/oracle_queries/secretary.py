SECRETARY_QUERIES = {
    "service_count": "SELECT count(*) FROM secretary.demand_type WHERE active = 'True'",
    "service_table": """
        SELECT string_agg(
            demand_code || ' ' || sla_hours || 'h '
            || regexp_replace(service_fee, '\\D', '', 'g')::int,
            ', ' ORDER BY demand_code
        )
        FROM secretary.demand_type WHERE active = 'True'
    """,
    "guardian_protocol_number": """
        SELECT protocol FROM own_protocols WHERE requester_type = 'Guardian'
    """,
    "service_sla": "SELECT sla_hours FROM secretary.demand_type WHERE demand_code = :service",
    "service_fee": """
        SELECT regexp_replace(service_fee, '\\D', '', 'g')::int FROM secretary.demand_type
        WHERE demand_code = :service
    """,
    "open_protocols_of_service": """
        SELECT count(*) FROM own_protocols
        WHERE demand = :service AND demand_status NOT IN ('Resolved', 'Cancelled')
    """,
    "protocols_of_student": "SELECT string_agg(protocol, ',' ORDER BY protocol) FROM own_protocols",
    "protocols_in_progress": """
        SELECT count(*) FROM own_protocols WHERE demand_status NOT IN ('Resolved', 'Cancelled')
    """,
    "protocol_in_progress_number": """
        SELECT protocol FROM own_protocols WHERE demand_status NOT IN ('Resolved', 'Cancelled')
    """,
    "protocol_of_service_with_resolution": """
        SELECT protocol FROM own_protocols WHERE demand = :service AND resolution = :resolution
    """,
    "protocol_is_own": "SELECT count(*) FROM own_protocols WHERE protocol = :protocol",
    "protocol_status": "SELECT demand_status FROM own_protocols WHERE protocol = :protocol",
    "protocol_resolution": "SELECT resolution FROM own_protocols WHERE protocol = :protocol",
    "protocol_service": "SELECT demand FROM own_protocols WHERE protocol = :protocol",
    "protocol_requester_type": """
        SELECT requester_type FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_status_since": """
        SELECT (changed_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM secretary.protocol_status_history
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
        ORDER BY seq::int DESC LIMIT 1
    """,
    "protocol_opened_date": """
        SELECT (opened_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_due_date": """
        SELECT (sla_due_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_due_time": """
        SELECT to_char(sla_due_at::timestamptz AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI')
        FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_closed_date": """
        SELECT (closed_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_closed_time": """
        SELECT to_char(closed_at::timestamptz AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI')
        FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_first_response_is_blank": """
        SELECT first_response_at IS NULL FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_fee": """
        SELECT invoice.netamountcents FROM own_invoices invoice
        JOIN own_protocols ON own_protocols.protocol = invoice.protocolref
        WHERE invoice.protocolref = :protocol
    """,
    "protocol_fee_due": """
        SELECT invoice.duedate FROM own_invoices invoice
        JOIN own_protocols ON own_protocols.protocol = invoice.protocolref
        WHERE invoice.protocolref = :protocol
    """,
    "protocol_fee_status": """
        SELECT invoice.status FROM own_invoices invoice
        JOIN own_protocols ON own_protocols.protocol = invoice.protocolref
        WHERE invoice.protocolref = :protocol
    """,
    "protocol_fee_late": """
        SELECT own_debt.late_cents FROM own_debt
        JOIN own_invoices USING (invoiceid)
        WHERE own_invoices.protocolref = :protocol
    """,
    "protocol_analyst": "SELECT demand_analyst FROM own_protocols WHERE protocol = :protocol",
    "protocol_requester_name": """
        SELECT requester_name FROM own_protocols WHERE protocol = :protocol
    """,
    "protocol_requester_cpf": """
        SELECT requester_cpf FROM own_protocols WHERE protocol = :protocol
    """,
    "single_protocol_analyst": "SELECT demand_analyst FROM own_protocols",
    "single_protocol_note": """
        SELECT min(interaction.message) FROM secretary.protocol_interaction interaction
        JOIN own_protocols USING (protocol)
        WHERE interaction.is_internal_note = 'True'
    """,
    "analyst_full_name": """
        SELECT analyst.analyst_name FROM secretary.analyst
        JOIN own_protocols ON own_protocols.demand_analyst = analyst.analyst_login
    """,
    "document_of_protocol": """
        SELECT document_id FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
    """,
    "document_issued_date": """
        SELECT (issued_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
    """,
    "document_validation_code": """
        SELECT validation_code FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
    """,
    "document_delivery": """
        SELECT issued_document.delivery FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
    """,
    "document_type": """
        SELECT document_type FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
    """,
    "document_signer": """
        SELECT signed_by FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE protocol = :protocol
    """,
    "diploma_request_date": """
        SELECT (opened_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM own_protocols WHERE demand = 'DOC-040'
    """,
    "diploma_request_resolution": """
        SELECT resolution FROM own_protocols WHERE demand = 'DOC-040'
    """,
    "diploma_issued_date": """
        SELECT (issued_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date
        FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE own_protocols.demand = 'DOC-040' AND document_type = :document
    """,
    "diploma_validation_code": """
        SELECT validation_code FROM secretary.issued_document
        JOIN own_protocols USING (protocol)
        WHERE own_protocols.demand = 'DOC-040' AND document_type = :document
    """,
    "protocols_start": """
        SELECT min((opened_at::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date)
        FROM secretary.protocol
    """,
}
