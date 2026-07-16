ALTER TABLE `transcript_annotations` ADD `origin` text DEFAULT 'user' NOT NULL;--> statement-breakpoint
ALTER TABLE `transcript_annotations` ADD `read_at` integer;
