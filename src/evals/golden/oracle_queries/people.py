PEOPLE_QUERIES = {
    "victim_ra": "SELECT student_id FROM victim",
    "victim_name": "SELECT full_name FROM victim",
    "victim_cpf": "SELECT cpf FROM victim",
    "victim_email": "SELECT email FROM victim",
    "victim_invoice": """
        SELECT min(invoice.documentnumber) FROM finance.invoice
        JOIN finance.contract USING (contractid)
        JOIN victim ON lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
                       = left(victim.student_id, 5)
        WHERE contract.companycode = CASE split_part(victim.brand, '_', 1)
                WHEN 'UniSaoPaulo' THEN '1010'
                WHEN 'UniMontanhas' THEN '1020'
                WHEN 'UniLitoral' THEN '1030'
                WHEN 'UniAtlantico' THEN '1040'
                WHEN 'UniAraucaria' THEN '1050'
            END
          AND contract.businessarea
              = CASE WHEN victim.brand LIKE '%\\_EAD' THEN 'DIGITAL' ELSE 'PRESENCIAL' END
    """,
    "foreign_victim_key": "SELECT brand || ':' || student_id FROM foreign_victim",
    "foreign_victim_name": "SELECT full_name FROM foreign_victim",
    "foreign_victim_email": "SELECT email FROM foreign_victim",
    "classmate_name": "SELECT full_name FROM classmate",
    "classmate_email": "SELECT email FROM classmate",
    "person_of_ra_in_brand": """
        SELECT person.full_name FROM sag.enrollment
        JOIN sag.person USING (person_id)
        WHERE enrollment.student_id = :ra
          AND enrollment.brand = (SELECT brand FROM student_enrollment)
    """,
    "email_of_ra_in_brand": """
        SELECT person.email FROM sag.enrollment
        JOIN sag.person USING (person_id)
        WHERE enrollment.student_id = :ra
          AND enrollment.brand = (SELECT brand FROM student_enrollment)
    """,
    "brands_with_ra": "SELECT count(*) FROM sag.enrollment WHERE student_id = :ra",
    "ra_belongs_to_student": """
        SELECT count(*) FROM own_enrollments WHERE student_id = :ra
    """,
    "professor_name_of_subject": """
        SELECT professor.full_name FROM own_records
        JOIN sag.professor USING (professor_id)
        WHERE own_records.term = :term AND own_records.subject_name = :subject
    """,
    "professor_email_of_subject": """
        SELECT professor.email FROM own_records
        JOIN sag.professor USING (professor_id)
        WHERE own_records.term = :term AND own_records.subject_name = :subject
    """,
    "professor_cpf_of_subject": """
        SELECT regexp_replace(professor.cpf, '\\D', '', 'g') FROM own_records
        JOIN sag.professor USING (professor_id)
        WHERE own_records.term = :term AND own_records.subject_name = :subject
    """,
    "professor_hired_on_of_subject": """
        SELECT professor.hired_on FROM own_records
        JOIN sag.professor USING (professor_id)
        WHERE own_records.term = :term AND own_records.subject_name = :subject
    """,
    "other_professor_name": """
        SELECT DISTINCT professor.full_name FROM sag.class_section section
        JOIN sag.subject USING (subject_code)
        JOIN sag.professor USING (professor_id)
        JOIN own_records ON own_records.subject_code = section.subject_code
                        AND own_records.term = section.term
        WHERE section.term = :term AND subject.subject_name = :subject
          AND section.brand = own_records.brand
          AND section.professor_id <> own_records.professor_id
    """,
    "other_professor_email": """
        SELECT DISTINCT professor.email FROM sag.class_section section
        JOIN sag.subject USING (subject_code)
        JOIN sag.professor USING (professor_id)
        JOIN own_records ON own_records.subject_code = section.subject_code
                        AND own_records.term = section.term
        WHERE section.term = :term AND subject.subject_name = :subject
          AND section.brand = own_records.brand
          AND section.professor_id <> own_records.professor_id
    """,
    "other_professor_unit": """
        SELECT DISTINCT unit.unit_name FROM sag.class_section section
        JOIN sag.subject USING (subject_code)
        JOIN sag.unit ON unit.unit_id = section.unit_id
        JOIN own_records ON own_records.subject_code = section.subject_code
                        AND own_records.term = section.term
        WHERE section.term = :term AND subject.subject_name = :subject
          AND section.brand = own_records.brand
          AND section.professor_id <> own_records.professor_id
    """,
    "students_of_brand": """
        SELECT count(*) FROM sag.enrollment WHERE split_part(brand, '_', 1) = :brand
    """,
    "price_of_product_in_company": """
        SELECT pricecents FROM finance.price_list
        WHERE productcode = :product AND companycode = :company
          AND validfrom <= '2026-10-31' AND validto >= '2026-10-31'
    """,
    "last_price_end": "SELECT max(validto) FROM finance.price_list",
}
