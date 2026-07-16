CREATE TABLE `memory_categories` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`name` text(64) NOT NULL,
	`name_lower` text(64) NOT NULL,
	`guidance` text NOT NULL,
	`auto_recall` integer DEFAULT true NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `memcat_user_idx` ON `memory_categories` (`user_id`);
--> statement-breakpoint
CREATE UNIQUE INDEX `memcat_user_name_idx` ON `memory_categories` (`user_id`,`name_lower`);
--> statement-breakpoint
ALTER TABLE `memories` ADD `category_id` text(36) REFERENCES memory_categories(`id`) ON DELETE SET NULL;
--> statement-breakpoint
CREATE INDEX `mem_category_idx` ON `memories` (`category_id`);