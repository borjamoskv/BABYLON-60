// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Main Application Logic (Modularized)
   ═══════════════════════════════════════════════════════════ */

import './style.css';

import { renderThreatGrid } from './data/threats.js';
import { renderLiveFeed } from './components/liveFeed.js';
import { initASLSandbox } from './components/aslSandbox.js';
import { initSovereignCouncil } from './components/sovereignCouncil.js';
import { initEvidenceLedger } from './components/evidenceLedger.js';
import { initLegionSwarm } from './components/legionSwarm.js';
import { initArchitectSwarm } from './components/architectSwarm.js';
import './css/architectSwarm.css';
import { connectTelemetry } from './services/telemetry.js';
import { initRouter as initAuditRouter } from './components/auditReport.js';
import { initCommissionModal } from './components/commissionModal.js';
import './css/commissionModal.css';
import { initBountyFilters } from './components/bountyFilters.js';
import { initNexusGraph } from './components/nexusGraph.js';

import {
  initNavScroll,
  initMobileMenu,
  initSmoothScroll,
  initActiveNavTracking,
  initBackToTop,
  initScrollProgress
} from './ui/navigation.js';

import {
  initScrollReveal,
  animateCounters,
  initScoreBars,
  initLabMetrics,
  initTerminalAnimation,
  initTypingCursor,
  initFooterYear
} from './ui/animations.js';

import {
  initHeroInteractive,
  initParticleGrid
} from './ui/canvas.js';

import {
  initAmbientOrbs,
  initHeroTerminal,
  initLiveThreatCounter,
  initThreatRiskBars,
  initScrollProgressBar,
  initWarpReveal,
} from './ui/sovereign.js';

// ── Initialize ──
document.addEventListener('DOMContentLoaded', () => {
  // Sovereign — structural first
  initAmbientOrbs();
  initScrollProgressBar();

  // Core components
  renderThreatGrid();
  initScrollReveal();
  animateCounters();
  initNavScroll();
  initMobileMenu();
  initHeroInteractive();
  initParticleGrid();
  initActiveNavTracking();
  initScrollProgress();
  initSmoothScroll();
  initScoreBars();
  initLabMetrics();
  initTerminalAnimation();
  renderLiveFeed();
  initASLSandbox();
  initBackToTop();
  initTypingCursor();
  initFooterYear();
  initSovereignCouncil();
  initEvidenceLedger();
  initArchitectSwarm();
  initLegionSwarm();
  connectTelemetry();
  initAuditRouter();
  initCommissionModal();
  initBountyFilters();
  initNexusGraph();

  // Sovereign — visual polish (after all components mounted)
  initHeroTerminal();
  initLiveThreatCounter();
  initThreatRiskBars();
  initWarpReveal();
});

