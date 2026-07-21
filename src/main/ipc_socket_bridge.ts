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
 * Implementa resiliencia total y buffer de peticiones para evitar cuelgues por SIGKILL.
 */
export class IpcSocketBridge {
  private socketPath: string;
  private client: net.Socket | null = null;
  private webContents: WebContents | null = null;
  private buffer: string = '';
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private decoder = new StringDecoder('utf8');
  private payloadQueue: IpcPayload[] = [];
  private retryCount = 0;
  private readonly maxRetries = 30;
  private isConnected = false;

  // Límite de seguridad termodinámica para la cache NDJSON (10MB)
  private readonly MAX_BUFFER_SIZE = 10 * 1024 * 1024; 

  constructor() {
    if (!process.env.CORTEX_IPC_SOCKET) {
      try {
        const fs = require('fs');
        const path = require('path');
        const envPath = path.join(process.cwd(), '.env');
        if (fs.existsSync(envPath)) {
          const envContent = fs.readFileSync(envPath, 'utf8');
          const match = envContent.match(/^CORTEX_IPC_SOCKET=(.*)$/m);
          if (match) {
            process.env.CORTEX_IPC_SOCKET = match[1].trim();
          }
        }
      } catch (e) {
        // ignore
      }
    }

    this.socketPath = process.env.CORTEX_IPC_SOCKET || '/tmp/cortex_ipc.sock';
    process.env.CORTEX_IPC_SOCKET = this.socketPath;
  }

  /**
   * Enlaza el puente bidireccional con el Renderer para cumplir Ω44.
   */
  public setWebContents(contents: WebContents): void {
    this.webContents = contents;
  }

  public connect(): void {
    if (this.isConnected) return;

    this.client = net.createConnection(this.socketPath, () => {
      this.isConnected = true;
      this.retryCount = 0;
      console.log(`[C5-REAL] Electron connected to Agent Igor IPC at ${this.socketPath}`);
      
      // Vaciar cola de peticiones pendientes acumuladas durante el arranque
      while (this.payloadQueue.length > 0) {
        const pending = this.payloadQueue.shift();
        if (pending) this.sendPayload(pending);
      }

      // Invariante Ω43: Heartbeat activo (Liveness)
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = setInterval(() => {
        this.sendPayload({ type: 'HEARTBEAT', data: { timestamp: Date.now() } });
      }, 5000);
    });

    this.client.on('error', (err) => {
      if (!this.isConnected && this.retryCount < this.maxRetries) {
        this.retryCount++;
        console.warn(`[C5-REAL] IPC socket non-ready (${err.message}). Retrying connection (${this.retryCount}/${this.maxRetries})...`);
        setTimeout(() => this.connect(), 1000);
        return;
      }

      console.warn(`[C5-REAL] IPC Connection Warning after ${this.retryCount} retries: ${err.message}. Running in offline UI mode.`);
    });

    // Invariante Ω43: Prevención Zombie
    this.client.on('end', () => {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
      this.isConnected = false;
      this.client = null;
      console.warn(`[C5-REAL] IPC: Python socket connection ended.`);
    });

    this.client.on('close', (hadError) => {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
      this.isConnected = false;
      this.client = null;
      if (hadError) {
        console.warn(`[C5-REAL] IPC: Socket closed with error. Will attempt auto-reconnect.`);
        setTimeout(() => this.connect(), 2000);
      }
    });

    // Invariante Ω45: Fragmentación NDJSON y Prevención de Corrupción UTF-8
    this.client.on('data', (data) => {
      this.buffer += this.decoder.write(data);
      
      if (this.buffer.length > this.MAX_BUFFER_SIZE) {
        console.warn(`[C5-REAL] Warning: NDJSON Buffer overflow (>${this.MAX_BUFFER_SIZE} bytes). Clearing buffer.`);
        this.buffer = '';
        return;
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
            console.warn(`[C5-REAL] NDJSON Stream Warning: Ignored malformed payload chunk. ${e instanceof Error ? e.message : 'Unknown'}`);
          }
        }
      }
    });
  }

  public sendPayload(payload: IpcPayload): void {
    if (this.client && !this.client.destroyed && this.isConnected) {
      try {
        const serialized = JSON.stringify(payload);
        this.client.write(serialized + '\n');
      } catch (e) {
        console.warn(`[C5-REAL] Warning: Failed to serialize IPC payload: ${e instanceof Error ? e.message : 'Unknown'}`);
      }
    } else {
      // Si el socket aún no está listo, guardar en cola para transmisión post-conexión
      if (this.payloadQueue.length < 200) {
        this.payloadQueue.push(payload);
      }
      if (!this.isConnected && this.retryCount === 0) {
        this.connect();
      }
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
