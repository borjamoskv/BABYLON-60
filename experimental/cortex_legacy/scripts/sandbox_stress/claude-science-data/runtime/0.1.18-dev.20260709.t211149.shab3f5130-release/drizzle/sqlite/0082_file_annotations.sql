CREATE TABLE IF NOT EXISTS `file_annotations` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`project_id` text(255) NOT NULL,
	`host` text(128) NOT NULL,
	`path` text(4096) NOT NULL,
	`note` text DEFAULT '' NOT NULL,
	`author` text(64) DEFAULT 'user' NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_file_annotations_project_host_path` ON `file_annotations` (`project_id`,`host`,`path`);
