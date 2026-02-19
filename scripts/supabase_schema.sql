# Supabase Migration Script (SQL)
# You can run this directly in the Supabase SQL Editor if the automated script fails locally.

-- Create critical tables if they don't exist (simplified)
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    company_name TEXT,
    status TEXT NOT NULL DEFAULT 'NEW',
    score REAL DEFAULT 0.0,
    segment TEXT,
    personalized_hook TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    status TEXT DEFAULT 'To Do',
    priority TEXT DEFAULT 'Medium',
    lead_id TEXT REFERENCES leads(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Allow Anon (Frontend) Access
CREATE POLICY "Enable access for anon" ON leads FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable access for anon" ON tasks FOR ALL TO anon USING (true) WITH CHECK (true);

-- Allow Service Role (Backend) Access
CREATE POLICY "Enable access for service_role" ON leads FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Enable access for service_role" ON tasks FOR ALL TO service_role USING (true) WITH CHECK (true);
