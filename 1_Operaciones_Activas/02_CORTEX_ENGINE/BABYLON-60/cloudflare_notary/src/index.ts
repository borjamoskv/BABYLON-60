// C5-REAL EXERGY CERTIFIED
import { Hono } from 'hono'
import { cors } from 'hono/cors'

type Bindings = {
  BFT_DB: D1Database
}

const app = new Hono<{ Bindings: Bindings }>()

app.use('*', cors({
  origin: ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:4173'],
  allowHeaders: ['Content-Type'],
  allowMethods: ['POST', 'GET', 'OPTIONS'],
}))

app.get('/health', (c) => c.json({ status: 'C5-REAL Notary Active', exergy: 100 }))

app.post('/seal', async (c) => {
  try {
    const { logs } = await c.req.json()
    if (!logs || !Array.isArray(logs) || logs.length === 0 || logs.length > 100) {
      return c.json({ error: 'Invalid payload: logs must be a non-empty array of max 100 items' }, 400)
    }

    // Harden Notary: Input validation for each log entry
    for (const log of logs) {
      if (!log || typeof log !== 'object') return c.json({ error: 'Invalid log entry structure' }, 400);
      if (typeof log.nodeId !== 'string' || typeof log.parentId !== 'string' ||
          typeof log.payloadHash !== 'string' || typeof log.status !== 'string') {
        return c.json({ error: 'Invalid log entry types: strictly string fields required' }, 400);
      }
      if (log.payloadHash.length > 128 || log.nodeId.length > 128) {
         return c.json({ error: 'Entropy constraint violation: hash size too large' }, 400);
      }
    }

    const stmts = logs.map(log =>
      c.env.BFT_DB.prepare(
        'INSERT INTO bft_seals (node_id, parent_id, payload_hash, status) VALUES (?, ?, ?, ?)'
      ).bind(log.nodeId, log.parentId, log.payloadHash, log.status)
    )

    await c.env.BFT_DB.batch(stmts)
    return c.json({ status: 'Sealed', count: stmts.length })
  } catch (error) {
    console.error("Seal Error", error);
    return c.json({ error: 'Internal Entropy Error' }, 500)
  }
})

app.get('/ledger', async (c) => {
  const { results } = await c.env.BFT_DB.prepare(
    'SELECT * FROM bft_seals ORDER BY timestamp DESC LIMIT 100'
  ).all()
  return c.json({ ledger: results })
})

export default app
