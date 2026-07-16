CREATE TABLE `user_agents` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`name` text(32) NOT NULL,
	`display_name` text(255) NOT NULL,
	`description` text NOT NULL,
	`system_prompt` text NOT NULL,
	`icon_key` text(64) DEFAULT 'lightning' NOT NULL,
	`color_key` text(64) DEFAULT 'accent-main' NOT NULL,
	`tags` text DEFAULT '[]' NOT NULL,
	`skill_names` text DEFAULT '[]' NOT NULL,
	`base_agent` text(255),
	`enabled` integer DEFAULT true NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_user_agents_user_id` ON `user_agents` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_user_agents_user_name` ON `user_agents` (`user_id`,`name`);
