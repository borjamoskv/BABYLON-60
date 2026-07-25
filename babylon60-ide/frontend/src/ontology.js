import { isTauri } from "./api.js";
let invoke = null;
if (isTauri) {
  import("@tauri-apps/api/core")
    .then((m) => {
      invoke = m.invoke;
    })
    .catch(() => {});
}
export const Domain = Object.freeze([
  "SOURCE",
  "MATRIX",
  "PULSE",
  "KINETIC",
  "LOGIC",
  "VECTOR",
  "STORAGE",
  "OSINT",
  "CLOCK",
  "COMPILER",
]);
export const Primitive = Object.freeze([
  "INIT",
  "MUTATE",
  "BIND",
  "QUERY",
  "STREAM",
  "COMMIT",
  "SYNC",
  "HALT",
  "FORK",
  "JOIN",
]);
export const Modifier = Object.freeze([
  "RAW",
  "ATOMIC",
  "PERSIST",
  "EPHEMERAL",
  "ASYNC",
  "SYNC",
  "QUANTIZED",
  "MAPPED",
  "WRAPPED",
  "LOCKED",
]);
export async function listVectors() {
  if (isTauri && invoke) {
    return await invoke("list_ontology_vectors");
  }
  const res = await fetch("/api/ontology/vectors");
  if (!res.ok) throw new Error(`Ontology fetch failed: ${res.statusText}`);
  return res.json();
}
export async function dispatchVector(domain, primitive, modifier) {
  if (isTauri && invoke) {
    return await invoke("dispatch_vector", { domain, primitive, modifier });
  }
  const res = await fetch("/api/ontology/dispatch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain, primitive, modifier }),
  });
  if (!res.ok) throw new Error(`Dispatch failed: ${res.statusText}`);
  return res.json();
}
export function vectorIndex(domain, primitive, modifier) {
  return (
    Domain.indexOf(domain) * 100 +
    Primitive.indexOf(primitive) * 10 +
    Modifier.indexOf(modifier)
  );
}
