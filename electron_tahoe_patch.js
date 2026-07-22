// C5-REAL
// electron_tahoe_patch.js
// Inject at the top of main.js: require('./electron_tahoe_patch.js')

const os = require('os');

function applyTahoeMitigation() {
  const isMac = process.platform === 'darwin';
  if (!isMac) return;

  const releaseParams = os.release().split('.');
  const darwinVersion = parseInt(releaseParams[0], 10);

  // macOS Tahoe corresponds to Darwin kernel version 26
  if (darwinVersion >= 26) {
    console.log("[C5-REAL] macOS Tahoe (Darwin 26+) detected. Disabling hardware acceleration to prevent Jetsam SIGKILL.");
    try {
      const { app } = require('electron');
      if (app) {
        app.disableHardwareAcceleration();
      }
    } catch (e) {
      // Electron app module not available in this context
    }
  }
}

applyTahoeMitigation();
