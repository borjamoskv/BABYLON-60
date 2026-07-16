CREATE INDEX `ix_content_snapshots_created_at` ON `content_snapshots` (`created_at`);--> statement-breakpoint
CREATE INDEX `ix_artifact_versions_lineage_snapshot_hash` ON `artifact_versions` (`lineage_snapshot_hash`);--> statement-breakpoint
CREATE INDEX `ix_artifact_versions_env_snapshot_hash` ON `artifact_versions` (`env_snapshot_hash`);