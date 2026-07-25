# lib.rs patch
with open("babylon60-ide/src-tauri/src/lib.rs") as f:
    content = f.read()

content = content.replace("use std::sync::Mutex;", "use tokio::sync::Mutex;")
content = content.replace(
    "fn get_ledger_events(state: State<AppState>, limit: u32) -> Result<Vec<CortexEvent>, String> {\n    let ledger = state.ledger.lock().unwrap();\n    ledger.get_events(limit).map_err(|e| e.to_string())\n}",
    "async fn get_ledger_events(state: State<'_, AppState>, limit: u32) -> Result<Vec<CortexEvent<'static>>, String> {\n    let ledger = state.ledger.lock().await;\n    ledger.get_events(limit).map_err(|e| e.to_string())\n}",
)
content = content.replace(
    "fn append_ledger_event(state: State<AppState>, event_type: String, payload: Value) -> Result<CortexEvent, String> {\n    let ledger = state.ledger.lock().unwrap();\n    ledger.append_event(&event_type, &payload).map_err(|e| e.to_string())\n}",
    "async fn append_ledger_event(state: State<'_, AppState>, event_type: String, payload: Value) -> Result<CortexEvent<'static>, String> {\n    let ledger = state.ledger.lock().await;\n    ledger.append_event(&event_type, &payload).map_err(|e| e.to_string())\n}",
)

with open("babylon60-ide/src-tauri/src/lib.rs", "w") as f:
    f.write(content)

# ledger.rs patch
with open("babylon60-ide/src-tauri/src/ledger.rs") as f:
    ledger_content = f.read()

import re

old_struct = r"""#\[derive\(Debug, Clone, Serialize, Deserialize\)\]
pub struct CortexEvent \{
    pub id: Option<i64>,
    pub timestamp: String,
    pub event_type: String,
    pub payload: String,
    pub prev_hash: String,
    pub event_hash: String,
\}"""

new_struct = """use std::borrow::Cow;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CortexEvent<'a> {
    pub id: Option<i64>,
    pub timestamp: Cow<'a, str>,
    pub event_type: Cow<'a, str>,
    pub payload: Cow<'a, str>,
    pub prev_hash: Cow<'a, str>,
    pub event_hash: Cow<'a, str>,
}"""
ledger_content = re.sub(old_struct, new_struct, ledger_content)

old_append = r"pub fn append_event\(&self, event_type: &str, payload: &serde_json::Value\) -> Result<CortexEvent>"
new_append = (
    r"pub fn append_event<'a>(&self, event_type: &'a str, payload: &serde_json::Value) -> Result<CortexEvent<'static>>"
)
ledger_content = re.sub(old_append, new_append, ledger_content)

# Update return values inside append_event to use Cow::Owned for static lifetimes where we just constructed the strings
old_return = r"""Ok\(CortexEvent \{
            id: Some\(self\.conn\.last_insert_rowid\(\)\),
            timestamp,
            event_type: event_type\.to_string\(\),
            payload: payload_str,
            prev_hash,
            event_hash,
        \}\)"""

new_return = """Ok(CortexEvent {
            id: Some(self.conn.last_insert_rowid()),
            timestamp: Cow::Owned(timestamp),
            event_type: Cow::Owned(event_type.to_string()),
            payload: Cow::Owned(payload_str),
            prev_hash: Cow::Owned(prev_hash),
            event_hash: Cow::Owned(event_hash),
        })"""
ledger_content = re.sub(old_return, new_return, ledger_content)

# Update get_events
old_get_events = r"pub fn get_events\(&self, limit: u32\) -> Result<Vec<CortexEvent>>"
new_get_events = r"pub fn get_events(&self, limit: u32) -> Result<Vec<CortexEvent<'static>>>"
ledger_content = re.sub(old_get_events, new_get_events, ledger_content)

old_row_get = r"""Ok\(CortexEvent \{
                id: row\.get\(0\)\?,
                timestamp: row\.get\(1\)\?,
                event_type: row\.get\(2\)\?,
                payload: row\.get\(3\)\?,
                prev_hash: row\.get\(4\)\?,
                event_hash: row\.get\(5\)\?,
            \}\)"""
new_row_get = """Ok(CortexEvent {
                id: row.get(0)?,
                timestamp: Cow::Owned(row.get(1)?),
                event_type: Cow::Owned(row.get(2)?),
                payload: Cow::Owned(row.get(3)?),
                prev_hash: Cow::Owned(row.get(4)?),
                event_hash: Cow::Owned(row.get(5)?),
            })"""
ledger_content = re.sub(old_row_get, new_row_get, ledger_content)

with open("babylon60-ide/src-tauri/src/ledger.rs", "w") as f:
    f.write(ledger_content)
