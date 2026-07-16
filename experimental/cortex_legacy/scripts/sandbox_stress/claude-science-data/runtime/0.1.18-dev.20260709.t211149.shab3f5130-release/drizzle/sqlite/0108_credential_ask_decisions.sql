CREATE TABLE `credential_ask_decisions` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`provider` text(16) NOT NULL,
	`decision` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_credential_ask_decisions_user` ON `credential_ask_decisions` (`user_id`,`provider`,`created_at`);
