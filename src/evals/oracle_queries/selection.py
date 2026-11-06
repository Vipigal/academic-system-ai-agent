SELECTION_QUERIES = {
    "choose_student_free_of_service": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment JOIN sag.person USING (person_id)
        WHERE enrollment.brand = :brand AND enrollment.enrollment_status = :status
          AND regexp_replace(person.cpf, '\\D', '', 'g') IN (
              SELECT regexp_replace(single.cpf, '\\D', '', 'g')
              FROM sag.enrollment JOIN sag.person single USING (person_id)
              GROUP BY 1 HAVING count(*) = 1
          )
          AND regexp_replace(person.cpf, '\\D', '', 'g') NOT IN (
              SELECT lpad(requester_cpf, 11, '0') FROM secretary.protocol
              WHERE demand = :service AND requester_cpf IS NOT NULL
          )
          AND enrollment.student_id NOT IN (
              SELECT lpad(stu_id, 6, '0') FROM secretary.protocol
              WHERE demand = :service AND stu_id IS NOT NULL
          )
    """,
    "choose_indebted_student_free_of_service": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment JOIN sag.person USING (person_id)
        WHERE enrollment.brand = 'UniLitoral' AND enrollment.enrollment_status = 'ACTIVE'
          AND regexp_replace(person.cpf, '\\D', '', 'g') IN (
              SELECT regexp_replace(single.cpf, '\\D', '', 'g')
              FROM sag.enrollment JOIN sag.person single USING (person_id)
              GROUP BY 1 HAVING count(*) = 1
          )
          AND regexp_replace(person.cpf, '\\D', '', 'g') NOT IN (
              SELECT lpad(requester_cpf, 11, '0') FROM secretary.protocol
              WHERE demand = :service AND requester_cpf IS NOT NULL
          )
          AND enrollment.student_id NOT IN (
              SELECT lpad(stu_id, 6, '0') FROM secretary.protocol
              WHERE demand = :service AND stu_id IS NOT NULL
          )
          AND left(enrollment.student_id, 5) IN (
              SELECT lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
              FROM finance.contract JOIN finance.invoice USING (contractid)
              WHERE contract.companycode = '1030' AND contract.businessarea = 'PRESENCIAL'
                AND invoice.status = 'OVERDUE'
          )
    """,
    "choose_graduated_student_with_cancelled_service": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment JOIN sag.person USING (person_id)
        JOIN secretary.protocol
          ON lpad(protocol.requester_cpf, 11, '0') = regexp_replace(person.cpf, '\\D', '', 'g')
         AND lpad(protocol.stu_id, 6, '0') = enrollment.student_id
        WHERE enrollment.enrollment_status = 'GRADUATED' AND protocol.demand = :service
          AND protocol.demand_status = 'Cancelled'
          AND regexp_replace(person.cpf, '\\D', '', 'g') IN (
              SELECT regexp_replace(single.cpf, '\\D', '', 'g')
              FROM sag.enrollment JOIN sag.person single USING (person_id)
              GROUP BY 1 HAVING count(*) = 1
          )
    """,
    "choose_student_with_active_and_graduated_enrollments": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment JOIN sag.person USING (person_id)
        WHERE enrollment.enrollment_status = 'ACTIVE'
          AND regexp_replace(person.cpf, '\\D', '', 'g') IN (
              SELECT regexp_replace(graduated.cpf, '\\D', '', 'g')
              FROM sag.enrollment JOIN sag.person graduated USING (person_id)
              WHERE enrollment.enrollment_status = 'GRADUATED'
          )
    """,
    "choose_active_student": """
        SELECT brand || ':' || student_id FROM sag.enrollment
        WHERE enrollment_status = 'ACTIVE' AND brand = 'UniSaoPaulo'
        ORDER BY student_id LIMIT 1
    """,
    "choose_online_student_with_av2": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment
        JOIN sag.student_class USING (brand, student_id)
        JOIN sag.class_section USING (class_id)
        WHERE enrollment.enrollment_status = 'ACTIVE' AND enrollment.brand LIKE '%\\_EAD'
          AND class_section.term = '2026/2' AND student_class.result = 'IN_PROGRESS'
          AND EXISTS (
              SELECT 1 FROM lms.mdl_user account
              WHERE upper(trim(account.student_id)) = 'EAD_' || left(enrollment.student_id, 5)
          )
    """,
    "choose_campus_paulista_student": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment JOIN sag.unit USING (unit_id)
        WHERE enrollment.brand = 'UniSaoPaulo' AND enrollment.enrollment_status = 'ACTIVE'
          AND unit.unit_name = 'CAMPUS PAULISTA'
    """,
    "choose_active_student_with_active_scholarship": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment
        JOIN finance.contract
          ON contract.companycode = '1010' AND contract.businessarea = 'PRESENCIAL'
         AND lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
             = left(enrollment.student_id, 5)
        JOIN finance.discount USING (contractid)
        WHERE enrollment.brand = 'UniSaoPaulo' AND enrollment.enrollment_status = 'ACTIVE'
          AND discount.discounttype = 'MERIT' AND discount.validfrom <= '2026-10-31'
          AND (discount.validto IS NULL OR discount.validto >= '2026-10-31')
    """,
    "choose_active_student_before_lms": """
        SELECT min(brand || ':' || student_id) FROM sag.enrollment
        WHERE enrollment_status = 'ACTIVE' AND date_of_enrollment < '2023-01-15'
    """,
    "choose_student_of_other_brand_without_ra": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment
        WHERE enrollment.enrollment_status = 'ACTIVE' AND enrollment.student_id <> :ra
          AND enrollment.brand IN (
              SELECT other.brand FROM sag.enrollment other WHERE other.student_id = :ra
          )
    """,
    "choose_company_paid_student_with_colleague": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM sag.enrollment
        JOIN finance.contract
          ON contract.companycode = CASE split_part(enrollment.brand, '_', 1)
                 WHEN 'UniSaoPaulo' THEN '1010'
                 WHEN 'UniMontanhas' THEN '1020'
                 WHEN 'UniLitoral' THEN '1030'
                 WHEN 'UniAtlantico' THEN '1040'
                 WHEN 'UniAraucaria' THEN '1050'
             END
         AND contract.businessarea
             = CASE WHEN enrollment.brand LIKE '%\\_EAD' THEN 'DIGITAL' ELSE 'PRESENCIAL' END
         AND lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
             = left(enrollment.student_id, 5)
        JOIN finance.customer USING (customerid)
        WHERE customer.customertype = 'COMPANY'
          AND (SELECT count(*) FROM finance.contract other
               WHERE other.customerid = contract.customerid) > 1
          AND (SELECT count(*) FROM sag.enrollment same
               JOIN sag.person same_person USING (person_id)
               JOIN sag.person this_person ON this_person.person_id = enrollment.person_id
               WHERE regexp_replace(same_person.cpf, '\\D', '', 'g')
                     = regexp_replace(this_person.cpf, '\\D', '', 'g')) = 1
    """,
    "choose_student_with_single_noted_protocol": """
        SELECT min(enrollment.brand || ':' || enrollment.student_id)
        FROM secretary.protocol
        JOIN secretary.unit USING (unit_code)
        JOIN sag.enrollment
          ON enrollment.brand = replace(translate(unit.brand_name, 'ãáâ', 'aaa'), ' ', '')
             || CASE unit.unit_type WHEN 'Polo EAD' THEN '_EAD' ELSE '' END
         AND enrollment.student_id = lpad(protocol.stu_id, 6, '0')
        JOIN sag.person USING (person_id)
        WHERE protocol.requester_type = 'Student' AND protocol.demand_analyst <> ''
          AND lpad(protocol.requester_cpf, 11, '0') = regexp_replace(person.cpf, '\\D', '', 'g')
          AND EXISTS (
              SELECT 1 FROM secretary.protocol_interaction note
              WHERE note.protocol = protocol.protocol AND note.is_internal_note = 'True'
          )
          AND (SELECT count(*) FROM secretary.protocol same
               WHERE lpad(same.requester_cpf, 11, '0')
                     = regexp_replace(person.cpf, '\\D', '', 'g')) = 1
          AND (SELECT count(*) FROM sag.enrollment same
               JOIN sag.person same_person USING (person_id)
               WHERE regexp_replace(same_person.cpf, '\\D', '', 'g')
                     = regexp_replace(person.cpf, '\\D', '', 'g')) = 1
          AND NOT EXISTS (
              SELECT 1 FROM secretary.protocol guardian
              WHERE guardian.requester_type = 'Guardian'
                AND lpad(guardian.stu_id, 6, '0') = enrollment.student_id
          )
    """,
}
