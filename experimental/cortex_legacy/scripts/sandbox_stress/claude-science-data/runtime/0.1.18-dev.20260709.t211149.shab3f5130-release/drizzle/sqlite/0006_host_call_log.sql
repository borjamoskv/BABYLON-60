CREATE TABLE IF NOT EXISTS `host_call_log` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`execution_log_id` text(36) NOT NULL,
	`seq` integer NOT NULL,
	`method` text(64) NOT NULL,
	`args_json` text NOT NULL,
	`derivable` integer DEFAULT 0 NOT NULL,
	`data_inline` text,
	`data_ref` text,
	`error` text,
	`bytes` integer NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`execution_log_id`) REFERENCES `execution_log`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_host_call_log_by_cell` ON `host_call_log` (`execution_log_id`,`seq`);
