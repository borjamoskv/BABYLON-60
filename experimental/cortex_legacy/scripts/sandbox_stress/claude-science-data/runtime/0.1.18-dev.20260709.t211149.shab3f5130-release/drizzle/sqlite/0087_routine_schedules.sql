CREATE TABLE `routine_schedules` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`owner_user_id` text(255) NOT NULL,
	`label` text(120),
	`on_tick` text NOT NULL,
	`every_minutes` integer NOT NULL,
	`enabled` integer DEFAULT false NOT NULL,
	`locked_at` integer,
	`paused_reason` text,
	`next_due` integer NOT NULL,
	`tick_count` integer DEFAULT 0 NOT NULL,
	`missed_ticks` integer DEFAULT 0 NOT NULL,
	`last_fire_at` integer,
	`last_ok_at` integer,
	`idle_streak` integer DEFAULT 0 NOT NULL,
	`last_results` text,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX IF NOT EXISTS `routine_schedules_root_frame_id_unique` ON `routine_schedules` (`root_frame_id`);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_routine_due` ON `routine_schedules` (`next_due`) WHERE enabled = 1;
