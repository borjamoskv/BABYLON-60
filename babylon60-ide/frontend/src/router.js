// BABYLON60 IDE — Client-side router
const routes = {};
let currentRoute = null;

export function registerRoute(name, renderFn) {
  routes[name] = renderFn;
}

export function navigate(name) {
  if (currentRoute === name) return;
  currentRoute = name;

  // Update sidebar
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.route === name);
  });

  // Render content
  const main = document.getElementById('main-content');
  if (routes[name]) {
    main.innerHTML = '';
    routes[name](main);
  }

  // Update URL hash
  history.replaceState(null, '', `#${name}`);
}

export function getCurrentRoute() {
  return currentRoute;
}

export function getInitialRoute() {
  const hash = location.hash.replace('#', '');
  return hash && routes[hash] ? hash : 'ledger';
}
