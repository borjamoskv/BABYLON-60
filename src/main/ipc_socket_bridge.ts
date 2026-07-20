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
  private socketPath = '/tmp/babylon60_igor.sock';
  private client: net.Socket | null = null;
  private buffer: string = '';

  public connect(): void {
    this.client = net.createConnection(this.socketPath, () => {
      console.log(`[C5-REAL] Electron connected to Agent Igor IPC at ${this.socketPath}`);
    });

    this.client.on('error', (err) => {
      throw new Error(`[C5-REAL] FATAL: IPC Connection Error. Fail-Fast Triggered. ${err.message}`);
    });

    this.client.on('data', (data) => {
      this.buffer += data.toString();
      const lines = this.buffer.split('\n');
      this.buffer = lines.pop() || '';
      for (const line of lines) {
        if (line.trim()) {
          console.log('[C5-REAL] Parsed Agent Igor NDJSON:', JSON.parse(line));
        }
      }
    });
  }

  public sendPayload(payload: IpcPayload): void {
    if (this.client && !this.client.destroyed) {
      this.client.write(JSON.stringify(payload) + '\n');
    } else {
      throw new Error('[C5-REAL] FATAL: Cannot send payload. IPC socket destroyed.');
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
