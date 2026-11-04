CREATE TABLE `annotation_history` (
	`id` text PRIMARY KEY NOT NULL,
	`annotation_id` text NOT NULL,
	`version` integer NOT NULL,
	`actor_id` text NOT NULL,
	`snapshot_json` text NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`annotation_id`) REFERENCES `annotations`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `annotation_history_annotation_idx` ON `annotation_history` (`annotation_id`);--> statement-breakpoint
CREATE TABLE `annotation_runs` (
	`id` text PRIMARY KEY NOT NULL,
	`text_id` text NOT NULL,
	`text_version` integer NOT NULL,
	`framework_id` text NOT NULL,
	`framework_version` integer NOT NULL,
	`mode` text NOT NULL,
	`status` text NOT NULL,
	`provider` text,
	`model` text,
	`warnings_json` text DEFAULT '[]' NOT NULL,
	`created_at` text NOT NULL,
	`finished_at` text,
	FOREIGN KEY (`text_id`) REFERENCES `texts`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `annotation_runs_text_idx` ON `annotation_runs` (`text_id`);--> statement-breakpoint
CREATE TABLE `annotations` (
	`id` text PRIMARY KEY NOT NULL,
	`text_id` text NOT NULL,
	`text_version` integer NOT NULL,
	`framework_id` text NOT NULL,
	`framework_version` integer NOT NULL,
	`run_id` text NOT NULL,
	`start_offset` integer NOT NULL,
	`end_offset` integer NOT NULL,
	`surface` text NOT NULL,
	`category` text NOT NULL,
	`original_category` text NOT NULL,
	`category_label` text NOT NULL,
	`confidence_milli` integer NOT NULL,
	`rationale` text NOT NULL,
	`congruent` text DEFAULT '' NOT NULL,
	`evidence_json` text NOT NULL,
	`counter_evidence_json` text NOT NULL,
	`review_status` text DEFAULT 'pending' NOT NULL,
	`review_note` text DEFAULT '' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`source` text NOT NULL,
	`record_json` text NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	FOREIGN KEY (`text_id`) REFERENCES `texts`(`id`) ON UPDATE no action ON DELETE cascade,
	FOREIGN KEY (`run_id`) REFERENCES `annotation_runs`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `annotations_current_idx` ON `annotations` (`text_id`,`text_version`);--> statement-breakpoint
CREATE INDEX `annotations_review_idx` ON `annotations` (`review_status`);--> statement-breakpoint
CREATE TABLE `frameworks` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`name` text NOT NULL,
	`description` text DEFAULT '' NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`nodes_json` text NOT NULL,
	`prompt` text DEFAULT '' NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `frameworks_owner_idx` ON `frameworks` (`owner_id`);--> statement-breakpoint
CREATE TABLE `mutation_guards` (
	`id` text PRIMARY KEY NOT NULL,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `projects` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_id` text NOT NULL,
	`name` text NOT NULL,
	`description` text DEFAULT '' NOT NULL,
	`demo_key` text,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `projects_owner_idx` ON `projects` (`owner_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `projects_demo_idx` ON `projects` (`owner_id`,`demo_key`);--> statement-breakpoint
CREATE TABLE `text_versions` (
	`id` text PRIMARY KEY NOT NULL,
	`text_id` text NOT NULL,
	`version` integer NOT NULL,
	`title` text NOT NULL,
	`content` text NOT NULL,
	`genre` text DEFAULT '' NOT NULL,
	`context` text DEFAULT '' NOT NULL,
	`created_at` text NOT NULL,
	FOREIGN KEY (`text_id`) REFERENCES `texts`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `text_versions_identity_idx` ON `text_versions` (`text_id`,`version`);--> statement-breakpoint
CREATE TABLE `texts` (
	`id` text PRIMARY KEY NOT NULL,
	`project_id` text NOT NULL,
	`title` text NOT NULL,
	`content` text NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`genre` text DEFAULT '' NOT NULL,
	`context` text DEFAULT '' NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	FOREIGN KEY (`project_id`) REFERENCES `projects`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `texts_project_idx` ON `texts` (`project_id`);