CREATE INDEX `ix_artifact_versions_slim_covering` ON `artifact_versions` (`id`,`artifact_id`,`version_number`,`frame_id`,`content_type`,`size_bytes`,`checksum`,`storage_path`,`created_at`,`agent_name`,`language`,`is_intermediate`,`parent_version_id`,`lineage_snapshot_hash`,`env_snapshot_hash`,`producing_cell_id`,`is_checkpoint`);--> statement-breakpoint
CREATE INDEX `ix_artifact_versions_artifact_version_id` ON `artifact_versions` (`artifact_id`,`version_number`,`id`);--> statement-breakpoint
ANALYZE `artifacts`;--> statement-breakpoint
ANALYZE `artifact_versions`;