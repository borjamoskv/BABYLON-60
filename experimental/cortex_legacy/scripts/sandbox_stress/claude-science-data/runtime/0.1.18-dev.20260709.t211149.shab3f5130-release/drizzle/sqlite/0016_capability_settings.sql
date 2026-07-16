CREATE TABLE `capability_settings` (
	`user_id` text(255) NOT NULL,
	`kind` text(32) NOT NULL,
	`key` text(255) NOT NULL,
	`enabled` integer DEFAULT true NOT NULL,
	`updated_at` integer NOT NULL,
	PRIMARY KEY(`user_id`, `kind`, `key`)
);
--> statement-breakpoint
CREATE INDEX `ix_capability_settings_user_kind` ON `capability_settings` (`user_id`,`kind`);