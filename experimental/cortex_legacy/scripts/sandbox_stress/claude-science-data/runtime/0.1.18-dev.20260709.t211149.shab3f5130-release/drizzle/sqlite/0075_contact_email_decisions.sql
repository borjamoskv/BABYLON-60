CREATE TABLE `contact_email_decisions` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`decision` text NOT NULL,
	`email` text,
	`notice_version` text(64) NOT NULL,
	`notice_text` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_contact_email_decisions_user` ON `contact_email_decisions` (`user_id`,`created_at`);
