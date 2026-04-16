create table if not exists public.admin_users (
    id serial primary key,
    username varchar not null unique,
    password_hash varchar not null,
    created_at timestamptz default now()
);

update public.timetable
set end_time = end_time + interval '12 hours'
where is_break = true
  and start_time >= end_time;

update public.timetable
set subject_code = null,
    subject_name = null
where is_break = true;

alter table public.timetable
    add constraint timetable_class_day_period_unique unique (class_name, day, period);

alter table public.timetable
    add constraint timetable_valid_time_range check (start_time < end_time);

alter table public.timetable
    add constraint timetable_break_has_no_subject check (
        (is_break = false) or (subject_code is null and subject_name is null)
    );

alter table public.attendance_sessions
    drop constraint if exists attendance_sessions_day_check;

alter table public.attendance_sessions
    add constraint attendance_sessions_day_check check (
        day::text = any (array['MON','TUE','WED','THU','FRI','SAT','SUN'])
    );
