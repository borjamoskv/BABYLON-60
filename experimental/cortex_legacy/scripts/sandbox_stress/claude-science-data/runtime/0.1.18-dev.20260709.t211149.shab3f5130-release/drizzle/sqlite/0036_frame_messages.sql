CREATE TABLE `frame_messages` (
	`frame_id` text(36) NOT NULL,
	`idx` integer NOT NULL,
	`msg_json` text NOT NULL,
	PRIMARY KEY(`frame_id`, `idx`),
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
