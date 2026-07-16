CREATE TABLE `session_claims` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`frame_id` text(36) NOT NULL,
	`step_id` text(255),
	`claim_text` text NOT NULL,
	`entities` text,
	`source` text(32) NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_session_claims_root` ON `session_claims` (`root_frame_id`);
--> statement-breakpoint
CREATE INDEX `ix_session_claims_frame` ON `session_claims` (`frame_id`);
--> statement-breakpoint
CREATE TABLE `verification_checks` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`artifact_version_id` text(36),
	`claim_id` text(36),
	`claim` text,
	`verdict` text NOT NULL CHECK (`verdict` IN ('pass','warn','fail','inconclusive')),
	`severity` text(16),
	`evidence` text,
	`rebuttal` text,
	`reviewer_idx` integer,
	`reviewer_model` text(64),
	`reviewer_frame_id` text(36),
	`source_ref` text NOT NULL,
	`status` text NOT NULL DEFAULT 'open' CHECK (`status` IN ('open','resolved','unaddressed')),
	`reflag_count` integer,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`claim_id`) REFERENCES `session_claims`(`id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE INDEX `ix_verification_checks_root` ON `verification_checks` (`root_frame_id`);
--> statement-breakpoint
CREATE INDEX `ix_verification_checks_status` ON `verification_checks` (`root_frame_id`,`status`);
--> statement-breakpoint
CREATE INDEX `ix_verification_checks_claim` ON `verification_checks` (`claim_id`);
