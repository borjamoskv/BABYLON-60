CREATE TABLE `compute_usage` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`job_id` text(255) NOT NULL,
	`environment` text(64) NOT NULL,
	`tier_type` text(8) NOT NULL,
	`provider` text(64) NOT NULL,
	`frame_id` text(36),
	`project_id` text(36),
	`started_at` integer NOT NULL,
	`ended_at` integer,
	`expires_at` integer
);
--> statement-breakpoint
CREATE UNIQUE INDEX `uq_compute_usage_job_id` ON `compute_usage` (`job_id`);--> statement-breakpoint
CREATE INDEX `ix_compute_usage_ended_at` ON `compute_usage` (`ended_at`);--> statement-breakpoint
CREATE INDEX `ix_compute_usage_started_at` ON `compute_usage` (`started_at`);--> statement-breakpoint
CREATE INDEX `ix_compute_usage_expires_at` ON `compute_usage` (`expires_at`);
