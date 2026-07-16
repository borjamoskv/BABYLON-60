ALTER TABLE `frame_messages` ADD COLUMN `msg_uuid` TEXT;
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_frame_messages_msg_uuid` ON `frame_messages` (`frame_id`, `msg_uuid`);
--> statement-breakpoint
DROP INDEX IF EXISTS `ix_frame_messages_frame_uuid`;
