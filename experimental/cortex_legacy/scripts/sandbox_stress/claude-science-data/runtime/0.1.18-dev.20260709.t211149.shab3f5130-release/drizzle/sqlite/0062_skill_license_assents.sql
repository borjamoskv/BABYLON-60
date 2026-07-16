CREATE TABLE `skill_license_assents` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`org_id` text(255),
	`resource_key` text(255) NOT NULL,
	`skill_name` text(255) NOT NULL,
	`decision` text NOT NULL,
	`notice_version` text(64) NOT NULL,
	`notice_text` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_skill_license_assents_user_resource` ON `skill_license_assents` (`user_id`,`resource_key`,`created_at`);
