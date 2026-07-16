CREATE INDEX `mem_src_frame_idx` ON `memories` (`source_frame_id`);--> statement-breakpoint
CREATE INDEX `mem_subj_ver_idx` ON `memories` (`subject_version_id`);--> statement-breakpoint
CREATE INDEX `mem_superseded_idx` ON `memories` (`superseded_by`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_latest_version_id` ON `artifacts` (`latest_version_id`);
