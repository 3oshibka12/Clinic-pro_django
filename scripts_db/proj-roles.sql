-- create role admin;
-- create role registrar;
-- create role doctor_role;
-- create role analyst;
-- create role patient_role;

alter role doctor_role nologin;
alter role patient_role nologin;
alter role registrar nologin;
alter role analyst nologin;

--
grant doctor_role to bog;
grant patient_role to bog;
grant registrar to bog;
grant analyst to bog;

--

grant all privileges on all tables in schema public to admin;
grant all privileges on all sequences in schema public to admin;
grant execute on all functions in schema public to admin;



grant select, insert, update, delete on clinic_patient to registrar;
grant select, insert, update, delete on clinic_appointment to registrar;
grant select on clinic_doctor to registrar;
grant select on clinic_schedule to registrar;
grant select on doctor_schedule to registrar;
grant select on patient_info to registrar;
grant select on today_appoint to registrar;



grant select on clinic_patient to patient_role;
grant select, insert on clinic_appointment to patient_role;
grant select, update, delete on clinic_prescription to patient_role;
grant select on clinic_doctor to patient_role;
grant select on clinic_schedule to patient_role;
grant select on clinic_diagnosis to patient_role;
grant select on clinic_drug to patient_role;
grant select on doctor_schedule to patient_role;



grant select on clinic_patient to doctor_role;
grant select on clinic_appointment to doctor_role;
grant select, insert, update on clinic_prescription to doctor_role;
grant select on clinic_diagnosis to doctor_role;
grant select on clinic_drug to doctor_role;
grant select on clinic_schedule to doctor_role;
grant select on patient_info to doctor_role;
grant select on today_appoint to doctor_role;



grant select on all tables in schema public to analyst;
grant select on doctor_schedule to analyst;
grant select on patient_info to analyst;
grant select on today_appoint to analyst;
grant select on static_per_month to analyst;

--

grant all privileges on table django_session to doctor_role, patient_role, registrar, analyst;
grant all privileges on table auth_user to doctor_role, patient_role, registrar, analyst;
grant select on table django_content_type to doctor_role, patient_role, registrar, analyst;
grant select on table django_migrations to doctor_role, patient_role, registrar, analyst;



alter table clinic_appointment force row level security;
alter table clinic_prescription force row level security;



alter table clinic_appointment disable row level security;


alter table clinic_appointment enable row level security;

--clinic appointment

create policy final_patient_policy on clinic_appointment
    for all
    to patient_role
    using (
        id_pat = nullif(current_setting('app.user_id', true), '')::integer
    )
    with check (
        id_pat = nullif(current_setting('app.user_id', true), '')::integer
    );



create policy final_doctor_policy on clinic_appointment
    for select
    to doctor_role
    using (
        id_doc = nullif(current_setting('app.user_id', true), '')::integer
    );



create policy final_staff_policy on clinic_appointment
    for all
    to registrar, analyst
    using (true)
    with check (true);







--clinic patient

alter table clinic_patient enable row level security;

drop policy if exists doctor_view_patients on clinic_patient;
drop policy if exists patient_view_self on clinic_patient;

create policy doctor_view_patients on clinic_patient
    for select
    to doctor_role
    using (true);

create policy patient_view_self on clinic_patient
    for select
    to patient_role
    using (
        id_pat = nullif(current_setting('app.user_id', true), '')::integer
    );

create policy staff_view_patients on clinic_patient
    for all
    to registrar, analyst
    using (true)
    with check (true);




--clinic_prescription

alter table clinic_prescription disable row level security;

create policy doctor_manage_prescription on clinic_prescription
    for all
    to doctor_role
    using (true)
    with check (true);

create policy patient_view_prescription on clinic_prescription
    for all
    to patient_role
    using (
        exists (
            select 1 from clinic_appointment a
            where a.id_rec = clinic_prescription.id_rec_id
            and a.id_pat = nullif(current_setting('app.user_id', true), '')::integer
        )
    );








grant delete on clinic_appointment to patient_role;

grant update, delete on clinic_appointment to registrar;

grant insert on clinic_historyappointment to patient_role;
grant insert on clinic_historyappointment to registrar;

grant insert on clinic_historyappointment to doctor_role;
grant insert on clinic_historyappointment to registrar;
grant insert on clinic_historyappointment to patient_role;

--GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO doctor_role, registrar, patient_role;
