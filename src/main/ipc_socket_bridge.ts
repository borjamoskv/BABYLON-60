import * as net from 'net';
import { ipcMain } from 'electron';

/**
 * C5-REAL: ELECTRON-PYTHON BRIDGING (IPC PURITY)
 * Conecta el Main Process de Electron (Node.js) con el Socket Unix del Agent Igor (Python).
 */
export class IpcSocketBridge {
  private socketPath = '/tmp/babylon60_igor.sock';
  private client: net.Socket | null = null;

  public connect(): void {
    this.client = net.createConnection(this.socketPath, () => {
      console.log(`[C5-REAL] Electron connected to Agent Igor IPC at ${this.socketPath}`);
    });

    this.client.on('error', (err) => {
      console.error('[C4-SIM] IPC Connection Error. Is dual_context.py running?', err);
    });

    this.client.on('data', (data) => {
      // Recibe respuestas de inferencia del agente (ej: comandos CDP)
      console.log('[C5-REAL] Data from Agent Igor:', data.toString());
      // Aquí se rutearían comandos hacia ide_cdp_bridge.ts
    });
  }

  public sendPayload(payload: any): void {
    if (this.client && !this.client.destroyed) {
      this.client.write(JSON.stringify(payload) + '\n');
    } else {
      console.warn('[C4-SIM] Cannot send payload: IPC socket destroyed or disconnected.');
    }
  }

  public setupRendererBindings(): void {
    // Escucha eventos del Renderer (React) enviados vía ContextBridge
    ipcMain.on('agent:send-ast', (event, astData) => {
      this.sendPayload({ type: 'AST', data: astData });
    });
    
    // Este evento normalmente provendría de ide_cdp_bridge.ts, pero lo exponemos por si acaso
    ipcMain.on('agent:send-aom', (event, aomData) => {
      this.sendPayload({ type: 'AOM', data: aomData });
    });
  }
}
