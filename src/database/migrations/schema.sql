CREATE TABLE IF NOT EXISTS settlement_calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT NOT NULL,
    policy_limits REAL NOT NULL,
    deductible REAL NOT NULL,
    total_damages REAL NOT NULL,
    depreciation REAL NOT NULL,
    actual_cash_value REAL NOT NULL,
    replacement_cost_value REAL NOT NULL,
    settlement_amount REAL NOT NULL,
    calculation_date TEXT NOT NULL,
    notes TEXT,
    damage_items TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(id)
);

CREATE TABLE IF NOT EXISTS board_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    columns TEXT NOT NULL,  -- JSON array of column IDs
    filters TEXT NOT NULL,  -- JSON object of filter criteria
    sort_by TEXT,          -- Column ID to sort by
    sort_direction TEXT NOT NULL DEFAULT 'asc',
    is_default BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES boards(id)
); 