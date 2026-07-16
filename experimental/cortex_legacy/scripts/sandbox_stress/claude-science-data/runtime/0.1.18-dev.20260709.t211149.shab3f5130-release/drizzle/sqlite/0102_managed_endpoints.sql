CREATE TABLE `managed_endpoints` (
	`name` text(128) PRIMARY KEY NOT NULL,
	`url` text(2048) NOT NULL,
	`port` integer NOT NULL,
	`credential_name` text(128),
	`skill_name` text(128) NOT NULL,
	`start_script` text NOT NULL,
	`stop_script` text NOT NULL,
	`live_path` text(512) NOT NULL,
	`approved_script_hash` text(64) NOT NULL,
	`state` text(16) DEFAULT 'stopped' NOT NULL,
	`state_changed_at` integer,
	`last_error` text,
	`transcript` text,
	`created_at` integer NOT NULL
);
