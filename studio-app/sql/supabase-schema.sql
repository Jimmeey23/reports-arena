-- Run in the Supabase SQL Editor. Matches ai/store.py.
-- Server-only access: configure SUPABASE_KEY with the service_role key.
begin;

create table if not exists public.chat_messages (
  id bigint generated always as identity primary key,
  session_id text not null,
  role text not null,
  content text not null,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.report_edits (
  id bigint generated always as identity primary key,
  run_id text not null,
  el_id text not null,
  op text not null,
  html text default '',
  sort integer default 0,
  updated_at timestamptz default now(),
  unique (run_id, el_id, op)
);

create table if not exists public.ai_cache (
  key text primary key,
  value jsonb not null,
  created_at timestamptz default now()
);

create table if not exists public.reports (
  run_id text primary key,
  studio text,
  label text,
  -- The app sends formatted IST text, not an ISO timestamp.
  built_at text,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.app_config (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz default now()
);

create index if not exists p57_chat_session_created
  on public.chat_messages (session_id, created_at);
create index if not exists p57_report_edits_run_sort
  on public.report_edits (run_id, sort);
create index if not exists p57_reports_studio_created
  on public.reports (studio, created_at desc);

alter table public.chat_messages enable row level security;
alter table public.report_edits enable row level security;
alter table public.ai_cache enable row level security;
alter table public.reports enable row level security;
alter table public.app_config enable row level security;

-- No browser-facing policies: only the server accesses these tables.
revoke all on table public.chat_messages, public.report_edits,
  public.ai_cache, public.reports, public.app_config from anon, authenticated;
grant usage on schema public to service_role;
grant select, insert, update, delete on table public.chat_messages,
  public.report_edits, public.ai_cache, public.reports, public.app_config
  to service_role;
grant usage, select on sequence public.chat_messages_id_seq,
  public.report_edits_id_seq to service_role;

notify pgrst, 'reload schema';
commit;
