create or replace function shed_tg_f()
    returns trigger
    language 'plpgsql'
as
$$
begin
    if exists (
        select 1 from clinic_schedule
        where id_doc = new.id_doc
          and day = new.day
		  and clinic_schedule.time_start != coalesce(new.time_start, old.time_start)
          and not (time_end <= new.time_start or new.time_end <= time_start)
    ) then
        raise exception 'Время %s - %s уже занято', new.time_start, new.time_end;
    end if;
    return new;
end;
$$;
--		 < - выше (раньше); > - ниже (позже)


create or replace trigger shed_tg
	before insert or update
	on clinic_schedule
	for each row
	execute procedure shed_tg_f();


--



create or replace function appo_tg_f()
    returns trigger
    language 'plpgsql'
as
$$
begin
    if exists (
        select 1 from clinic_appointment
        where id_doc = new.id_doc
          and visit_time = new.visit_time
          and id_rec != coalesce(new.id_rec, 0)
    ) then
        raise exception 'Это время уже занято у данного врача';
    end if;
    return new;
end;
$$;

create or replace trigger appo_tg
	before insert or update
	on clinic_appointment
	for each row
	execute procedure appo_tg_f();



--


create table if not exists clinic_historyappointment (
	id_change serial primary key,
	id_rec int not null,
	id_pat int not null references clinic_patient(id_pat),
	id_doc int not null references clinic_doctor(id_doc),
	visit_time timestamp not null,
	cabinet int not null
);

create or replace function his_tg_f()
	returns trigger
	language 'plpgsql'
	as
$$
begin
	insert into clinic_historyappointment (id_rec, id_pat, id_doc, visit_time, cabinet)
		values (old.id_rec, old.id_pat, old.id_doc, old.visit_time, old.cabinet);
	return null;
end;
$$;


create or replace trigger his_tg
	after update or delete
	on clinic_appointment
	for each row
	execute procedure his_tg_f();



-- select * from clinic_historyappointment