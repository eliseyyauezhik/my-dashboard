-- =============================================================
-- Phase 6 Milestone A: Knowledge Base Schema Migration
-- Run this in Supabase SQL Editor (https://supabase.com → SQL Editor)
-- =============================================================

-- 1. Enrich projects table with grouping & life area columns
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS life_area   TEXT,
  ADD COLUMN IF NOT EXISTS group_id    TEXT,
  ADD COLUMN IF NOT EXISTS group_title TEXT,
  ADD COLUMN IF NOT EXISTS priority    INTEGER DEFAULT 50;

-- 2. Create ideas table
CREATE TABLE IF NOT EXISTS ideas (
  id              TEXT PRIMARY KEY,
  title           TEXT NOT NULL,
  description     TEXT,
  tags            TEXT[],
  priority        TEXT DEFAULT 'medium',
  life_area       TEXT,
  theme           TEXT,
  theme_label     TEXT,
  route           TEXT,
  route_label     TEXT,
  related_project TEXT,
  related_project_id TEXT,
  relevance_score INTEGER DEFAULT 50,
  next_step       TEXT,
  added_date      DATE,
  status          TEXT DEFAULT 'open',
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 3. Create notes table
CREATE TABLE IF NOT EXISTS notes (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  content         TEXT,
  tags            TEXT[],
  life_area       TEXT,
  theme           TEXT,
  source          TEXT,
  source_url      TEXT,
  related_project TEXT,
  is_actionable   BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 4. Create goals table
CREATE TABLE IF NOT EXISTS goals (
  id              TEXT PRIMARY KEY,
  title           TEXT NOT NULL,
  description     TEXT,
  life_area       TEXT NOT NULL,
  status          TEXT DEFAULT 'active',
  focus_themes    TEXT[],
  project_ids     TEXT[],
  target_date     DATE,
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- 5. Enable RLS on new tables
ALTER TABLE ideas  ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes  ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals  ENABLE ROW LEVEL SECURITY;

-- 6. Create read policies for anon key
CREATE POLICY "anon_read_ideas" ON ideas FOR SELECT USING (true);
CREATE POLICY "anon_read_notes" ON notes FOR SELECT USING (true);
CREATE POLICY "anon_read_goals" ON goals FOR SELECT USING (true);

-- 7. Create insert policies (for service_role / n8n bot)
CREATE POLICY "service_insert_ideas" ON ideas FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_notes" ON notes FOR INSERT WITH CHECK (true);
CREATE POLICY "service_insert_goals" ON goals FOR INSERT WITH CHECK (true);

-- 8. Create update policies
CREATE POLICY "service_update_ideas" ON ideas FOR UPDATE USING (true);
CREATE POLICY "service_update_notes" ON notes FOR UPDATE USING (true);
CREATE POLICY "service_update_goals" ON goals FOR UPDATE USING (true);

SELECT 'Migration complete! Tables: ideas, notes, goals created. Projects enriched.' AS result;
