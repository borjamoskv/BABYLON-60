import * as net from 'net';
import { ipcMain, WebContents } from 'electron';
import { StringDecoder } from 'string_decoder';

export interface IpcPayload {
  type: 'AST' | 'AOM' | 'CMD' | 'HEARTBEAT';
  data: Record<string, unknown>;
  file?: string;
}

/**
 * C5-REAL: ELECTRON-PYTHON BRIDGING (IPC PURITY - Ω44)
 * Conecta el Main Process de Electron (Node.js) con el Socket Unix del Agent Igor (Python).
 */
export class IpcSocketBridge {
  private socketPath: string;
  private client: net.Socket | null = null;
  private webContents: WebContents | null = null;
  private buffer: string = '';
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private decoder = new StringDecoder('utf8');
  
  // Límite de seguridad termodinámica para la cache NDJSON (10MB)
  private readonly MAX_BUFFER_SIZE = 10 * 1024 * 1024; 

  constructor() {
    if (!process.env.CORTEX_IPC_SOCKET) {
      console.error('[C5-REAL] FATAL (Ω14): CORTEX_IPC_SOCKET no está definido en el entorno. Prohibido hardcodear rutas.');
      process.kill(process.pid, 'SIGKILL');
    }
    // Asignación segura garantizada por la purga de arriba
    this.socketPath = process.env.CORTEX_IPC_SOCKET as string;
  }

  /**
   * Enlaza el puente bidireccional con el Renderer para cumplir Ω44.
   */
  public setWebContents(contents: WebContents): void {
    this.webContents = contents;
  }

  public connect(): void {
    this.client = net.createConnection(this.socketPath, () => {
      console.log(`[C5-REAL] Electron connected to Agent Igor IPC at ${this.socketPath}`);
      
      // Invariante Ω43: Heartbeat activo (Liveness)
      this.heartbeatTimer = setInterval(() => {
        this.sendPayload({ type: 'HEARTBEAT', data: { timestamp: Date.now() } });
      }, 5000);
    });

    // Invariante Ω26: Fallo Inmediato
    this.client.on('error', (err) => {
      console.error(`[C5-REAL] FATAL (Ω26): IPC Connection Error. Fail-Fast Triggered. ${err.message}`);
      process.kill(process.pid, 'SIGKILL');
    });

    // Invariante Ω43: Prevención Zombie
    this.client.on('end', () => {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
      console.error(`[C5-REAL] FATAL (Ω43): Python socket cerró la conexión (end). Zombie IPC prevenido. Ejecutando SIGKILL.`);
      process.kill(process.pid, 'SIGKILL');
    });

    this.client.on('close', (hadError) => {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
      console.error(`[C5-REAL] FATAL (Ω43): Python socket cerrado (close). Error: ${hadError}. Purga atómica.`);
      process.kill(process.pid, 'SIGKILL');
    });

    // Invariante Ω45: Fragmentación NDJSON y Prevención de Corrupción UTF-8
    this.client.on('data', (data) => {
      // Uso de StringDecoder para evitar corrupción de caracteres multi-byte en bordes TCP
      this.buffer += this.decoder.write(data);
      
      // Control de OOM
      if (this.buffer.length > this.MAX_BUFFER_SIZE) {
        console.error(`[C5-REAL] FATAL (Ω45): NDJSON Buffer overflow (>${this.MAX_BUFFER_SIZE} bytes).`);
        process.kill(process.pid, 'SIGKILL');
      }

      const lines = this.buffer.split('\n');
      this.buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim()) {
          try {
            const payload = JSON.parse(line);
            if (this.webContents && !this.webContents.isDestroyed()) {
              this.webContents.send('agent:receive-response', payload);
            } else {
              console.warn('[C5-REAL] Anergía: WebContents inyectado no existe o fue destruido. Payload descartado.');
            }
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
      try {
        const serialized = JSON.stringify(payload);
        this.client.write(serialized + '\n');
      } catch (e) {
        console.error(`[C5-REAL] FATAL (Ω26): JSON Stringify Error (Circular Reference). ${e instanceof Error ? e.message : 'Unknown'}`);
        process.kill(process.pid, 'SIGKILL');
      }
    } else {
      console.error('[C5-REAL] FATAL (Ω43): Cannot send payload. IPC socket destroyed o desconectado.');
      process.kill(process.pid, 'SIGKILL');
    }
  }

  public setupRendererBindings(): void {
    // Purga de eventos previos para prevenir fugas de memoria y duplicación O(N^2)
    ipcMain.removeAllListeners('agent:send-ast');
    ipcMain.removeAllListeners('agent:send-aom');
    ipcMain.removeAllListeners('agent:send-cmd');

    ipcMain.on('agent:send-ast', (event, astData: Record<string, unknown>) => {
      this.sendPayload({ type: 'AST', data: astData });
    });
    
    ipcMain.on('agent:send-aom', (event, aomData: Record<string, unknown>) => {
      this.sendPayload({ type: 'AOM', data: aomData });
    });

    ipcMain.on('agent:send-cmd', (event, cmdData: Record<string, unknown>) => {
      this.sendPayload({ type: 'CMD', data: cmdData });
    });
  }
}
