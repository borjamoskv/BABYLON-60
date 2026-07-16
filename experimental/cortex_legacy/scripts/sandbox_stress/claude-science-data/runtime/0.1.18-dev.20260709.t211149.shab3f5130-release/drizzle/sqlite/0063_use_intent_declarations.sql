CREATE TABLE `use_intent_declarations` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`org_id` text(255),
	`intent` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_use_intent_declarations_user` ON `use_intent_declarations` (`user_id`,`created_at`);
