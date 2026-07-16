CREATE INDEX `ix_frames_updated_at` ON `frames` (`updated_at`);--> statement-breakpoint
CREATE INDEX `ix_frames_project_task_summary` ON `frames` (`project_id`,`updated_at`) WHERE task_summary IS NOT NULL;--> statement-breakpoint
CREATE INDEX `ix_artifact_versions_parent_version_id` ON `artifact_versions` (`parent_version_id`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_created_at` ON `artifacts` (`created_at`);