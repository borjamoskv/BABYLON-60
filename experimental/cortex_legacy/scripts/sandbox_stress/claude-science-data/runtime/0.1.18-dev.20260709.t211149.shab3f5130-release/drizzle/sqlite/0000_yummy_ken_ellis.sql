CREATE TABLE `agent_skill_assignments` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`skill_id` text(36) NOT NULL,
	`agent_name` text(255) NOT NULL,
	`user_id` text(255) NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`skill_id`) REFERENCES `custom_skills`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_agent_skill_assignments_skill_id` ON `agent_skill_assignments` (`skill_id`);--> statement-breakpoint
CREATE INDEX `ix_agent_skill_assignments_agent_name` ON `agent_skill_assignments` (`agent_name`);--> statement-breakpoint
CREATE INDEX `ix_agent_skill_assignments_user_id` ON `agent_skill_assignments` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_agent_skill_user` ON `agent_skill_assignments` (`skill_id`,`agent_name`,`user_id`);--> statement-breakpoint
CREATE TABLE `agents` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`name` text(255) NOT NULL,
	`url` text(512) NOT NULL,
	`description` text,
	`parameters` text,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `agents_name_unique` ON `agents` (`name`);--> statement-breakpoint
CREATE INDEX `ix_agents_name` ON `agents` (`name`);--> statement-breakpoint
CREATE TABLE `anthropic_api_keys` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`encrypted_api_key` text NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `anthropic_api_keys_user_id_unique` ON `anthropic_api_keys` (`user_id`);--> statement-breakpoint
CREATE INDEX `ix_anthropic_api_keys_user_id` ON `anthropic_api_keys` (`user_id`);--> statement-breakpoint
CREATE TABLE `artifact_dependencies` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`artifact_version_id` text(36) NOT NULL,
	`depends_on_version_id` text(36) NOT NULL,
	`reference_name` text(255),
	`created_at` integer NOT NULL,
	FOREIGN KEY (`artifact_version_id`) REFERENCES `artifact_versions`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`depends_on_version_id`) REFERENCES `artifact_versions`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_artifact_deps_version` ON `artifact_dependencies` (`artifact_version_id`);--> statement-breakpoint
CREATE INDEX `ix_artifact_deps_depends_on` ON `artifact_dependencies` (`depends_on_version_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_artifact_deps_version_pair` ON `artifact_dependencies` (`artifact_version_id`,`depends_on_version_id`);--> statement-breakpoint
CREATE TABLE `artifact_folders` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`project_id` text(255) NOT NULL,
	`parent_id` text(36),
	`name` text(255) NOT NULL,
	`sort_order` integer NOT NULL,
	`root_frame_id` text(36),
	`is_conversation_folder` integer NOT NULL,
	`is_user_uploads_folder` integer NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`parent_id`) REFERENCES `artifact_folders`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE INDEX `ix_artifact_folders_project_id` ON `artifact_folders` (`project_id`);--> statement-breakpoint
CREATE INDEX `ix_artifact_folders_parent_id` ON `artifact_folders` (`parent_id`);--> statement-breakpoint
CREATE INDEX `ix_artifact_folders_root_frame_id` ON `artifact_folders` (`root_frame_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `ix_folders_project_parent_name` ON `artifact_folders` (`project_id`,`parent_id`,`name`);--> statement-breakpoint
CREATE INDEX `ix_folders_parent_order` ON `artifact_folders` (`parent_id`,`sort_order`);--> statement-breakpoint
CREATE INDEX `ix_folders_project_root_frame` ON `artifact_folders` (`project_id`,`root_frame_id`);--> statement-breakpoint
CREATE TABLE `artifact_versions` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`artifact_id` text(36) NOT NULL,
	`version_number` integer NOT NULL,
	`frame_id` text(36),
	`content_type` text(100) NOT NULL,
	`size_bytes` integer NOT NULL,
	`checksum` text(64) NOT NULL,
	`storage_path` text(512) NOT NULL,
	`created_at` integer NOT NULL,
	`extracted_code` text,
	`code_description` text,
	`lineage_messages` text,
	`agent_name` text(255),
	`language` text(50),
	`is_intermediate` integer NOT NULL,
	`dependency_mappings` text,
	`environment_snapshot` text,
	`annotations` text,
	`parent_version_id` text(36),
	FOREIGN KEY (`artifact_id`) REFERENCES `artifacts`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_artifact_versions_artifact_id` ON `artifact_versions` (`artifact_id`);--> statement-breakpoint
CREATE INDEX `ix_artifact_versions_frame_id` ON `artifact_versions` (`frame_id`);--> statement-breakpoint
CREATE TABLE `artifacts` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`project_id` text(255) NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`frame_id` text(36),
	`filename` text(255) NOT NULL,
	`created_at` integer NOT NULL,
	`latest_version_id` text(36),
	`is_user_upload` integer NOT NULL,
	`is_ephemeral` integer NOT NULL,
	`folder_id` text(36),
	`sort_order` integer NOT NULL,
	`priority` text(20) DEFAULT 'unknown' NOT NULL,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`latest_version_id`) REFERENCES `artifact_versions`(`id`) ON UPDATE no action ON DELETE set null,
	FOREIGN KEY (`folder_id`) REFERENCES `artifact_folders`(`id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE INDEX `ix_artifacts_project_id` ON `artifacts` (`project_id`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_root_frame_id` ON `artifacts` (`root_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_frame_id` ON `artifacts` (`frame_id`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_is_user_upload` ON `artifacts` (`is_user_upload`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_folder_id` ON `artifacts` (`folder_id`);--> statement-breakpoint
CREATE INDEX `ix_artifacts_project_not_ephemeral` ON `artifacts` (`project_id`) WHERE is_ephemeral = 0;--> statement-breakpoint
CREATE INDEX `ix_artifacts_conversation_priority` ON `artifacts` (`project_id`,`root_frame_id`,`priority`);--> statement-breakpoint
CREATE TABLE `cloud_credentials` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`provider` text(16) NOT NULL,
	`name` text(128) NOT NULL,
	`credential_type` text(32) NOT NULL,
	`encrypted_credentials` text NOT NULL,
	`encrypted_refresh_token` text,
	`token_expires_at` integer,
	`default_bucket` text(512),
	`region` text(64),
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_cloud_credentials_user_id` ON `cloud_credentials` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_cloud_credentials_user_name` ON `cloud_credentials` (`user_id`,`name`);--> statement-breakpoint
CREATE TABLE `compaction_archives` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`frame_id` text(36) NOT NULL,
	`compaction_index` integer NOT NULL,
	`message_count` integer NOT NULL,
	`token_count` integer,
	`summary` text NOT NULL,
	`messages` text NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_compaction_archives_frame_id` ON `compaction_archives` (`frame_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_compaction_archives_frame_idx` ON `compaction_archives` (`frame_id`,`compaction_index`);--> statement-breakpoint
CREATE TABLE `custom_agent_prompts` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`agent_name` text(255) NOT NULL,
	`prompt_text` text NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_custom_agent_prompts_user_id` ON `custom_agent_prompts` (`user_id`);--> statement-breakpoint
CREATE INDEX `ix_custom_agent_prompts_agent_name` ON `custom_agent_prompts` (`agent_name`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_custom_agent_prompts_user_agent` ON `custom_agent_prompts` (`user_id`,`agent_name`);--> statement-breakpoint
CREATE TABLE `custom_mcp_servers` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`name` text(64) NOT NULL,
	`description` text(1024),
	`url` text(2048) NOT NULL,
	`transport` text(32) NOT NULL,
	`oauth_server_url` text(2048),
	`client_id` text(255),
	`scopes` text(1024),
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_custom_mcp_servers_user_id` ON `custom_mcp_servers` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_custom_mcp_servers_user_name` ON `custom_mcp_servers` (`user_id`,`name`);--> statement-breakpoint
CREATE TABLE `custom_skills` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`name` text(64) NOT NULL,
	`description` text(1024) NOT NULL,
	`content` text NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_custom_skills_user_id` ON `custom_skills` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_custom_skills_user_name` ON `custom_skills` (`user_id`,`name`);--> statement-breakpoint
CREATE TABLE `events` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`frame_id` text(36) NOT NULL,
	`event_type` text(50) NOT NULL,
	`payload` text,
	`timestamp` integer NOT NULL,
	FOREIGN KEY (`frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_events_frame_id` ON `events` (`frame_id`);--> statement-breakpoint
CREATE INDEX `ix_events_event_type` ON `events` (`event_type`);--> statement-breakpoint
CREATE INDEX `ix_events_timestamp` ON `events` (`timestamp`);--> statement-breakpoint
CREATE TABLE `frames` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`parent_frame_id` text(36),
	`root_frame_id` text(36),
	`agent_name` text(255) NOT NULL,
	`status` text(50) NOT NULL,
	`input_data` text,
	`output_data` text,
	`context_data` text,
	`model` text(255),
	`effort` text(20),
	`input_tokens` integer,
	`output_tokens` integer,
	`total_cost` real,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	`completed_at` integer,
	`project_id` text(255),
	`name` text(255),
	`conversation_type` text(50) NOT NULL,
	`artifact_id` text(36),
	`task_summary` text,
	`mentioned_artifact_ids` text,
	`specialists_used` text,
	`is_hidden` integer,
	FOREIGN KEY (`parent_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE set null,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE set null,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_frames_parent_frame_id` ON `frames` (`parent_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_frames_root_frame_id` ON `frames` (`root_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_frames_agent_name` ON `frames` (`agent_name`);--> statement-breakpoint
CREATE INDEX `ix_frames_status` ON `frames` (`status`);--> statement-breakpoint
CREATE INDEX `ix_frames_project_id` ON `frames` (`project_id`);--> statement-breakpoint
CREATE INDEX `ix_frames_artifact_id` ON `frames` (`artifact_id`);--> statement-breakpoint
CREATE INDEX `ix_frames_created_at` ON `frames` (`created_at`);--> statement-breakpoint
CREATE INDEX `ix_frames_status_updated` ON `frames` (`status`,`updated_at`);--> statement-breakpoint
CREATE INDEX `ix_frames_root_by_project` ON `frames` (`project_id`,`created_at`) WHERE parent_frame_id IS NULL;--> statement-breakpoint
CREATE TABLE `mcp_agent_assignments` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`mcp_server_id` text(36) NOT NULL,
	`agent_name` text(255) NOT NULL,
	`user_id` text(255) NOT NULL,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`mcp_server_id`) REFERENCES `custom_mcp_servers`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_mcp_agent_assignments_mcp_server_id` ON `mcp_agent_assignments` (`mcp_server_id`);--> statement-breakpoint
CREATE INDEX `ix_mcp_agent_assignments_agent_name` ON `mcp_agent_assignments` (`agent_name`);--> statement-breakpoint
CREATE INDEX `ix_mcp_agent_assignments_user_id` ON `mcp_agent_assignments` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_mcp_agent_user` ON `mcp_agent_assignments` (`mcp_server_id`,`agent_name`,`user_id`);--> statement-breakpoint
CREATE TABLE `notes` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`project_id` text(255) NOT NULL,
	`user_id` text(255) NOT NULL,
	`target_type` text(50) NOT NULL,
	`target_frame_id` text(36) NOT NULL,
	`target_message_index` integer,
	`target_artifact_id` text(512),
	`content` text NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`target_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_notes_project_id` ON `notes` (`project_id`);--> statement-breakpoint
CREATE INDEX `ix_notes_target_frame_id` ON `notes` (`target_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_notes_project_type` ON `notes` (`project_id`,`target_type`);--> statement-breakpoint
CREATE INDEX `ix_notes_frame_message` ON `notes` (`target_frame_id`,`target_message_index`);--> statement-breakpoint
CREATE TABLE `notifications` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`sender_frame_id` text(36) NOT NULL,
	`recipient_frame_id` text(36) NOT NULL,
	`root_frame_id` text(36) NOT NULL,
	`notification_type` text(50) NOT NULL,
	`payload` text,
	`read_at` integer,
	`created_at` integer NOT NULL,
	FOREIGN KEY (`sender_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`recipient_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`root_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `ix_notifications_sender_frame_id` ON `notifications` (`sender_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_notifications_recipient_frame_id` ON `notifications` (`recipient_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_notifications_root_frame_id` ON `notifications` (`root_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_notifications_notification_type` ON `notifications` (`notification_type`);--> statement-breakpoint
CREATE INDEX `ix_notifications_recipient_unread` ON `notifications` (`recipient_frame_id`,`read_at`);--> statement-breakpoint
CREATE INDEX `ix_notifications_root_frame_type` ON `notifications` (`root_frame_id`,`notification_type`);--> statement-breakpoint
CREATE TABLE `oauth_tokens` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`mcp_server_id` text(36) NOT NULL,
	`encrypted_access_token` text NOT NULL,
	`encrypted_refresh_token` text,
	`token_type` text(32) NOT NULL,
	`expires_at` integer,
	`scopes` text(1024),
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	FOREIGN KEY (`mcp_server_id`) REFERENCES `custom_mcp_servers`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `oauth_tokens_mcp_server_id_unique` ON `oauth_tokens` (`mcp_server_id`);--> statement-breakpoint
CREATE INDEX `ix_oauth_tokens_user_id` ON `oauth_tokens` (`user_id`);--> statement-breakpoint
CREATE TABLE `projects` (
	`id` text(255) PRIMARY KEY NOT NULL,
	`name` text(255),
	`description` text,
	`context` text,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL,
	`user_id` text(255),
	`uploads_frame_id` text(36),
	FOREIGN KEY (`uploads_frame_id`) REFERENCES `frames`(`id`) ON UPDATE no action ON DELETE set null
);
--> statement-breakpoint
CREATE INDEX `ix_projects_user_id` ON `projects` (`user_id`);--> statement-breakpoint
CREATE INDEX `ix_projects_uploads_frame_id` ON `projects` (`uploads_frame_id`);--> statement-breakpoint
CREATE INDEX `ix_projects_user_updated` ON `projects` (`user_id`,`updated_at`);--> statement-breakpoint
CREATE TABLE `user_secrets` (
	`id` text(36) PRIMARY KEY NOT NULL,
	`user_id` text(255) NOT NULL,
	`name` text(128) NOT NULL,
	`provider` text(16) NOT NULL,
	`encrypted_value` text NOT NULL,
	`credential_type` text(32),
	`buckets` text,
	`region` text(64),
	`description` text(256),
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `ix_user_secrets_user_id` ON `user_secrets` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `uq_user_secrets_user_name` ON `user_secrets` (`user_id`,`name`);