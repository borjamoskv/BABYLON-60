-- 0067: read-grounding records on execution_log (#2899 read-tracing arm).
-- when=1781050000000 (next rung above 0066's 1781040000000; whens are dedup
-- keys under the migrator's strict < — renumber idx/tag only if the slot is
-- contested at merge, never the when once shipped).
ALTER TABLE `execution_log` ADD `files_read` text;