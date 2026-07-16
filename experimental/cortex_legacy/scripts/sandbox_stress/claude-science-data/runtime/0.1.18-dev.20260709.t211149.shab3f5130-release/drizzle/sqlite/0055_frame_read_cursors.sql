CREATE TABLE `frame_read_cursors` (
	`root_frame_id` text(36) PRIMARY KEY NOT NULL,
	`message_uuid` text(36),
	`message_index` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);