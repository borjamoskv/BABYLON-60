DELETE FROM `notifications` WHERE `notification_type` = 'child_landed' AND `read_at` IS NOT NULL;
