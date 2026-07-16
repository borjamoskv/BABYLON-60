ALTER TABLE compute_usage ADD COLUMN root_frame_id text(36);--> statement-breakpoint
ALTER TABLE compute_usage ADD COLUMN result text;--> statement-breakpoint
CREATE INDEX IF NOT EXISTS ix_compute_usage_root_frame_id ON compute_usage (root_frame_id);--> statement-breakpoint
UPDATE compute_usage SET root_frame_id = (SELECT root_frame_id FROM frames WHERE frames.id = compute_usage.frame_id) WHERE root_frame_id IS NULL AND frame_id IS NOT NULL;