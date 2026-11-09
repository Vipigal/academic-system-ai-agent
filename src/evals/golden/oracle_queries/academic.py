ACADEMIC_QUERIES = {
    "term_av2_start": "SELECT av2_start FROM sag.term WHERE term = :term",
    "term_end": "SELECT end_date FROM sag.term WHERE term = :term",
    "last_term_end": "SELECT end_date FROM sag.term ORDER BY term DESC LIMIT 1",
    "student_status": "SELECT enrollment_status FROM student_enrollment",
    "student_curriculum": "SELECT curriculum_id FROM student_enrollment",
    "student_course": """
        SELECT course.course_name
        FROM student_enrollment JOIN sag.course USING (course)
    """,
    "student_gpa": "SELECT replace(gpa, '.', ',') FROM student_enrollment",
    "student_gpa_matches_records": """
        SELECT round(avg(final_grade::numeric), 2) = (SELECT gpa::numeric FROM student_enrollment)
        FROM sag.student_class
        JOIN student_enrollment USING (brand, student_id)
        WHERE final_grade IS NOT NULL AND result <> 'EXEMPT'
    """,
    "student_completion": "SELECT current_curriculum_completion FROM student_enrollment",
    "enrollment_status_date": """
        SELECT status_date FROM own_enrollments WHERE enrollment_status = :status
    """,
    "enrollments_of_person": "SELECT count(*) FROM own_enrollments",
    "own_enrollment_statuses": """
        SELECT string_agg(enrollment_status, ', ' ORDER BY enrollment_status) FROM own_enrollments
    """,
    "student_enrollment_date": "SELECT date_of_enrollment FROM student_enrollment",
    "active_enrollments_of_person": """
        SELECT count(*) FROM own_enrollments WHERE enrollment_status = 'ACTIVE'
    """,
    "term_registrations": """
        SELECT count(*) FROM sag.term_enrollment
        JOIN own_enrollments USING (brand, student_id)
        WHERE term = :term
    """,
    "semester_subjects": """
        SELECT string_agg(
            subject.subject_name
            || CASE curriculum_subject.mandatory WHEN 'Y' THEN '' ELSE ' (optional)' END,
            ', ' ORDER BY subject.subject_name
        )
        FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND semester = :semester
    """,
    "curriculum_subject_count": """
        SELECT count(*) FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND subject.subject_name = :subject
    """,
    "curriculum_subject_semester": """
        SELECT curriculum_subject.semester FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND subject.subject_name = :subject
    """,
    "curriculum_subject_mandatory": """
        SELECT curriculum_subject.mandatory FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND subject.subject_name = :subject
    """,
    "curriculum_subject_prerequisite": """
        SELECT prerequisite.subject_name FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        JOIN sag.subject prerequisite
          ON prerequisite.subject_code = curriculum_subject.prerequisite_code
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND subject.subject_name = :subject
    """,
    "subject_final_of_result": """
        SELECT replace(final_grade, '.', ',') FROM own_records
        WHERE subject_name = :subject AND result = :result
    """,
    "subject_attendance_of_result": """
        SELECT attendance_pct FROM own_records WHERE subject_name = :subject AND result = :result
    """,
    "subject_term_of_result": """
        SELECT term FROM own_records WHERE subject_name = :subject AND result = :result
    """,
    "online_courses_of_brand": """
        SELECT string_agg(DISTINCT course.course_name, ', ' ORDER BY course.course_name)
        FROM sag.course_offer
        JOIN sag.unit USING (unit_id)
        JOIN sag.course USING (course)
        WHERE unit.brand = split_part((SELECT brand FROM student_enrollment), '_', 1) || '_EAD'
    """,
    "course_shifts_of_student_unit": """
        SELECT string_agg(DISTINCT course_offer.shift, ', ' ORDER BY course_offer.shift)
        FROM sag.course_offer
        JOIN sag.course USING (course)
        WHERE course_offer.unit_id = (SELECT unit_id FROM student_enrollment)
          AND course.course_name = :course
    """,
    "student_unit": """
        SELECT unit.unit_name FROM student_enrollment JOIN sag.unit USING (unit_id)
    """,
    "records_in_progress": """
        SELECT count(*) FROM own_records WHERE term = :term AND result = 'IN_PROGRESS'
    """,
    "subjects_in_progress": """
        SELECT string_agg(subject_name, ', ' ORDER BY subject_name)
        FROM own_records WHERE term = :term AND result = 'IN_PROGRESS'
    """,
    "sections_in_progress": """
        SELECT string_agg(DISTINCT section || ' ' || shift || ' ' || delivery, ', ')
        FROM own_records WHERE term = :term AND result = 'IN_PROGRESS'
    """,
    "records_with_av1": """
        SELECT count(*) FROM own_records
        WHERE term = :term AND result = 'IN_PROGRESS' AND grade_av1 IS NOT NULL
    """,
    "subjects_starting_with": """
        SELECT count(*) FROM own_records
        WHERE term = :term AND starts_with(subject_name, :prefix)
    """,
    "av1_of_subject": """
        SELECT replace(grade_av1, '.', ',') FROM own_records
        WHERE term = :term AND subject_name = :subject
    """,
    "av2_is_blank": """
        SELECT bool_and(grade_av2 IS NULL) FROM own_records WHERE term = :term
    """,
    "required_av2": """
        SELECT replace(round((6 - 0.4 * grade_av1::numeric) / 0.6, 1)::text, '.', ',')
        FROM own_records WHERE term = :term AND subject_name = :subject
    """,
    "attendance_of_subject": """
        SELECT attendance_pct FROM own_records WHERE term = :term AND subject_name = :subject
    """,
    "section_of_subject": """
        SELECT section FROM own_records WHERE term = :term AND subject_name = :subject
    """,
    "shift_of_subject": """
        SELECT shift FROM own_records WHERE term = :term AND subject_name = :subject
    """,
    "subject_was_approved": """
        SELECT bool_or(result = 'APPROVED') FROM own_records WHERE subject_name = :subject
    """,
    "final_grade_of_class": """
        SELECT replace(final_grade, '.', ',') FROM own_records WHERE class_id = :class_id
    """,
    "attendance_of_class": "SELECT attendance_pct FROM own_records WHERE class_id = :class_id",
    "result_of_class": "SELECT result FROM own_records WHERE class_id = :class_id",
    "term_of_class": "SELECT term FROM own_records WHERE class_id = :class_id",
    "subject_of_class": "SELECT subject_name FROM own_records WHERE class_id = :class_id",
    "completed_hours": """
        SELECT sum(subject.hours::int)
        FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND EXISTS (
              SELECT 1 FROM sag.student_class
              JOIN sag.class_section USING (class_id)
              JOIN student_enrollment
                ON student_enrollment.brand = student_class.brand
               AND student_enrollment.student_id = student_class.student_id
              WHERE class_section.subject_code = subject.subject_code
                AND student_class.result IN ('APPROVED', 'EXEMPT')
          )
    """,
    "curriculum_total_hours": """
        SELECT total_hours FROM sag.curriculum
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
    """,
    "missing_subjects": """
        SELECT count(*) FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND NOT EXISTS (
              SELECT 1 FROM sag.student_class
              JOIN sag.class_section USING (class_id)
              JOIN student_enrollment
                ON student_enrollment.brand = student_class.brand
               AND student_enrollment.student_id = student_class.student_id
              WHERE class_section.subject_code = subject.subject_code
                AND student_class.result IN ('APPROVED', 'EXEMPT')
          )
    """,
    "missing_subjects_with_hours": """
        SELECT string_agg(subject.subject_name || ' ' || subject.hours, ', '
                          ORDER BY subject.subject_name)
        FROM sag.curriculum_subject
        JOIN sag.subject USING (subject_code)
        WHERE curriculum_id = (SELECT curriculum_id FROM student_enrollment)
          AND NOT EXISTS (
              SELECT 1 FROM sag.student_class
              JOIN sag.class_section USING (class_id)
              JOIN student_enrollment
                ON student_enrollment.brand = student_class.brand
               AND student_enrollment.student_id = student_class.student_id
              WHERE class_section.subject_code = subject.subject_code
                AND student_class.result IN ('APPROVED', 'EXEMPT')
          )
    """,
    "failed_in_term": """
        SELECT count(*) FROM own_records WHERE term = :term AND result = 'FAILED'
    """,
    "failed_subjects_in_term": """
        SELECT string_agg(subject_name, ', ' ORDER BY subject_name)
        FROM own_records WHERE term = :term AND result = 'FAILED'
    """,
    "failed_final_grades_in_term": """
        SELECT replace(string_agg(DISTINCT final_grade, ', '), '.', ',')
        FROM own_records WHERE term = :term AND result = 'FAILED'
    """,
    "failed_with_av1_in_term": """
        SELECT count(*) FROM own_records
        WHERE term = :term AND result = 'FAILED' AND grade_av1 IS NOT NULL
    """,
    "lock_date": """
        SELECT event_date FROM sag.enrollment_status_history
        JOIN student_enrollment USING (brand, student_id)
        WHERE new_status = 'LOCKED' ORDER BY event_date DESC LIMIT 1
    """,
    "lock_protocol": """
        SELECT protocol_ref FROM sag.enrollment_status_history
        JOIN student_enrollment USING (brand, student_id)
        WHERE new_status = 'LOCKED' ORDER BY event_date DESC LIMIT 1
    """,
    "lock_reason": """
        SELECT reason FROM sag.enrollment_status_history
        JOIN student_enrollment USING (brand, student_id)
        WHERE new_status = 'LOCKED' ORDER BY event_date DESC LIMIT 1
    """,
}
