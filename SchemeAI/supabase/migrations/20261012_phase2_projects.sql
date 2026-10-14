-- ============================================================================
-- SchemeAI — Phase 2 Migration: Entrepreneur Projects & 3-Stage Tracking
-- Smart India Hackathon: AI-Driven Funding & Scheme Matching
-- Database: Supabase PostgreSQL
-- ============================================================================

-- Table: public.projects
create table if not exists public.projects (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    title text not null check (char_length(trim(title)) >= 2),
    problem_statement text not null check (char_length(trim(problem_statement)) >= 5),
    proposed_solution text not null check (char_length(trim(proposed_solution)) >= 5),
    category text not null,
    target_beneficiaries text not null,
    target_location text not null,
    estimated_budget numeric(14, 2) not null default 0.00 check (estimated_budget >= 0),
    current_stage text not null default 'Stage 1' check (
        current_stage in ('Stage 1', 'Stage 2', 'Stage 3', 'Completed')
    ),
    status text not null default 'In Progress' check (
        status in ('Draft', 'In Progress', 'Under Review', 'Completed')
    ),
    expected_impact text not null,
    image_url text,
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null
);

comment on table public.projects is 'Entrepreneur innovation projects submitted for SIH scheme matching & stage tracking';
comment on column public.projects.user_id is 'Authenticated owner ID from auth.users';

-- Table: public.project_stages
create table if not exists public.project_stages (
    id uuid primary key default gen_random_uuid(),
    project_id uuid not null references public.projects(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    stage_number integer not null check (stage_number in (1, 2, 3)),
    stage_name text not null,
    status text not null default 'Not Started' check (
        status in ('Not Started', 'In Progress', 'Completed')
    ),
    progress_percent integer default 0 check (progress_percent >= 0 and progress_percent <= 100),
    
    -- Stage 1: Idea Development
    idea_title text,
    problem_description text,
    solution_description text,
    target_beneficiaries text,
    
    -- Stage 2: Prototype Development
    prototype_details text,
    technologies_used text,
    prototype_link text,
    
    -- Stage 3: Product and Market Readiness
    product_features text,
    target_market text,
    pricing_model text,
    market_validation text,
    
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null,
    unique (project_id, stage_number)
);

comment on table public.project_stages is '3-Stage tracking milestones (Idea, Prototype, Market Readiness) for each project';

-- Performance Indexes
create index if not exists idx_projects_user_id on public.projects(user_id);
create index if not exists idx_projects_category on public.projects(category);
create index if not exists idx_projects_stage on public.projects(current_stage);
create index if not exists idx_projects_created_at on public.projects(created_at desc);

create index if not exists idx_project_stages_project_id on public.project_stages(project_id);
create index if not exists idx_project_stages_user_id on public.project_stages(user_id);

-- Enable Row Level Security (RLS)
alter table public.projects enable row level security;
alter table public.project_stages enable row level security;

-- Policies for public.projects
drop policy if exists "Users can view their own projects" on public.projects;
create policy "Users can view their own projects"
    on public.projects for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own projects" on public.projects;
create policy "Users can insert their own projects"
    on public.projects for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update their own projects" on public.projects;
create policy "Users can update their own projects"
    on public.projects for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own projects" on public.projects;
create policy "Users can delete their own projects"
    on public.projects for delete using (auth.uid() = user_id);

-- Policies for public.project_stages
drop policy if exists "Users can view their own project stages" on public.project_stages;
create policy "Users can view their own project stages"
    on public.project_stages for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own project stages" on public.project_stages;
create policy "Users can insert their own project stages"
    on public.project_stages for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update their own project stages" on public.project_stages;
create policy "Users can update their own project stages"
    on public.project_stages for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own project stages" on public.project_stages;
create policy "Users can delete their own project stages"
    on public.project_stages for delete using (auth.uid() = user_id);

-- Updated_at timestamp triggers
drop trigger if exists set_projects_updated_at on public.projects;
create trigger set_projects_updated_at
    before update on public.projects
    for each row execute function public.handle_updated_at();

drop trigger if exists set_project_stages_updated_at on public.project_stages;
create trigger set_project_stages_updated_at
    before update on public.project_stages
    for each row execute function public.handle_updated_at();

-- Trigger: Automatically seed 3 Stages when a project is inserted
create or replace function public.initialize_project_stages()
returns trigger as $$
begin
    insert into public.project_stages (
        project_id, user_id, stage_number, stage_name, status, progress_percent,
        idea_title, problem_description, solution_description, target_beneficiaries
    ) values (
        new.id, new.user_id, 1, 'Idea Development', 'In Progress', 30,
        new.title, new.problem_statement, new.proposed_solution, new.target_beneficiaries
    ) on conflict (project_id, stage_number) do nothing;

    insert into public.project_stages (
        project_id, user_id, stage_number, stage_name, status, progress_percent
    ) values (
        new.id, new.user_id, 2, 'Prototype Development', 'Not Started', 0
    ) on conflict (project_id, stage_number) do nothing;

    insert into public.project_stages (
        project_id, user_id, stage_number, stage_name, status, progress_percent
    ) values (
        new.id, new.user_id, 3, 'Product and Market Readiness', 'Not Started', 0
    ) on conflict (project_id, stage_number) do nothing;

    return new;
end;
$$ language plpgsql security definer;

drop trigger if exists auto_init_stages on public.projects;
create trigger auto_init_stages
    after insert on public.projects
    for each row execute function public.initialize_project_stages();
