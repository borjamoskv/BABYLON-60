INSERT INTO `mcp_tool_grants` (`id`, `user_id`, `server_id`, `tool_name`, `decision`, `created_at`)
SELECT
  lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' ||
    substr(lower(hex(randomblob(2))), 2) || '-' ||
    substr('89ab', 1 + (abs(random()) % 4), 1) ||
    substr(lower(hex(randomblob(2))), 2) || '-' || lower(hex(randomblob(6))),
  g.`user_id`, d.`column1`, g.`tool_name`, g.`decision`, g.`created_at`
FROM `mcp_tool_grants` g
CROSS JOIN (VALUES
  ('bundled:biomart'), ('bundled:pubmed'), ('bundled:clinical-trials'),
  ('bundled:chembl'), ('bundled:biorxiv'), ('bundled:npi-registry'),
  ('bundled:cms-coverage'), ('bundled:variants'), ('bundled:clinical-genomics'),
  ('bundled:expression'), ('bundled:regulation'), ('bundled:protein-annotation'),
  ('bundled:rna'), ('bundled:structures-interactions'), ('bundled:omics-archives'),
  ('bundled:genes-ontologies'), ('bundled:drug-regulatory'),
  ('bundled:research-resources'), ('bundled:cellguide'),
  ('bundled:cancer-models'), ('bundled:icd-10-codes'), ('bundled:chemistry'),
  ('bundled:genomes'), ('bundled:human-genetics'), ('bundled:literature')
) AS d
WHERE g.`server_id` = 'bundled:bio' AND g.`decision` IN ('deny', 'ask')
ON CONFLICT (`user_id`, `server_id`, `tool_name`) DO UPDATE SET
  `decision` = excluded.`decision`,
  `created_at` = excluded.`created_at`
WHERE `mcp_tool_grants`.`decision` = 'allow'
   OR (`mcp_tool_grants`.`decision` = 'ask' AND excluded.`decision` = 'deny');--> statement-breakpoint
DELETE FROM `mcp_tool_grants` WHERE `server_id` = 'bundled:bio' AND `decision` = 'allow';