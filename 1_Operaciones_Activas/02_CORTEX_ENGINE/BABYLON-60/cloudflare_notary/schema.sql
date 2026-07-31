DROP TABLE IF EXISTS bft_seals;

CREATE TABLE bft_seals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  node_id TEXT NOT NULL,
  parent_id TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bft_seals_node_id ON bft_seals(node_id);
