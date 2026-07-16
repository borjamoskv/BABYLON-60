CREATE TABLE IF NOT EXISTS `frame_backfill_poison` (
  `frame_id` text(36) PRIMARY KEY NOT NULL,
  `fail_count` integer NOT NULL DEFAULT 0,
  `terminal` integer NOT NULL DEFAULT 0,
  `reason` text,
  `updated_at` integer NOT NULL
);
