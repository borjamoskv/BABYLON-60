CREATE TABLE `memories` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`body` text NOT NULL,
	`subject_project_id` text(255),
	`subject_artifact_id` text(36),
	`subject_version_id` text(36),
	`subject_frame_id` text(36),
	`source_frame_id` text(36),
	`origin` text NOT NULL,
	`evidence` text DEFAULT 'stated' NOT NULL,
	`superseded_by` text(36),
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	`last_surfaced_at` integer,
	FOREIGN KEY (`subject_project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`subject_artifact_id`) REFERENCES `artifacts`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`subject_version_id`) REFERENCES `artifact_versions`(`id`) ON UPDATE no action ON DELETE set null,
	FOREIGN KEY (`subject_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE set null,
	FOREIGN KEY (`source_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE set null,
	FOREIGN KEY (`superseded_by`) REFERENCES `memories`(`id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE INDEX `mem_user_idx` ON `memories` (`user_id`,`superseded_by`);
--> statement-breakpoint
CREATE INDEX `mem_subj_proj_idx` ON `memories` (`subject_project_id`);
--> statement-breakpoint
CREATE INDEX `mem_subj_art_idx` ON `memories` (`subject_artifact_id`);
--> statement-breakpoint
ALTER TABLE `projects` ADD `memory_enabled` integer;
