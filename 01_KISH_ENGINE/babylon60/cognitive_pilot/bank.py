"""Versioned, synthetic software problems with parent-owned hidden oracles.

Fixtures are benchmark inputs, never observations of Babylon's performance.
Agents receive public cases only. Reference answers stay in the evaluator.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import random
from typing import cast

from blake3 import blake3


STAGES = ("quality", "transfer", "exploration", "activation", "retention")


@dataclass(frozen=True)
class Family:
    name: str
    domain: str
    specification: str
    starter: str


FAMILIES = (
    Family(
        "idempotency",
        "knowledge",
        "Input events=[[id,amount],...]. Sum amounts once per id, first occurrence wins.",
        "def solve(p):\n    return sum(e[1] for e in p['events'])",
    ),
    Family(
        "backoff",
        "knowledge",
        "Input count,base,cap. Return count delays: min(cap,base*2**i), i starts at zero.",
        "def solve(p):\n    return [p['base']*2**i for i in range(p['count'])]",
    ),
    Family(
        "cache",
        "knowledge",
        "Input now,entries=[[key,expiry],...], unique keys. Return sorted keys with expiry strictly > now.",
        "def solve(p):\n    return sorted(k for k,t in p['entries'] if t >= p['now'])",
    ),
    Family(
        "checkpoint",
        "knowledge",
        "Input seen and events, lists of ids. Return new ids once, preserving event order.",
        "def solve(p):\n    return [x for x in p['events'] if x not in p['seen']]",
    ),
    Family(
        "dependencies",
        "knowledge",
        "Input nodes and edges=[predecessor,successor]. Return lexicographically smallest topological order; null for a cycle.",
        "def solve(p):\n    return sorted(p['nodes'])",
    ),
    Family(
        "contract",
        "knowledge",
        "Input required field names and rows (objects). Return indices of rows containing every required field with non-null value; 0 and false are valid.",
        "def solve(p):\n    return [i for i,r in enumerate(p['rows']) if all(r.get(k) for k in p['required'])]",
    ),
    Family(
        "intervals",
        "creativity",
        "Input ranges=[[start,end],...], start<=end. Return sorted union, merging overlapping or touching closed intervals.",
        "def solve(p):\n    pass",
    ),
    Family(
        "allocation",
        "creativity",
        "Input weights,values (equal length, nonnegative integers), capacity. Return maximum total value of a subset whose total weight <= capacity; each item at most once.",
        "def solve(p):\n    pass",
    ),
    Family(
        "window",
        "creativity",
        "Input values and width>=1. Return maximum of each consecutive full window; [] when width exceeds length.",
        "def solve(p):\n    pass",
    ),
    Family(
        "offline_merge",
        "creativity",
        "Input records=[[key,version,value],...], integer version, string value. Select greatest version per key; ties choose lexicographically smallest value. Return [key,version,value] rows sorted by key.",
        "def solve(p):\n    pass",
    ),
    Family(
        "packing",
        "creativity",
        "Input weights and limit>0, all weights in [1,limit]. Return the minimum number of contiguous batches, each total <=limit, preserving order. Empty input returns 0.",
        "def solve(p):\n    pass",
    ),
    Family(
        "routing",
        "creativity",
        "Input nodes,edges=[[a,b,weight],...] directed nonnegative weights, source,target. Return shortest distance or null if unreachable.",
        "def solve(p):\n    pass",
    ),
)


def family(name: str) -> Family:
    return next(f for f in FAMILIES if f.name == name)


def oracle(name: str, p: dict[str, object]) -> object:
    """Trusted evaluator only. No generated source is executed here."""
    if name == "idempotency":
        first: dict[str, int] = {}
        for key, amount in cast(list[tuple[str, int]], p["events"]):
            first.setdefault(key, amount)
        return sum(first.values())
    if name == "backoff":
        return [
            min(int(cast(int, p["cap"])), int(cast(int, p["base"])) * 2**i) for i in range(int(cast(int, p["count"])))
        ]
    if name == "cache":
        return sorted(k for k, t in cast(list[tuple[str, int]], p["entries"]) if t > cast(int, p["now"]))
    if name == "checkpoint":
        seen = set(cast(list[str], p["seen"]))
        output = []
        for item in cast(list[str], p["events"]):
            if item not in seen:
                output.append(item)
                seen.add(item)
        return output
    if name == "dependencies":
        remaining = set(cast(list[str], p["nodes"]))
        edges = cast(list[tuple[str, str]], p["edges"])
        order = []
        while remaining:
            ready = sorted(x for x in remaining if not any(b == x and a in remaining for a, b in edges))
            if not ready:
                return None
            order.append(ready[0])
            remaining.remove(ready[0])
        return order
    if name == "contract":
        required = cast(list[str], p["required"])
        return [
            i
            for i, row in enumerate(cast(list[dict[str, object]], p["rows"]))
            if all(k in row and row[k] is not None for k in required)
        ]
    if name == "intervals":
        merged: list[list[int]] = []
        for a, b in sorted(cast(list[list[int]], p["ranges"])):
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(b, merged[-1][1])
            else:
                merged.append([a, b])
        return merged
    if name == "allocation":
        weights, values = cast(list[int], p["weights"]), cast(list[int], p["values"])
        capacity = cast(int, p["capacity"])
        return max(
            sum(values[i] for i in range(len(weights)) if mask >> i & 1)
            for mask in range(1 << len(weights))
            if sum(weights[i] for i in range(len(weights)) if mask >> i & 1) <= capacity
        )
    if name == "window":
        values, width = cast(list[int], p["values"]), cast(int, p["width"])
        return [max(values[i : i + width]) for i in range(len(values) - width + 1)]
    if name == "offline_merge":
        selected: dict[str, tuple[int, str]] = {}
        for key, version, value in cast(list[tuple[str, int, str]], p["records"]):
            if key not in selected or (-version, value) < (-selected[key][0], selected[key][1]):
                selected[key] = (version, value)
        return [[key, *selected[key]] for key in sorted(selected)]
    if name == "packing":
        count, total = 0, 0
        for weight in cast(list[int], p["weights"]):
            if total == 0 or total + weight > cast(int, p["limit"]):
                count += 1
                total = weight
            else:
                total += weight
        return count
    if name == "routing":
        distances = {cast(str, p["source"]): 0}
        for _ in cast(list[str], p["nodes"]):
            for origin, destination, weight in cast(list[tuple[str, str, int]], p["edges"]):
                if origin in distances and (
                    destination not in distances or distances[origin] + weight < distances[destination]
                ):
                    distances[destination] = distances[origin] + weight
        return distances.get(cast(str, p["target"]))
    raise ValueError(f"Unknown family: {name}")


def inputs(name: str, rng: random.Random, index: int) -> dict[str, object]:
    """Include empty inputs, ties, repeated ids, cycles and boundary values."""
    n = index % 9
    keys = [f"k{rng.randrange(5)}" for _ in range(n)]
    if name == "idempotency":
        return {"events": [[k, rng.randint(-8, 12)] for k in keys]}
    if name == "backoff":
        return {"count": n, "base": rng.randint(1, 4), "cap": rng.randint(2, 12)}
    if name == "cache":
        return {"now": 5, "entries": [[f"k{i}", rng.choice([4, 5, 6])] for i in range(n)]}
    if name == "checkpoint":
        return {"seen": keys[:2], "events": keys + keys[:2]}
    if name in {"dependencies", "routing"}:
        nodes = [f"n{i}" for i in range(max(2, n))]
        edges = [[a, b] for a in nodes for b in nodes if a != b and rng.random() < 0.15]
        if name == "dependencies":
            return {"nodes": nodes, "edges": edges}
        return {
            "nodes": nodes,
            "edges": [[a, b, rng.randrange(6)] for a, b in edges],
            "source": nodes[0],
            "target": nodes[-1],
        }
    if name == "contract":
        return {
            "required": ["a", "b"],
            "rows": [
                rng.choice([{"a": 0, "b": False}, {"a": None, "b": 2}, {"a": 1}, {"a": 3, "b": ""}]) for _ in range(n)
            ],
        }
    if name == "intervals":
        return {"ranges": [[a, a + rng.randrange(5)] for a in [rng.randint(-5, 8) for _ in range(n)]]}
    if name == "allocation":
        return {
            "weights": [rng.randrange(6) for _ in range(n)],
            "values": [rng.randrange(10) for _ in range(n)],
            "capacity": rng.randrange(12),
        }
    if name == "window":
        return {"values": [rng.randint(-10, 10) for _ in range(n)], "width": rng.randint(1, 5)}
    if name == "offline_merge":
        return {"records": [[k, rng.randrange(3), rng.choice(["a", "b", "c"])] for k in keys]}
    if name == "packing":
        return {"weights": [rng.randint(1, 7) for _ in range(n)], "limit": 7}
    raise ValueError(name)


def cases(name: str, stage: str, seed: int, hidden: bool = False) -> list[dict[str, object]]:
    material = f"bank-v1:{name}:{stage}:{seed}:{hidden}".encode()
    rng = random.Random(int.from_bytes(blake3(material).digest(), "big"))
    if not hidden:
        return [{"input": p, "expected": oracle(name, p)} for p in (inputs(name, rng, i) for i in range(3))]
    seen = {json.dumps(case["input"], sort_keys=True) for case in cases(name, stage, seed)}
    result: list[dict[str, object]] = []
    for index in range(2700):
        value = inputs(name, rng, index)
        key = json.dumps(value, sort_keys=True)
        if key not in seen:
            result.append({"input": value, "expected": oracle(name, value)})
            seen.add(key)
            if len(result) == 27:
                return result
    raise ValueError("Task bank cannot supply 27 distinct hidden inputs")


def public_task(name: str, stage: str, seed: int) -> dict[str, object]:
    item = family(name)
    return {
        "id": f"{name}.{stage}",
        "family": name,
        "domain": item.domain,
        "stage": stage,
        "specification": item.specification,
        "starter": item.starter,
        "public_cases": cases(name, stage, seed),
        "instruction": "Implement solve(p) as pure Python returning JSON-compatible values. No I/O or network. "
        "For exploration supply up to five executable implementations using distinct mechanisms. "
        "Return artifacts and concise factual descriptions only, never hidden reasoning.",
    }
