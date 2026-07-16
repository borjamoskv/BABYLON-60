CREATE TABLE `compute_providers` (
	`name` text(128) PRIMARY KEY NOT NULL,
	`family` text(16) NOT NULL,
	`memory_md` text DEFAULT '' NOT NULL,
	`environments` text DEFAULT '[]' NOT NULL,
	`memory_rev` integer DEFAULT 0 NOT NULL,
	`scratch_root` text(512),
	`scheduler` text(16),
	`probed_at` integer,
	`data_roots` text DEFAULT '[]' NOT NULL,
	`ssh_overrides` text
);
--> statement-breakpoint
CREATE TABLE `poller_lease` (
	`provider` text(128) PRIMARY KEY NOT NULL,
	`holder` text(64) NOT NULL,
	`expires_at` integer NOT NULL
);
--> statement-breakpoint
ALTER TABLE `compute_usage` ADD `client_uuid` text(36);
--> statement-breakpoint
ALTER TABLE `compute_usage` ADD `remote_workdir` text(512);
--> statement-breakpoint
ALTER TABLE `compute_usage` ADD `remote_handle` text;
--> statement-breakpoint
ALTER TABLE `compute_usage` ADD `state` text(16) DEFAULT 'pending' NOT NULL;
--> statement-breakpoint
ALTER TABLE `compute_usage` ADD `output_specs` text;
--> statement-breakpoint
CREATE INDEX `ix_compute_usage_state` ON `compute_usage` (`state`);
