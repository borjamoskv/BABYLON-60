INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:biomart', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_biomart_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:pubmed', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_pubmed_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:clinical-trials', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_clinical-trials_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:chembl', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_chembl_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:biorxiv', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_biorxiv_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:npi-registry', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_npi-registry_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:cms-coverage', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_cms-coverage_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:variants', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_variants_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:clinical-genomics', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_clinical-genomics_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:expression', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_expression_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:regulation', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_regulation_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:protein-annotation', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_protein-annotation_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:rna', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_rna_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:structures-interactions', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_structures-interactions_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:omics-archives', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_omics-archives_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:genes-ontologies', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_genes-ontologies_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:drug-regulatory', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_drug-regulatory_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:research-resources', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_research-resources_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';--> statement-breakpoint
INSERT OR IGNORE INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `excluded_tools`, `created_at`)
SELECT 'bundled:cellguide', `agent_name`, `user_id`, CASE WHEN `excluded_tools` IS NULL THEN NULL ELSE replace(`excluded_tools`, 'mcp_bio_', 'mcp_cellguide_') END, `created_at`
FROM `directory_attachments` WHERE `server_uuid` = 'bundled:bio';
-- The bundled:bio attachment row is RETAINED inert-but-present (finding
-- 3406921567): post-split nothing resolves bundled:bio, so the row is
-- ignored, but on rollback to a pre-split build the user's original
-- attachment + its excluded_tools protective list survive (a DELETE here
-- would let the old top-up loop re-insert a fresh row with NULL
-- excluded_tools, silently re-serving every tool the user removed).
-- Mirrors 0077's deny/ask retention.
