import { useRef, useCallback } from "react";

// Deep Topological Hash computation for DOM nodes (Zero-Allocation Exergy Optimized)
export function computeStructuralHash(element: HTMLElement | null): number {
  if (!element || typeof document === "undefined") return 0;

  let hash = 5381;

  // Inline rolling hash to eliminate O(N) string concatenation and GC friction
  const hashString = (str: string) => {
    for (let i = 0; i < str.length; i++) {
      hash = (hash * 33) ^ str.charCodeAt(i);
    }
  };

  // O(N) Native Tree Traversal
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_ELEMENT,
    null,
  );

  hashString(element.nodeName);
  if (element.id) hashString(element.id);
  if (element.className) hashString(element.className);

  let currentNode = walker.nextNode();
  while (currentNode) {
    const el = currentNode as HTMLElement;
    hashString(el.nodeName);
    if (el.id) hashString(el.id);
    if (el.className) hashString(el.className);
    currentNode = walker.nextNode();
  }

  return hash >>> 0; // Force unsigned 32-bit integer for deterministic comparisons
}

/**
 * CTRE-DOM (Commit-Time Reconciliation Engine)
 * Implements Optimistic Concurrency Control for React DOM hydration.
 * Ensures that high-latency stochastic decision loops (like AI renders)
 * do not overwrite a structurally mutated DOM.
 */
export function useCTREGuardian(
  targetRef: React.RefObject<HTMLElement | null>,
) {
  const expectedHashRef = useRef<number>(0);

  // t0: Capture the structural state (Snapshot UI Graph)
  const captureState = useCallback(() => {
    expectedHashRef.current = computeStructuralHash(targetRef.current);
  }, [targetRef]);

  // t1: CTRE intercepts the action
  const atomicCommit = useCallback(
    (mutationFn: () => void): boolean => {
      const currentHash = computeStructuralHash(targetRef.current);

      // Verificación de Isomorfismo Discreto
      if (currentHash !== expectedHashRef.current) {
        console.warn(
          "[CTRE] Structural mutation detected under observation. Safe Abort Rollback.",
        );
        return false;
      }

      // Inyección Mecánica Atómica inmediata
      mutationFn();
      return true; // Transacción confirmada
    },
    [targetRef],
  );

  return { captureState, atomicCommit };
}
