// === Twin Forge — Main Entry Point ===
import './styles/index.css';
import * as monaco from 'monaco-editor';
import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';
import { MISSIONS, ACHIEVEMENTS } from './data/missions.js';
import { storage } from './utils/storage.js';
import { runJS, runCanvasJS, usesCanvas } from './engine/js-runner.js';
import { runPython, isPyodideLoaded, isPyodideLoading } from './engine/py-runner.js';

// === Monaco Workers ===
self.MonacoEnvironment = {
  getWorker(_, label) {
    if (label === 'json') return new jsonWorker();
    if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker();
    if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker();
    if (label === 'typescript' || label === 'javascript') return new tsWorker();
    return new editorWorker();
  }
};

// === State ===
let activeProfile = null;
let editor = null;
let currentMission = null;
let currentLang = 'javascript';
let currentTab = 'missions';
let consoleLines = 0;

// === DOM ===
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const splash = $('#splash');
const ide = $('#ide');
const editorContainer = $('#editor-container');
const consoleOutput = $('#console-output');
const consoleCount = $('#console-count');
const langSelect = $('#lang-select');
const sidebarContent = $('#sidebar-content');
const canvasPreview = $('#canvas-preview');
const gameCanvas = $('#game-canvas');
const toolbarName = $('#toolbar-name');
const toolbarAvatar = $('#toolbar-avatar');

// === Profile Selection ===
$$('.splash__card').forEach(card => {
  card.addEventListener('click', () => selectProfile(card.dataset.profile));
});

function selectProfile(profile) {
  activeProfile = profile;
  storage.setProfile(profile);
  document.documentElement.setAttribute('data-theme', profile);
  toolbarName.textContent = profile === 'martina' ? 'Martina' : 'Pablo';
  toolbarAvatar.textContent = profile === 'martina' ? '👩‍💻' : '👨‍💻';

  splash.style.animation = 'fadeOut 0.4s ease-out forwards';
  setTimeout(() => {
    splash.style.display = 'none';
    ide.classList.add('active');
    initEditor();
    renderSidebar();
    checkSessionAchievements();
  }, 400);
}

// Auto-login
const savedProfile = storage.getProfile();
if (savedProfile) selectProfile(savedProfile);

// === Monaco Init ===
function initEditor() {
  monaco.editor.defineTheme('twinforge-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A6A6A', fontStyle: 'italic' },
      { token: 'keyword', foreground: activeProfile === 'martina' ? 'A855F7' : '06B6D4' },
      { token: 'string', foreground: activeProfile === 'martina' ? 'EC4899' : 'F97316' },
      { token: 'number', foreground: '22C55E' },
    ],
    colors: {
      'editor.background': '#0A0A0A',
      'editor.foreground': '#F0F0F0',
      'editor.lineHighlightBackground': '#1A1A1A',
      'editor.selectionBackground': activeProfile === 'martina' ? '#A855F730' : '#06B6D430',
      'editorCursor.foreground': activeProfile === 'martina' ? '#A855F7' : '#06B6D4',
      'editorLineNumber.foreground': '#444444',
      'editorLineNumber.activeForeground': activeProfile === 'martina' ? '#A855F7' : '#06B6D4',
    }
  });

  const welcomeCode = [
    '// ¡Bienvenido/a a Twin Forge! 🔧',
    '// Selecciona una misión en el panel izquierdo',
    '// o escribe tu propio código aquí.',
    '',
    'console.log("¡Hola, ' + (activeProfile === 'martina' ? 'Martina' : 'Pablo') + '!");',
    ''
  ].join('\n');

  editor = monaco.editor.create(editorContainer, {
    value: welcomeCode,
    language: 'javascript',
    theme: 'twinforge-dark',
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: 14,
    lineHeight: 22,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 2,
    wordWrap: 'on',
    padding: { top: 12 },
    bracketPairColorization: { enabled: true },
    smoothScrolling: true,
    cursorBlinking: 'smooth',
    cursorSmoothCaretAnimation: 'on',
  });

  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => runCode());
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saveCurrentFile());

  loadMission(MISSIONS[0]);
}

// === Language ===
langSelect.addEventListener('change', () => {
  currentLang = langSelect.value;
  const lang = currentLang === 'python' ? 'python' : currentLang === 'html' ? 'html' : 'javascript';
  monaco.editor.setModelLanguage(editor.getModel(), lang);
});

// === Run ===
$('#btn-run').addEventListener('click', runCode);

async function runCode() {
  const code = editor.getValue();
  const runBtn = $('#btn-run');
  runBtn.textContent = '⏳ ...';
  runBtn.disabled = true;

  let result;
  if (currentLang === 'python') {
    if (!isPyodideLoaded()) {
      addConsoleLine('system', '🐍 Cargando Python... (puede tardar unos segundos)');
    }
    result = await runPython(code);
  } else if (currentLang === 'html') {
    addConsoleLine('system', '🌐 Vista previa HTML');
    const blob = new Blob([code], { type: 'text/html' });
    window.open(URL.createObjectURL(blob), '_blank', 'width=600,height=400');
    result = { success: true, logs: [{ type: 'info', text: 'HTML abierto en nueva ventana' }] };
  } else if (usesCanvas(code)) {
    canvasPreview.classList.add('visible');
    gameCanvas.width = 320;
    gameCanvas.height = 240;
    result = runCanvasJS(code, gameCanvas);
  } else {
    result = await runJS(code);
  }

  if (result.logs) {
    result.logs.forEach(l => addConsoleLine(l.type, l.text));
  }

  // Stats
  const data = storage.getProfileData(activeProfile);
  const stats = data.stats;
  stats.totalRuns = (stats.totalRuns || 0) + 1;
  stats.totalLines = (stats.totalLines || 0) + code.split('\n').length;
  stats.errorFreeStreak = result.success ? (stats.errorFreeStreak || 0) + 1 : 0;
  storage.updateStats(activeProfile, stats);

  checkRunAchievements(result);

  // Validate mission
  if (currentMission && result.success) {
    try {
      const m = MISSIONS.find(m => m.id === currentMission.id);
      if (m && m.validate(result.logs)) completeMission(currentMission.id);
    } catch {}
  }

  runBtn.textContent = '▶ Ejecutar';
  runBtn.disabled = false;
}

// === Console ===
function addConsoleLine(type, text) {
  const line = document.createElement('div');
  line.className = `console__line console__line--${type}`;
  const time = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  line.innerHTML = `<span class="console__timestamp">${time}</span>${escapeHTML(text)}`;
  consoleOutput.appendChild(line);
  consoleOutput.scrollTop = consoleOutput.scrollHeight;
  consoleLines++;
  consoleCount.textContent = consoleLines;
}

function escapeHTML(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

$('#btn-clear').addEventListener('click', () => {
  consoleOutput.innerHTML = '';
  consoleLines = 0;
  consoleCount.textContent = '0';
});

// === Sidebar ===
$$('.sidebar__tab').forEach(tab => {
  tab.addEventListener('click', () => {
    $$('.sidebar__tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.dataset.tab;
    renderSidebar();
  });
});

function renderSidebar() {
  if (currentTab === 'missions') renderMissions();
  else if (currentTab === 'files') renderFiles();
  else if (currentTab === 'achievements') renderAchievements();
}

function renderMissions() {
  const data = storage.getProfileData(activeProfile);
  const completed = data.completedMissions || [];

  let html = '<div class="mission-list">';
  MISSIONS.forEach(m => {
    const isActive = currentMission?.id === m.id;
    const isDone = completed.includes(m.id);
    html += `<div class="mission-item ${isActive ? 'active' : ''} ${isDone ? 'completed' : ''}" data-mission-id="${m.id}">
      <span class="mission-item__icon">${m.icon}</span>
      <div class="mission-item__info">
        <div class="mission-item__title">${m.title}</div>
        <div class="mission-item__lang">${m.lang}</div>
      </div>
      ${isDone ? '<span class="mission-item__check">✓</span>' : ''}
    </div>`;
  });
  html += '</div>';

  // Mission detail
  if (currentMission) {
    html += `<div class="mission-detail visible">
      <div class="mission-detail__title">${currentMission.icon} ${currentMission.title}</div>
      <div class="mission-detail__desc">${currentMission.description}</div>
      <button class="mission-detail__hint-btn" id="hint-btn">💡 Pista</button>
      <div class="mission-detail__hint" id="hint-text"></div>
    </div>`;
  }

  sidebarContent.innerHTML = html;

  // Hint handler
  let hintLevel = 0;
  const hintBtn = sidebarContent.querySelector('#hint-btn');
  const hintText = sidebarContent.querySelector('#hint-text');
  if (hintBtn && currentMission) {
    hintBtn.addEventListener('click', () => {
      if (hintLevel < currentMission.hints.length) {
        hintText.textContent = currentMission.hints[hintLevel];
        hintText.classList.add('visible');
        hintLevel++;
      }
    });
  }

  // Mission click handlers
  sidebarContent.querySelectorAll('.mission-item').forEach(item => {
    item.addEventListener('click', () => {
      const id = parseInt(item.dataset.missionId);
      const mission = MISSIONS.find(m => m.id === id);
      if (mission) loadMission(mission);
    });
  });
}

function renderFiles() {
  const data = storage.getProfileData(activeProfile);
  const files = Object.keys(data.files || {});
  if (files.length === 0) {
    sidebarContent.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;padding:16px;text-align:center">Aún no has guardado ningún archivo.<br>Usa 💾 Guardar para guardar tu código.</div>';
    return;
  }
  sidebarContent.innerHTML = files.map(f => `<div class="file-item" data-file="${f}"><span class="file-item__icon">📄</span>${f}</div>`).join('');
  sidebarContent.querySelectorAll('.file-item').forEach(item => {
    item.addEventListener('click', () => {
      const content = storage.getFile(activeProfile, item.dataset.file);
      if (content) { editor.setValue(content); currentMission = null; }
    });
  });
}

function renderAchievements() {
  const data = storage.getProfileData(activeProfile);
  const unlocked = data.achievements || [];
  sidebarContent.innerHTML = '<div class="mission-list">' + ACHIEVEMENTS.map(a => {
    const isUnlocked = unlocked.includes(a.id);
    return `<div class="mission-item ${isUnlocked ? '' : 'completed'}">
      <span class="mission-item__icon">${isUnlocked ? a.icon : '🔒'}</span>
      <div class="mission-item__info">
        <div class="mission-item__title">${a.name}</div>
        <div class="mission-item__lang">${a.desc}</div>
      </div>
    </div>`;
  }).join('') + '</div>';
}

// === Load Mission ===
function loadMission(mission) {
  currentMission = mission;
  currentLang = mission.lang;
  langSelect.value = mission.lang === 'html' ? 'html' : mission.lang === 'python' ? 'python' : 'javascript';
  const monacoLang = mission.lang === 'python' ? 'python' : mission.lang === 'html' ? 'html' : 'javascript';
  monaco.editor.setModelLanguage(editor.getModel(), monacoLang);
  const saved = storage.getFile(activeProfile, `mission_${mission.id}`);
  editor.setValue(saved || mission.template);
  if (!usesCanvas(mission.template)) canvasPreview.classList.remove('visible');
  renderSidebar();
  addConsoleLine('system', `📋 Misión ${mission.id}: ${mission.title}`);
}

// === Complete Mission ===
function completeMission(missionId) {
  const data = storage.completeMission(activeProfile, missionId);
  addConsoleLine('system', '🎉 ¡Misión completada!');
  const completed = data.completedMissions;
  if (completed.length >= 5) tryUnlockAchievement('mission_5');
  if (completed.length >= 10) tryUnlockAchievement('mission_10');
  if (completed.length >= MISSIONS.length) tryUnlockAchievement('mission_all');
  const mission = MISSIONS.find(m => m.id === missionId);
  if (mission?.lang === 'python') tryUnlockAchievement('pythonista');
  if (missionId === 7) tryUnlockAchievement('artist');
  if (missionId === 8) tryUnlockAchievement('game_dev');
  const otherProfile = activeProfile === 'martina' ? 'pablo' : 'martina';
  const otherData = storage.getProfileData(otherProfile);
  if (otherData.completedMissions.includes(missionId)) tryUnlockAchievement('twin_sync');
  renderSidebar();
}

// === Achievements ===
function tryUnlockAchievement(id) {
  const isNew = storage.unlockAchievement(activeProfile, id);
  if (isNew) {
    const ach = ACHIEVEMENTS.find(a => a.id === id);
    if (ach) showAchievementToast(ach);
  }
}

function showAchievementToast(achievement) {
  const toast = document.createElement('div');
  toast.className = 'achievement-toast';
  toast.innerHTML = `
    <div class="achievement-toast__icon">${achievement.icon}</div>
    <div class="achievement-toast__text">
      <span class="achievement-toast__label">¡Logro Desbloqueado!</span>
      <span class="achievement-toast__name">${achievement.name}</span>
    </div>`;
  document.body.appendChild(toast);

  for (let i = 0; i < 12; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.textContent = ['✨', '⭐', '🔥', '💫'][Math.floor(Math.random() * 4)];
    p.style.cssText = `position:fixed;top:60px;right:${80 + Math.random() * 100}px;z-index:1999;font-size:1rem;pointer-events:none;animation:particleFly 1s ease-out forwards;--dx:${(Math.random() - 0.5) * 200}px;--dy:${(Math.random() - 0.5) * 200}px`;
    document.body.appendChild(p);
    setTimeout(() => p.remove(), 1000);
  }
  setTimeout(() => toast.remove(), 4500);
}

function checkRunAchievements(result) {
  const stats = storage.getProfileData(activeProfile).stats;
  if (stats.totalRuns === 1) tryUnlockAchievement('first_run');
  if (stats.errorFreeStreak >= 5) tryUnlockAchievement('no_errors_5');
  if (stats.totalLines >= 1000) tryUnlockAchievement('hacker');
  const hour = new Date().getHours();
  if (hour >= 23 || hour < 5) tryUnlockAchievement('night_owl');
  if (hour >= 5 && hour < 8) tryUnlockAchievement('early_bird');
  if (currentMission) {
    const current = editor.getValue();
    if (current !== currentMission.template && current.length > currentMission.template.length + 10)
      tryUnlockAchievement('custom_code');
  }
}

function checkSessionAchievements() {
  const stats = storage.getProfileData(activeProfile).stats;
  if (!stats.sessionStart) {
    storage.updateStats(activeProfile, { sessionStart: Date.now() });
  } else if (Date.now() - stats.sessionStart > 3600000) {
    tryUnlockAchievement('marathon');
  }
}

// === Save ===
$('#btn-save').addEventListener('click', saveCurrentFile);
function saveCurrentFile() {
  const code = editor.getValue();
  const filename = currentMission ? `mission_${currentMission.id}` : `archivo_${Date.now()}`;
  storage.saveFile(activeProfile, filename, code);
  addConsoleLine('system', `💾 Guardado: ${filename}`);
}

// === Toolbar Brand ===
$('#toolbar-brand').addEventListener('click', () => {
  if (confirm('¿Volver a la pantalla de inicio?')) {
    storage.setProfile(null);
    location.reload();
  }
});

// === Mobile menu ===
$('#btn-menu').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

// === Resize Handle ===
const resizeHandle = $('#resize-handle');
const consolePanel = $('#console-panel');
let isResizing = false;

resizeHandle.addEventListener('mousedown', () => {
  isResizing = true;
  resizeHandle.classList.add('dragging');
  const onMove = (e) => {
    if (!isResizing) return;
    const rect = $('.ide__main').getBoundingClientRect();
    consolePanel.style.height = Math.max(80, Math.min(rect.bottom - e.clientY, rect.height * 0.6)) + 'px';
  };
  const onUp = () => {
    isResizing = false;
    resizeHandle.classList.remove('dragging');
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
});

// Touch resize
resizeHandle.addEventListener('touchstart', () => {
  isResizing = true;
  const onMove = (e) => {
    if (!isResizing) return;
    const touch = e.touches[0];
    const rect = $('.ide__main').getBoundingClientRect();
    consolePanel.style.height = Math.max(80, Math.min(rect.bottom - touch.clientY, rect.height * 0.6)) + 'px';
  };
  const onEnd = () => {
    isResizing = false;
    document.removeEventListener('touchmove', onMove);
    document.removeEventListener('touchend', onEnd);
  };
  document.addEventListener('touchmove', onMove);
  document.addEventListener('touchend', onEnd);
});

// === Fade out keyframe ===
const style = document.createElement('style');
style.textContent = '@keyframes fadeOut{from{opacity:1}to{opacity:0}}@keyframes particleFly{0%{opacity:1;transform:translate(0,0) scale(1)}100%{opacity:0;transform:translate(var(--dx),var(--dy)) scale(0)}}';
document.head.appendChild(style);
