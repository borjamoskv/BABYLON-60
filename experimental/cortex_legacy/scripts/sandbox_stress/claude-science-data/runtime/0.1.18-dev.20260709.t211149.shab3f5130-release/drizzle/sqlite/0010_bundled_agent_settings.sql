CREATE TABLE `bundled_agent_settings` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`agent_name` text(255) NOT NULL,
	`enabled` integer DEFAULT true NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_bundled_agent_settings_user_id` ON `bundled_agent_settings` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_bundled_agent_settings_user_agent` ON `bundled_agent_settings` (`user_id`,`agent_name`);
