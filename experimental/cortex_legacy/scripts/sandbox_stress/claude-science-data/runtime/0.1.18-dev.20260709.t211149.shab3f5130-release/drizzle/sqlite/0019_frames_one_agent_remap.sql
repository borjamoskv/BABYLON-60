-- One-agent: remap legacy specialist agent names to OPERON for existing frames.
-- Preserves SKILL_CREATOR and user profiles (anything not in the dead-name set).
UPDATE `frames` SET `agent_name` = 'OPERON'
WHERE `agent_name` IN (
  'COORDINATOR', 'SINGLECELL', 'PROTEOMICS', 'BIOKNOWLEDGE', 'LITREVIEW',
  'GENOMICS', 'DATAML', 'CHEMINFORMATICS', 'CLINICALPHARMA', 'CLONING',
  'LABTOOLS', 'CONCIERGE'
);
