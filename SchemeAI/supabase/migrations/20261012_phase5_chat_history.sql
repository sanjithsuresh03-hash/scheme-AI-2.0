-- ============================================================================
-- SchemeAI — Phase 5 Migration: Gemini Chatbot Conversations & Messages
-- Smart India Hackathon: AI-Driven Funding & Scheme Matching
-- ============================================================================

-- Table: public.conversations
create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    title text not null default 'New Scheme Inquiry',
    language text default 'auto',
    created_at timestamptz default timezone('utc'::text, now()) not null,
    updated_at timestamptz default timezone('utc'::text, now()) not null
);

comment on table public.conversations is 'User chat conversation threads with the SchemeAI Gemini Assistant';
comment on column public.conversations.user_id is 'Authenticated owner ID from auth.users';

-- Table: public.chat_messages
create table if not exists public.chat_messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations(id) on delete cascade,
    user_id uuid not null references auth.users(id) on delete cascade,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null check (char_length(trim(content)) > 0),
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default timezone('utc'::text, now()) not null
);

comment on table public.chat_messages is 'Individual chat messages within a SchemeAI assistant conversation';

-- Indexes for fast retrieval
create index if not exists idx_conversations_user_id on public.conversations(user_id);
create index if not exists idx_conversations_updated_at on public.conversations(updated_at desc);

create index if not exists idx_chat_messages_conv_id on public.chat_messages(conversation_id);
create index if not exists idx_chat_messages_user_id on public.chat_messages(user_id);
create index if not exists idx_chat_messages_created_at on public.chat_messages(created_at asc);

-- Enable Row Level Security (RLS)
alter table public.conversations enable row level security;
alter table public.chat_messages enable row level security;

-- RLS Policies for conversations
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

-- RLS Policies for chat_messages
drop policy if exists "Users can view their own chat messages" on public.chat_messages;
create policy "Users can view their own chat messages"
    on public.chat_messages for select using (auth.uid() = user_id);

drop policy if exists "Users can insert their own chat messages" on public.chat_messages;
create policy "Users can insert their own chat messages"
    on public.chat_messages for insert with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own chat messages" on public.chat_messages;
create policy "Users can delete their own chat messages"
    on public.chat_messages for delete using (auth.uid() = user_id);

-- Automatic updated_at trigger for conversations
drop trigger if exists set_conversations_updated_at on public.conversations;
create trigger set_conversations_updated_at
    before update on public.conversations
    for each row execute function public.handle_updated_at();
