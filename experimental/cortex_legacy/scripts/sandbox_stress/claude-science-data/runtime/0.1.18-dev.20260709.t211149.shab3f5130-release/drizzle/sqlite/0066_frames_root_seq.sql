-- when=1781040000000 (coordinated with #2858's ladder: 1781010000000/1781020000000
-- frozen theirs, 1781030000000 dead buffer — equal `when` = silent skip under the
-- migrator's strict <; whens are dedup keys and never move again, idx/tag only).
-- Index/triggers are IF NOT EXISTS; the ADD COLUMN cannot be guarded in the
-- sqlite dialect (no house precedent either — 0056-0059/0064 are bare ALTERs);
-- the unique when-slot is what prevents re-apply.
ALTER TABLE `frames` ADD `root_seq` integer DEFAULT 0 NOT NULL;--> statement-breakpoint
UPDATE `frames` SET `root_seq` = 1 WHERE `root_frame_id` IS NOT NULL;--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_frames_root_seq` ON `frames` (`root_frame_id`,`root_seq`);--> statement-breakpoint
CREATE TRIGGER IF NOT EXISTS `trg_frames_root_seq_ins` AFTER INSERT ON `frames`
WHEN NEW.`root_frame_id` IS NOT NULL
BEGIN
  UPDATE `frames` SET `root_seq` = (
    SELECT COALESCE(MAX(`root_seq`), 0) + 1 FROM `frames`
    WHERE `root_frame_id` = NEW.`root_frame_id`
  ) WHERE `id` = NEW.`id`;
END;--> statement-breakpoint
CREATE TRIGGER IF NOT EXISTS `trg_frames_root_seq_upd` AFTER UPDATE ON `frames`
WHEN NEW.`root_frame_id` IS NOT NULL AND NEW.`root_seq` IS OLD.`root_seq`
BEGIN
  UPDATE `frames` SET `root_seq` = (
    SELECT COALESCE(MAX(`root_seq`), 0) + 1 FROM `frames`
    WHERE `root_frame_id` = NEW.`root_frame_id`
  ) WHERE `id` = NEW.`id`;
END;