-- =============================================================
-- Milestone C: Project Dependency Graph
-- Run in Supabase SQL Editor
-- =============================================================

-- 1. Table for project dependencies (graph edges)
CREATE TABLE IF NOT EXISTS project_relations (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_id      TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  to_id        TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  relation     TEXT DEFAULT 'depends_on',
  -- relation types: depends_on | spawned_from | part_of | uses | related
  note         TEXT,
  created_at   TIMESTAMPTZ DEFAULT now(),
  UNIQUE (from_id, to_id, relation)
);

-- 2. RLS
ALTER TABLE project_relations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read_relations" ON project_relations FOR SELECT USING (true);
CREATE POLICY "service_insert_relations" ON project_relations FOR INSERT WITH CHECK (true);

-- 3. Add `action_taken` field to signals (for Milestone C)
ALTER TABLE signals ADD COLUMN IF NOT EXISTS action_taken TEXT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS action_result TEXT;

-- 4. Seed initial relations (based on our projects analysis)
INSERT INTO project_relations (from_id, to_id, relation, note) VALUES
  -- Monitoring Hub is the core of everything
  ('tgaggregator',           'knowledge-hub-unified', 'part_of',      'Aggregator feeds Hub'),
  ('interest-monitoring-loop', 'knowledge-hub-unified', 'part_of',   'Loop feeds Hub'),
  ('мой-дашборд',             'knowledge-hub-unified', 'part_of',    'Dashboard visualizes Hub'),

  -- AI Agent ecosystem
  ('самосовершенствующиеся-агенты', 'skills',         'uses',        'Agents use skill modules'),
  ('skills',                'ai-agent-core-workspace', 'part_of',     'Skills live in core workspace'),
  ('antigravity-dashboard-workspace', 'ai-agent-core-workspace', 'part_of', null),

  -- Tech radar & map feed the skills pipeline
  ('карта-технологий',       'skills',                'spawned_from', 'Map inspired skill ideas'),
  ('tech-radar-skill',       'skills',                'spawned_from', 'Tech Radar → skill candidates'),

  -- CoPaw feeds monitoring
  ('copaw-бот',              'tgaggregator',          'uses',        'CoPaw sends signals to aggregator'),

  -- Idea Generator relates to knowledge hub
  ('генератор-идей',         'knowledge-hub-unified', 'related',     null),

  -- Work projects use AI agent workspace
  ('ии-агент-для-гимназии',  'ai-agent-core-workspace', 'uses',     'Gymnasium AI built on core stack'),
  ('grant-presentation',     'ии-агент-для-гимназии', 'related',    'Grant supports AI agent project'),
  ('gymnasium-landing',      'ии-агент-для-гимназии', 'related',    null),
  ('smartmeeting-backend',   'ai-agent-core-workspace', 'uses',     'SmartMeeting is an agent skill'),
  ('system-interest-map',    'interest-monitoring-loop', 'spawned_from', 'System map grew from loop analysis')

ON CONFLICT (from_id, to_id, relation) DO NOTHING;

SELECT count(*) AS relations_seeded FROM project_relations;
