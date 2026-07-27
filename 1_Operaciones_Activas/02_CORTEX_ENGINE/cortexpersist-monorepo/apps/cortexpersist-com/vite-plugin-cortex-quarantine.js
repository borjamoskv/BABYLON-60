export default function cortexQuarantinePlugin() {
  return {
    name: 'cortex-quarantine',
    enforce: 'pre',
    transform(code, id) {
      if (code.includes('/* @C5-QUARANTINE */')) {
        const isReact = id.endsWith('.tsx') || id.endsWith('.jsx');
        const isAstro = id.endsWith('.astro');
        
        if (isAstro) {
          // For Astro components, inject a fixed overlay to blur/red-tint the component
          return code + `\n<style> :root { filter: grayscale(80%) sepia(50%) hue-rotate(-50deg); transition: filter 2s ease; } </style>\n<div style="position: fixed; inset: 0; z-index: 9999; background: rgba(255, 0, 0, 0.05); pointer-events: none; border: 4px solid red; mix-blend-mode: multiply;"></div>`;
        }
        
        if (isReact) {
          // For React components, wrap the default export or inject a warning block.
          // Since it's hard to reliably wrap the default export without an AST parser,
          // we inject a console warning and a global style hack that targets the root.
          return code + `\n
if (typeof window !== 'undefined') {
  console.warn("☣️ [CORTEX-QUARANTINE] Component " + ${JSON.stringify(id)} + " is quarantined due to hazard > 0.70. Visual isolation applied.");
  const style = document.createElement('style');
  style.innerHTML = 'body { filter: grayscale(100%) blur(1px) !important; background-color: #3a0000 !important; overflow: hidden; pointer-events: none; } body::after { content: "SYSTEM DEGRADED - HAZARD > 0.70"; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); color: red; font-size: 3rem; font-family: monospace; z-index: 99999; font-weight: bold; background: black; padding: 2rem; border: 4px solid red; }';
  document.head.appendChild(style);
}
`;
        }
      }
      return null;
    }
  };
}
