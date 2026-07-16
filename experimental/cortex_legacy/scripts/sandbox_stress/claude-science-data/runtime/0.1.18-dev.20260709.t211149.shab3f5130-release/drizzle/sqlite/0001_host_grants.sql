CREATE TABLE `host_grants` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`host_path` text(4096) NOT NULL,
	`mount_name` text(255) NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_host_grants_user_id` ON `host_grants` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_host_grants_user_path` ON `host_grants` (`user_id`,`host_path`);
