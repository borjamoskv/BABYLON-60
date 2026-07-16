CREATE TABLE IF NOT EXISTS `frame_system_prompts` (
	`frame_id` text(36) PRIMARY KEY NOT NULL,
	`hash` text NOT NULL,
	`updated_at` integer NOT NULL,
	`payload` text NOT NULL,
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS `frame_branch_archives` (
	`frame_id` text(36) NOT NULL,
	`branch_id` text NOT NULL,
	`payload` text NOT NULL,
	`updated_at` integer NOT NULL,
	PRIMARY KEY(`frame_id`, `branch_id`),
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);