PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES (1);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    mtime REAL NOT NULL,
    size INTEGER NOT NULL,
    last_indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kits (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    summary TEXT
);

CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    file_id INTEGER REFERENCES files(id) ON DELETE SET NULL,
    line_start INTEGER,
    line_end INTEGER,
    parent_id INTEGER REFERENCES symbols(id) ON DELETE SET NULL,
    kit_id INTEGER REFERENCES kits(id) ON DELETE SET NULL,
    raw_declaration TEXT
);

CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind);
CREATE INDEX IF NOT EXISTS idx_symbols_parent_id ON symbols(parent_id);
CREATE INDEX IF NOT EXISTS idx_symbols_kit_id ON symbols(kit_id);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY,
    source_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    target_symbol_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
    target_text TEXT,
    UNIQUE (source_symbol_id, relation_type, target_symbol_id, target_text)
);

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_symbol_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_symbol_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);

CREATE TABLE IF NOT EXISTS docs (
    id INTEGER PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    body TEXT NOT NULL,
    UNIQUE (symbol_id, source)
);
