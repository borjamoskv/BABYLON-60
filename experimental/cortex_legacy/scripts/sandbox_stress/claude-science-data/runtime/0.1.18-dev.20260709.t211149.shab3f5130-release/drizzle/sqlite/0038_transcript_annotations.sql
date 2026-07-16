CREATE TABLE `transcript_annotations` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`message_uuid` text(36),
	`message_index` integer NOT NULL,
	`block_index` integer DEFAULT 0 NOT NULL,
	`source` text NOT NULL,
	`tool_name` text(255),
	`anchor_text` text NOT NULL,
	`start_offset` integer,
	`end_offset` integer,
	`kind` text NOT NULL,
	`note` text DEFAULT '' NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_transcript_annotations_root` ON `transcript_annotations` (`root_frame_id`);
