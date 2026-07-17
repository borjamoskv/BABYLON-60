// BABYLON60 IDE — Client-side router (3-Zone Architecture)
const routes = {};
let currentRoute = null;

export function registerRoute(name, renderFn) {
  routes[name] = renderFn;
}

export function navigate(name) {
  if (!routes[name]) return;
  if (currentRoute === name) return;
  currentRoute = name;

  // Render content into focus-zone body
  const main = document.getElementById('main-content');
  if (routes[name]) {
    main.innerHTML = '';
    routes[name](main);
  }

  // Update URL hash (no page reload)
  history.replaceState(null, '', `#${name}`);
}

export function getCurrentRoute() {
  return currentRoute;
}

export function getInitialRoute() {
  const hash = location.hash.replace('#', '');
  return hash && routes[hash] ? hash : 'canvas';
}
