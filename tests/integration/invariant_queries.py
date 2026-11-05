SAMPLE_PEOPLE = r"""
    WITH people AS (
        SELECT min(person.person_id) OVER (PARTITION BY regexp_replace(person.cpf, '\D', '', 'g'))
                   AS person_id,
               enrollment.brand,
               enrollment.student_id
        FROM sag.person JOIN sag.enrollment ON enrollment.person_id = person.person_id
    ),
    records AS (
        SELECT people.person_id, people.brand, count(*) AS total
        FROM people
        JOIN sag.student_class
          ON student_class.brand = people.brand AND student_class.student_id = people.student_id
        GROUP BY people.person_id, people.brand
    ),
    per_brand AS (
        SELECT DISTINCT ON (split_part(brand, '_', 1)) person_id FROM records
        ORDER BY split_part(brand, '_', 1), person_id
    ),
    per_modality AS (
        SELECT DISTINCT ON (brand LIKE '%\_EAD') person_id FROM records
        ORDER BY brand LIKE '%\_EAD', person_id
    ),
    many AS (
        SELECT person_id FROM people GROUP BY person_id HAVING count(*) > 1
        ORDER BY person_id LIMIT 1
    ),
    guardian AS (
        SELECT people.person_id FROM secretary.protocol
        JOIN secretary.unit ON unit.unit_code = protocol.unit_code
        JOIN people
          ON people.brand = replace(translate(unit.brand_name, 'ãáâ', 'aaa'), ' ', '')
             || CASE unit.unit_type WHEN 'Polo EAD' THEN '_EAD' ELSE '' END
         AND people.student_id = lpad(protocol.stu_id, 6, '0')
        WHERE protocol.requester_type = 'Guardian'
        ORDER BY people.person_id LIMIT 1
    )
    SELECT person_id FROM per_brand
    UNION SELECT person_id FROM per_modality
    UNION SELECT person_id FROM many
    UNION SELECT person_id FROM guardian
"""
GUARDIAN_PROTOCOLS = "SELECT protocol FROM secretary.protocol WHERE requester_type = 'Guardian'"
OWN_INVOICES = (
    "SELECT invoiceid FROM finance.invoice WHERE contractid = ANY(string_to_array(:contracts, ','))"
)
OWN_CONFIRMED_PAYMENTS = (
    "SELECT paymentid FROM finance.payment JOIN finance.invoice USING (invoiceid) "
    "WHERE contractid = ANY(string_to_array(:contracts, ',')) AND payment.status = 'CONFIRMED'"
)
OWN_RECORDS = (
    "SELECT brand || ':' || student_id || '/' || class_id FROM sag.student_class "
    "WHERE brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))"
)
OWN_SUBJECTS = """
    SELECT class_section.subject_code FROM sag.student_class
    JOIN sag.class_section ON class_section.class_id = student_class.class_id
    WHERE student_class.brand || ':' || student_class.student_id
          = ANY(string_to_array(:enrollments, ','))
    UNION
    SELECT curriculum_subject.subject_code FROM sag.curriculum_subject
    WHERE curriculum_subject.curriculum_id IN (
        SELECT curriculum_id FROM sag.enrollment
        WHERE brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))
        UNION
        SELECT curriculum_id FROM sag.student_class
        WHERE brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))
    )
"""
FOREIGN_IDENTIFIERS = """
    SELECT invoiceid FROM finance.invoice
    WHERE NOT contractid = ANY(string_to_array(:contracts, ','))
    UNION SELECT paymentid FROM finance.payment JOIN finance.invoice USING (invoiceid)
    WHERE NOT contractid = ANY(string_to_array(:contracts, ','))
    UNION SELECT contractid FROM finance.contract
    WHERE NOT contractid = ANY(string_to_array(:contracts, ','))
    UNION SELECT agreementid FROM finance.agreement
    WHERE NOT contractid = ANY(string_to_array(:contracts, ','))
    UNION SELECT protocol FROM secretary.protocol
    WHERE NOT protocol = ANY(string_to_array(:protocols, ','))
    UNION SELECT brand || ':' || student_id FROM sag.enrollment
    WHERE NOT brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))
    UNION SELECT student_lms_id FROM lms.mdl_user
    WHERE student_id IS NOT NULL AND NOT student_lms_id = ANY(string_to_array(:accounts, ','))
"""
FOREIGN_ENROLLMENTS = """
    SELECT DISTINCT ON (brand = ANY(string_to_array(:brands, ',')))
           brand || ':' || student_id
    FROM sag.enrollment
    WHERE NOT brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))
    ORDER BY brand = ANY(string_to_array(:brands, ',')), student_id
"""
FOREIGN_PROTOCOLS = """
    SELECT DISTINCT ON (requester_type) protocol FROM secretary.protocol
    WHERE NOT protocol = ANY(string_to_array(:protocols, ','))
    ORDER BY requester_type, protocol DESC
"""
FOREIGN_SUBJECTS = """
    SELECT DISTINCT ON (student_class.brand = ANY(string_to_array(:brands, ',')))
           class_section.subject_code
    FROM sag.student_class
    JOIN sag.class_section ON class_section.class_id = student_class.class_id
    WHERE class_section.subject_code NOT IN (
        SELECT class_section.subject_code FROM sag.student_class
        JOIN sag.class_section ON class_section.class_id = student_class.class_id
        WHERE student_class.brand || ':' || student_class.student_id
              = ANY(string_to_array(:enrollments, ','))
        UNION
        SELECT curriculum_subject.subject_code FROM sag.curriculum_subject
        WHERE curriculum_subject.curriculum_id IN (
            SELECT curriculum_id FROM sag.enrollment
            WHERE brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))
            UNION
            SELECT curriculum_id FROM sag.student_class
            WHERE brand || ':' || student_id = ANY(string_to_array(:enrollments, ','))
        )
    )
    ORDER BY student_class.brand = ANY(string_to_array(:brands, ',')), class_section.subject_code
"""
FOREIGN_UNITS = """
    SELECT DISTINCT ON (brand) unit_name FROM sag.unit
    WHERE brand IN (SELECT DISTINCT brand FROM sag.unit ORDER BY brand LIMIT 2)
    ORDER BY brand, unit_id
"""
CPFS = r"""
    SELECT cpf FROM sag.person
    UNION SELECT regexp_replace(cpf, '\D', '', 'g') FROM sag.person
    UNION SELECT lpad(requester_cpf, 11, '0') FROM secretary.protocol WHERE requester_cpf <> ''
    UNION SELECT taxid FROM finance.customer
    UNION SELECT cpf FROM sag.professor
    UNION SELECT regexp_replace(cpf, '\D', '', 'g') FROM sag.professor
"""
FORBIDDEN_VALUES = """
    SELECT name FROM finance.customer
    UNION SELECT email FROM finance.customer
    UNION SELECT phone FROM finance.customer
    UNION SELECT requester_name FROM secretary.protocol
    UNION SELECT demand_analyst FROM secretary.protocol WHERE demand_analyst <> ''
    UNION SELECT author FROM secretary.protocol_interaction WHERE author_type = 'Analyst'
    UNION SELECT changed_by FROM secretary.protocol_status_history WHERE changed_by <> 'system'
    UNION SELECT collectionstage FROM finance.receivable_snapshot
    UNION SELECT agingbucket FROM finance.receivable_snapshot
"""
INTERNAL_NOTES = (
    "SELECT DISTINCT message FROM secretary.protocol_interaction WHERE is_internal_note = 'True'"
)
