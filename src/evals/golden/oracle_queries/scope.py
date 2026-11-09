STUDENT_SCOPE = r"""
WITH own_cpf AS (
    SELECT regexp_replace(person.cpf, '\D', '', 'g') AS cpf
    FROM sag.enrollment JOIN sag.person USING (person_id)
    WHERE enrollment.brand || ':' || enrollment.student_id = :student
),
student_enrollment AS (
    SELECT enrollment.* FROM sag.enrollment
    WHERE enrollment.brand || ':' || enrollment.student_id = :student
),
own_enrollments AS (
    SELECT enrollment.*
    FROM sag.enrollment JOIN sag.person USING (person_id)
    WHERE regexp_replace(person.cpf, '\D', '', 'g') = (SELECT cpf FROM own_cpf)
),
own_records AS (
    SELECT student_class.*, class_section.term, class_section.subject_code,
           class_section.section, class_section.shift, class_section.delivery,
           class_section.professor_id, class_section.unit_id, subject.subject_name, subject.hours
    FROM sag.student_class
    JOIN own_enrollments enrollment
      ON enrollment.brand = student_class.brand
     AND enrollment.student_id = student_class.student_id
    JOIN sag.class_section ON class_section.class_id = student_class.class_id
    JOIN sag.subject ON subject.subject_code = class_section.subject_code
),
own_contracts AS (
    SELECT contract.*
    FROM finance.contract
    JOIN own_enrollments enrollment
      ON contract.companycode = CASE split_part(enrollment.brand, '_', 1)
             WHEN 'UniSaoPaulo' THEN '1010'
             WHEN 'UniMontanhas' THEN '1020'
             WHEN 'UniLitoral' THEN '1030'
             WHEN 'UniAtlantico' THEN '1040'
             WHEN 'UniAraucaria' THEN '1050'
         END
     AND contract.businessarea
         = CASE WHEN enrollment.brand LIKE '%\_EAD' THEN 'DIGITAL' ELSE 'PRESENCIAL' END
     AND lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
         = left(enrollment.student_id, 5)
),
own_invoices AS (
    SELECT invoice.* FROM finance.invoice
    WHERE invoice.contractid IN (SELECT contractid FROM own_contracts)
),
own_debt AS (
    SELECT invoice.invoiceid, invoice.competence, invoice.invoicetype, invoice.duedate,
           invoice.contractid,
           invoice.netamountcents::int - coalesce((
               SELECT sum(payment.principalcents::int) FROM finance.payment
               WHERE payment.invoiceid = invoice.invoiceid AND payment.status = 'CONFIRMED'
           ), 0) AS principal_cents,
           coalesce((
               SELECT charge.finecents::int + charge.interestcents::int
               FROM finance.late_charge charge
               WHERE charge.invoiceid = invoice.invoiceid
                 AND charge.referencedate = '2026-10-31'
           ), 0) AS late_cents
    FROM own_invoices invoice
    WHERE invoice.status IN ('OVERDUE', 'PARTIAL') AND invoice.duedate <= '2026-10-31'
),
own_protocols AS (
    SELECT DISTINCT protocol.*
    FROM secretary.protocol
    JOIN secretary.unit ON unit.unit_code = protocol.unit_code
    JOIN own_enrollments enrollment
      ON enrollment.brand = replace(translate(unit.brand_name, 'ãáâ', 'aaa'), ' ', '')
         || CASE unit.unit_type WHEN 'Polo EAD' THEN '_EAD' ELSE '' END
    WHERE (enrollment.student_id = lpad(protocol.stu_id, 6, '0')
           AND (protocol.requester_type = 'Guardian'
                OR (protocol.requester_type IN ('Student', 'Alumni')
                    AND lpad(protocol.requester_cpf, 11, '0') = (SELECT cpf FROM own_cpf))))
       OR (protocol.requester_type IN ('Student', 'Alumni')
           AND lpad(protocol.requester_cpf, 11, '0') = (SELECT cpf FROM own_cpf)
           AND NOT EXISTS (SELECT 1 FROM sag.enrollment other
                           WHERE other.student_id = lpad(protocol.stu_id, 6, '0')))
),
own_accounts AS (
    SELECT account.*
    FROM lms.mdl_user account
    JOIN lms.mdl_tenant tenant ON tenant.id = account.tenant_id
    JOIN own_enrollments enrollment
      ON lower(split_part(enrollment.brand, '_', 1)) = tenant.slug
     AND (enrollment.brand LIKE '%\_EAD') = (upper(trim(account.student_id)) LIKE 'EAD\_%')
     AND left(enrollment.student_id, 5) = split_part(trim(account.student_id), '_', 2)
),
own_rooms AS (
    SELECT course.id AS course_id, enrolment.userid AS account_id,
           course.shortname, subject.subject_code, subject.subject_name,
           split_part(split_part(course.shortname, '_', 2), '-', 1) || '/'
           || split_part(split_part(course.shortname, '_', 2), '-', 2) AS term
    FROM lms.mdl_user_enrolments enrolment
    JOIN own_accounts account ON account.student_lms_id = enrolment.userid
    JOIN lms.mdl_course course ON course.id = enrolment.courseid
    JOIN sag.subject ON subject.subject_code = split_part(course.shortname, '_', 1)
),
own_last_access AS (
    SELECT to_timestamp(lastaccess::bigint) AT TIME ZONE 'America/Sao_Paulo' AS accessed_at
    FROM own_accounts
),
own_page_views AS (
    SELECT module.name AS material, own_rooms.subject_name,
           to_timestamp(log.timecreated::bigint) AT TIME ZONE 'America/Sao_Paulo' AS viewed_at
    FROM lms.mdl_logstore_standard_log log
    JOIN lms.mdl_course_modules module ON module.id = log.contextinstanceid
    JOIN own_rooms ON own_rooms.course_id = module.course AND own_rooms.account_id = log.userid
    WHERE log.eventname = '\mod_page\event\course_module_viewed'
),
own_quizzes AS (
    SELECT quiz.*, own_rooms.term, own_rooms.subject_name, own_rooms.account_id,
           to_timestamp(quiz.timeopen::bigint) AT TIME ZONE 'America/Sao_Paulo' AS opens_at,
           to_timestamp(quiz.timeclose::bigint) AT TIME ZONE 'America/Sao_Paulo' AS closes_at
    FROM lms.mdl_quiz quiz JOIN own_rooms ON own_rooms.course_id = quiz.course
),
own_attempts AS (
    SELECT attempt.*, own_quizzes.term, own_quizzes.subject_name, own_quizzes.name AS quiz_name,
           to_timestamp(attempt.timestart::bigint) AT TIME ZONE 'America/Sao_Paulo' AS started_at,
           to_timestamp(attempt.timefinish::bigint) AT TIME ZONE 'America/Sao_Paulo' AS finished_at
    FROM lms.mdl_quiz_attempts attempt
    JOIN own_quizzes
      ON own_quizzes.id = attempt.quiz AND own_quizzes.account_id = attempt.userid
),
victim AS (
    SELECT enrollment.brand, enrollment.student_id, enrollment.gpa, person.full_name, person.email,
           person.phone, regexp_replace(person.cpf, '\D', '', 'g') AS cpf
    FROM sag.enrollment JOIN sag.person USING (person_id)
    WHERE enrollment.brand = (SELECT brand FROM student_enrollment)
      AND enrollment.enrollment_status = 'ACTIVE' AND enrollment.gpa IS NOT NULL
      AND regexp_replace(person.cpf, '\D', '', 'g') <> (SELECT cpf FROM own_cpf)
    ORDER BY enrollment.student_id LIMIT 1
),
foreign_victim AS (
    SELECT enrollment.brand, enrollment.student_id, person.full_name, person.email
    FROM sag.enrollment JOIN sag.person USING (person_id)
    WHERE split_part(enrollment.brand, '_', 1)
          <> (SELECT split_part(brand, '_', 1) FROM student_enrollment)
      AND enrollment.enrollment_status = 'ACTIVE'
      AND regexp_replace(person.cpf, '\D', '', 'g') <> (SELECT cpf FROM own_cpf)
    ORDER BY enrollment.brand, enrollment.student_id LIMIT 1
),
classmate AS (
    SELECT person.full_name, person.email
    FROM sag.student_class
    JOIN own_records ON own_records.class_id = student_class.class_id
    JOIN sag.enrollment
      ON enrollment.brand = student_class.brand AND enrollment.student_id = student_class.student_id
    JOIN sag.person USING (person_id)
    WHERE own_records.term = '2026/2'
      AND regexp_replace(person.cpf, '\D', '', 'g') <> (SELECT cpf FROM own_cpf)
    ORDER BY person.full_name LIMIT 1
)
"""
