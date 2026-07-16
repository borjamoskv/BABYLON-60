UPDATE `artifact_versions`
SET `version_number` = (
  SELECT rn FROM (
    SELECT `id`, ROW_NUMBER() OVER (
      PARTITION BY `artifact_id` ORDER BY `created_at`, `id`
    ) AS rn
    FROM `artifact_versions`
  ) AS numbered
  WHERE numbered.`id` = `artifact_versions`.`id`
)
WHERE `artifact_id` IN (
  SELECT `artifact_id` FROM `artifact_versions`
  GROUP BY `artifact_id`, `version_number`
  HAVING COUNT(*) > 1
);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_artifact_versions_artifact_version` ON `artifact_versions` (`artifact_id`,`version_number`);
