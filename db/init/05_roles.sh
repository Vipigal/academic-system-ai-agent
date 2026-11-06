#!/usr/bin/env bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 --no-psqlrc --quiet \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v password="${API_DB_PASSWORD:?defina API_DB_PASSWORD}" <<'SQL'
CREATE ROLE api LOGIN PASSWORD :'password';

REVOKE ALL ON DATABASE :"DBNAME" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"DBNAME" TO api;

GRANT USAGE ON SCHEMA sag, lms, secretary, finance, agent TO api;

GRANT SELECT ON
    finance.agreement, finance.contract, finance.customer, finance.discount, finance.invoice,
    finance.late_charge, finance.payment, finance.product,
    lms.mdl_course, lms.mdl_course_modules, lms.mdl_logstore_standard_log, lms.mdl_quiz,
    lms.mdl_quiz_attempts, lms.mdl_user, lms.mdl_user_enrolments,
    sag.class_section, sag.course, sag.course_offer, sag.curriculum, sag.curriculum_subject,
    sag.enrollment, sag.enrollment_status_history, sag.person, sag.professor, sag.student_class,
    sag.subject, sag.term, sag.term_enrollment, sag.unit,
    secretary.demand_type, secretary.issued_document, secretary.protocol,
    secretary.protocol_interaction, secretary.protocol_status_history
TO api;

GRANT INSERT ON secretary.protocol, secretary.protocol_status_history, secretary.protocol_interaction
TO api;

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA agent TO api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA agent TO api;
SQL
