CREATE TABLE IF NOT EXISTS `queued_user_messages` (
	`seq` integer PRIMARY KEY NOT NULL,
	`frame_id` text(36) NOT NULL,
	`payload` text NOT NULL,
	`intent_id` text NOT NULL,
	`state` text DEFAULT 'queued' NOT NULL,
	`resolved_at` integer,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `queued_user_messages_intent_id_unique` ON `queued_user_messages` (`intent_id`);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_queued_user_messages_frame` ON `queued_user_messages` (`frame_id`);