CREATE TABLE `execution_log` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`frame_id` text(36) NOT NULL,
	`cell_index` integer NOT NULL,
	`kernel_id` text(36) NOT NULL,
	`conda_env` text(255) NOT NULL,
	`language` text(16) NOT NULL,
	`source` text NOT NULL,
	`stdout` text,
	`stderr` text,
	`exit_status` text(16) NOT NULL,
	`created_at` integer NOT NULL,
	`files_written` text,
	`error_lineno` integer,
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_execution_log_frame` ON `execution_log` (`frame_id`,`cell_index`);--> statement-breakpoint
ALTER TABLE `artifact_versions` ADD COLUMN `producing_cell_id` text(36);--> statement-breakpoint
ALTER TABLE `artifact_versions` ADD COLUMN `cell_sources` text;--> statement-breakpoint
ALTER TABLE `artifact_versions` ADD COLUMN `is_checkpoint` integer DEFAULT 0;