CREATE TABLE `safety_feedback` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`user_id` text(255) NOT NULL,
	`type` text(64) NOT NULL,
	`model` text(255),
	`reason` text,
	`response_id` text(64),
	`context_snapshot` text,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_safety_feedback_root_frame_id` ON `safety_feedback` (`root_frame_id`);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_safety_feedback_type` ON `safety_feedback` (`type`);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `ux_safety_feedback_root_frame_user_type` ON `safety_feedback` (`root_frame_id`,`user_id`,`type`);
