-- idx 43 is contested: PRs #1735/#1595/#1767 all target it. Whoever lands
-- 2nd-4th renumbers (file + _journal.json idx/tag + sqlite.ts JSDoc).
CREATE TABLE `canvas_drafts` (
	`artifact_id` text(36) PRIMARY KEY NOT NULL,
	`content` text NOT NULL,
	`mtime` integer NOT NULL,
	FOREIGN KEY (`artifact_id`) REFERENCES `artifacts`(`id`) ON UPDATE no action ON DELETE cascade
);
