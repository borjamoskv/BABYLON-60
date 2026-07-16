CREATE INDEX IF NOT EXISTS `ix_frames_vroot_cost`
  ON `frames` (coalesce(`root_frame_id`, `id`), `updated_at`, `total_cost`, `aux_cost`);
