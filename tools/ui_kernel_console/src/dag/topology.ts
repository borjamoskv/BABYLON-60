/**
 * Orden topológico determinista (Kahn con montículo mínimo) y profundidad causal.
 *
 * Coste: O(V log V + E). El término log V es el precio del desempate determinista (siempre se
 * extrae el nodo listo de menor identificador); detectar ciclos por sí solo sería O(V + E).
 * El orden entre identificadores es el de sus bytes UTF-8, igual en cualquier lenguaje.
 *
 * Precondición: identificadores únicos y todo padre presente en `nodes`. La función no la asume a
 * ciegas: devuelve `precondition_violated` en lugar de producir un orden sobre datos incoherentes.
 */

import { compareBytes, utf8 } from "../crypto/bytes.ts";

export interface TopologyNode {
  readonly node_id: string;
  readonly parent_ids: readonly string[];
}

export interface TopologyResult {
  /** `true` solo si todos los nodos quedaron ordenados. */
  readonly acyclic: boolean;
  /** Identificadores en orden topológico (prefijo ordenable si hay ciclo). */
  readonly order: readonly string[];
  /** Profundidad (camino más largo desde una raíz) de cada elemento de `order`, en el mismo orden. */
  readonly depths: readonly number[];
  /** Nodos que forman parte de un ciclo o dependen de uno, ordenados por identificador. */
  readonly unresolved: readonly string[];
  /** Identificador duplicado o padre inexistente detectado; el resto de campos queda vacío. */
  readonly precondition_violated: boolean;
}

const EMPTY: TopologyResult = Object.freeze({
  acyclic: false,
  order: Object.freeze([]),
  depths: Object.freeze([]),
  unresolved: Object.freeze([]),
  precondition_violated: true,
});

/** Montículo binario mínimo de enteros. */
class MinHeap {
  private readonly items: number[] = [];

  get size(): number {
    return this.items.length;
  }

  push(value: number): void {
    const a = this.items;
    a.push(value);
    let i = a.length - 1;
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (a[parent]! <= a[i]!) break;
      const tmp = a[parent]!;
      a[parent] = a[i]!;
      a[i] = tmp;
      i = parent;
    }
  }

  pop(): number {
    const a = this.items;
    const top = a[0]!;
    const last = a.pop()!;
    if (a.length > 0) {
      a[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1;
        const r = l + 1;
        let smallest = i;
        if (l < a.length && a[l]! < a[smallest]!) smallest = l;
        if (r < a.length && a[r]! < a[smallest]!) smallest = r;
        if (smallest === i) break;
        const tmp = a[smallest]!;
        a[smallest] = a[i]!;
        a[i] = tmp;
        i = smallest;
      }
    }
    return top;
  }
}

/** Índices de `ids` ordenados por los bytes UTF-8 del identificador. */
export function sortIndicesById(ids: readonly string[]): number[] {
  const encoded = ids.map((id) => utf8(id));
  const indices = ids.map((_, i) => i);
  indices.sort((a, b) => compareBytes(encoded[a]!, encoded[b]!));
  return indices;
}

export function topologicalOrder(nodes: readonly TopologyNode[]): TopologyResult {
  const n = nodes.length;
  const indexOf = new Map<string, number>();
  for (let i = 0; i < n; i++) {
    const id = nodes[i]!.node_id;
    if (indexOf.has(id)) return EMPTY;
    indexOf.set(id, i);
  }

  // rank[i] = posición del nodo i en el orden por identificador; el montículo compara rangos.
  const byId = sortIndicesById(nodes.map((x) => x.node_id));
  const rank = new Int32Array(n);
  for (let r = 0; r < n; r++) rank[byId[r]!] = r;

  const inDegree = new Int32Array(n);
  const children: number[][] = Array.from({ length: n }, () => []);
  for (let i = 0; i < n; i++) {
    for (const parentId of nodes[i]!.parent_ids) {
      const p = indexOf.get(parentId);
      if (p === undefined) return EMPTY;
      inDegree[i] = inDegree[i]! + 1;
      children[p]!.push(i);
    }
  }

  const depth = new Int32Array(n);
  const heap = new MinHeap();
  for (let i = 0; i < n; i++) {
    if (inDegree[i] === 0) heap.push(rank[i]!);
  }

  const order: string[] = [];
  const depths: number[] = [];
  while (heap.size > 0) {
    const current = byId[heap.pop()]!;
    order.push(nodes[current]!.node_id);
    depths.push(depth[current]!);
    for (const child of children[current]!) {
      if (depth[child]! < depth[current]! + 1) depth[child] = depth[current]! + 1;
      inDegree[child] = inDegree[child]! - 1;
      if (inDegree[child] === 0) heap.push(rank[child]!);
    }
  }

  const unresolved: string[] = [];
  if (order.length !== n) {
    for (const i of byId) {
      if (inDegree[i]! > 0) unresolved.push(nodes[i]!.node_id);
    }
  }

  return {
    acyclic: order.length === n,
    order,
    depths,
    unresolved,
    precondition_violated: false,
  };
}
