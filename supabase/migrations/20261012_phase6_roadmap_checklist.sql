-- ============================================================================
-- SchemeAI — Database Migration (Phase 6: Application Roadmap & Document Checklist)
-- Smart India Hackathon: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
-- Database: Supabase PostgreSQL
-- ============================================================================

-- Table 1: public.user_scheme_roadmap_progress
-- Tracks user-specific step status for verified application roadmaps
create table if not exists public.user_scheme_roadmap_progress (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    scheme_id text not null,
    step_id text not null,
    status text not null check (status in ('Not started', 'In progress', 'Completed')),
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null,
    constraint uq_user_scheme_step unique (user_id, scheme_id, step_id)
);

-- Table 2: public.user_scheme_checklist_progress
-- Tracks readiness of verified document checklist items without storing actual documents or sensitive data
create table if not exists public.user_scheme_checklist_progress (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    scheme_id text not null,
    item_id text not null,
    status text not null check (status in ('Not checked', 'Ready', 'Needs attention', 'Needs verification')),
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null,
    constraint uq_user_scheme_item unique (user_id, scheme_id, item_id)
);

-- Indexes for fast retrieval by user and scheme
create index if not exists idx_roadmap_user_scheme on public.user_scheme_roadmap_progress(user_id, scheme_id);
create index if not exists idx_roadmap_updated_at on public.user_scheme_roadmap_progress(updated_at desc);
create index if not exists idx_checklist_user_scheme on public.user_scheme_checklist_progress(user_id, scheme_id);
create index if not exists idx_checklist_updated_at on public.user_scheme_checklist_progress(updated_at desc);

-- Enable Row Level Security (RLS)
alter table public.user_scheme_roadmap_progress enable row level security;
alter table public.user_scheme_checklist_progress enable row level security;

-- RLS Policies for Roadmap Progress
drop policy if exists "Users can view their own roadmap progress" on public.user_scheme_roadmap_progress;
create policy "Users can view their own roadmap progress"
    on public.user_scheme_roadmap_progress for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own roadmap progress" on public.user_scheme_roadmap_progress;
create policy "Users can insert their own roadmap progress"
    on public.user_scheme_roadmap_progress for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update their own roadmap progress" on public.user_scheme_roadmap_progress;
create policy "Users can update their own roadmap progress"
    on public.user_scheme_roadmap_progress for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own roadmap progress" on public.user_scheme_roadmap_progress;
create policy "Users can delete their own roadmap progress"
    on public.user_scheme_roadmap_progress for delete using (auth.uid() = user_id);

-- RLS Policies for Document Checklist Progress
drop policy if exists "Users can view their own checklist progress" on public.user_scheme_checklist_progress;
create policy "Users can view their own checklist progress"
    on public.user_scheme_checklist_progress for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own checklist progress" on public.user_scheme_checklist_progress;
create policy "Users can insert their own checklist progress"
    on public.user_scheme_checklist_progress for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update their own checklist progress" on public.user_scheme_checklist_progress;
create policy "Users can update their own checklist progress"
    on public.user_scheme_checklist_progress for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own checklist progress" on public.user_scheme_checklist_progress;
create policy "Users can delete their own checklist progress"
    on public.user_scheme_checklist_progress for delete using (auth.uid() = user_id);

-- Auto-update timestamps triggers
drop trigger if exists set_roadmap_updated_at on public.user_scheme_roadmap_progress;
create trigger set_roadmap_updated_at
    before update on public.user_scheme_roadmap_progress
    for each row execute function public.handle_updated_at();

drop trigger if exists set_checklist_updated_at on public.user_scheme_checklist_progress;
create trigger set_checklist_updated_at
    before update on public.user_scheme_checklist_progress
    for each row execute function public.handle_updated_at();
