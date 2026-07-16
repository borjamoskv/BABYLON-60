-- ⌘K name-bypass covering index (port of codon 74567e7c / v84).
-- workItems.searchWorkItemsAsFrameData evaluates `name/task_summary LIKE
-- '%q%'` over this compact partial index (via INDEXED BY) instead of the
-- wide frames table, whose rows drag the context_data blob — measured
-- 52 ms -> 1.6 ms per keystroke on a 5k-row wide-table fixture. `id` makes
-- the id-only scan covering; agent_name/is_hidden keep the concierge/hidden
-- filters in-index; the partial WHERE mirrors the bench listing's fixed
-- filters (_wiWhere).
CREATE INDEX IF NOT EXISTS `ix_frames_bench_name_search`
    ON `frames` (`project_id`,`name`,`task_summary`,`updated_at`,`agent_name`,`is_hidden`,`id`)
    WHERE parent_frame_id IS NULL AND task_summary IS NOT NULL;