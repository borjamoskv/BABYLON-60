use rusqlite::{Connection, Result};
use std::path::Path;
use crate::models::{MemoryEvent, IdeaThread};

pub struct CortexDatabase {
    conn: Connection,
}

impl CortexDatabase {
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conn = Connection::open(path)?;
        let mut db = Self { conn };
        db.initialize_schema()?;
        Ok(db)
    }

    fn initialize_schema(&mut self) -> Result<()> {
        let tx = self.conn.transaction()?;
        
        // MemoryEvent Table
        tx.execute(
            "CREATE TABLE IF NOT EXISTS memory_events (
                event_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                conversation_id TEXT,
                message_id TEXT,
                source_uri TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                normalized_text TEXT NOT NULL,
                entities JSON NOT NULL,
                raw_hash TEXT NOT NULL,
                extractor_version TEXT NOT NULL,
                extraction_confidence REAL NOT NULL
            )",
            [],
        )?;

        // IdeaThread Table
        tx.execute(
            "CREATE TABLE IF NOT EXISTS idea_threads (
                idea_id TEXT PRIMARY KEY,
                core_concept TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                recurrence_count INTEGER NOT NULL,
                dormant_days INTEGER NOT NULL,
                events JSON NOT NULL,
                score REAL NOT NULL
            )",
            [],
        )?;

        // Inferences Table (Ontology Law O1 & O2)
        tx.execute(
            "CREATE TABLE IF NOT EXISTS inferences (
                inference_id TEXT PRIMARY KEY,
                derived_from_threads JSON NOT NULL,
                model_id TEXT NOT NULL,
                prompt_digest TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                proposal_summary TEXT NOT NULL,
                confidence REAL NOT NULL
            )",
            [],
        )?;

        // ProposalContext Table (Crosses Trust Boundary)
        tx.execute(
            "CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                inference_ref TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                justification TEXT NOT NULL,
                evaluated_risk TEXT NOT NULL
            )",
            [],
        )?;

        tx.commit()?;
        Ok(())
    }

    pub fn insert_event(&self, event: &MemoryEvent) -> Result<()> {
        let entities_json = serde_json::to_string(&event.entities).unwrap();
        
        self.conn.execute(
            "INSERT OR REPLACE INTO memory_events (
                event_id, provider, conversation_id, message_id, source_uri, timestamp, event_type,
                raw_text, normalized_text, entities, raw_hash, extractor_version, extraction_confidence
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13)",
            (
                &event.event_id,
                &event.source.provider,
                &event.source.conversation_id,
                &event.source.message_id,
                &event.source.source_uri,
                event.timestamp.to_rfc3339(),
                &event.event_type,
                &event.raw_text,
                &event.normalized_text,
                entities_json,
                &event.raw_hash,
                &event.extractor_version,
                event.extraction_confidence,
            ),
        )?;
        Ok(())
    }

    pub fn insert_thread(&self, thread: &IdeaThread) -> Result<()> {
        let events_json = serde_json::to_string(&thread.events).unwrap();
        
        self.conn.execute(
            "INSERT OR REPLACE INTO idea_threads (
                idea_id, core_concept, first_seen, last_seen, recurrence_count, dormant_days, events, score
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            (
                &thread.idea_id,
                &thread.core_concept,
                thread.first_seen.to_rfc3339(),
                thread.last_seen.to_rfc3339(),
                thread.recurrence_count,
                thread.dormant_days,
                events_json,
                thread.score,
            ),
        )?;
        Ok(())
    }

    pub fn get_event(&self, event_id: &str) -> Result<Option<MemoryEvent>> {
        let mut stmt = self.conn.prepare(
            "SELECT event_id, provider, conversation_id, message_id, source_uri, timestamp, event_type,
                    raw_text, normalized_text, entities, raw_hash, extractor_version, extraction_confidence
             FROM memory_events WHERE event_id = ?1",
        )?;

        let mut rows = stmt.query([event_id])?;
        if let Some(row) = rows.next()? {
            let ts_str: String = row.get(5)?;
            let timestamp = chrono::DateTime::parse_from_rfc3339(&ts_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let entities_str: String = row.get(9)?;
            let entities: Vec<String> = serde_json::from_str(&entities_str).unwrap_or_default();

            Ok(Some(MemoryEvent {
                event_id: row.get(0)?,
                source: crate::models::SourceRef {
                    provider: row.get(1)?,
                    conversation_id: row.get(2)?,
                    message_id: row.get(3)?,
                    source_uri: row.get(4)?,
                },
                timestamp,
                event_type: row.get(6)?,
                raw_text: row.get(7)?,
                normalized_text: row.get(8)?,
                entities,
                raw_hash: row.get(10)?,
                extractor_version: row.get(11)?,
                extraction_confidence: row.get(12)?,
            }))
        } else {
            Ok(None)
        }
    }

    pub fn get_thread(&self, idea_id: &str) -> Result<Option<IdeaThread>> {
        let mut stmt = self.conn.prepare(
            "SELECT idea_id, core_concept, first_seen, last_seen, recurrence_count, dormant_days, events, score
             FROM idea_threads WHERE idea_id = ?1",
        )?;

        let mut rows = stmt.query([idea_id])?;
        if let Some(row) = rows.next()? {
            let first_str: String = row.get(2)?;
            let first_seen = chrono::DateTime::parse_from_rfc3339(&first_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let last_str: String = row.get(3)?;
            let last_seen = chrono::DateTime::parse_from_rfc3339(&last_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let events_str: String = row.get(6)?;
            let events: Vec<String> = serde_json::from_str(&events_str).unwrap_or_default();

            Ok(Some(IdeaThread {
                idea_id: row.get(0)?,
                core_concept: row.get(1)?,
                first_seen,
                last_seen,
                recurrence_count: row.get(4)?,
                dormant_days: row.get(5)?,
                events,
                score: row.get(7)?,
            }))
        } else {
            Ok(None)
        }
    }

    /// Retrieves dormant threads ranked by exergy score (Milestone M0: RESURRECT).
    pub fn get_top_resurrect_candidates(&self, limit: usize) -> Result<Vec<IdeaThread>> {
        let mut stmt = self.conn.prepare(
            "SELECT idea_id, core_concept, first_seen, last_seen, recurrence_count, dormant_days, events, score
             FROM idea_threads
             WHERE dormant_days >= 7
             ORDER BY score DESC, dormant_days DESC
             LIMIT ?1",
        )?;

        let thread_iter = stmt.query_map([limit as i64], |row| {
            let first_str: String = row.get(2)?;
            let first_seen = chrono::DateTime::parse_from_rfc3339(&first_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let last_str: String = row.get(3)?;
            let last_seen = chrono::DateTime::parse_from_rfc3339(&last_str)
                .map(|dt| dt.with_timezone(&chrono::Utc))
                .unwrap_or_else(|_| chrono::Utc::now());

            let events_str: String = row.get(6)?;
            let events: Vec<String> = serde_json::from_str(&events_str).unwrap_or_default();

            Ok(IdeaThread {
                idea_id: row.get(0)?,
                core_concept: row.get(1)?,
                first_seen,
                last_seen,
                recurrence_count: row.get(4)?,
                dormant_days: row.get(5)?,
                events,
                score: row.get(7)?,
            })
        })?;

        let mut results = Vec::new();
        for t in thread_iter {
            results.push(t?);
        }
        Ok(results)
    }

    /// Resurrects a dormant thread by returning the IdeaThread along with all backing MemoryEvents.
    pub fn resurrect_thread(&self, idea_id: &str) -> Result<Option<(IdeaThread, Vec<MemoryEvent>)>> {
        if let Some(thread) = self.get_thread(idea_id)? {
            let mut events = Vec::new();
            for ev_id in &thread.events {
                if let Some(ev) = self.get_event(ev_id)? {
                    events.push(ev);
                }
            }
            Ok(Some((thread, events)))
        } else {
            Ok(None)
        }
    }

    pub fn insert_inference(&self, inf: &crate::models::Inference) -> Result<()> {
        let threads_json = serde_json::to_string(&inf.derived_from_threads).unwrap();
        self.conn.execute(
            "INSERT OR REPLACE INTO inferences (
                inference_id, derived_from_threads, model_id, prompt_digest, generated_at, proposal_summary, confidence
            ) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            (
                &inf.inference_id,
                threads_json,
                &inf.model_id,
                &inf.prompt_digest,
                inf.generated_at.to_rfc3339(),
                &inf.proposal_summary,
                inf.confidence,
            ),
        )?;
        Ok(())
    }

    pub fn insert_proposal(&self, prop: &crate::models::ProposalContext) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO proposals (
                proposal_id, inference_ref, suggested_action, justification, evaluated_risk
            ) VALUES (?1, ?2, ?3, ?4, ?5)",
            (
                &prop.proposal_id,
                &prop.inference_ref,
                &prop.suggested_action,
                &prop.justification,
                &prop.evaluated_risk,
            ),
        )?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{SourceRef, MemoryEvent, IdeaThread, Inference, ProposalContext};

    #[test]
    fn test_cortex_resurrect_lifecycle() {
        let db = CortexDatabase::open(":memory:").unwrap();

        // 1. Ingest an auditable MemoryEvent
        let ev1 = MemoryEvent {
            event_id: "mem_001".into(),
            source: SourceRef {
                provider: "markdown_vault".into(),
                conversation_id: None,
                message_id: None,
                source_uri: "file:///Users/borja/notes/thermodynamic_computing.md".into(),
            },
            timestamp: chrono::Utc::now(),
            event_type: "idea".into(),
            raw_text: "Landauer limit bounds dissipation on irreversible bit erasure.".into(),
            normalized_text: "landauer limit dissipation bit erasure".into(),
            entities: vec!["Landauer".into(), "Thermodynamics".into()],
            raw_hash: "a1b2c3d4".into(),
            extractor_version: "v1.0.0".into(),
            extraction_confidence: 0.99,
        };
        db.insert_event(&ev1).unwrap();

        // 2. Create an IdeaThread linked to ev1 with 45 dormant days
        let thread1 = IdeaThread {
            idea_id: "idea_landauer_01".into(),
            core_concept: "Landauer Bound in Silicon".into(),
            first_seen: chrono::Utc::now() - chrono::Duration::days(60),
            last_seen: chrono::Utc::now() - chrono::Duration::days(45),
            recurrence_count: 5,
            dormant_days: 45,
            events: vec!["mem_001".into()],
            score: IdeaThread::compute_score(0.8, 0.7, 0.5, 0.9, 0.8, 0.4, 0.6, 0.1),
        };
        db.insert_thread(&thread1).unwrap();

        // 3. Query top resurrect candidates
        let candidates = db.get_top_resurrect_candidates(5).unwrap();
        assert_eq!(candidates.len(), 1);
        assert_eq!(candidates[0].idea_id, "idea_landauer_01");

        // 4. RESURRECT: recover thread and backing event
        let resurrected = db.resurrect_thread("idea_landauer_01").unwrap().expect("Thread should exist");
        assert_eq!(resurrected.0.idea_id, "idea_landauer_01");
        assert_eq!(resurrected.1.len(), 1);
        assert_eq!(resurrected.1[0].source.source_uri, "file:///Users/borja/notes/thermodynamic_computing.md");

        // 5. Model generates an Inference and Proposal (crossing trust boundary)
        let inf = Inference {
            inference_id: "inf_landauer_01".into(),
            derived_from_threads: vec!["idea_landauer_01".into()],
            model_id: "gemini-3.8-flash".into(),
            prompt_digest: "digest_123".into(),
            generated_at: chrono::Utc::now(),
            proposal_summary: "Re-anchor thermodynamic cache limits".into(),
            confidence: 0.92,
        };
        db.insert_inference(&inf).unwrap();

        let prop = ProposalContext {
            proposal_id: "prop_landauer_01".into(),
            inference_ref: "inf_landauer_01".into(),
            suggested_action: "Adjust KUDURRU-64 cache eviction".into(),
            justification: "Dormant insight from Landauer bound notes".into(),
            evaluated_risk: "Low".into(),
        };
        db.insert_proposal(&prop).unwrap();
    }
}
