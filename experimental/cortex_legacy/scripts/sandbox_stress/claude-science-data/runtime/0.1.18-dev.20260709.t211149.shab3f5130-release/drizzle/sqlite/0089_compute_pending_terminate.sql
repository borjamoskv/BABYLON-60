CREATE TABLE IF NOT EXISTS `compute_pending_terminate` (
	`sandbox_id` text(255) PRIMARY KEY NOT NULL,
	`provider` text(128) NOT NULL,
	`enqueued_at` integer NOT NULL,
	`attempts` integer DEFAULT 0 NOT NULL
);
