CREATE TABLE `annotations` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`project_id` text(255) NOT NULL,
	`target_kind` text(16) NOT NULL,
	`target_key` text(4352) NOT NULL,
	`label_idx` integer NOT NULL,
	`content_checksum` text(64),
	`body` text NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX IF NOT EXISTS `ix_annotations_project_target` ON `annotations` (`project_id`,`target_key`);
--> statement-breakpoint
INSERT INTO `annotations`
  (`id`, `project_id`, `target_kind`, `target_key`, `label_idx`,
   `content_checksum`, `body`, `created_at`, `updated_at`)
SELECT
  coalesce(json_extract(a.value, '$.id'), lower(hex(randomblob(16)))),
  art.project_id,
  'artifact',
  'av:' || av.id,
  max(
    a.key,
    CASE
      WHEN unicode(json_extract(a.value,'$.label')) BETWEEN 9312 AND 9331
        THEN unicode(json_extract(a.value,'$.label')) - 9312
      WHEN substr(json_extract(a.value,'$.label'),1,1) = '('
        THEN CAST(trim(json_extract(a.value,'$.label'),'()') AS integer) - 1
      ELSE a.key
    END
  ),
  av.checksum,
  a.value,
  coalesce(
    CAST(strftime('%s', json_extract(a.value, '$.created_at')) AS integer) * 1000,
    av.created_at
  ),
  NULL
FROM artifact_versions av
JOIN artifacts art ON art.id = av.artifact_id
JOIN json_each(av.annotations) a
WHERE av.annotations IS NOT NULL
  AND json_type(av.annotations) = 'array';
--> statement-breakpoint
INSERT INTO `annotations`
  (`id`, `project_id`, `target_kind`, `target_key`, `label_idx`,
   `content_checksum`, `body`, `created_at`, `updated_at`)
SELECT
  fa.id,
  fa.project_id,
  CASE WHEN fa.host = 'local' THEN 'local' ELSE 'remote' END,
  'file:' || replace(replace(fa.host, '%', '%25'), ':', '%3A') || ':' || fa.path,
  fa.idx,
  NULL,
  json_object(
    'id', fa.id,
    'label', CASE WHEN fa.idx < 20 THEN char(9312 + fa.idx)
                  ELSE '(' || (fa.idx + 1) || ')' END,
    'type', 'point',
    'text', fa.note,
    'x_percent', NULL,
    'y_percent', NULL,
    'created_at',
      strftime('%Y-%m-%dT%H:%M:%fZ', fa.created_at / 1000.0, 'unixepoch')
  ),
  fa.created_at,
  NULL
FROM (
  SELECT *, row_number() OVER
    (PARTITION BY project_id, host, path ORDER BY created_at, id) - 1 AS idx
  FROM file_annotations
) fa;
--> statement-breakpoint
DROP TABLE IF EXISTS `file_annotations`;
