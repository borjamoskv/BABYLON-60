ALTER TABLE `compute_providers` ADD `max_timeout_sec` integer;
--> statement-breakpoint
ALTER TABLE `compute_providers` ADD `enabled` integer DEFAULT true NOT NULL;
