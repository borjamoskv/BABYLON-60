import { useSyncExternalStore } from 'react';

export type HashRoute =
  | { name: 'overview' }
  | { name: 'decisions'; decisionId?: string }
  | { name: 'proof'; decisionId?: string }
  | { name: 'targets' };

function parseHash(hash: string): HashRoute {
  const normalized = hash.replace(/^#\/?/, '');

  if (!normalized) {
    return { name: 'overview' };
  }

  const [section, decisionId] = normalized.split('/');

  if (section === 'decisions') {
    return { name: 'decisions', decisionId };
  }

  if (section === 'proofs') {
    return { name: 'proof', decisionId };
  }

  if (section === 'targets') {
    return { name: 'targets' };
  }

  return { name: 'overview' };
}

let cachedHash = '';
let cachedRoute: HashRoute = { name: 'overview' };

function getSnapshot() {
  if (typeof window === 'undefined') {
    return cachedRoute;
  }

  const nextHash = window.location.hash;
  if (nextHash === cachedHash) {
    return cachedRoute;
  }

  cachedHash = nextHash;
  cachedRoute = parseHash(nextHash);
  return cachedRoute;
}

function subscribe(callback: () => void) {
  window.addEventListener('hashchange', callback);
  return () => window.removeEventListener('hashchange', callback);
}

export function routeHref(route: HashRoute) {
  if (route.name === 'overview') {
    return '#/';
  }

  if (route.name === 'proof') {
    return route.decisionId ? `#/proofs/${route.decisionId}` : '#/proofs';
  }

  return route.decisionId ? `#/decisions/${route.decisionId}` : '#/decisions';
}

export function decisionHref(decisionId: string) {
  return routeHref({ name: 'decisions', decisionId });
}

export function proofHref(decisionId: string) {
  return routeHref({ name: 'proof', decisionId });
}

export function replaceHash(hash: string) {
  const nextUrl = `${window.location.pathname}${window.location.search}${hash}`;
  window.history.replaceState(null, '', nextUrl);
  window.dispatchEvent(new HashChangeEvent('hashchange'));
}

export function useHashRoute() {
  return useSyncExternalStore(subscribe, getSnapshot, () => ({ name: 'overview' } as HashRoute));
}
