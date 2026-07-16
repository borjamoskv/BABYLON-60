UPDATE `frames` SET `is_hidden` = 0 WHERE `is_hidden` = 1 AND `parent_frame_id` IS NULL;
