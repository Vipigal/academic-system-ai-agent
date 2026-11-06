CREATE INDEX contract_owner ON finance.contract
    (companycode, businessarea, lpad(split_part(btrim(academicref), '-', 1), 5, '0'));
CREATE INDEX invoice_contract ON finance.invoice (contractid);
CREATE INDEX payment_invoice ON finance.payment (invoiceid);
CREATE INDEX late_charge_invoice ON finance.late_charge (invoiceid);
CREATE INDEX discount_contract ON finance.discount (contractid);
CREATE INDEX agreement_contract ON finance.agreement (contractid);

CREATE INDEX lms_user_owner ON lms.mdl_user (tenant_id, upper(btrim(student_id)));
CREATE INDEX user_enrolment_user ON lms.mdl_user_enrolments (userid);
CREATE INDEX quiz_attempt_user ON lms.mdl_quiz_attempts (userid);
CREATE INDEX log_user ON lms.mdl_logstore_standard_log (userid);
CREATE INDEX course_tenant ON lms.mdl_course (tenant_id);
CREATE INDEX quiz_course ON lms.mdl_quiz (course);
CREATE INDEX course_module_course ON lms.mdl_course_modules (course);

CREATE INDEX protocol_student ON secretary.protocol (lpad(stu_id, 6, '0'));
CREATE INDEX protocol_requester_cpf ON secretary.protocol (lpad(requester_cpf, 11, '0'));
CREATE INDEX protocol_interaction_protocol ON secretary.protocol_interaction (protocol);
CREATE INDEX issued_document_protocol ON secretary.issued_document (protocol);

CREATE INDEX person_cpf ON sag.person (regexp_replace(cpf, '\D', '', 'g'));
CREATE INDEX enrollment_person ON sag.enrollment (person_id);
CREATE INDEX enrollment_student ON sag.enrollment (student_id);
CREATE INDEX student_class_enrollment ON sag.student_class (brand, student_id);
CREATE INDEX enrollment_history_enrollment ON sag.enrollment_status_history (brand, student_id);

ANALYZE;
