import * as net from 'net';
import { ipcMain } from 'electron';

export interface IpcPayload {
  type: 'AST' | 'AOM' | 'CMD';
  data: Record<string, unknown>;
  file?: string;
}

/**
 * C5-REAL: ELECTRON-PYTHON BRIDGING (IPC PURITY)
 * Conecta el Main Process de Electron (Node.js) con el Socket Unix del Agent Igor (Python).
 */
export class IpcSocketBridge {
  private socketPath: string;
  private client: net.Socket | null = null;

  constructor() {
    if (!process.env.CORTEX_IPC_SOCKET) {
      console.error('[C5-REAL] FATAL (Ω14): CORTEX_IPC_SOCKET no está definido en el entorno. Prohibido hardcodear rutas.');
      process.kill(process.pid, 'SIGKILL');
    }
    // Asignación segura garantizada por la purga de arriba
    this.socketPath = process.env.CORTEX_IPC_SOCKET as string;
  }
  private buffer: string = '';

  public connect(): void {
    this.client = net.createConnection(this.socketPath, () => {
      console.log(`[C5-REAL] Electron connected to Agent Igor IPC at ${this.socketPath}`);
    });

    this.client.on('error', (err) => {
      console.error(`[C5-REAL] FATAL (Ω26): IPC Connection Error. Fail-Fast Triggered. ${err.message}`);
      process.kill(process.pid, 'SIGKILL');
    });

    this.client.on('data', (data) => {
      this.buffer += data.toString();
      const lines = this.buffer.split('\n');
      this.buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.trim()) {
          try {
            console.log('[C5-REAL] Parsed Agent Igor NDJSON:', JSON.parse(line));
          } catch (e) {
            console.error(`[C5-REAL] FATAL (Ω26): JSON Parse Error en IPC Payload. ${e instanceof Error ? e.message : 'Unknown'}`);
            process.kill(process.pid, 'SIGKILL');
          }
        }
      }
    });
  }

  public sendPayload(payload: IpcPayload): void {
    if (this.client && !this.client.destroyed) {
      this.client.write(JSON.stringify(payload) + '\n');
    } else {
      console.error('[C5-REAL] FATAL (Ω43): Cannot send payload. IPC socket destroyed o desconectado.');
      process.kill(process.pid, 'SIGKILL');
    }
  }

  public setupRendererBindings(): void {
    ipcMain.on('agent:send-ast', (event, astData: Record<string, unknown>) => {
      this.sendPayload({ type: 'AST', data: astData });
    });
    
    ipcMain.on('agent:send-aom', (event, aomData: Record<string, unknown>) => {
      this.sendPayload({ type: 'AOM', data: aomData });
    });
  }
}
