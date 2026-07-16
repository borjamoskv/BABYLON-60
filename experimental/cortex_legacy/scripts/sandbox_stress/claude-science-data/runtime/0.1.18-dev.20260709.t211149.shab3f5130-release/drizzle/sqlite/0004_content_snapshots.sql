CREATE TABLE `content_snapshots` (
	`hash` text(64) PRIMARY KEY NOT NULL,
	`content` text NOT NULL,
	`size_bytes` integer NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
ALTER TABLE `artifact_versions` ADD COLUMN `lineage_snapshot_hash` text(64);--> statement-breakpoint
ALTER TABLE `artifact_versions` ADD COLUMN `env_snapshot_hash` text(64);
