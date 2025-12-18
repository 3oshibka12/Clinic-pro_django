
CREATE OR REPLACE VIEW static_per_month AS
SELECT 
    row_number() OVER () as id,
    d.fname, 
    d.lname, 
    d.specialization,
    count(a.id_rec) as appointment_count
FROM clinic_doctor d
JOIN clinic_appointment a ON d.id_doc = a.id_doc
WHERE extract(month from a.visit_time) = extract(month from current_date)
GROUP BY d.fname, d.lname, d.specialization;










CREATE OR REPLACE VIEW view_doctor_future_appointments AS
SELECT 
    a.id_rec,
    a.visit_time,
    a.cabinet,
    p.fname || ' ' || p.lname AS patient_name,
    p.birth_date
FROM clinic_appointment a
JOIN clinic_patient p ON a.id_pat = p.id_pat
WHERE 
    a.visit_time >= NOW() 
    AND 
    a.id_doc = NULLIF(current_setting('app.user_id', true), '')::integer;


CREATE OR REPLACE VIEW view_doctor_past_appointments AS
SELECT 
    a.id_rec,
    a.visit_time,
    p.fname || ' ' || p.lname AS patient_name,
    EXISTS(SELECT 1 FROM clinic_prescription pr WHERE pr.id_rec_id = a.id_rec) as has_prescription
FROM clinic_appointment a
JOIN clinic_patient p ON a.id_pat = p.id_pat
WHERE 
    a.visit_time < NOW() 
    AND 
    a.id_doc = NULLIF(current_setting('app.user_id', true), '')::integer;



CREATE OR REPLACE VIEW view_patient_history AS
SELECT 
    a.id_rec,
    a.visit_time,
    d.lname || ' ' || d.fname || ' (' || d.specialization || ')' AS doctor_info,
    a.cabinet,
    diag.name AS diagnosis,
    drug.name AS drug_name,
    pr.treatment,
    pr.frequency,
    pr.duration
FROM clinic_appointment a
JOIN clinic_doctor d ON a.id_doc = d.id_doc
LEFT JOIN clinic_prescription pr ON a.id_rec = pr.id_rec_id
LEFT JOIN clinic_diagnosis diag ON pr.id_diag_id = diag.id_diag
LEFT JOIN clinic_drug drug ON pr.id_drug_id = drug.id_drug
WHERE 
    a.id_pat = NULLIF(current_setting('app.user_id', true), '')::integer
ORDER BY a.visit_time DESC;