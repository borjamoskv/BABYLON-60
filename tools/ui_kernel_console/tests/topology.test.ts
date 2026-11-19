import assert from "node:assert/strict";
import { test } from "node:test";
import { topologicalOrder, type TopologyNode } from "../src/dag/topology.ts";

function lcg(seed: number): () => number {
  let x = seed >>> 0;
  return () => {
    x = (Math.imul(1664525, x) + 1013904223) >>> 0;
    return x / 0x1_0000_0000;
  };
}

const id = (i: number): string => `EV_${String(i).padStart(8, "0")}_000000`;

/** Referencia cuadrática: en cada paso coloca el menor identificador cuyos padres ya están colocados. */
function referenceOrder(nodes: readonly TopologyNode[]): { order: string[]; depths: number[] } {
  const placed = new Map<string, number>();
  const order: string[] = [];
  const depths: number[] = [];
  const remaining = [...nodes].sort((a, b) => (a.node_id < b.node_id ? -1 : a.node_id > b.node_id ? 1 : 0));
  for (;;) {
    const idx = remaining.findIndex((n) => n.parent_ids.every((p) => placed.has(p)));
    if (idx < 0) break;
    const [n] = remaining.splice(idx, 1);
    const depth = n!.parent_ids.length === 0 ? 0 : Math.max(...n!.parent_ids.map((p) => placed.get(p)!)) + 1;
    placed.set(n!.node_id, depth);
    order.push(n!.node_id);
    depths.push(depth);
  }
  return { order, depths };
}

function randomDag(n: number, rand: () => number): TopologyNode[] {
  // Etiquetas barajadas para que el orden por identificador no coincida con el de construcción.
  const labels = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [labels[i], labels[j]] = [labels[j]!, labels[i]!];
  }
  return Array.from({ length: n }, (_, i) => {
    const parents = new Set<string>();
    const k = i === 0 ? 0 : Math.floor(rand() * Math.min(4, i + 1));
    for (let p = 0; p < k; p++) parents.add(id(labels[Math.floor(rand() * i)]!));
    return { node_id: id(labels[i]!), parent_ids: [...parents] };
  });
}

function shuffled<T>(items: readonly T[], rand: () => number): T[] {
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j]!, out[i]!];
  }
  return out;
}

test("orden topológico: coincide con la referencia cuadrática en 300 DAG pseudoaleatorios", () => {
  const rand = lcg(60);
  for (let round = 0; round < 300; round++) {
    const nodes = randomDag(1 + Math.floor(rand() * 40), rand);
    const expected = referenceOrder(nodes);
    const actual = topologicalOrder(nodes);
    assert.ok(actual.acyclic);
    assert.deepEqual(actual.order, expected.order);
    assert.deepEqual(actual.depths, expected.depths);
    assert.deepEqual(actual.unresolved, []);
  }
});

test("orden topológico: invariante ante permutación del array y del orden de los padres", () => {
  const rand = lcg(7);
  for (let round = 0; round < 50; round++) {
    const nodes = randomDag(30, rand);
    const base = topologicalOrder(nodes);
    const permuted = shuffled(nodes, rand).map((n) => ({ node_id: n.node_id, parent_ids: shuffled(n.parent_ids, rand) }));
    const again = topologicalOrder(permuted);
    assert.deepEqual(again.order, base.order);
    assert.deepEqual(again.depths, base.depths);
  }
});

test("orden topológico: los ciclos se detectan siempre y el recorrido termina", () => {
  const a = id(1);
  const b = id(2);
  const c = id(3);
  const d = id(4);
  const cases: [string, TopologyNode[], string[], string[]][] = [
    ["autorreferencia", [{ node_id: a, parent_ids: [a] }], [], [a]],
    ["ciclo de dos", [{ node_id: a, parent_ids: [b] }, { node_id: b, parent_ids: [a] }], [], [a, b]],
    ["ciclo con cola", [{ node_id: a, parent_ids: [] }, { node_id: b, parent_ids: [a, d] }, { node_id: c, parent_ids: [b] }, { node_id: d, parent_ids: [c] }], [a], [b, c, d]],
    ["descendiente de un ciclo", [{ node_id: a, parent_ids: [b] }, { node_id: b, parent_ids: [a] }, { node_id: c, parent_ids: [a] }], [], [a, b, c]],
  ];
  for (const [label, nodes, order, unresolved] of cases) {
    const result = topologicalOrder(nodes);
    assert.equal(result.acyclic, false, label);
    assert.deepEqual(result.order, order, label);
    assert.deepEqual(result.unresolved, unresolved, label);
    assert.equal(result.precondition_violated, false, label);
  }
});

test("orden topológico: grafo incoherente (id duplicado, padre ausente) no produce orden", () => {
  const a = id(1);
  assert.ok(topologicalOrder([{ node_id: a, parent_ids: [] }, { node_id: a, parent_ids: [] }]).precondition_violated);
  assert.ok(topologicalOrder([{ node_id: a, parent_ids: [id(9)] }]).precondition_violated);
  const empty = topologicalOrder([]);
  assert.ok(empty.acyclic && empty.order.length === 0);
});

test("orden topológico: coste casi lineal en la forma que degrada a cuadrático una cola reordenada", () => {
  // Estrella: una raíz y V-1 hijos listos a la vez. Con «push + sort» por nodo esto es Θ(V² log V).
  const star = (v: number): TopologyNode[] => [
    { node_id: id(0), parent_ids: [] },
    ...Array.from({ length: v - 1 }, (_, i) => ({ node_id: id(v - i), parent_ids: [id(0)] })),
  ];
  const time = (v: number): number => {
    const nodes = star(v);
    const t0 = performance.now();
    const r = topologicalOrder(nodes);
    const elapsed = performance.now() - t0;
    assert.ok(r.acyclic && r.order.length === v);
    return elapsed;
  };
  time(2000); // calentamiento
  const small = Math.min(time(8000), time(8000), time(8000));
  const large = Math.min(time(64000), time(64000), time(64000));
  // 8× nodos: n log n predice ~10×; cuadrático predice 64×.
  assert.ok(large < 2000, `64k nodos tardaron ${large.toFixed(1)} ms`);
  assert.ok(large / Math.max(small, 0.5) < 32, `razón 64k/8k = ${(large / small).toFixed(1)}`);
});
