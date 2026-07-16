-- Relocate per-connector tool exclusions from user_agents.excluded_tools
-- to the attachment rows, so scope = (agent × connector) and exclusions
-- are cleaned up on detach. Covers BOTH attachment tables: custom MCP
-- servers (mcp_agent_assignments) and bundled/directory/local servers
-- (directory_attachments). Pre-launch → no data migration from
-- user_agents.excluded_tools; existing per-agent values are dropped when
-- that column is removed in 0021.
ALTER TABLE "mcp_agent_assignments" ADD COLUMN "excluded_tools" text NOT NULL DEFAULT '[]';
--> statement-breakpoint
ALTER TABLE "directory_attachments" ADD COLUMN "excluded_tools" text NOT NULL DEFAULT '[]';
