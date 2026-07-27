# Cortex Memory
Stateful memory layer for AI agents.
Most AI agents are stateless.
Cortex makes them remember.
---
## Quickstart
```bash
cd docker && docker compose up
```

## Python SDK
```python
from cortex import CortexClient
client = CortexClient()
client.add("u1", "a1", "user likes infra systems")
print(client.query("u1", "what does user like?"))
```

## API
POST /memory/add
POST /memory/query


---

```yaml
AESTHETIC:    INDUSTRIAL NOIR 2026 (#0A0A0A / #2B3BE5)
EPISTEMOLOGY: C5-REAL EDG V6 — Error Navigation System
CORE TENET:   Optimize for correction, not certainty. Uncertainty is telemetry, not weakness.
UPDATED:      June 2026 — Falsifiable Memory Infrastructure
```
