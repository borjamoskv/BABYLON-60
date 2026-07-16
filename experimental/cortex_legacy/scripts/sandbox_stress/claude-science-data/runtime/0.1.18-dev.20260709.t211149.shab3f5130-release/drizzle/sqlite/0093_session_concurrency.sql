CREATE TABLE `session_concurrency` (
	`root_frame_id` text(36) PRIMARY KEY NOT NULL,
	`max_concurrent` integer NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_compute_usage_root_open` ON `compute_usage` (`root_frame_id`) WHERE ended_at IS NULL;
