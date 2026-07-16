ALTER TABLE compute_providers ADD COLUMN scratch_root_source text NOT NULL DEFAULT 'probe';--> statement-breakpoint
ALTER TABLE compute_providers ADD COLUMN home text;--> statement-breakpoint
ALTER TABLE compute_providers ADD COLUMN scratch_root_revalidate_failed_at integer;
