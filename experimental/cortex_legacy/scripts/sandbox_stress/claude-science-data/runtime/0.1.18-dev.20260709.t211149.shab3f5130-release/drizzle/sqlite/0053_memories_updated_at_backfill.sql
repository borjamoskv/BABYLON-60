UPDATE memories SET updated_at = created_at WHERE last_surfaced_at IS NOT NULL AND abs(updated_at - last_surfaced_at) < 1000;
