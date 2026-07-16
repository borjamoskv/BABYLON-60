-- Aux LLM spend columns + per-class usage buckets (additive, nullable).
ALTER TABLE `frames` ADD COLUMN `aux_input_tokens` integer;--> statement-breakpoint
ALTER TABLE `frames` ADD COLUMN `aux_output_tokens` integer;--> statement-breakpoint
ALTER TABLE `frames` ADD COLUMN `aux_cache_read_tokens` integer;--> statement-breakpoint
ALTER TABLE `frames` ADD COLUMN `aux_cache_write_tokens` integer;--> statement-breakpoint
ALTER TABLE `frames` ADD COLUMN `aux_cost` real;--> statement-breakpoint
ALTER TABLE `frames` ADD COLUMN `token_class_usage` text;
