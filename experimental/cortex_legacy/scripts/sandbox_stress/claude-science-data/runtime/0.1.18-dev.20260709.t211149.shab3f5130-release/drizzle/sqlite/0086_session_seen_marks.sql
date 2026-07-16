CREATE TABLE `session_seen_marks` (
	`root_frame_id` text(36) PRIMARY KEY NOT NULL,
	`seen_token` text(128) NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
