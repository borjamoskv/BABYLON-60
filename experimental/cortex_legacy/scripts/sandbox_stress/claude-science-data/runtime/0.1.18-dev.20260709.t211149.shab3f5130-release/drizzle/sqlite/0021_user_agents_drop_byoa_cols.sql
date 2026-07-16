-- Finish one-agent removal: drop BYOA-era columns from user_agents.
-- excluded_tools relocated to the attachment rows in 0020; base_agent was
-- the BYOA "clone-from" reference and has no consumers in one-agent mode.
-- SQLite ≥3.35 supports ALTER TABLE DROP COLUMN directly.
ALTER TABLE "user_agents" DROP COLUMN "excluded_tools";
--> statement-breakpoint
ALTER TABLE "user_agents" DROP COLUMN "base_agent";
