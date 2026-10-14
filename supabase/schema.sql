-- ============================================================================
-- SchemeAI — Database Schema (Phase 1)
-- Smart India Hackathon Project: AI-Driven Funding & Scheme Matching for Marginalized Entrepreneurs
-- Database: Supabase PostgreSQL
-- ============================================================================

-- IMPORTANT SECURITY & COMPLIANCE NOTES:
-- 1. Authentication is handled exclusively by Supabase Auth (auth.users).
--    Passwords MUST NEVER be stored in public.profiles.
-- 2. PRIVACY COMPLIANCE: Do NOT collect or store Aadhaar numbers.
--    Do NOT store identity document contents in this database.
-- 3. Row Level Security (RLS) is strictly enabled on public.profiles so each
--    entrepreneur can only view, insert, and modify their own data.

-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- ============================================================================
-- Table: public.profiles
-- ============================================================================
create table if not exists public.profiles (
    -- Linked directly to Supabase Auth user id
    id uuid primary key references auth.users(id) on delete cascade,
    
    -- Personal & Demographic Details
    full_name text not null check (char_length(trim(full_name)) >= 2),
    email text not null check (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    mobile_number text check (mobile_number is null or mobile_number ~ '^[0-9]{10}$'),
    age integer check (age is null or (age >= 18 and age <= 120)),
    gender text check (gender is null or gender in ('Male', 'Female', 'Transgender', 'Other', 'Prefer not to say')),
    community text check (community is null or community in ('OC', 'BC', 'MBC', 'SC', 'ST', 'General', 'Other')),
    annual_income numeric(14, 2) check (annual_income is null or annual_income >= 0),
    district text,
    state text,
    education text check (education is null or education in ('Degree', 'Diploma', 'ITI', 'Other')),
    
    -- Enterprise & Readiness Criteria
    is_student boolean default false not null,
    is_registered_company boolean default false not null,
    is_dpiit_recognised boolean default false not null,
    existing_govt_funding_lakhs numeric(10, 2) default 0.00 not null check (existing_govt_funding_lakhs >= 0),
    is_first_time_entrepreneur boolean default true not null,
    is_woman_led boolean default false not null,
    preferred_stage text default 'Let AI Suggest' check (
        preferred_stage in ('Stage 1', 'Stage 2', 'Stage 3', 'Let AI Suggest')
    ),
    
    -- Timestamps
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null
);

-- Comments on table columns for schema documentation
comment on table public.profiles is 'Entrepreneur profiles for SchemeAI matching, linked to Supabase auth.users';
comment on column public.profiles.id is 'Matches auth.users(id). Enforced via foreign key & RLS.';
comment on column public.profiles.community is 'Beneficiary community (OC, BC, MBC, SC, ST) used for affirmative scheme matching.';
comment on column public.profiles.preferred_stage is 'Entrepreneurial stage: Stage 1 (Ideation), Stage 2 (Early Traction), Stage 3 (Scaling), or Let AI Suggest.';

-- Indexes for efficient queries
create index if not exists idx_profiles_community on public.profiles(community);
create index if not exists idx_profiles_state on public.profiles(state);
create index if not exists idx_profiles_stage on public.profiles(preferred_stage);
create index if not exists idx_profiles_created_at on public.profiles(created_at desc);

-- ============================================================================
-- Row Level Security (RLS) Configuration
-- ============================================================================
alter table public.profiles enable row level security;

-- Drop existing policies if re-running
drop policy if exists "Users can view their own profile" on public.profiles;
drop policy if exists "Users can insert their own profile" on public.profiles;
drop policy if exists "Users can update their own profile" on public.profiles;
drop policy if exists "Users can delete their own profile" on public.profiles;

-- 1. SELECT policy: Users can only view their own profile
create policy "Users can view their own profile"
    on public.profiles
    for select
    using (auth.uid() = id);

-- 2. INSERT policy: Users can only insert a profile with their own auth.uid()
create policy "Users can insert their own profile"
    on public.profiles
    for insert
    with check (auth.uid() = id);

-- 3. UPDATE policy: Users can only update their own profile
create policy "Users can update their own profile"
    on public.profiles
    for update
    using (auth.uid() = id)
    with check (auth.uid() = id);

-- 4. DELETE policy: Users can only delete their own profile
create policy "Users can delete their own profile"
    on public.profiles
    for delete
    using (auth.uid() = id);

-- ============================================================================
-- Trigger: Automatic updated_at timestamp update
-- ============================================================================
create or replace function public.handle_updated_at()
returns trigger as $$
begin
    new.updated_at = timezone('utc'::text, now());
    return new;
end;
$$ language plpgsql security definer;

drop trigger if exists set_updated_at on public.profiles;
create trigger set_updated_at
    before update on public.profiles
    for each row
    execute function public.handle_updated_at();

-- ============================================================================
-- Optional Helper Function: Check Profile Completion
-- ============================================================================
create or replace function public.is_profile_complete(user_id uuid)
returns boolean as $$
declare
    profile_record public.profiles%rowtype;
begin
    select * into profile_record from public.profiles where id = user_id;
    if not found then
        return false;
    end if;
    
    if profile_record.full_name is null or profile_record.community is null or profile_record.state is null then
        return false;
    end if;
    
    return true;
end;
$$ language plpgsql security definer;


-- ============================================================================
-- PHASE 2: Entrepreneur Project Submission & 3-Stage Tracking
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

-- Indexes for performance
create index if not exists idx_projects_user_id on public.projects(user_id);
create index if not exists idx_projects_category on public.projects(category);
create index if not exists idx_projects_stage on public.projects(current_stage);
create index if not exists idx_projects_created_at on public.projects(created_at desc);

create index if not exists idx_project_stages_project_id on public.project_stages(project_id);
create index if not exists idx_project_stages_user_id on public.project_stages(user_id);

-- ============================================================================
-- Row Level Security (RLS) for Phase 2 Tables
-- ============================================================================
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

-- Automatic updated_at triggers
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
    -- Stage 1: Idea Development
    insert into public.project_stages (
        project_id, user_id, stage_number, stage_name, status, progress_percent,
        idea_title, problem_description, solution_description, target_beneficiaries
    ) values (
        new.id, new.user_id, 1, 'Idea Development', 'In Progress', 30,
        new.title, new.problem_statement, new.proposed_solution, new.target_beneficiaries
    ) on conflict (project_id, stage_number) do nothing;

    -- Stage 2: Prototype Development
    insert into public.project_stages (
        project_id, user_id, stage_number, stage_name, status, progress_percent
    ) values (
        new.id, new.user_id, 2, 'Prototype Development', 'Not Started', 0
    ) on conflict (project_id, stage_number) do nothing;

    -- Stage 3: Product and Market Readiness
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


-- ============================================================================
-- PHASE 5: Gemini Chatbot Conversations & Messages
-- ============================================================================

create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    title text not null default 'New Scheme Inquiry',
    language text default 'auto',
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null
);

create table if not exists public.chat_messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null check (char_length(trim(content)) > 0),
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default timezone('utc'::text, now()) not null
);

create index if not exists idx_conversations_user_id on public.conversations(user_id);
create index if not exists idx_conversations_updated_at on public.conversations(updated_at desc);
create index if not exists idx_chat_messages_conv_id on public.chat_messages(conversation_id);
create index if not exists idx_chat_messages_user_id on public.chat_messages(user_id);
create index if not exists idx_chat_messages_created_at on public.chat_messages(created_at asc);

alter table public.conversations enable row level security;
alter table public.chat_messages enable row level security;

drop policy if exists "Users can view their own conversations" on public.conversations;
create policy "Users can view their own conversations"
    on public.conversations for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own conversations" on public.conversations;
create policy "Users can insert their own conversations"
    on public.conversations for insert with check (auth.uid() = user_id);

drop policy if exists "Users can update their own conversations" on public.conversations;
create policy "Users can update their own conversations"
    on public.conversations for update using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own conversations" on public.conversations;
create policy "Users can delete their own conversations"
    on public.conversations for delete using (auth.uid() = user_id);

drop policy if exists "Users can view their own chat messages" on public.chat_messages;
create policy "Users can view their own chat messages"
    on public.chat_messages for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own chat messages" on public.chat_messages;
create policy "Users can insert their own chat messages"
    on public.chat_messages for insert with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own chat messages" on public.chat_messages;
create policy "Users can delete their own chat messages"
    on public.chat_messages for delete using (auth.uid() = user_id);

drop trigger if exists set_conversations_updated_at on public.conversations;
create trigger set_conversations_updated_at
    before update on public.conversations
    for each row execute function public.handle_updated_at();


-- ============================================================================
-- PHASE 6: Application Roadmap & Document Checklist Progress
-- ============================================================================

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

create index if not exists idx_roadmap_user_scheme on public.user_scheme_roadmap_progress(user_id, scheme_id);
create index if not exists idx_roadmap_updated_at on public.user_scheme_roadmap_progress(updated_at desc);
create index if not exists idx_checklist_user_scheme on public.user_scheme_checklist_progress(user_id, scheme_id);
create index if not exists idx_checklist_updated_at on public.user_scheme_checklist_progress(updated_at desc);

alter table public.user_scheme_roadmap_progress enable row level security;
alter table public.user_scheme_checklist_progress enable row level security;

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

drop trigger if exists set_roadmap_updated_at on public.user_scheme_roadmap_progress;
create trigger set_roadmap_updated_at
    before update on public.user_scheme_roadmap_progress
    for each row execute function public.handle_updated_at();

drop trigger if exists set_checklist_updated_at on public.user_scheme_checklist_progress;
create trigger set_checklist_updated_at
    before update on public.user_scheme_checklist_progress
    for each row execute function public.handle_updated_at();



