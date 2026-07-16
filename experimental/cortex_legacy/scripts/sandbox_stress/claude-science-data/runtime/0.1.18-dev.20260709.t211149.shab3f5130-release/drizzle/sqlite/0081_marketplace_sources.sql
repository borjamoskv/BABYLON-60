CREATE TABLE IF NOT EXISTS `marketplace_sources` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`slug` text(255) NOT NULL,
	`kind` text NOT NULL,
	`marketplace_name` text(255) NOT NULL,
	`pinned_sha` text(40) NOT NULL,
	`license` text(100) NOT NULL,
	`offered_skills` text,
	`created_at` integer NOT NULL,
	`last_imported_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `ux_marketplace_sources_user_slug` ON `marketplace_sources` (`user_id`,`slug`);
