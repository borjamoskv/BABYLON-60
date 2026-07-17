/**
 * BABYLON60 IDE — Frontend Core Application
 * Single Page Application wiring for Industrial Noir 2026.
 */
import { get, post, connectWebSocket } from './api.js';
import { registerRoute, navigate, getInitialRoute } from './router.js';

// Global state
let databaseList = [];
let telemetrySocket = null;
let activeTooltip = null;

// Initialize layout & sidebar on page load
document.addEventListener('DOMContentLoaded', async () => {
  setupSidebar();
  setupRouter();
  await refreshDatabaseCount();
  
  // Navigate to initial route
  const initRoute = getInitialRoute();
  navigate(initRoute);
});

// Refresh database count and footer metadata
async function refreshDatabaseCount() {
  try {
    databaseList = await get('/api/databases');
    const dbCountEl = document.querySelector('.db-count .count');
    if (dbCountEl) {
      dbCountEl.textContent = databaseList.length;
    }
  } catch (err) {
    console.error('Failed to fetch databases:', err);
  }
}

// Render Sidebar Navigation
function setupSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.innerHTML = `
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <div class="dot"></div>
        BABYLON·60
      </div>
      <div class="sidebar-subtitle">SOVEREIGN AGENT MEMORY</div>
      <div class="sidebar-status">
        <div class="status-indicator"></div>
        <span class="status-text">CONNECTED</span>
      </div>
    </div>
    <div class="sidebar-nav">
      <div class="nav-section-label">INSPECTOR</div>
      <div class="nav-item" data-route="ledger">
        <span class="icon">⧉</span>
        <span>BFT Ledger</span>
        <span class="shortcut">⌘1</span>
      </div>
      <div class="nav-item" data-route="databases">
        <span class="icon">⛁</span>
        <span>Ontologies</span>
        <span class="shortcut">⌘2</span>
      </div>
      <div class="nav-section-label">ANALYSIS</div>
      <div class="nav-item" data-route="query">
        <span class="icon">❯_</span>
        <span>SQL Console</span>
        <span class="shortcut">⌘3</span>
      </div>
      <div class="nav-item" data-route="telemetry">
        <span class="icon">⚡</span>
        <span>Telemetry</span>
        <span class="shortcut">⌘4</span>
      </div>
    </div>
    <div class="sidebar-footer">
      <div class="db-count">
        Databases: <span class="count">0</span>
      </div>
      <div style="margin-top: 4px; opacity: 0.5;">MOSKV-1 APEX v1.0.2</div>
    </div>
  `;

  // Attach nav click handlers
  sidebar.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      navigate(item.dataset.route);
    });
  });

  // Global hotkeys (Cmd+1 to Cmd+4 / Ctrl+1 to Ctrl+4)
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && ['1', '2', '3', '4'].includes(e.key)) {
      e.preventDefault();
      const routes = ['ledger', 'databases', 'query', 'telemetry'];
      navigate(routes[parseInt(e.key) - 1]);
    }
  });
}

// Connection State Helpers
function setConnectionState(state, text) {
  const indicator = document.querySelector('.status-indicator');
  const textEl = document.querySelector('.status-text');
  if (!indicator || !textEl) return;

  indicator.className = 'status-indicator';
  if (state === 'error') {
    indicator.classList.add('error');
  } else if (state === 'loading') {
    indicator.classList.add('loading');
  }
  textEl.textContent = text.toUpperCase();
}

// Router wiring and hash listening
function setupRouter() {
  registerRoute('ledger', renderLedgerPage);
  registerRoute('databases', renderDatabasesPage);
  registerRoute('query', renderQueryPage);
  registerRoute('telemetry', renderTelemetryPage);

  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#', '');
    if (hash) navigate(hash);
  });
}

// Tooltip helpers
function showTooltip(e, content) {
  if (activeTooltip) activeTooltip.remove();
  
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip fade-in';
  tooltip.innerHTML = content;
  document.body.appendChild(tooltip);
  activeTooltip = tooltip;

  const rect = e.target.getBoundingClientRect();
  tooltip.style.left = `${rect.left + window.scrollX + 20}px`;
  tooltip.style.top = `${rect.top + window.scrollY - 10}px`;
}

function hideTooltip() {
  if (activeTooltip) {
    activeTooltip.remove();
    activeTooltip = null;
  }
}


/* ═══════════════════════════════════════════════════════════════
   PAGE: LEDGER VIEW
   ═══════════════════════════════════════════════════════════════ */
async function renderLedgerPage(container) {
  container.innerHTML = `
    <div class="panel-header slide-in">
      <div class="panel-title">BFT MASTER LEDGER</div>
      <div class="panel-badge live">ACTIVE</div>
    </div>
    <div class="panel-body slide-in">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Ledger File</div>
          <div class="stat-value lapis" id="stat-db-name">-</div>
          <div class="stat-sub">SQLite storage</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Entries</div>
          <div class="stat-value gold" id="stat-total-entries">0</div>
          <div class="stat-sub" id="stat-latest-time">-</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Consensus State</div>
          <div class="stat-value verify" id="stat-integrity">UNKNOWN</div>
          <div class="stat-sub" id="stat-latest-lamport">Lamport: -</div>
        </div>
      </div>

      <div class="card" style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div class="card-title">Cryptographic Hash Chain Verification</div>
          <button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Integrity</button>
        </div>
        <div class="verify-progress" style="display: none;">
          <div class="verify-progress-bar"></div>
        </div>
        <div class="chain-container" id="chain-visual-grid">
          <div class="empty-state" style="padding: 20px 0;">
            <div class="icon">⚿</div>
            <div class="desc">Execute verification to map blocks and assert consensus state.</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title" style="margin-bottom: 12px;">Ledger Sequence</div>
        <div style="overflow-x: auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Seq</th>
                <th>Stream</th>
                <th>Event Type</th>
                <th>Lamport T</th>
                <th>Taint Provenance</th>
                <th>Timestamp</th>
                <th>Entry Hash</th>
              </tr>
            </thead>
            <tbody id="ledger-table-body">
              <tr>
                <td colspan="7" class="empty-state" style="text-align: center;">Loading ledger entries...</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination">
          <button class="btn" id="btn-ledger-prev" disabled>◀ Prev</button>
          <span style="font-family: var(--font-mono); font-size: 0.75rem;" id="ledger-page-info">Page 1</span>
          <button class="btn" id="btn-ledger-next" disabled>Next ▶</button>
        </div>
      </div>
    </div>

    <!-- Details Sidebar Overlay -->
    <div id="entry-detail-panel" class="card" style="display: none; position: fixed; top: var(--header-height); right: 0; width: 450px; height: calc(100vh - var(--header-height)); border-radius: 0; border-left: 1px solid var(--edge); z-index: 10; display: flex; flex-direction: column; background: var(--kiln); transform: translateX(100%); transition: transform var(--transition-normal);">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px; border-bottom: 1px solid var(--edge);">
        <div class="card-title" id="detail-title" style="margin-bottom: 0;">Entry #0</div>
        <button class="btn" id="btn-close-detail" style="padding: 2px 8px;">✕</button>
      </div>
      <div style="flex: 1; overflow-y: auto; padding: 16px; font-family: var(--font-mono); font-size: 0.75rem;">
        <div style="margin-bottom: 14px;">
          <div class="stat-label">Event UUID</div>
          <div id="detail-uuid" style="color: var(--dust); word-break: break-all; margin-top: 4px;">-</div>
        </div>
        <div style="margin-bottom: 14px;">
          <div class="stat-label">Cortex Taint Signature</div>
          <div id="detail-taint" style="color: var(--lapis-bright); word-break: break-all; margin-top: 4px;">-</div>
        </div>
        <div style="margin-bottom: 14px;">
          <div class="stat-label">Linkages</div>
          <div style="margin-top: 4px;">Prev: <span id="detail-prev-hash" style="color: var(--dust-dim);">-</span></div>
          <div style="margin-top: 2px;">Curr: <span id="detail-curr-hash" style="color: var(--verify);">-</span></div>
        </div>
        <div>
          <div class="stat-label" style="margin-bottom: 6px;">Payload State</div>
          <pre id="detail-payload" style="background: var(--tablet); border: 1px solid var(--edge); padding: 10px; border-radius: var(--radius-sm); color: var(--dust-dim); overflow-x: auto; font-family: var(--font-mono); line-height: 1.5;"></pre>
        </div>
      </div>
    </div>
  `;

  let limit = 50;
  let offset = 0;

  // Load metrics & initial table
  const fetchStats = async () => {
    try {
      const stats = await get('/api/ledger/stats');
      if (stats.exists) {
        document.getElementById('stat-db-name').textContent = stats.db_path;
        document.getElementById('stat-total-entries').textContent = stats.entries;
        if (stats.latest && stats.latest.created_at) {
          document.getElementById('stat-latest-time').textContent = stats.latest.created_at;
          document.getElementById('stat-latest-lamport').textContent = `Lamport: t=${stats.latest.lamport_t}`;
        }
      } else {
        document.getElementById('stat-db-name').textContent = 'NOT FOUND';
        document.getElementById('stat-integrity').textContent = 'NO LEDGER';
        document.getElementById('stat-integrity').className = 'stat-value break';
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadEntriesTable = async () => {
    try {
      const res = await get(`/api/ledger/entries?limit=${limit}&offset=${offset}`);
      const tbody = document.getElementById('ledger-table-body');
      tbody.innerHTML = '';

      if (!res.entries || res.entries.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No entries in this ledger database yet.</td></tr>`;
        return;
      }

      res.entries.forEach(entry => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        tr.innerHTML = `
          <td class="seq-cell">#${entry.seq}</td>
          <td class="stream-cell">${escapeHtml(entry.stream)}</td>
          <td style="color: var(--dust); font-weight: 500;">${escapeHtml(entry.event_type)}</td>
          <td>${entry.lamport_t}</td>
          <td style="font-size: 0.65rem; color: var(--dust-faint); max-width: 150px; overflow: hidden; text-overflow: ellipsis;">
            ${escapeHtml(entry.cortex_taint || 'None')}
          </td>
          <td class="time-cell">${entry.created_at}</td>
          <td class="hash-cell">${entry.entry_hash.slice(0, 16)}...</td>
        `;

        tr.addEventListener('click', () => showEntryDetail(entry.seq));
        tbody.appendChild(tr);
      });

      // Pagination state
      document.getElementById('btn-ledger-prev').disabled = offset === 0;
      document.getElementById('btn-ledger-next').disabled = offset + limit >= res.total;
      document.getElementById('ledger-page-info').textContent = `Showing ${offset + 1} - ${Math.min(offset + limit, res.total)} of ${res.total}`;
    } catch (err) {
      console.error(err);
    }
  };

  // Entry Detail Handler
  const showEntryDetail = async (seq) => {
    try {
      const entry = await get(`/api/ledger/entry/${seq}`);
      const panel = document.getElementById('entry-detail-panel');
      
      document.getElementById('detail-title').textContent = `Ledger Entry #${entry.seq}`;
      document.getElementById('detail-uuid').textContent = entry.event_id;
      document.getElementById('detail-taint').textContent = entry.cortex_taint || 'None';
      document.getElementById('detail-prev-hash').textContent = entry.prev_hash;
      document.getElementById('detail-curr-hash').textContent = entry.entry_hash;
      
      let parsedPayload = {};
      try {
        parsedPayload = JSON.parse(entry.payload_json);
      } catch {
        parsedPayload = entry.payload_json;
      }
      document.getElementById('detail-payload').textContent = JSON.stringify(parsedPayload, null, 2);

      panel.style.display = 'flex';
      // Force layout calculation, then animate in
      void panel.offsetWidth;
      panel.style.transform = 'translateX(0)';
    } catch (err) {
      alert(`Failed to load entry details: ${err.message}`);
    }
  };

  const closeEntryDetail = () => {
    const panel = document.getElementById('entry-detail-panel');
    panel.style.transform = 'translateX(100%)';
    setTimeout(() => {
      panel.style.display = 'none';
    }, 220);
  };

  // Verification process
  const verifyChainAction = async () => {
    const btn = document.getElementById('btn-verify-chain');
    const pBar = document.querySelector('.verify-progress');
    const pBarFill = document.querySelector('.verify-progress-bar');
    const grid = document.getElementById('chain-visual-grid');

    btn.disabled = true;
    pBar.style.display = 'block';
    pBarFill.style.width = '20%';
    setConnectionState('loading', 'VERIFYING CHAIN');

    try {
      pBarFill.style.width = '60%';
      const res = await post('/api/ledger/verify');
      pBarFill.style.width = '100%';

      grid.innerHTML = '';
      if (!res.entries || res.entries.length === 0) {
        grid.innerHTML = `<div class="empty-state"><div class="desc">No verified entries.</div></div>`;
        return;
      }

      // Draw blocks
      res.entries.forEach(b => {
        const block = document.createElement('div');
        block.className = `chain-block ${b.valid ? '' : 'invalid'}`;
        
        block.addEventListener('mouseenter', (e) => {
          const statusText = b.valid ? `<span style="color: var(--verify);">VALID linkage</span>` : `<span style="color: var(--break); font-weight:700;">BROKEN: ${b.errors.join(', ')}</span>`;
          showTooltip(e, `
            <strong>Sequence #${b.seq}</strong><br/>
            Stream: ${escapeHtml(b.stream)}<br/>
            Lamport T: ${b.lamport_t}<br/>
            Hash: <span style="font-family: var(--font-mono);">${b.entry_hash}</span><br/>
            Status: ${statusText}
          `);
        });
        block.addEventListener('mouseleave', hideTooltip);
        block.addEventListener('click', () => showEntryDetail(b.seq));
        grid.appendChild(block);
      });

      // Update header indicators
      const integrityVal = document.getElementById('stat-integrity');
      if (res.valid) {
        integrityVal.textContent = 'INTEGRITY OK';
        integrityVal.className = 'stat-value verify';
        setConnectionState('connected', 'CONNECTED');
      } else {
        integrityVal.textContent = `COMPROMISED (Seq #${res.broken_at})`;
        integrityVal.className = 'stat-value break';
        setConnectionState('error', 'LEDGER BROKEN');
      }
    } catch (err) {
      grid.innerHTML = `<div class="empty-state"><div class="icon">⚠</div><div class="desc" style="color: var(--break);">${escapeHtml(err.message)}</div></div>`;
      setConnectionState('error', 'ERROR');
    } finally {
      btn.disabled = false;
      setTimeout(() => { pBar.style.display = 'none'; }, 600);
    }
  };

  // Pagination triggers
  document.getElementById('btn-ledger-prev').addEventListener('click', () => {
    if (offset >= limit) {
      offset -= limit;
      loadEntriesTable();
    }
  });

  document.getElementById('btn-ledger-next').addEventListener('click', () => {
    offset += limit;
    loadEntriesTable();
  });

  document.getElementById('btn-verify-chain').addEventListener('click', verifyChainAction);
  document.getElementById('btn-close-detail').addEventListener('click', closeEntryDetail);

  await fetchStats();
  await loadEntriesTable();
}


/* ═══════════════════════════════════════════════════════════════
   PAGE: DATABASE EXPLORER
   ═══════════════════════════════════════════════════════════════ */
async function renderDatabasesPage(container) {
  container.innerHTML = `
    <div class="panel-header slide-in">
      <div class="panel-title">ONTOLOGY DATABASE EXPLORER</div>
      <div class="panel-badge beta">EXPLORER</div>
    </div>
    <div class="panel-body slide-in" style="display: flex; gap: 20px; overflow: hidden; height: calc(100% - var(--header-height));">
      
      <!-- Left sidebar: database file tree -->
      <div class="card" style="width: 280px; min-width: 280px; display: flex; flex-direction: column; overflow-y: auto;">
        <div class="card-title">Discovered Files</div>
        <div id="db-tree-container" class="tree-node" style="padding-left: 0;">
          <div class="loading-text">Loading workspace directories...</div>
        </div>
      </div>

      <!-- Right main view: table preview -->
      <div style="flex: 1; display: flex; flex-direction: column; gap: 20px; overflow: hidden;">
        
        <!-- Schema section -->
        <div class="card" id="db-schema-card" style="display: none; flex-direction: column; max-height: 200px;">
          <div class="card-title" id="schema-card-title">Schema Information</div>
          <div style="flex: 1; overflow-y: auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>CID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>NotNull</th>
                  <th>Default</th>
                  <th>PK</th>
                </tr>
              </thead>
              <tbody id="schema-table-body"></tbody>
            </table>
          </div>
        </div>

        <!-- Row browser section -->
        <div class="card" id="db-rows-card" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
          <div class="card-title" id="rows-card-title">Table Browser</div>
          <div style="flex: 1; overflow: auto;" id="table-rows-container">
            <div class="empty-state">
              <div class="icon">⛁</div>
              <div class="desc">Select a database and table from the tree on the left to inspect records.</div>
            </div>
          </div>
          <div class="pagination" id="rows-pagination" style="display: none; border-top: 1px solid var(--edge); margin-top: auto;">
            <button class="btn" id="btn-rows-prev" disabled>◀ Prev</button>
            <span style="font-family: var(--font-mono); font-size: 0.75rem;" id="rows-page-info">Page 1</span>
            <button class="btn" id="btn-rows-next" disabled>Next ▶</button>
          </div>
        </div>
      </div>

    </div>
  `;

  let currentDb = null;
  let currentTable = null;
  let rowsLimit = 50;
  let rowsOffset = 0;

  // Load database tree
  const loadDatabaseTree = async () => {
    const tree = document.getElementById('db-tree-container');
    try {
      const dbs = await get('/api/databases');
      tree.innerHTML = '';
      
      if (dbs.length === 0) {
        tree.innerHTML = `<div class="empty-state" style="padding: 10px 0;"><div class="desc">No databases found.</div></div>`;
        return;
      }

      dbs.forEach(db => {
        const dbItem = document.createElement('div');
        dbItem.className = 'tree-item';
        dbItem.innerHTML = `<span class="tree-icon">⛁</span><span>${escapeHtml(db.name)}</span><span class="tree-count">${db.size_human}</span>`;
        
        const tableNode = document.createElement('div');
        tableNode.className = 'tree-node';
        tableNode.style.display = 'none';

        dbItem.addEventListener('click', async () => {
          const isCollapsed = tableNode.style.display === 'none';
          // Close others to keep clean
          tree.querySelectorAll('.tree-node').forEach(n => n.style.display = 'none');
          tree.querySelectorAll('.tree-item').forEach(i => i.classList.remove('active'));

          if (isCollapsed) {
            dbItem.classList.add('active');
            tableNode.style.display = 'block';
            if (tableNode.innerHTML === '') {
              tableNode.innerHTML = `<div style="padding: 4px 16px; opacity:0.5; font-size:0.7rem;">Querying tables...</div>`;
              try {
                const tables = await get(`/api/databases/${db.name}/tables`);
                tableNode.innerHTML = '';
                tables.forEach(tbl => {
                  const tblItem = document.createElement('div');
                  tblItem.className = 'tree-item';
                  tblItem.style.paddingLeft = '8px';
                  tblItem.innerHTML = `<span class="tree-icon">▤</span><span>${escapeHtml(tbl.name)}</span><span class="tree-count">${tbl.row_count}</span>`;
                  tblItem.addEventListener('click', (e) => {
                    e.stopPropagation();
                    tableNode.querySelectorAll('.tree-item').forEach(i => i.classList.remove('active'));
                    tblItem.classList.add('active');
                    selectSubtable(db.name, tbl.name);
                  });
                  tableNode.appendChild(tblItem);
                });
              } catch (err) {
                tableNode.innerHTML = `<div style="padding:4px 16px; color:var(--break); font-size:0.7rem;">${escapeHtml(err.message)}</div>`;
              }
            }
          }
        });

        tree.appendChild(dbItem);
        tree.appendChild(tableNode);
      });
    } catch (err) {
      tree.innerHTML = `<div style="color:var(--break); font-size:0.75rem; padding: 10px;">${escapeHtml(err.message)}</div>`;
    }
  };

  const selectSubtable = async (dbname, tablename) => {
    currentDb = dbname;
    currentTable = tablename;
    rowsOffset = 0;
    
    // Show cards
    document.getElementById('db-schema-card').style.display = 'flex';
    document.getElementById('schema-card-title').textContent = `SCHEMA — ${dbname}.${tablename}`;
    document.getElementById('rows-card-title').textContent = `RECORDS — ${dbname}.${tablename}`;

    await loadTableSchema();
    await loadTableRows();
  };

  const loadTableSchema = async () => {
    const tbody = document.getElementById('schema-table-body');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; opacity:0.5;">Loading schema...</td></tr>';
    try {
      const cols = await get(`/api/databases/${currentDb}/schema/${currentTable}`);
      tbody.innerHTML = '';
      cols.forEach(col => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${col.cid}</td>
          <td style="color: var(--dust); font-weight:600;">${escapeHtml(col.name)}</td>
          <td style="color: var(--lapis-bright);">${escapeHtml(col.type)}</td>
          <td>${col.notnull ? 'YES' : 'NO'}</td>
          <td>${col.default !== null ? escapeHtml(String(col.default)) : 'NULL'}</td>
          <td style="color: ${col.pk ? 'var(--gold)' : 'var(--dust-ghost)'}; font-weight: 700;">${col.pk ? 'PRIMARY KEY' : '-'}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:var(--break); text-align:center;">${escapeHtml(err.message)}</td></tr>`;
    }
  };

  const loadTableRows = async () => {
    const container = document.getElementById('table-rows-container');
    const pagination = document.getElementById('rows-pagination');
    container.innerHTML = '<div style="text-align:center; padding: 30px; opacity:0.5;">Querying records...</div>';
    pagination.style.display = 'none';

    try {
      const res = await get(`/api/databases/${currentDb}/tables/${currentTable}?limit=${rowsLimit}&offset=${rowsOffset}`);
      container.innerHTML = '';

      if (res.rows.length === 0) {
        container.innerHTML = `<div class="empty-state"><div class="desc">No rows found in this table.</div></div>`;
        return;
      }

      // Draw table structure
      const table = document.createElement('table');
      table.className = 'data-table';
      
      const thead = document.createElement('thead');
      const headerTr = document.createElement('tr');
      res.columns.forEach(col => {
        headerTr.innerHTML += `<th>${escapeHtml(col)}</th>`;
      });
      thead.appendChild(headerTr);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      res.rows.forEach(row => {
        const tr = document.createElement('tr');
        res.columns.forEach(col => {
          const val = row[col];
          let displayVal = val === null ? '<span style="opacity:0.3;">NULL</span>' : escapeHtml(String(val));
          if (typeof val === 'string' && val.length > 120) {
            displayVal = `<span title="${escapeHtml(val)}">${escapeHtml(val.slice(0, 120))}...</span>`;
          }
          tr.innerHTML += `<td>${displayVal}</td>`;
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      container.appendChild(table);

      // Pagination update
      pagination.style.display = 'flex';
      document.getElementById('btn-rows-prev').disabled = rowsOffset === 0;
      document.getElementById('btn-rows-next').disabled = rowsOffset + rowsLimit >= res.total;
      document.getElementById('rows-page-info').textContent = `Showing ${rowsOffset + 1} - ${Math.min(rowsOffset + rowsLimit, res.total)} of ${res.total}`;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--break); padding:30px; text-align:center;">${escapeHtml(err.message)}</div>`;
    }
  };

  // Row browser pagination
  document.getElementById('btn-rows-prev').addEventListener('click', () => {
    if (rowsOffset >= rowsLimit) {
      rowsOffset -= rowsLimit;
      loadTableRows();
    }
  });

  document.getElementById('btn-rows-next').addEventListener('click', () => {
    rowsOffset += rowsLimit;
    loadTableRows();
  });

  await loadDatabaseTree();
}


/* ═══════════════════════════════════════════════════════════════
   PAGE: SQL QUERY CONSOLE
   ═══════════════════════════════════════════════════════════════ */
async function renderQueryPage(container) {
  container.innerHTML = `
    <div class="panel-header slide-in">
      <div class="panel-title">SQL READ-ONLY CONSOLE</div>
      <div class="panel-badge beta">SANDBOX</div>
    </div>
    <div class="panel-body slide-in" style="display: flex; flex-direction: column; gap: 20px; overflow: hidden; height: calc(100% - var(--header-height));">
      
      <!-- Control / Editor card -->
      <div class="card" style="display: flex; flex-direction: column; gap: 12px; min-height: 250px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="card-title" style="margin-bottom: 0;">Query Console</div>
          <select class="select" id="query-db-select" style="min-width: 200px;">
            <option value="">Select target database...</option>
          </select>
        </div>

        <div class="code-editor" style="flex: 1; display: flex; flex-direction: column;">
          <textarea id="query-sql-text" placeholder="SELECT * FROM ledger_entries ORDER BY seq DESC LIMIT 10;" spellcheck="false"></textarea>
          <div class="code-editor-toolbar">
            <span style="font-size:0.6rem; color:var(--dust-faint); letter-spacing:0.04em;">READ-ONLY ENFORCED (MUTATIONS BLOCKED)</span>
            <button class="btn btn-primary" id="btn-run-query">⚡ Run Query</button>
          </div>
        </div>
      </div>

      <!-- Results Card -->
      <div class="card" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;" id="query-results-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div class="card-title" style="margin-bottom: 0;">Output Console</div>
          <div style="font-size: 0.65rem; color: var(--dust-faint);" id="query-meta">-</div>
        </div>
        <div style="flex: 1; overflow: auto;" id="query-output-container">
          <div class="empty-state">
            <div class="icon">❯_</div>
            <div class="desc">Enter SQL query and click Run to display output schema and records.</div>
          </div>
        </div>
      </div>

    </div>
  `;

  // Populate db select dropdown
  const select = document.getElementById('query-db-select');
  try {
    const dbs = await get('/api/databases');
    dbs.forEach(db => {
      const opt = document.createElement('option');
      opt.value = db.name;
      opt.textContent = `${db.name} (${db.size_human})`;
      select.appendChild(opt);
    });
    // Default select first database if available
    if (dbs.length > 0) {
      select.value = dbs[0].name;
    }
  } catch (err) {
    console.error(err);
  }

  // Execute query action
  const executeQuery = async () => {
    const db = select.value;
    const sql = document.getElementById('query-sql-text').value.trim();
    const container = document.getElementById('query-output-container');
    const meta = document.getElementById('query-meta');
    const btn = document.getElementById('btn-run-query');

    if (!db) {
      alert('Please select a target database.');
      return;
    }
    if (!sql) {
      alert('Please enter a SQL statement.');
      return;
    }

    btn.disabled = true;
    container.innerHTML = '<div style="text-align:center; padding: 40px; opacity:0.5;">Executing transaction against read-only core...</div>';
    meta.textContent = '-';

    try {
      const res = await post('/api/query', { database: db, sql: sql });
      container.innerHTML = '';
      meta.textContent = `Rows: ${res.row_count} | Elapsed: ${res.elapsed_ms}ms`;

      if (res.row_count === 0) {
        container.innerHTML = `<div class="empty-state"><div class="desc">Query executed successfully. 0 records returned.</div></div>`;
        return;
      }

      // Draw output table
      const table = document.createElement('table');
      table.className = 'data-table';
      
      const thead = document.createElement('thead');
      const headerTr = document.createElement('tr');
      res.columns.forEach(col => {
        headerTr.innerHTML += `<th>${escapeHtml(col)}</th>`;
      });
      thead.appendChild(headerTr);
      table.appendChild(thead);

      const tbody = document.createElement('tbody');
      res.rows.forEach(row => {
        const tr = document.createElement('tr');
        res.columns.forEach(col => {
          const val = row[col];
          let displayVal = val === null ? '<span style="opacity:0.3;">NULL</span>' : escapeHtml(String(val));
          if (typeof val === 'string' && val.length > 150) {
            displayVal = `<span title="${escapeHtml(val)}">${escapeHtml(val.slice(0, 150))}...</span>`;
          }
          tr.innerHTML += `<td>${displayVal}</td>`;
        });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      container.appendChild(table);

    } catch (err) {
      container.innerHTML = `
        <div class="empty-state" style="color: var(--break);">
          <div class="icon">✕</div>
          <div class="title" style="color: var(--break);">SQL Execution Error</div>
          <div class="desc" style="color: var(--dust-dim); margin-top: 6px;">${escapeHtml(err.message)}</div>
        </div>
      `;
    } finally {
      btn.disabled = false;
    }
  };

  document.getElementById('btn-run-query').addEventListener('click', executeQuery);

  // Command+Enter / Ctrl+Enter helper to execute
  document.getElementById('query-sql-text').addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      executeQuery();
    }
  });
}


/* ═══════════════════════════════════════════════════════════════
   PAGE: TELEMETRY STREAM
   ═══════════════════════════════════════════════════════════════ */
function renderTelemetryPage(container) {
  container.innerHTML = `
    <div class="panel-header slide-in">
      <div class="panel-title">SYSTEM TELEMETRY LIVE FEED</div>
      <div class="panel-badge live" id="telemetry-connection-badge">CONNECTING...</div>
    </div>
    <div class="panel-body slide-in">
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total DB footprints</div>
          <div class="stat-value lapis" id="telemetry-db-total-size">0.00 MB</div>
          <div class="stat-sub" id="telemetry-db-count">0 database files mapped</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active WAL files</div>
          <div class="stat-value gold" id="telemetry-wal-count">0</div>
          <div class="stat-sub">Write-Ahead Logging enabled</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Max RSS footprint</div>
          <div class="stat-value verify" id="telemetry-rss-footprint">0.00 MB</div>
          <div class="stat-sub" id="telemetry-cpu-times">CPU: u0.00s / s0.00s</div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        
        <!-- DB details card -->
        <div class="card" style="display:flex; flex-direction:column; min-height: 250px;">
          <div class="card-title">Database Storage Map</div>
          <div style="flex:1; overflow-y:auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Footprint Size</th>
                </tr>
              </thead>
              <tbody id="telemetry-db-table-body">
                <tr><td colspan="2" class="empty-state">Awaiting live feed snapshot...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Git info card -->
        <div class="card" style="display:flex; flex-direction:column;">
          <div class="card-title">Version Control Ledger</div>
          <div style="flex: 1; display:flex; flex-direction:column; gap:16px; font-family: var(--font-mono); font-size:0.75rem; color: var(--dust-dim);">
            <div>
              <div class="stat-label">Git Sentinel Status</div>
              <div id="telemetry-git-state" style="color:var(--dust); font-weight:600; margin-top:4px;">-</div>
            </div>
            <div>
              <div class="stat-label">Current HEAD linkage</div>
              <div id="telemetry-git-head" style="color:var(--lapis-bright); margin-top:4px;">-</div>
            </div>
            <div>
              <div class="stat-label">Compressed pack footprint</div>
              <div id="telemetry-git-pack-size" style="color:var(--dust); margin-top:4px;">-</div>
            </div>
            <div style="margin-top: auto; opacity:0.3; font-size:0.6rem; border-top:1px solid var(--edge); padding-top:10px;">
              Project Root: <span id="telemetry-project-root">-</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  `;

  // Establish live websocket connection
  if (telemetrySocket) {
    try { telemetrySocket.close(); } catch {}
  }

  const badge = document.getElementById('telemetry-connection-badge');

  telemetrySocket = connectWebSocket('/ws/telemetry', 
    // onMessage callback
    (snapshot) => {
      badge.textContent = 'LIVE FEED';
      badge.className = 'panel-badge live';
      
      // Update sizes
      document.getElementById('telemetry-db-total-size').textContent = `${snapshot.total_db_size_mb} MB`;
      document.getElementById('telemetry-db-count').textContent = `${snapshot.databases.length} database files mapped`;
      document.getElementById('telemetry-wal-count').textContent = snapshot.wal_files.length;
      
      // Process CPU/RSS
      if (snapshot.process && snapshot.process.max_rss_mb !== undefined) {
        document.getElementById('telemetry-rss-footprint').textContent = `${snapshot.process.max_rss_mb} MB`;
        document.getElementById('telemetry-cpu-times').textContent = `CPU: u${snapshot.process.user_time_s}s / s${snapshot.process.system_time_s}s`;
      }

      // Populate DB list table
      const tbody = document.getElementById('telemetry-db-table-body');
      tbody.innerHTML = '';
      snapshot.databases.forEach(db => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td style="color:var(--dust); font-weight:600;">${escapeHtml(db.name)}</td>
          <td>${db.size_mb} MB</td>
        `;
        tbody.appendChild(tr);
      });

      // Populate Git info
      const git = snapshot.git;
      if (git && git.exists) {
        document.getElementById('telemetry-git-state').innerHTML = '<span style="color:var(--verify);">ACTIVE & WATCHING</span>';
        document.getElementById('telemetry-git-head').textContent = git.head || 'UNKNOWN';
        document.getElementById('telemetry-git-pack-size').textContent = `${git.pack_size_mb} MB`;
      } else {
        document.getElementById('telemetry-git-state').innerHTML = '<span style="color:var(--break);">NOT INSTANTIATED</span>';
        document.getElementById('telemetry-git-head').textContent = 'None';
        document.getElementById('telemetry-git-pack-size').textContent = '0.00 MB';
      }
      document.getElementById('telemetry-project-root').textContent = snapshot.project_root;
    },
    // onError callback
    () => {
      badge.textContent = 'DISCONNECTED';
      badge.className = 'panel-badge beta';
      setConnectionState('error', 'DISCONNECTED');
    }
  );

  // Auto clean socket when moving pages
  const checkStateInterval = setInterval(() => {
    const mainEl = document.getElementById('main-content');
    // If the telemetry views are not in active main element anymore, kill socket
    if (!mainEl || !document.getElementById('telemetry-connection-badge')) {
      if (telemetrySocket) {
        try { telemetrySocket.close(); } catch {}
        telemetrySocket = null;
      }
      clearInterval(checkStateInterval);
    }
  }, 1000);
}


/* ═══════════════════════════════════════════════════════════════
   UTILITY HELPERS
   ═══════════════════════════════════════════════════════════════ */
function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
