const routes = Object.create(null);
let currentRoute = null;
export function registerRoute(name, renderFn) {
  if (typeof name === 'string' && typeof renderFn === 'function') {
    routes[name] = renderFn;
  }
}
export function navigate(name) {
  if (currentRoute === name) return;
  if (!Object.prototype.hasOwnProperty.call(routes, name) || typeof routes[name] !== 'function') {
    return;
  }
  currentRoute = name;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.route === name);
  });
  const main = document.getElementById('main-content');
  if (main) {
    main.innerHTML = '';
    routes[name](main);
  }
  history.replaceState(null, '', `#${name}`);
}
export function rerender() {
  const main = document.getElementById('main-content');
  if (currentRoute && main && Object.prototype.hasOwnProperty.call(routes, currentRoute) && typeof routes[currentRoute] === 'function') {
    main.innerHTML = '';
    routes[currentRoute](main);
  }
}
export function getCurrentRoute() {
  return currentRoute;
}
export function getInitialRoute() {
  const rawHash = location.hash.replace('#', '');
  const hash = rawHash.replace(/[^a-zA-Z0-9_-]/g, '');
  return hash && Object.prototype.hasOwnProperty.call(routes, hash) && typeof routes[hash] === 'function' ? hash : 'ledger';
}
