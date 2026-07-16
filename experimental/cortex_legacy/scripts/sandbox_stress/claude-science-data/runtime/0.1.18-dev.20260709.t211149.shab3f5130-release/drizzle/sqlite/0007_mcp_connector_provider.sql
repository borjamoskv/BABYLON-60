ALTER TABLE custom_mcp_servers ADD COLUMN source text DEFAULT 'custom' NOT NULL;
--> statement-breakpoint
CREATE TABLE `directory_attachments` (
	`server_uuid` text(36) NOT NULL,
	`agent_name` text(255) NOT NULL,
	`user_id` text(255) NOT NULL,
	`created_at` integer NOT NULL,
	PRIMARY KEY(`server_uuid`, `agent_name`, `user_id`)
);
--> statement-breakpoint
CREATE INDEX `ix_directory_attachments_agent_name` ON `directory_attachments` (`agent_name`);--> statement-breakpoint
CREATE INDEX `ix_directory_attachments_user_id` ON `directory_attachments` (`user_id`);--> statement-breakpoint
INSERT INTO `directory_attachments` (`server_uuid`, `agent_name`, `user_id`, `created_at`)
  SELECT a.`mcp_server_id`, a.`agent_name`, a.`user_id`, a.`created_at`
  FROM `mcp_agent_assignments` a
  JOIN `custom_mcp_servers` s ON s.`id` = a.`mcp_server_id`
  WHERE s.`source` = 'directory';--> statement-breakpoint
DELETE FROM `custom_mcp_servers` WHERE `source` = 'directory';
--> statement-breakpoint
CREATE TABLE `mcp_tool_grants` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`server_id` text(255) NOT NULL,
	`tool_name` text(255) NOT NULL,
	`decision` text NOT NULL,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_mcp_tool_grants_user_id` ON `mcp_tool_grants` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `ux_mcp_tool_grants_user_server_tool` ON `mcp_tool_grants` (`user_id`,`server_id`,`tool_name`);--> statement-breakpoint
ALTER TABLE `oauth_tokens` ADD COLUMN `client_id` text(255);
