LMS_QUERIES = {
    "term_online_opens_date": """
        SELECT DISTINCT opens_at::date FROM own_quizzes WHERE term = :term AND name = :quiz
    """,
    "term_online_opens_time": """
        SELECT DISTINCT to_char(opens_at, 'HH24:MI') FROM own_quizzes
        WHERE term = :term AND name = :quiz
    """,
    "term_online_closes_date": """
        SELECT DISTINCT closes_at::date FROM own_quizzes WHERE term = :term AND name = :quiz
    """,
    "term_online_closes_time": """
        SELECT DISTINCT to_char(closes_at, 'HH24:MI') FROM own_quizzes
        WHERE term = :term AND name = :quiz
    """,
    "quiz_opens_date": """
        SELECT opens_at::date FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "quiz_opens_time": """
        SELECT to_char(opens_at, 'HH24:MI') FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "quiz_closes_date": """
        SELECT closes_at::date FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "quiz_closes_time": """
        SELECT to_char(closes_at, 'HH24:MI') FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "quiz_time_limit_minutes": """
        SELECT timelimit::int / 60 FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "quiz_attempts_allowed": """
        SELECT attempts FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "quiz_attempts_remaining": """
        SELECT own_quizzes.attempts::int - (
            SELECT count(*) FROM lms.mdl_quiz_attempts attempt
            WHERE attempt.quiz = own_quizzes.id AND attempt.userid = own_quizzes.account_id
        )
        FROM own_quizzes
        WHERE term = :term AND subject_name = :subject AND name = :quiz
    """,
    "attempt_state": """
        SELECT state FROM own_attempts
        WHERE term = :term AND subject_name = :subject AND quiz_name = :quiz
          AND attempt = :attempt
    """,
    "attempt_grade_is_blank": """
        SELECT sumgrades IS NULL FROM own_attempts
        WHERE term = :term AND subject_name = :subject AND quiz_name = :quiz
          AND attempt = :attempt
    """,
    "attempt_grade": """
        SELECT replace(sumgrades, '.', ',') FROM own_attempts
        WHERE term = :term AND subject_name = :subject AND quiz_name = :quiz
          AND attempt = :attempt
    """,
    "attempt_started_date": """
        SELECT started_at::date FROM own_attempts
        WHERE term = :term AND subject_name = :subject AND quiz_name = :quiz
          AND attempt = :attempt
    """,
    "attempt_finished_date": """
        SELECT finished_at::date FROM own_attempts
        WHERE term = :term AND subject_name = :subject AND quiz_name = :quiz
          AND attempt = :attempt
    """,
    "attempt_finished_time": """
        SELECT to_char(finished_at, 'HH24:MI') FROM own_attempts
        WHERE term = :term AND subject_name = :subject AND quiz_name = :quiz
          AND attempt = :attempt
    """,
    "last_access_date": "SELECT accessed_at::date FROM own_last_access",
    "last_access_time": "SELECT to_char(accessed_at, 'HH24:MI') FROM own_last_access",
    "account_suspended": "SELECT suspended FROM own_accounts",
    "lms_accounts": "SELECT count(*) FROM own_accounts",
    "material_views": """
        SELECT count(*) FROM own_page_views WHERE subject_name = :subject AND material = :material
    """,
    "material_last_view_date": """
        SELECT max(viewed_at)::date FROM own_page_views
        WHERE subject_name = :subject AND material = :material
    """,
    "material_last_view_time": """
        SELECT to_char(max(viewed_at), 'HH24:MI') FROM own_page_views
        WHERE subject_name = :subject AND material = :material
    """,
    "lms_rooms_start": """
        SELECT min((to_timestamp(startdate::bigint) AT TIME ZONE 'America/Sao_Paulo')::date)
        FROM lms.mdl_course WHERE split_part(shortname, '_', 2) ~ '^[0-9]{4}-[0-9]$'
    """,
    "lms_log_start": """
        SELECT min((to_timestamp(timecreated::bigint) AT TIME ZONE 'America/Sao_Paulo')::date)
        FROM lms.mdl_logstore_standard_log
    """,
}
